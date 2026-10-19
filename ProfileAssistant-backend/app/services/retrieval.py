from dataclasses import dataclass
from math import sqrt
from typing import Protocol

from app.core.config import Config
from app.services.chunking import ProfileChunk


class Embedder(Protocol):
    def embed(self, documents: list[str]): ...

    def query_embed(self, query: str): ...


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: ProfileChunk
    score: float


class ProfileRetriever:
    """An in-memory cosine-similarity index for the small profile document set."""

    def __init__(self, chunks: list[ProfileChunk], embedder: Embedder):
        if not chunks:
            raise ValueError("At least one profile chunk is required.")

        self._chunks = list(chunks)
        self._embedder = embedder
        self._vectors = [self._normalize(vector) for vector in embedder.embed(
            [chunk.text for chunk in self._chunks]
        )]
        if len(self._vectors) != len(self._chunks):
            raise ValueError("The embedder must return one vector per profile chunk.")
        self._validate_dimensions(self._vectors)

    @classmethod
    def from_chunks(cls, chunks: list[ProfileChunk]) -> "ProfileRetriever":
        from fastembed import TextEmbedding

        embedder = TextEmbedding(model_name=Config.PROFILE_EMBEDDING_MODEL)
        return cls(chunks, embedder)

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        if not query.strip():
            raise ValueError("query must not be empty.")
        top_k = Config.PROFILE_RETRIEVAL_TOP_K if top_k is None else top_k
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        query_vectors = list(self._embedder.query_embed(query))
        if len(query_vectors) != 1:
            raise ValueError("The embedder must return exactly one query vector.")
        query_vector = self._normalize(query_vectors[0])
        self._validate_dimensions([*self._vectors, query_vector])

        scored = [
            RetrievedChunk(chunk=chunk, score=self._dot(query_vector, vector))
            for chunk, vector in zip(self._chunks, self._vectors, strict=True)
        ]
        scored.sort(key=lambda result: result.score, reverse=True)
        return scored[:top_k]

    @staticmethod
    def _normalize(vector) -> tuple[float, ...]:
        values = tuple(float(value) for value in vector)
        if not values:
            raise ValueError("Embedding vectors must not be empty.")
        magnitude = sqrt(sum(value * value for value in values))
        if magnitude == 0:
            raise ValueError("Embedding vectors must not be zero vectors.")
        return tuple(value / magnitude for value in values)

    @staticmethod
    def _validate_dimensions(vectors: list[tuple[float, ...]]) -> None:
        if vectors and any(len(vector) != len(vectors[0]) for vector in vectors):
            raise ValueError("All embedding vectors must have the same dimensions.")

    @staticmethod
    def _dot(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        return sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))