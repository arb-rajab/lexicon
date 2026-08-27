"""OR-semantics keyword retrieval (FR-005).

`to_tsquery` with terms joined by `|`, ranked by `ts_rank` — never
`plainto_tsquery` (AND semantics), which spike Finding 1 measured at 0%
recall@3 on natural-language questions (docs/spikes/session1-hybrid-
retrieval/RESULTS.md). tests/test_retrieval_guard.py greps this module (and
the rest of the retrieval package) to keep that regression from ever
reappearing — the code-level guard 12-session-handoff.md's Session 3 risk
note asked for.
"""

import re
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session


def keyword_search(
    db: Session, corpus_id: uuid.UUID, query: str, k: int
) -> list[tuple[uuid.UUID, float]]:
    terms = re.findall(r"[A-Za-z0-9_]+", query)
    if not terms:
        return []
    or_query = " | ".join(terms)

    rows = db.execute(
        text(
            """
            SELECT c.id, ts_rank(c.content_tsv, to_tsquery('english', :q)) AS score
            FROM chunk c
            JOIN document d ON d.id = c.document_id
            WHERE d.corpus_id = :corpus_id
              AND c.content_tsv @@ to_tsquery('english', :q)
            ORDER BY score DESC
            LIMIT :k
            """
        ),
        {"q": or_query, "corpus_id": str(corpus_id), "k": k},
    ).fetchall()
    return [(row[0], float(row[1])) for row in rows]
