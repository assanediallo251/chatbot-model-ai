import re
from dataclasses import dataclass

from app.core.config import settings
from app.services.pdf_extractor import PageText


@dataclass(frozen=True)
class TextChunk:
    content: str
    page_number: int | None
    token_count: int
    metadata: dict[str, int | str | None]


class TextChunker:
    def __init__(
        self,
        chunk_size: int = settings.chunk_size,
        chunk_overlap: int = settings.chunk_overlap,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: list[PageText]) -> list[TextChunk]:
        chunks: list[TextChunk] = []

        for page in pages:
            cleaned = self.clean_text(page.text)
            if not cleaned:
                continue

            for text in self._split_text(cleaned):
                chunks.append(
                    TextChunk(
                        content=text,
                        page_number=page.page_number,
                        token_count=self._estimate_token_count(text),
                        metadata={
                            "page_number": page.page_number,
                            "strategy": "char_window_with_overlap",
                        },
                    )
                )

        return chunks

    @staticmethod
    def clean_text(text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" *\n *", "\n", text)
        return text.strip()

    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            window = text[start:end]

            if end < len(text):
                boundary = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("? "))
                if boundary > self.chunk_size * 0.55:
                    end = start + boundary + 1
                    window = text[start:end]

            cleaned_window = window.strip()
            if cleaned_window:
                chunks.append(cleaned_window)

            if end >= len(text):
                break
            start = max(end - self.chunk_overlap, start + 1)

        return chunks

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        return max(1, len(re.findall(r"\S+", text)))
