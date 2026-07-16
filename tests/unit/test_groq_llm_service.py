from app.schemas.chat import SourceChunk
from app.services.groq_llm_service import GroqLLMService


def test_build_user_prompt_contains_question_context_and_sources() -> None:
    source = SourceChunk(
        document_id="00000000-0000-0000-0000-000000000001",
        document_name="isi.pdf",
        chunk_id="00000000-0000-0000-0000-000000000002",
        page_number=2,
        chunk_index=0,
        score=0.91,
        excerpt="Projet chatbot ISI",
    )

    prompt = GroqLLMService._build_user_prompt(
        question="Quel est l'objectif ?",
        context="Le projet met en place un chatbot intelligent.",
        sources=[source],
    )

    assert "Quel est l'objectif ?" in prompt
    assert "Le projet met en place un chatbot intelligent." in prompt
    assert "isi.pdf p.2" in prompt
    assert "Ne fabrique aucune information" in prompt
