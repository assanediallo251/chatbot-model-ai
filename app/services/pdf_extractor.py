from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader

from app.core.exceptions import InvalidUploadError


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


class PDFExtractor:
    def extract_pages(self, content: bytes) -> list[PageText]:
        try:
            reader = PdfReader(BytesIO(content))
        except Exception as exc:
            raise InvalidUploadError("Le fichier PDF est invalide ou illisible.") from exc

        pages: list[PageText] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(PageText(page_number=index, text=text))

        if not pages:
            raise InvalidUploadError("Aucun texte exploitable n'a ete trouve dans ce PDF.")

        return pages
