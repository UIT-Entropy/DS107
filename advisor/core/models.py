from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class IndexBuildReport:
    chunks_path: str
    index_path: str
    metadata_path: str
    chunk_count: int
    embedding_model: str
    delay_seconds: float


@dataclass(slots=True)
class SearchResult:
    chunk: dict[str, Any]
    embedding_score: float
    rerank_score: float = 0.0
    rank: int = 0
    reasons: list[str] = field(default_factory=list)

    @property
    def source_label(self) -> str:
        return f"S{self.rank}"


@dataclass(slots=True)
class AdvisorAnswer:
    text: str
    sources: list[SearchResult]
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "session_id": self.session_id,
            "sources": [
                {
                    "label": source.source_label,
                    "rank": source.rank,
                    "embedding_score": source.embedding_score,
                    "rerank_score": source.rerank_score,
                    "reasons": source.reasons,
                    "chunk": source.chunk,
                }
                for source in self.sources
            ],
        }
