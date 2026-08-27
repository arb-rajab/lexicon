"""NFR-001 regression test: recall@3 on the Session 1 spike corpus must not
regress below the spike's measured 100% baseline (docs/spikes/session1-
hybrid-retrieval/RESULTS.md), now that hybrid retrieval is real application
code (ingestion/service.py, retrieval/service.py) instead of a throwaway
script.
"""

from sqlalchemy.orm import Session

from lexicon.retrieval.service import hybrid_retrieve
from tests.support.spike_corpus import load_spike_corpus

# The 9 "scoreable" queries from the spike (spike.py's TEST_QUERIES), minus
# the 2 negative controls (adjacent-but-absent / out-of-corpus), which have
# no expected_source and are exercised separately by the proof test.
SCOREABLE_QUERIES = [
    ("What class do I import to add CORS support in FastAPI?", "cors.md"),
    ("How do I allow cookies to be sent on cross-origin requests?", "cors.md"),
    (
        "How can I run some code after already sending the response back to the client?",
        "background-tasks.md",
    ),
    ("How do I make sure a database session gets closed after each request?", "sql-databases.md"),
    ("How do I check a plaintext password against a stored hash at login?", "oauth2-jwt.md"),
    ("How do I broadcast a message to every client connected over a socket?", "websockets.md"),
    ("What's the recommended base image for containerizing a FastAPI app?", "docker.md"),
    (
        "How do I share one dependency function across several different path operations?",
        "dependencies.md",
    ),
    ("How do I add a custom header to every single HTTP response my app sends?", "middleware.md"),
]


def test_hybrid_retrieval_recall_at_3_matches_spike_baseline(db: Session) -> None:
    corpus_id = load_spike_corpus(db)

    hits = 0
    misses = []
    for query, expected_source in SCOREABLE_QUERIES:
        results = hybrid_retrieve(db, corpus_id, query, top_n=3)
        sources = {r.source_filename for r in results}
        if expected_source in sources:
            hits += 1
        else:
            misses.append((query, expected_source, sources))

    recall_at_3 = hits / len(SCOREABLE_QUERIES)
    assert recall_at_3 == 1.0, (
        f"Recall@3 regressed below the spike's 100% baseline (NFR-001): {recall_at_3:.0%}. "
        f"Misses: {misses}"
    )


def test_ingestion_scopes_retrieval_to_one_corpus(db: Session) -> None:
    # FR-014: a query against corpus A never retrieves chunks from corpus B.
    corpus_a = load_spike_corpus(db, filenames=("cors.md",))
    corpus_b = load_spike_corpus(db, filenames=("docker.md",))

    results_a = hybrid_retrieve(
        db, corpus_a, "What's the recommended base image for containerizing a FastAPI app?", top_n=5
    )
    assert all(r.source_filename != "docker.md" for r in results_a)

    results_b = hybrid_retrieve(
        db, corpus_b, "What class do I import to add CORS support in FastAPI?", top_n=5
    )
    assert all(r.source_filename != "cors.md" for r in results_b)
