"""pgvector cosine-distance retrieval, HNSW index — matches the Session 1
spike's proven vector-search configuration exactly (03-architecture.md).
"""

import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


def vector_search(
    db: Session, corpus_id: uuid.UUID, query_embedding: list[float], k: int
) -> list[tuple[uuid.UUID, float]]:
    rows = db.execute(
        text(
            """
            SELECT c.id, 1 - (c.embedding <=> (:qv)::vector) AS score
            FROM chunk c
            JOIN document d ON d.id = c.document_id
            WHERE d.corpus_id = :corpus_id
            ORDER BY c.embedding <=> (:qv)::vector
            LIMIT :k
            """
        ),
        {"qv": _vector_literal(query_embedding), "corpus_id": str(corpus_id), "k": k},
    ).fetchall()
    return [(row[0], float(row[1])) for row in rows]
