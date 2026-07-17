from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import ChatMessage
from app.schemas.chat import ChatResponse
from app.services.embedding_service import EmbeddingService
from app.services.external_search_service import (
    ExternalSearchResult,
    ExternalSearchService,
    external_result_to_source,
)
from app.services.groq_llm_service import GroqLLMService
from app.services.isi_scope import is_isi_question
from app.services.vector_search_service import VectorSearchService, retrieved_to_source


class RAGService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService | None = None,
        llm_service: GroqLLMService | None = None,
        external_search_service: ExternalSearchService | None = None,
    ) -> None:
        self.session = session
        self.embedding_service = embedding_service or EmbeddingService()
        self.llm_service = llm_service or GroqLLMService()
        self.external_search_service = external_search_service or ExternalSearchService()
        self.search_service = VectorSearchService(session)

    async def ask(self, question: str, top_k: int | None = None) -> ChatResponse:
        if not is_isi_question(question):
            answer = (
                "Je suis desole, je peux repondre uniquement aux questions "
                "concernant l'Institut Superieur d'Informatique (ISI)."
            )
            await self._save_chat_message(question, answer, [])
            return ChatResponse(answer=answer, sources=[])

        question_embedding = await self.embedding_service.embed_query(question)
        retrieved_chunks = await self.search_service.search(
            question_embedding,
            top_k or settings.retrieval_top_k,
            only_isi=settings.isi_corpus_filter_enabled,
        )

        document_sources = [retrieved_to_source(item) for item in retrieved_chunks]
        top_score = document_sources[0].score if document_sources else 0.0
        external_results: list[ExternalSearchResult] = []
        if self.external_search_service.should_search(
            question,
            has_document_sources=bool(document_sources),
            top_score=top_score,
        ):
            external_results = await self.external_search_service.search(question)

        external_sources = [
            external_result_to_source(result, index)
            for index, result in enumerate(external_results, start=1)
        ]
        sources = [*external_sources, *document_sources]
        if not sources:
            answer = (
                "Je ne peux repondre qu'a partir des documents ISI officiels "
                f"ou lies a {settings.isi_official_url}. Aucun passage pertinent "
                "n'a ete trouve dans ce perimetre."
            )
        else:
            context = self._build_context(retrieved_chunks, external_results)
            answer = await self.llm_service.answer(question, context, sources)

        await self._save_chat_message(
            question,
            answer,
            [source.model_dump(mode="json") for source in sources],
        )

        return ChatResponse(answer=answer, sources=sources)

    async def _save_chat_message(
        self,
        question: str,
        answer: str,
        sources: list[dict],
    ) -> None:
        self.session.add(
            ChatMessage(
                question=question,
                answer=answer,
                sources=sources,
            )
        )
        await self.session.commit()

    @staticmethod
    def _build_context(
        retrieved_chunks: list,
        external_results: list[ExternalSearchResult],
    ) -> str:
        sections: list[str] = []
        for index, result in enumerate(external_results, start=1):
            sections.append(
                f"[Web {index} | {result.title} | {result.url}]\n"
                f"{result.content}"
            )
        for index, item in enumerate(retrieved_chunks, start=1):
            page = item.chunk.page_number or "?"
            sections.append(
                f"[Document {index} | {item.document.filename} | page {page}]\n"
                f"{item.chunk.content}"
            )
        return "\n\n".join(sections)
