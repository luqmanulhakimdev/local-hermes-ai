from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.rag.vector_store import VectorStore


@dataclass(frozen=True)
class RAGConfig:
    top_k: int = 3
    threshold: float = 0.65
    max_context_length: int = 4000
    db_path: str = "data/rag.db"

    def __post_init__(self):
        if isinstance(self.top_k, bool) or not isinstance(self.top_k, int):
            raise TypeError("top_k must be a positive integer")
        if self.top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        if isinstance(self.threshold, bool) or not isinstance(self.threshold, (int, float)):
            raise TypeError("threshold must be a number between 0.0 and 1.0")
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")

        if isinstance(self.max_context_length, bool) or not isinstance(self.max_context_length, int):
            raise TypeError("max_context_length must be a positive integer")
        if self.max_context_length <= 0:
            raise ValueError("max_context_length must be greater than 0")

        if not isinstance(self.db_path, (str, Path)) or not str(self.db_path).strip():
            raise ValueError("db_path must be a non-empty string or Path")


@dataclass(frozen=True)
class ContextChunk:
    content: str
    source: str
    score: float


@dataclass(frozen=True)
class RetrievedContext:
    query: str
    chunks: list[ContextChunk]
    max_length: int = 4000
    error: str | None = None

    @property
    def has_content(self) -> bool:
        return bool(self.chunks)

    @property
    def sources(self) -> list[str]:
        seen = set()
        res = []
        for c in self.chunks:
            if c.source not in seen:
                seen.add(c.source)
                res.append(c.source)
        return res

    @property
    def scores(self) -> list[float]:
        return [c.score for c in self.chunks]

    def formatted_context(self) -> str:
        if not self.chunks:
            return ""

        parts = []
        for i, c in enumerate(self.chunks, 1):
            parts.append(
                f"[Document {i}] (Source: {c.source}, Similarity: {c.score:.4f})\n{c.content}"
            )

        full_text = "\n\n".join(parts)
        if len(full_text) > self.max_length:
            return full_text[: self.max_length - 15] + "... [TRUNCATED]"
        return full_text


class RAGContextRetriever:
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        config: RAGConfig | None = None,
    ):
        self.config = config or RAGConfig()
        self.vector_store = vector_store or VectorStore(db_path=str(self.config.db_path))

    def retrieve(self, query: str, strict: bool = False) -> RetrievedContext:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must not be empty")

        try:
            results = self.vector_store.search(
                query,
                top_k=self.config.top_k,
                threshold=self.config.threshold,
            )
            chunks = [
                ContextChunk(
                    content=r["content"],
                    source=r["source"],
                    score=r["score"],
                )
                for r in results
            ]
            return RetrievedContext(
                query=query,
                chunks=chunks,
                max_length=self.config.max_context_length,
            )
        except Exception as e:
            if strict:
                raise
            return RetrievedContext(
                query=query,
                chunks=[],
                max_length=self.config.max_context_length,
                error=f"{type(e).__name__}: {e}",
            )
