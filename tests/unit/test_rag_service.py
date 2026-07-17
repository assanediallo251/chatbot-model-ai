import pytest

from app.services.external_search_service import ExternalSearchResult
from app.services.rag_service import RAGService


class _FakeSession:
    def __init__(self) -> None:
        self.messages = []
        self.committed = False

    def add(self, message) -> None:
        self.messages.append(message)

    async def commit(self) -> None:
        self.committed = True


class _FailingEmbeddingService:
    async def embed_query(self, question: str) -> list[float]:
        raise AssertionError("Out-of-scope questions must not call embeddings")


class _FakeExternalSearchService:
    def should_search(self, question: str, has_document_sources: bool, top_score: float) -> bool:
        return True

    async def search(self, question: str) -> list[ExternalSearchResult]:
        return [
            ExternalSearchResult(
                title="Administration - Groupe ISI",
                url="https://siege.groupeisi.com/administration/",
                content="M. Thierno SAMBE est Directeur General.",
                excerpt="M. Thierno SAMBE est Directeur General.",
                score=1.0,
            )
        ]


@pytest.mark.asyncio
async def test_rag_rejects_out_of_scope_question_without_sources() -> None:
    session = _FakeSession()
    service = RAGService(session=session, embedding_service=_FailingEmbeddingService())

    response = await service.ask("parles moi du president diomaye")

    assert response.sources == []
    assert "uniquement aux questions concernant" in response.answer
    assert session.committed is True
    assert session.messages[0].sources == []


def test_build_context_prioritizes_external_sources() -> None:
    context = RAGService._build_context(
        retrieved_chunks=[],
        external_results=awaitable_external_results(),
    )

    assert context.startswith("[Web 1 | Administration - Groupe ISI")


def awaitable_external_results() -> list[ExternalSearchResult]:
    return [
        ExternalSearchResult(
            title="Administration - Groupe ISI",
            url="https://siege.groupeisi.com/administration/",
            content="M. Thierno SAMBE est Directeur General.",
            excerpt="M. Thierno SAMBE est Directeur General.",
            score=1.0,
        )
    ]
