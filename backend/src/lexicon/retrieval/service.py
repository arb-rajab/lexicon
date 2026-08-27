"""Hybrid retrieval orchestration (FR-006) — same shape as the Session 1
spike: keyword-OR and vector each retrieve top_n candidates, RRF fuses them
into the final top_n passed to generation (03-architecture.md's Key flows).
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from lexicon.db import models
from lexicon.ingestion.embeddings import embed_query
from lexicon.retrieval.fusion import reciprocal_rank_fusion
from lexicon.retrieval.keyword import keyword_search
from lexicon.retrieval.vector import vector_search


@dataclass
class RetrievedChunkContext:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    source_filename: str
    section_heading: str
    content: str
    fusion_rank: int
    fusion_score: float
    keyword_rank: int | None
    vector_rank: int | None


def hybrid_retrieve(
    db: Session, corpus_id: uuid.UUID, query: str, top_n: int
) -> list[RetrievedChunkContext]:
    query_embedding = embed_query(query)
    keyword_results = keyword_search(db, corpus_id, query, top_n)
    vector_results = vector_search(db, corpus_id, query_embedding, top_n)
    fused = reciprocal_rank_fusion(keyword_results, vector_results, top_n)

    if not fused:
        return []

    chunk_ids = [f.chunk_id for f in fused]
    rows = db.query(models.Chunk).filter(models.Chunk.id.in_(chunk_ids)).all()
    chunk_by_id = {c.id: c for c in rows}

    contexts: list[RetrievedChunkContext] = []
    for fused_result in fused:
        chunk = chunk_by_id.get(fused_result.chunk_id)
        if chunk is None:
            continue
        contexts.append(
            RetrievedChunkContext(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                source_filename=chunk.document.source_filename,
                section_heading=chunk.section_heading,
                content=chunk.content,
                fusion_rank=fused_result.fusion_rank,
                fusion_score=fused_result.fusion_score,
                keyword_rank=fused_result.keyword_rank,
                vector_rank=fused_result.vector_rank,
            )
        )
    return contexts
