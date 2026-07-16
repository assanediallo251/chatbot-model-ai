from app.services.pdf_extractor import PageText
from app.services.text_chunker import TextChunker


def test_chunk_pages_splits_long_page_with_overlap() -> None:
    text = " ".join(f"mot{i}" for i in range(180))
    chunker = TextChunker(chunk_size=180, chunk_overlap=30)

    chunks = chunker.chunk_pages([PageText(page_number=3, text=text)])

    assert len(chunks) > 1
    assert all(chunk.page_number == 3 for chunk in chunks)
    assert all(chunk.token_count > 0 for chunk in chunks)
    assert all(len(chunk.content) <= 180 for chunk in chunks)


def test_clean_text_normalizes_spaces_and_newlines() -> None:
    raw_text = "  ISI   \n\n\n  Master 1\tGL  "

    cleaned = TextChunker.clean_text(raw_text)

    assert cleaned == "ISI\n\nMaster 1 GL"
