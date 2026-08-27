"""
Session 1 feasibility spike — hybrid (keyword + vector) retrieval on a real
corpus, via Postgres + pgvector.

This is a throwaway spike script, not application code. It exists to answer
one question honestly: does hybrid retrieval actually beat keyword-only or
vector-only search on this project's kind of corpus? Results are printed and
also written to results.json for RESULTS.md to quote from directly.
"""

import json
import re
from pathlib import Path

import psycopg2
from fastembed import TextEmbedding

CORPUS_DIR = Path(__file__).parent / "corpus"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # 384-dim, ONNX, no torch dependency
DB_DSN = "dbname=spike user=postgres password=spike host=lexicon-spike-pg port=5432"

# ---------------------------------------------------------------------------
# 1. Chunk the corpus by markdown heading (## / ###), which is a reasonable
#    proxy for "one self-contained idea" in documentation — matching how a
#    real ingestion pipeline would chunk structured docs.
# ---------------------------------------------------------------------------


def chunk_markdown(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    chunks = []
    current_heading = "(intro)"
    current_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append({"heading": current_heading, "text": body})

    for line in lines:
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            flush()
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()
    # Drop trivial chunks (pure code fences or <20 words) — noise, not signal.
    return [c for c in chunks if len(c["text"].split()) >= 20]


def load_corpus() -> list[dict]:
    records = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        for chunk in chunk_markdown(path):
            records.append({"source": path.name, **chunk})
    return records


# ---------------------------------------------------------------------------
# 2. Load into Postgres: a tsvector column for keyword search, a vector(384)
#    column for embeddings.
# ---------------------------------------------------------------------------


def setup_db(conn, records: list[dict], embeddings: list[list[float]]) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS chunks;")
        cur.execute(
            """
            CREATE TABLE chunks (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                heading TEXT NOT NULL,
                body TEXT NOT NULL,
                tsv tsvector,
                embedding vector(384)
            );
            """
        )
        for rec, emb in zip(records, embeddings, strict=True):
            cur.execute(
                """
                INSERT INTO chunks (source, heading, body, tsv, embedding)
                VALUES (%s, %s, %s, to_tsvector('english', %s), %s)
                """,
                (rec["source"], rec["heading"], rec["text"], rec["text"], emb),
            )
        cur.execute("CREATE INDEX ON chunks USING GIN (tsv);")
        cur.execute("CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);")
    conn.commit()


# ---------------------------------------------------------------------------
# 3. Retrieval methods
# ---------------------------------------------------------------------------


def keyword_search(conn, query: str, k: int) -> list[tuple]:
    """AND semantics (plainto_tsquery) — the naive/default way to do Postgres
    full-text search. Kept as a baseline because the gap between this and
    keyword_search_or below is itself a spike finding worth recording."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, source, heading, ts_rank(tsv, plainto_tsquery('english', %s)) AS score
            FROM chunks
            WHERE tsv @@ plainto_tsquery('english', %s)
            ORDER BY score DESC
            LIMIT %s
            """,
            (query, query, k),
        )
        return cur.fetchall()


