from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import ChatMessage
from app.schemas.chat import ChatResponse
from app.services.embedding_service import EmbeddingService
from app.services.groq_llm_service import GroqLLMService
from app.services.vector_search_service import VectorSearchService, retrieved_to_source


class RAGService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService | None = None,
        llm_service: GroqLLMService | None = None,
    ) -> None:
        self.session = session
        self.embedding_service = embedding_service or EmbeddingService()
        self.llm_service = llm_service or GroqLLMService()
        self.search_service = VectorSearchService(session)

    async def ask(self, question: str, top_k: int | None = None) -> ChatResponse:
        question_embedding = await self.embedding_service.embed_query(question)
        retrieved_chunks = await self.search_service.search(
            question_embedding,
            top_k or settings.retrieval_top_k,
        )

        sources = [retrieved_to_source(item) for item in retrieved_chunks]
        if not sources:
            answer = (
                "Je ne peux pas repondre avec les documents disponibles, car aucun "
                "passage pertinent n'a ete trouve."
            )
        else:
            context = self._build_context(retrieved_chunks)
            answer = await self.llm_service.answer(question, context, sources)

        self.session.add(
            ChatMessage(
                question=question,
                answer=answer,
                sources=[source.model_dump(mode="json") for source in sources],
            )
        )
        await self.session.commit()

        return ChatResponse(answer=answer, sources=sources)

    @staticmethod
    def _build_context(retrieved_chunks: list) -> str:
        sections: list[str] = []
        for index, item in enumerate(retrieved_chunks, start=1):
            page = item.chunk.page_number or "?"
            sections.append(
                f"[Source {index} | {item.document.filename} | page {page}]\n"
                f"{item.chunk.content}"
            )
        return "\n\n".join(sections)
