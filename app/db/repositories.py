import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentChunk


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_hash(self, file_hash: str) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.file_hash == file_hash)
        )
        return result.scalar_one_or_none()

    async def get(self, document_id: uuid.UUID) -> Document | None:
        return await self.session.get(Document, document_id)

    async def list(self) -> list[Document]:
        result = await self.session.execute(select(Document).order_by(Document.created_at.desc()))
        return list(result.scalars().all())

    async def delete(self, document_id: uuid.UUID) -> bool:
        result = await self.session.execute(delete(Document).where(Document.id == document_id))
        await self.session.commit()
        return result.rowcount > 0


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_many(self, chunks: list[DocumentChunk]) -> None:
        self.session.add_all(chunks)
