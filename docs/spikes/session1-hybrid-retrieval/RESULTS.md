# Feasibility spike — hybrid retrieval on a real corpus

> Session 1 — Discovery & Planning. Run on 2026-08-27. This is a throwaway
> spike, not application code — see `spike.py`. Raw output: `results.json`.

## Setup

- **Corpus:** 8 pages of official FastAPI documentation (MIT-licensed,
  fetched from `tiangolo/fastapi` at the `master` ref — see
  `corpus/LICENCE-NOTE.md` for the file list, source URLs, and why this
  corpus was chosen over fiction/trivia). Chunked by markdown heading into
  **108 chunks** across **9 source documents**.
- **Keyword search:** Postgres full-text search (`tsvector`/`tsquery`,
  `ts_rank`, GIN index).
- **Vector search:** `pgvector`, HNSW index, cosine distance. Embeddings from
  `BAAI/bge-small-en-v1.5` (384-dim, via `fastembed`/ONNX — chosen over
  `sentence-transformers` to avoid a torch dependency in a throwaway spike;
  this is not a Session-3 model choice).
- **Hybrid:** Reciprocal Rank Fusion (RRF, k=60) over the keyword and vector
  rank lists.
- **Infra:** `pgvector/pgvector:pg17` + `python:3.12-slim`, both in Docker,
  matching how Session 0 already runs things on this machine (no local
  Python installed). Torn down after the run; nothing was left running.
- **Test set:** 11 hand-written queries against the known corpus — 9
  "scoreable" queries with a known correct source document, plus 2 negative
  controls with no correct answer in the corpus (see below). Queries were
  written *before* looking at retrieval output, split across three kinds:
  **keyword-friendly** (shares vocabulary with the answer), **semantic
  paraphrase** (deliberately avoids the answer's vocabulary — e.g. asking
  "run code after sending the response" instead of "background tasks"), and
  two adversarial negative controls (below).

## Headline result: Recall@3

| Method | Recall@3 (9 scoreable queries) |
|---|---|
| Keyword, AND semantics (`plainto_tsquery`) | **0 / 9 (0%)** |
| Keyword, OR semantics (`to_tsquery` with `\|`) | 9 / 9 (100%) |
| Vector only | 9 / 9 (100%) |
| Hybrid (RRF, keyword-OR + vector) | 9 / 9 (100%) |

**Caveat, stated honestly:** with only 9 source documents and one correct
document per query, Recall@3 is a low bar — three guesses out of nine
documents. This spike proves hybrid retrieval *works end-to-end* against a
real corpus and real pgvector infrastructure; it does not prove retrieval
quality at production scale. A harder, larger-corpus benchmark is
Session 2+ work (the evaluation harness is this repo's other deep SDLC
phase, Verification & Testing).

## Finding 1 (mediocre, and worth keeping): naive keyword search failed completely

The first run used Postgres's default `plainto_tsquery`, which ANDs every
non-stopword term together. **It returned zero results for all nine
scoreable queries** — not "ranked poorly," *zero matches*, because natural
questions ("What class do I import to add CORS support in FastAPI?") rarely
have every one of their content words — "class," "import," "add," "cors,"
"support," "fastapi" — co-occurring in one 100-word documentation chunk.

This was not a misconfiguration to route around quietly. It is the
finding: **AND-semantics full-text search is close to useless against
natural-language questions**, and any implementation plan that assumes
"add Postgres full-text search" is sufficient keyword search is wrong.
Switching to OR semantics (`to_tsquery` joined with `|`, ranked by
`ts_rank`) fixed it completely (0% → 100% recall@3). This is now a concrete,
checkable implementation requirement for Session 2+, not a vague "consider
tsquery options" note — the AND variant must not ship.

## Finding 2 (the important one): high similarity does not mean correct

Two negative-control queries had **no correct answer anywhere in the
corpus**:

| Query | Kind | Top vector similarity |
|---|---|---|
| "How do I set up 'Sign in with Google' as an OAuth2 identity provider?" | topically adjacent, but absent | **0.701** |
| "What is the boiling point of tungsten?" | fully out-of-corpus | 0.515 |

For comparison, the nine *genuinely answerable* queries scored between
0.706 and 0.848 top similarity.

The fully-unrelated query (tungsten) is cleanly separable — its score
(0.515) sits well below every correct-answer score. **The topically-adjacent
query is not separable at all.** "Sign in with Google" scored 0.701 —
squarely inside the range of genuinely correct retrievals — because the
corpus's OAuth2/JWT password-flow chunk is semantically close to "OAuth2
identity provider" even though it never discusses Google or third-party
sign-in. A system that refused only below a fixed similarity threshold
(e.g. "refuse if top score < 0.6") would confidently hand this chunk to the
generation step and risk a fabricated-but-plausible answer about a feature
the documentation never covers — exactly the failure mode this project
exists to prevent (see `00-project-brief.md`, "cost of a wrong answer").

**Implication for the architecture, recorded now so Session 2+ doesn't
relitigate it:** retrieval-score thresholding alone is an insufficient
refusal mechanism. Refusal needs a second check — an explicit
"does this retrieved passage actually answer the question" verification
(e.g. an LLM-graded groundedness/entailment check between the retrieved
chunk and the answer, not just retrieval confidence) — before the citation
is emitted. This is a scope input to `03-architecture.md`, not something
this spike builds.

## What this spike does and does not prove

**Proves:**
- Hybrid retrieval is technically feasible end-to-end: real documents →
  chunked → embedded → indexed in pgvector → queried via keyword + vector +
  RRF fusion, all inside the project's actual planned infra (Postgres +
  pgvector, Docker).
- OR-semantics keyword search and vector search each independently reach
  100% recall@3 on this corpus; naive AND-semantics keyword search does
  not (0%) — a concrete implementation constraint, not a guess.
- Similarity scores alone cannot distinguish "topically close but wrong"
  from "actually correct" — refusal needs a groundedness check beyond a
  retrieval-score threshold.

**Does not prove:**
- Retrieval quality at realistic corpus scale (thousands of documents,
  ambiguous/overlapping topics, multiple correct answers per query). Recall@3
  over 9 documents is a weak signal at this size.
- That RRF hybrid fusion outperforms vector-only in the way it's supposed
  to (reranking, weighted diversity) — on this corpus vector-only alone
  already hit 100% recall@3, so hybrid had no failures left to fix. A larger,
  harder corpus is needed to actually observe hybrid's advantage over
  vector-only, which is expected to show up on exact-match/rare-token
  queries (error codes, config keys, version numbers) that this small,
  prose-heavy corpus didn't happen to test.
- Anything about generation quality, citation accuracy, or the groundedness
  check named in Finding 2 — none of that exists yet.

## How to reproduce

```
docker network create lexicon-spike-net
docker run -d --name lexicon-spike-pg --network lexicon-spike-net \
  -e POSTGRES_PASSWORD=spike -e POSTGRES_DB=spike pgvector/pgvector:pg17
docker run --rm --network lexicon-spike-net \
  -v "$(pwd)/docs/spikes/session1-hybrid-retrieval:/spike" -w /spike \
  python:3.12-slim bash -c "pip install -r requirements.txt && python spike.py"
docker rm -f lexicon-spike-pg && docker network rm lexicon-spike-net
```
