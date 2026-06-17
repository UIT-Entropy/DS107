from __future__ import annotations

import math
from typing import Any

from advisor.core.models import SearchResult


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def vector_search(
    indexed_rows: list[dict[str, Any]],
    query_embedding: list[float],
    limit: int,
) -> list[SearchResult]:
    results: list[SearchResult] = []
    for row in indexed_rows:
        score = cosine_similarity(query_embedding, row["embedding"])
        results.append(SearchResult(chunk=row["chunk"], embedding_score=score))
    return sorted(results, key=lambda result: result.embedding_score, reverse=True)[:limit]

