import re
import unicodedata

from sqlalchemy import ColumnElement, or_

from app.core.config import settings
from app.db.models import Document, DocumentChunk

_ISI_WORD_PATTERN = re.compile(r"(?<![a-z0-9])isi(?![a-z0-9])")
_IN_SCOPE_TERMS = {
    "admission",
    "adresse",
    "administration",
    "alumni",
    "bourse",
    "campus",
    "certificat",
    "comptabilite",
    "contact",
    "cout",
    "departement",
    "diplome",
    "directeur",
    "e-learning",
    "ecole",
    "etablissement",
    "filiere",
    "formation",
    "frais",
    "genie",
    "horaire",
    "informatique",
    "inscription",
    "licence",
    "master",
    "mensualite",
    "mission",
    "objectif",
    "paiement",
    "pdg",
    "pedagogie",
    "prix",
    "programme",
    "projet",
    "reseaux",
    "scolarite",
    "stage",
    "tarif",
    "technologie",
}
_OUT_OF_SCOPE_TERMS = {
    "basket",
    "diomaye",
    "election",
    "football",
    "gouvernement",
    "meteo",
    "politique",
    "president",
}


def normalize_scope_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return ascii_text.casefold()


def is_isi_corpus_text(*values: str | None) -> bool:
    text = "\n".join(value or "" for value in values)
    normalized_text = normalize_scope_text(text)

    for keyword in settings.isi_corpus_keyword_list:
        if normalize_scope_text(keyword) in normalized_text:
            return True

    return _ISI_WORD_PATTERN.search(normalized_text) is not None


def is_isi_question(question: str) -> bool:
    normalized_question = normalize_scope_text(question)
    if is_isi_corpus_text(question):
        return True
    if any(term in normalized_question for term in _OUT_OF_SCOPE_TERMS):
        return False
    if any(term in normalized_question for term in _IN_SCOPE_TERMS):
        return True
    return False


def isi_corpus_sql_filter() -> ColumnElement[bool]:
    text_columns = (Document.filename, DocumentChunk.content)
    clauses: list[ColumnElement[bool]] = []

    for keyword in settings.isi_corpus_keyword_list:
        pattern = f"%{keyword}%"
        clauses.extend(column.ilike(pattern) for column in text_columns)

    clauses.extend(column.op("~*")(settings.isi_acronym_regex) for column in text_columns)
    return or_(*clauses)
