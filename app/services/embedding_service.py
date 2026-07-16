from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from functools import lru_cache
from typing import TYPE_CHECKING

import anyio

from app.core.config import settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=2)
def _load_model(model_name: str) -> SentenceTransformer:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class EmbeddingService:
    def __init__(
        self,
        provider: str = settings.embedding_provider,
        model_name: str = settings.embedding_model,
        dimensions: int = settings.embedding_dimensions,
    ) -> None:
        self.provider = provider
        self.model_name = model_name
        self.dimensions = dimensions
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = _load_model(self.model_name)
        return self._model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.provider == "hashing":
            return await anyio.to_thread.run_sync(self._embed_hashing_texts_sync, texts)
        if self.provider == "sentence_transformers":
            return await anyio.to_thread.run_sync(self._embed_sentence_transformer_sync, texts)
        raise ValueError(f"Unsupported embedding provider: {self.provider}")

    async def embed_query(self, question: str) -> list[float]:
        embeddings = await self.embed_texts([question])
        return embeddings[0]

    def _embed_sentence_transformer_sync(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=settings.embedding_batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.astype(float).tolist()

    def _embed_hashing_texts_sync(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_hashing_text_sync(text) for text in texts]

    def _embed_hashing_text_sync(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = self._tokens(text)
        if not tokens:
            return vector

        features = tokens + [
            f"{left}_{right}" for left, right in zip(tokens, tokens[1:], strict=False)
        ]
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            raw = int.from_bytes(digest, byteorder="big", signed=False)
            index = raw % self.dimensions
            sign = 1.0 if raw & 1 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = unicodedata.normalize("NFKD", text.lower())
        ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
        return re.findall(r"[a-z0-9]{2,}", ascii_text)
