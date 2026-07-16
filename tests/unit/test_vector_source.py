import uuid
from types import SimpleNamespace

from app.services.vector_search_service import RetrievedChunk, retrieved_to_source


def test_retrieved_to_source_limits_excerpt_and_score() -> None:
    document_id = uuid.uuid4()
    chunk_id = uuid.uuid4()
    retrieved = RetrievedChunk(
        chunk=SimpleNamespace(
            id=chunk_id,
            content="A" * 700,
            page_number=1,
            chunk_index=4,
        ),
        document=SimpleNamespace(
            id=document_id,
            filename="brochure.pdf",
        ),
        distance=0.18,
    )

    source = retrieved_to_source(retrieved)

    assert source.document_id == document_id
    assert source.chunk_id == chunk_id
    assert source.document_name == "brochure.pdf"
    assert source.score == 0.82
    assert len(source.excerpt) == 450
    assert source.excerpt.endswith("...")
