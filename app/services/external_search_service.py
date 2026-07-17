from __future__ import annotations

import asyncio
import re
import uuid
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

import httpx

from app.core.config import settings
from app.schemas.chat import SourceChunk
from app.services.isi_scope import is_isi_corpus_text, normalize_scope_text

_TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")
_STOPWORDS = {
    "avec",
    "dans",
    "des",
    "est",
    "les",
    "mon",
    "nous",
    "par",
    "pas",
    "pour",
    "que",
    "qui",
    "sur",
    "une",
    "vous",
}


@dataclass(frozen=True)
class ExternalSearchResult:
    title: str
    url: str
    content: str
    excerpt: str
    score: float


class _HTMLTextExtractor(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    @property
    def title(self) -> str:
        return _clean_text(" ".join(self._title_parts))

    @property
    def text(self) -> str:
        return _clean_text(" ".join(self._text_parts))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg", "noscript"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(_normalize_url(urljoin(self.base_url, href)))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
        else:
            self._text_parts.append(data)


class ExternalSearchService:
    def should_search(self, question: str, has_document_sources: bool, top_score: float) -> bool:
        if not settings.external_search_enabled:
            return False
        if not has_document_sources:
            return True
        if top_score < settings.external_search_min_score:
            return True

        normalized_question = normalize_scope_text(question)
        return any(
            normalize_scope_text(keyword) in normalized_question
            for keyword in settings.external_search_trigger_keyword_list
        )

    async def search(self, question: str) -> list[ExternalSearchResult]:
        queue = list(dict.fromkeys(settings.external_search_seed_url_list))
        visited: set[str] = set()
        results: list[ExternalSearchResult] = _static_official_results(question)
        if results:
            return results[: settings.external_search_max_sources]

        try:
            async with asyncio.timeout(settings.external_search_total_timeout_seconds):
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=settings.external_search_timeout_seconds,
                    headers={"User-Agent": "isi-chatbot-rag/0.1"},
                ) as client:
                    while queue and len(visited) < settings.external_search_max_pages:
                        url = _normalize_url(queue.pop(0))
                        if url in visited or not _is_allowed_url(url):
                            continue
                        visited.add(url)

                        page = await self._fetch_page(client, url)
                        if page is None:
                            continue

                        title, text, links = page
                        if is_isi_corpus_text(title, url, text):
                            score = _score_page(question, title, url, text)
                            if score >= settings.external_search_min_score:
                                results.append(
                                    ExternalSearchResult(
                                        title=title or _host_label(url),
                                        url=url,
                                        content=text[:4000],
                                        excerpt=_excerpt(text),
                                        score=score,
                                    )
                                )

                        for link in links:
                            if (
                                len(queue) + len(visited)
                                >= settings.external_search_max_pages * 3
                            ):
                                break
                            if link not in visited and _is_allowed_url(link):
                                queue.append(link)
        except TimeoutError:
            pass

        results.sort(key=lambda result: result.score, reverse=True)
        return results[: settings.external_search_max_sources]

    @staticmethod
    async def _fetch_page(
        client: httpx.AsyncClient,
        url: str,
    ) -> tuple[str, str, list[str]] | None:
        try:
            response = await asyncio.wait_for(
                client.get(url),
                timeout=settings.external_search_timeout_seconds,
            )
            response.raise_for_status()
        except (TimeoutError, httpx.HTTPError):
            return None

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return None

        parser = _HTMLTextExtractor(str(response.url))
        parser.feed(response.text)
        return parser.title, parser.text, parser.links


def external_result_to_source(result: ExternalSearchResult, index: int) -> SourceChunk:
    document_id = uuid.uuid5(uuid.NAMESPACE_URL, result.url)
    chunk_id = uuid.uuid5(uuid.NAMESPACE_URL, f"{result.url}#{index}")
    title = result.title or _host_label(result.url)
    return SourceChunk(
        document_id=document_id,
        document_name=f"Web - {title}",
        chunk_id=chunk_id,
        page_number=None,
        chunk_index=index,
        score=round(result.score, 4),
        excerpt=result.excerpt,
    )


def _score_page(question: str, title: str, url: str, text: str) -> float:
    query_terms = _tokens(question)
    if not query_terms:
        return 0.0

    normalized_text = normalize_scope_text(f"{title} {url} {text}")
    matches = {term for term in query_terms if term in normalized_text}
    score = len(matches) / len(query_terms)

    normalized_question = normalize_scope_text(question)
    billing_terms = {"tarif", "prix", "cout", "frais", "scolarite", "mensualite", "paiement"}
    if any(term in normalized_question for term in billing_terms):
        if any(term in normalized_text for term in billing_terms):
            score += 0.35

    if "groupeisi" in normalize_scope_text(url):
        score += 0.1

    return min(score, 1.0)


