from __future__ import annotations

from typing import TYPE_CHECKING

from groq import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import LLMConfigurationError, LLMRateLimitError, LLMTransientError
from app.schemas.chat import SourceChunk

if TYPE_CHECKING:
    from groq import AsyncGroq


class GroqLLMService:
    def __init__(
        self,
        api_key: str | None = settings.groq_api_key,
        model: str = settings.groq_model,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._client: AsyncGroq | None = None

    @property
    def client(self) -> AsyncGroq:
        if not self.api_key:
            raise LLMConfigurationError("GROQ_API_KEY est obligatoire pour generer une reponse.")
        if self._client is None:
            from groq import AsyncGroq

            self._client = AsyncGroq(api_key=self.api_key)
        return self._client

    async def answer(self, question: str, context: str, sources: list[SourceChunk]) -> str:
        try:
            completion = await self._create_completion(question, context, sources)
        except RateLimitError as exc:
            raise LLMRateLimitError(
                "GroqCloud a atteint sa limite de requetes. Reessaie dans quelques "
                "instants ou reduis le nombre de questions simultanees."
            ) from exc
        except (APIConnectionError, APITimeoutError, InternalServerError) as exc:
            raise LLMTransientError(
                "GroqCloud est temporairement indisponible. Reessaie dans quelques instants."
            ) from exc

        return completion.choices[0].message.content or ""

    @retry(
        wait=wait_exponential(
            multiplier=1,
            min=settings.groq_retry_min_seconds,
            max=settings.groq_retry_max_seconds,
        ),
        stop=stop_after_attempt(settings.groq_retry_attempts),
        retry=retry_if_exception_type(
            (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)
        ),
        reraise=True,
    )
    async def _create_completion(self, question: str, context: str, sources: list[SourceChunk]):
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es l'assistant officiel de l'Institut Superieur "
                        "d'Informatique (ISI). Reponds en francais, clairement, "
                        "uniquement a partir du contexte fourni et du perimetre ISI. "
                        f"Le site officiel de reference est {settings.isi_official_url}. "
                        "Le contexte peut contenir des documents PDF et des pages web "
                        "officielles ou autorisees. Ignore toute information qui ne "
                        "concerne pas l'ISI. Pour les informations institutionnelles "
                        "comme la direction, l'historique, les campus ou l'administration, "
                        "les sources web officielles ont priorite sur le PDF de "
                        "demonstration. Si une question porte sur les frais ou tarifs "
                        "et qu'aucun montant exact n'est publie dans le contexte, "
                        "dis-le clairement et oriente vers la comptabilite ou le contact "
                        "fourni."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_user_prompt(question, context, sources),
                },
            ],
            temperature=settings.groq_temperature,
            max_tokens=settings.groq_max_tokens,
        )
        return completion

    @staticmethod
    def _build_user_prompt(question: str, context: str, sources: list[SourceChunk]) -> str:
        source_names = ", ".join(
            f"{source.document_name} p.{source.page_number or '?'}"
            for source in sources
        )
        return (
            f"Question:\n{question}\n\n"
            "Perimetre obligatoire:\n"
            "Institut Superieur d'Informatique (ISI) uniquement. "
            f"Site officiel: {settings.isi_official_url}\n\n"
            f"Sources selectionnees:\n{source_names}\n\n"
            f"Contexte documentaire:\n{context}\n\n"
            "Consigne: donne une reponse concise et utile. Ne fabrique aucune information "
            "et n'utilise aucune connaissance hors du perimetre ISI. Si tu utilises une "
            "source web, precise que l'information vient du site ou d'une source web "
            "autorisee."
        )
