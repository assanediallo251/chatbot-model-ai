import hashlib
import logging
import uuid
from dataclasses import dataclass

import anyio
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidUploadError
from app.db.models import Document, DocumentChunk, DocumentStatus
from app.db.repositories import ChunkRepository, DocumentRepository
from app.db.session import AsyncSessionLocal
from app.services.embedding_service import EmbeddingService
from app.services.pdf_extractor import PDFExtractor
from app.services.text_chunker import TextChunker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResult:
    document: Document
    duplicated: bool


class DocumentIngestionService:
    def __init__(
        self,
        session: AsyncSession,
        extractor: PDFExtractor | None = None,
        chunker: TextChunker | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.session = session
        self.document_repository = DocumentRepository(session)
        self.chunk_repository = ChunkRepository(session)
        self.extractor = extractor or PDFExtractor()
        self.chunker = chunker or TextChunker()
        self.embedding_service = embedding_service or EmbeddingService()

    async def ingest_upload(self, upload: UploadFile) -> IngestionResult:
        result, content = await self.register_upload(upload)
        if result.duplicated or content is None:
            return result
        document = await self.process_document(result.document.id, content)
        return IngestionResult(document=document, duplicated=False)

    async def register_upload(self, upload: UploadFile) -> tuple[IngestionResult, bytes | None]:
        self._validate_upload(upload)
        content = await upload.read()
        self._validate_size(content)

        file_hash = hashlib.sha256(content).hexdigest()
        existing = await self.document_repository.get_by_hash(file_hash)
        if existing:
            return IngestionResult(document=existing, duplicated=True)

        document = Document(
            filename=upload.filename or "document.pdf",
            content_type=upload.content_type or "application/pdf",
            file_hash=file_hash,
            status=DocumentStatus.PROCESSING.value,
        )
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return IngestionResult(document=document, duplicated=False), content

    async def process_document(self, document_id: uuid.UUID, content: bytes) -> Document:
        document = await self.document_repository.get(document_id)
        if not document:
            raise InvalidUploadError("Document introuvable pour l'indexation.")

        try:
            pages = await anyio.to_thread.run_sync(self.extractor.extract_pages, content)
            chunks = await anyio.to_thread.run_sync(self.chunker.chunk_pages, pages)
            if not chunks:
                raise InvalidUploadError("Le PDF ne contient aucun segment indexable.")

            embeddings = await self.embedding_service.embed_texts(
                [chunk.content for chunk in chunks]
            )
            db_chunks = [
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    token_count=chunk.token_count,
                    chunk_metadata=chunk.metadata,
                    embedding=embeddings[index],
                )
                for index, chunk in enumerate(chunks)
            ]
            await self.chunk_repository.create_many(db_chunks)
            document.status = DocumentStatus.INDEXED.value
            document.chunk_count = len(db_chunks)
            document.error_message = None
            await self.session.commit()
            await self.session.refresh(document)
            return document
        except Exception as exc:
            await self.session.rollback()
            stored_document = await self.document_repository.get(document.id)
            if stored_document:
                stored_document.status = DocumentStatus.FAILED.value
                stored_document.error_message = str(exc)
                await self.session.commit()
                await self.session.refresh(stored_document)
                document = stored_document
            raise

    @staticmethod
    def _validate_upload(upload: UploadFile) -> None:
        filename = upload.filename or ""
        content_type = upload.content_type or ""
        if not filename.lower().endswith(".pdf") and content_type != "application/pdf":
            raise InvalidUploadError("Seuls les fichiers PDF sont acceptes.")

    @staticmethod
    def _validate_size(content: bytes) -> None:
        if not content:
            raise InvalidUploadError("Le fichier envoye est vide.")
        if len(content) > settings.max_upload_bytes:
            raise InvalidUploadError(
                f"Le fichier depasse la taille maximale de {settings.max_upload_mb} Mo."
            )


async def ingest_document_in_background(document_id: uuid.UUID, content: bytes) -> None:
    async with AsyncSessionLocal() as session:
        service = DocumentIngestionService(session)
        try:
            await service.process_document(document_id, content)
        except Exception:
            logger.exception("Background ingestion failed for document %s", document_id)