def _static_official_results(question: str) -> list[ExternalSearchResult]:
    normalized_question = normalize_scope_text(question)
    results: list[ExternalSearchResult] = []

    leadership_terms = {"directeur", "direction", "president", "pdg", "responsable"}
    if any(term in normalized_question for term in leadership_terms):
        content = (
            "Page officielle Administration du Groupe ISI. Direction mentionnee: "
            "M. Abdou SAMBE est President du groupe. M. Thierno SAMBE est Directeur "
            "General. Mme Mane DIOP est Directrice Administrative et Financiere. "
            "Mme Aissatou G. DIOMBERA est Directrice des Etudes. La page indique "
            "aussi les contacts officiels: Km1 Avenue Cheikh Anta Diop, Dakar, "
            "+221 33 822 19 81, +221 76 664 85 44, contact@groupeisi.com."
        )
        results.append(
            ExternalSearchResult(
                title="Administration - Groupe ISI",
                url="https://siege.groupeisi.com/administration/",
                content=content,
                excerpt=content,
                score=1.0,
            )
        )

    history_terms = {
        "histoire",
        "historique",
        "presentation",
        "creation",
        "fondation",
        "parcours",
    }
    if any(term in normalized_question for term in history_terms):
        content = (
            "Pages officielles Presentation et Mot du PDG du Groupe ISI. L'Institut "
            "Superieur d'Informatique est situe au Km1 Avenue Cheikh Anta Diop. "
            "Il est sous la tutelle du Ministere de l'Enseignement Superieur prive "
            "et ses diplomes sont controles par l'ANAQ-Sup. La presentation indique "
            "que l'ISI contribue depuis plus de 27 ans a la formation des jeunes "
            "cadres africains, avec 09 campus et plus de trente nationalites. Une "
            "page plus recente du siege mentionne 31 annees d'expertise. Le Groupe "
            "ISI delivre des diplomes de Licence et Master reconnus par l'entreprise, "
            "l'ANAQ-Sup et le CAMES. La presentation mentionne aussi des distinctions: "
            "meilleure academie d'excellence CISCO en Afrique sub-saharienne en 2015, "
            "meilleure ecole IT en 2016, entreprise dynamique et innovante en 2017, "
            "premier prix Resakss data challenge en 2018, meilleure academie Huawei "
            "en 2019."
        )
        results.append(
            ExternalSearchResult(
                title="Presentation - Groupe ISI",
                url="https://www.groupeisi.com/?page_id=47335",
                content=content,
                excerpt=content,
                score=1.0,
            )
        )

    billing_terms = {"tarif", "prix", "cout", "frais", "scolarite", "mensualite", "paiement"}
    if any(term in normalized_question for term in billing_terms):
        content = (
            "Page officielle de paiement et de comptabilite du Groupe ISI. "
            "La page indique que les visiteurs peuvent contacter la comptabilite pour "
            "toute question ou demande d'information. Adresse: KM1 Avenue Cheikh Anta "
            "Diop, Dakar 28110. Telephone: (+221) 33 822 19 81. Autre telephone "
            "mentionne: +221 76 664 85 44. Email: contact@groupeisi.com. "
            "Horaires de comptabilite: lundi a vendredi 08:00 - 13:00 et 15:00 - "
            "18:00; samedi 08:00 - 13:00. La page mentionne le paiement des frais de "
            "scolarite mais ne publie pas de grille tarifaire ni de montants exacts "
            "dans les informations accessibles."
        )
        results.append(
            ExternalSearchResult(
                title="Paiement - Groupe ISI",
                url="https://siege.groupeisi.com/paiement/",
                content=content,
                excerpt=content,
                score=1.0,
            )
        )

    return results


def _tokens(value: str) -> set[str]:
    normalized = normalize_scope_text(value)
    return {
        token
        for token in _TOKEN_PATTERN.findall(normalized)
        if token not in _STOPWORDS
    }


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _excerpt(content: str, limit: int = 550) -> str:
    normalized = _clean_text(content)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_url(url: str) -> str:
    url, _fragment = urldefrag(url)
    return url.rstrip("/")


def _is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.casefold()
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    return any(
        host == domain or host.endswith(f".{domain}")
        for domain in settings.external_search_allowed_domain_list
    )


def _host_label(url: str) -> str:
    return urlparse(url).netloc or url
