from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Document, DocumentChunk, DocumentStatus
from app.schemas.chat import SourceChunk
from app.services.isi_scope import isi_corpus_sql_filter


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    document: Document
    distance: float

    @property
    def score(self) -> float:
        return max(0.0, min(1.0, 1.0 - self.distance))


class VectorSearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        embedding: list[float],
        top_k: int,
        only_isi: bool = True,
    ) -> list[RetrievedChunk]:
        distance = DocumentChunk.embedding.cosine_distance(embedding).label("distance")
        statement = (
            select(DocumentChunk, Document, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.status == DocumentStatus.INDEXED.value)
        )
        if only_isi and settings.isi_corpus_filter_enabled:
            statement = statement.where(isi_corpus_sql_filter())

        statement = statement.order_by(distance).limit(top_k)
        rows = (await self.session.execute(statement)).all()
        return [
            RetrievedChunk(chunk=chunk, document=document, distance=float(distance_value))
            for chunk, document, distance_value in rows
        ]


def retrieved_to_source(retrieved: RetrievedChunk) -> SourceChunk:
    return SourceChunk(
        document_id=UUID(str(retrieved.document.id)),
        document_name=retrieved.document.filename,
        chunk_id=UUID(str(retrieved.chunk.id)),
        page_number=retrieved.chunk.page_number,
        chunk_index=retrieved.chunk.chunk_index,
        score=round(retrieved.score, 4),
        excerpt=_excerpt(retrieved.chunk.content),
    )


def _excerpt(content: str, limit: int = 450) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
