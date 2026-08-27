"""Reciprocal Rank Fusion (RRF, k=60) — matches the Session 1 spike exactly
(FR-006, 03-architecture.md)."""

import uuid
from dataclasses import dataclass


@dataclass
class FusedResult:
    chunk_id: uuid.UUID
    fusion_rank: int
    fusion_score: float
    keyword_rank: int | None
    vector_rank: int | None


def reciprocal_rank_fusion(
    keyword_results: list[tuple[uuid.UUID, float]],
    vector_results: list[tuple[uuid.UUID, float]],
    k: int,
    rrf_k: int = 60,
) -> list[FusedResult]:
    scores: dict[uuid.UUID, float] = {}
    keyword_ranks: dict[uuid.UUID, int] = {}
    vector_ranks: dict[uuid.UUID, int] = {}

    for rank, (chunk_id, _score) in enumerate(keyword_results, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
        keyword_ranks[chunk_id] = rank

    for rank, (chunk_id, _score) in enumerate(vector_results, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
        vector_ranks[chunk_id] = rank

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return [
        FusedResult(
            chunk_id=chunk_id,
            fusion_rank=i + 1,
            fusion_score=score,
            keyword_rank=keyword_ranks.get(chunk_id),
            vector_rank=vector_ranks.get(chunk_id),
        )
        for i, (chunk_id, score) in enumerate(ranked)
    ]
