from __future__ import annotations

from typing import TYPE_CHECKING

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import LLMConfigurationError
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

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    async def answer(self, question: str, context: str, sources: list[SourceChunk]) -> str:
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es l'assistant officiel de l'Institut Superieur "
                        "d'Informatique (ISI). Reponds en francais, clairement, "
                        "uniquement a partir du contexte fourni. Si le contexte ne "
                        "permet pas de repondre, dis que l'information n'est pas "
                        "disponible dans les documents fournis."
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
        return completion.choices[0].message.content or ""

    @staticmethod
    def _build_user_prompt(question: str, context: str, sources: list[SourceChunk]) -> str:
        source_names = ", ".join(
            f"{source.document_name} p.{source.page_number or '?'}"
            for source in sources
        )
        return (
            f"Question:\n{question}\n\n"
            f"Sources selectionnees:\n{source_names}\n\n"
            f"Contexte documentaire:\n{context}\n\n"
            "Consigne: donne une reponse concise et utile. Ne fabrique aucune information."
        )