def keyword_search_or(conn, query: str, k: int) -> list[tuple]:
    """OR semantics: any query term may match, ranked by how many/how well.
    More forgiving for natural-language questions than AND semantics."""
    or_query = " | ".join(re.findall(r"[A-Za-z0-9_]+", query))
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, source, heading, ts_rank(tsv, to_tsquery('english', %s)) AS score
            FROM chunks
            WHERE tsv @@ to_tsquery('english', %s)
            ORDER BY score DESC
            LIMIT %s
            """,
            (or_query, or_query, k),
        )
        return cur.fetchall()


def vector_search(conn, query_embedding: list[float], k: int) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, source, heading, 1 - (embedding <=> %s::vector) AS score
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, k),
        )
        return cur.fetchall()


def hybrid_search_rrf(kw_results: list[tuple], vec_results: list[tuple], k: int, rrf_k: int = 60) -> list[tuple]:
    """Reciprocal Rank Fusion over the two ranked lists."""
    scores: dict[int, float] = {}
    meta: dict[int, tuple] = {}
    for rank, row in enumerate(kw_results, start=1):
        scores[row[0]] = scores.get(row[0], 0.0) + 1.0 / (rrf_k + rank)
        meta[row[0]] = row
    for rank, row in enumerate(vec_results, start=1):
        scores[row[0]] = scores.get(row[0], 0.0) + 1.0 / (rrf_k + rank)
        meta[row[0]] = row
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return [(*meta[cid][:3], score) for cid, score in ranked]


# ---------------------------------------------------------------------------
# 4. Test queries with ground-truth expected source doc.
#    Mix of: keyword-friendly (exact term overlap), semantic-paraphrase
#    (no term overlap with the answer), topically-adjacent-but-absent
#    (should NOT match confidently), and fully out-of-corpus (negative
#    control for a refusal threshold).
# ---------------------------------------------------------------------------

TEST_QUERIES = [
    {
        "query": "What class do I import to add CORS support in FastAPI?",
        "expected_source": "cors.md",
        "kind": "keyword-friendly",
    },
    {
        "query": "How do I allow cookies to be sent on cross-origin requests?",
        "expected_source": "cors.md",
        "kind": "keyword-friendly",
    },
    {
        "query": "How can I run some code after already sending the response back to the client?",
        "expected_source": "background-tasks.md",
        "kind": "semantic-paraphrase",
    },
    {
        "query": "How do I make sure a database session gets closed after each request?",
        "expected_source": "sql-databases.md",
        "kind": "semantic-paraphrase",
    },
    {
        "query": "How do I check a plaintext password against a stored hash at login?",
        "expected_source": "oauth2-jwt.md",
        "kind": "semantic-paraphrase",
    },
    {
        "query": "How do I broadcast a message to every client connected over a socket?",
        "expected_source": "websockets.md",
        "kind": "semantic-paraphrase",
    },
    {
        "query": "What's the recommended base image for containerizing a FastAPI app?",
        "expected_source": "docker.md",
        "kind": "keyword-friendly",
    },
    {
        "query": "How do I share one dependency function across several different path operations?",
        "expected_source": "dependencies.md",
        "kind": "semantic-paraphrase",
    },
    {
        "query": "How do I add a custom header to every single HTTP response my app sends?",
        "expected_source": "middleware.md",
        "kind": "semantic-paraphrase",
    },
    {
        "query": "How do I set up 'Sign in with Google' as an OAuth2 identity provider?",
        "expected_source": None,
        "kind": "adjacent-but-absent",
    },
    {
        "query": "What is the boiling point of tungsten?",
        "expected_source": None,
        "kind": "out-of-corpus",
    },
]


def main() -> None:
    print("Loading + chunking corpus...")
    records = load_corpus()
    print(f"  {len(records)} chunks from {len(set(r['source'] for r in records))} documents")

    print(f"Loading embedding model {EMBED_MODEL} (first run downloads ~130MB)...")
    model = TextEmbedding(model_name=EMBED_MODEL)

    print("Embedding chunks...")
    chunk_embeddings = [e.tolist() for e in model.embed([r["text"] for r in records])]

    conn = psycopg2.connect(DB_DSN)
    print("Loading into Postgres + pgvector...")
    setup_db(conn, records, chunk_embeddings)

    print("Running test queries...\n")
    k = 3
    per_query_results = []
    method_hits = {"keyword_and": 0, "keyword_or": 0, "vector": 0, "hybrid": 0}
    scoreable = [q for q in TEST_QUERIES if q["expected_source"]]

    for tq in TEST_QUERIES:
        query = tq["query"]
        q_embedding = list(model.embed([query]))[0].tolist()

        kw_and = keyword_search(conn, query, k)
        kw_or = keyword_search_or(conn, query, k)
        vec = vector_search(conn, q_embedding, k)
        hyb = hybrid_search_rrf(kw_or, vec, k)  # hybrid uses the OR variant — see RESULTS.md

        def sources(rows):
            return [r[1] for r in rows]

        kw_and_hit = tq["expected_source"] in sources(kw_and) if tq["expected_source"] else None
        kw_or_hit = tq["expected_source"] in sources(kw_or) if tq["expected_source"] else None
        vec_hit = tq["expected_source"] in sources(vec) if tq["expected_source"] else None
        hyb_hit = tq["expected_source"] in sources(hyb) if tq["expected_source"] else None

        if tq["expected_source"]:
            method_hits["keyword_and"] += int(bool(kw_and_hit))
            method_hits["keyword_or"] += int(bool(kw_or_hit))
            method_hits["vector"] += int(bool(vec_hit))
            method_hits["hybrid"] += int(bool(hyb_hit))

        top_vec_score = vec[0][3] if vec else None

        result = {
            "query": query,
            "kind": tq["kind"],
            "expected_source": tq["expected_source"],
            "keyword_and_top3": [{"source": r[1], "heading": r[2], "score": round(float(r[3]), 4)} for r in kw_and],
            "keyword_or_top3": [{"source": r[1], "heading": r[2], "score": round(float(r[3]), 4)} for r in kw_or],
            "vector_top3": [{"source": r[1], "heading": r[2], "score": round(float(r[3]), 4)} for r in vec],
            "hybrid_top3": [{"source": r[1], "heading": r[2], "score": round(float(r[3]), 4)} for r in hyb],
            "keyword_and_hit": kw_and_hit,
            "keyword_or_hit": kw_or_hit,
            "vector_hit": vec_hit,
            "hybrid_hit": hyb_hit,
            "top_vector_similarity": round(float(top_vec_score), 4) if top_vec_score is not None else None,
        }
        per_query_results.append(result)

        print(f"[{tq['kind']}] {query}")
        print(f"  expected: {tq['expected_source']}")
        print(f"  keyword(AND) top3: {sources(kw_and)}  hit={kw_and_hit}")
        print(f"  keyword(OR)  top3: {sources(kw_or)}  hit={kw_or_hit}")
        print(f"  vector       top3: {sources(vec)}  hit={vec_hit}")
        print(f"  hybrid       top3: {sources(hyb)}  hit={hyb_hit}")
        print(f"  top vector similarity: {top_vec_score}")
        print()

    n = len(scoreable)
    summary = {
        "num_chunks": len(records),
        "num_scoreable_queries": n,
        "recall_at_3": {method: round(hits / n, 3) for method, hits in method_hits.items()},
        "queries": per_query_results,
    }

    print("=" * 70)
    print(f"Recall@{k} over {n} scoreable queries:")
    for method, hits in method_hits.items():
        print(f"  {method:12s}: {hits}/{n}  ({hits/n:.0%})")

    out_path = Path(__file__).parent / "results.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nFull results written to {out_path}")

    conn.close()


if __name__ == "__main__":
    main()
