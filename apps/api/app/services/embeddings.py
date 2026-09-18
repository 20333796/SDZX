import math
from collections.abc import Sequence
from typing import Protocol

import httpx

from app.config import Settings, get_settings


class EmbeddingError(RuntimeError):
    pass


class EmbeddingProvider(Protocol):
    model_name: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OllamaEmbeddingProvider:
    def __init__(self, base_url: str, model_name: str, timeout_seconds: int):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = httpx.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model_name, "input": list(texts)},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise EmbeddingError("Embedding service is unavailable") from error
        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingError("Embedding service returned an invalid response")
        vectors: list[list[float]] = []
        dimension: int | None = None
        for vector in embeddings:
            if not isinstance(vector, list) or not vector or not all(isinstance(value, (int, float)) for value in vector):
                raise EmbeddingError("Embedding service returned an invalid vector")
            normalized = [float(value) for value in vector]
            if dimension is None:
                dimension = len(normalized)
            elif len(normalized) != dimension:
                raise EmbeddingError("Embedding service returned vectors with different dimensions")
            vectors.append(normalized)
        return vectors


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider | None:
    current = settings or get_settings()
    if not current.embedding_enabled:
        return None
    return OllamaEmbeddingProvider(
        current.embedding_base_url or "",
        current.embedding_model or "",
        current.embedding_timeout_seconds,
    )


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
    if denominator == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / denominator
