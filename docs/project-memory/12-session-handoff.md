# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Session completed
- Session number and title: **Session 1 — Discovery & Planning**
- Objective: Produce the deep-phase Discovery evidence — validate the
  problem and users with real reasoning, the explicit "why RAG, not
  fine-tuning or search alone" comparison with a failure-cost analysis, and
  a feasibility spike proving hybrid retrieval works on a sample corpus.
- Status: **complete**

## Work completed
- Rewrote `00-project-brief.md` in full (no "draft"/"stub" markers): a real
  problem statement (who has this problem, why a general chatbot / pure
  keyword search / fine-tuning each fall short for this specific need),
  stakeholders, business assumptions (stated honestly as unvalidated
  hypotheses — this is a portfolio project with no live user base), a
  concrete "cost of a wrong answer" section grounded in specific scenarios
  (a hallucinated API default causing a production incident; a wrong
  retention-policy answer causing an illegal data deletion; a hallucinated
  "still supported" deprecated auth flag), and 5 success metrics — quoting
  the spike's real numbers where they exist, and stating methodology
  without a fabricated number where they don't (latency, prompt-injection
  resistance — neither has a generation surface to measure yet).
- Wrote `00b-rag-vs-alternatives.md`: a genuine options-considered
  comparison (keyword-only / fine-tuning / hybrid RAG) in this portfolio's
  ADR rigor (Context / Options considered / Decision / Trade-offs /
  Consequences / Revisit triggers), deliberately placed outside
  `docs/adr/` and left unnumbered because `00a-ledger-confirmation.md`
  records that formal ADRs begin at Session 3 — this file exists so
  Session 3 can reference it rather than re-litigate the comparison.
  Fine-tuning is rejected on cost-of-staying-current and
  structural-non-citability grounds, not on the pre-existing README
  non-goal alone (the reasoning and the governance rule independently
  agree). Hybrid (not vector-only) is chosen because vector embeddings are
  structurally weaker on exact-token lookups (error codes, config keys) —
  a gap this spike's corpus happened not to test, stated honestly as a
  revisit trigger rather than hidden.
- **Ran a real, executed feasibility spike** —
  `docs/spikes/session1-hybrid-retrieval/` — against a real, licence-clean
  corpus (8 pages of official FastAPI documentation, MIT-licensed, fetched
  from `tiangolo/fastapi`, `docs/en/docs/` tree; provenance and licence
  rationale recorded in `corpus/LICENCE-NOTE.md`), using the project's
  actual planned infrastructure (`pgvector/pgvector:pg17` + `python:3.12-slim`
  in Docker, matching how Session 0 already runs things on this
  no-local-Python machine). 108 chunks across 9 documents; 11 hand-written
  test queries (9 scoreable + 2 negative controls), written before looking
  at retrieval output.
  - **Finding 1 (mediocre, reported honestly, not hidden):** naive
    AND-semantics Postgres full-text search (`plainto_tsquery`) scored
    **0/9 (0%) recall@3** — it requires every content word of a natural
    question to co-occur in one chunk, which ordinary phrasing rarely
    satisfies. Switching to OR semantics fixed it completely (0% → 100%).
    This is now a concrete implementation constraint for Session 2+: the
    AND variant must not ship.
  - **Finding 2 (the important one):** a topically-adjacent-but-wrong query
    ("Sign in with Google" against a corpus that only documents
    password-flow JWT auth) scored a top vector similarity of **0.701** —
    inside the 0.706–0.848 range of the nine genuinely correct retrievals
    in the same run — while a fully-unrelated query (tungsten's boiling
    point) was cleanly separable at 0.515. **Retrieval-similarity-only
    refusal is proven unsafe by this measurement**, not merely suspected:
    it would confidently hand a wrong-but-related passage to generation.
    Recorded as a fixed architectural input for Session 2+'s refusal
    design (an explicit groundedness/entailment check is required) and as
    a new non-goal ("similarity-threshold-only refusal") in
    `01-scope-and-non-goals.md`.
  - Also recorded honestly what the spike does **not** prove: retrieval
    quality at realistic corpus scale (9 documents is a low bar for
    recall@3), and hybrid's expected advantage over vector-only on
    exact-token queries (this corpus didn't happen to test that case).
- Wrote `01-scope-and-non-goals.md` in full: a checkable MVP boundary
  (8 items, all unchecked — nothing is built yet, Session 1 is discovery),
  and a non-goals table expanding the README's permanent-boundaries
  preview into full reasoning + reconsideration conditions, plus **two new
  non-goals this session's analysis surfaced**: "retrieval-quality
  guarantees on unbounded/very-large corpora without harness evidence at
  that scale" (the spike's own corpus-size caveat, formalised) and
  "similarity-threshold-only refusal" (Finding 2, formalised).
- Updated `README.md`: status banner (Session 0 → Session 1 complete),
  project-status line, and the non-goals section's pointer (now points to
  a produced table, not a future promise).
- Updated `docs/SDLC-EVIDENCE.md`'s Phase 1 (Discovery & Planning) row with
  real evidence citations, replacing "not yet produced."
- Docker resources used for the spike (a `pgvector/pgvector:pg17` container
  and a bridge network) were torn down after the run; nothing was left
  running. The spike's local pip/HF cache directory was also deleted —
  only the corpus, script, requirements, and results/report are committed.

## Files created or changed
- `docs/project-memory/00-project-brief.md` — rewritten in full, no draft
  markers remaining.
- `docs/project-memory/00b-rag-vs-alternatives.md` — new: the
  options-considered RAG-vs-alternatives comparison.
- `docs/project-memory/01-scope-and-non-goals.md` — written in full (was an
  empty template).
- `docs/spikes/session1-hybrid-retrieval/` — new: `spike.py`,
  `requirements.txt`, `RESULTS.md`, `results.json` (raw output),
  `corpus/*.md` (8 files) + `corpus/LICENCE-NOTE.md`.
- `README.md` — status banner, project-status line, non-goals pointer.
- `docs/SDLC-EVIDENCE.md` — Phase 1 row updated with real evidence
  citations.
- `docs/project-memory/12-session-handoff.md` — this file.

## Decisions made
- **RAG (hybrid retrieval + grounded generation), not fine-tuning or
  keyword-only search** — full reasoning in `00b-rag-vs-alternatives.md`.
  This is this repository's central Discovery-phase decision per
  `00a-ledger-confirmation.md` and is now backed by both comparative
  reasoning and a real measurement, not asserted.
- **Hybrid keyword search must use OR semantics, not Postgres's default
  AND semantics (`plainto_tsquery`)** — measured, not a style preference.
  Recorded as an MVP-boundary requirement in `01-scope-and-non-goals.md`.
- **Retrieval-confidence thresholding alone is ruled out as the refusal
  mechanism** — an explicit groundedness/entailment check is required.
  This is now a fixed input to Session 2+'s architecture, not an open
  design question to relitigate.
- **`00b-rag-vs-alternatives.md` is deliberately not a numbered ADR under
  `docs/adr/`** — `00a-ledger-confirmation.md` records that formal ADRs
  begin at Session 3 (architecture); this session's decision is Discovery
  reasoning, written at ADR rigor, but not in the ADR sequence. Session 3
  should reference it, not renumber or duplicate it.
- Embedding model for the spike (`BAAI/bge-small-en-v1.5` via `fastembed`/
  ONNX) was chosen to avoid a torch dependency in a throwaway script — this
  is **not** a production model decision; Session 3's architecture is free
  to choose differently.

## Validation performed
- The spike was executed for real inside Docker (`pgvector/pgvector:pg17`
  + `python:3.12-slim`), against a real downloaded corpus, with real
  queries run against real Postgres full-text search and pgvector indexes
  — not simulated or hand-computed. Full command transcript and honest
  results (including the 0% AND-semantics keyword result) are in
  `docs/spikes/session1-hybrid-retrieval/RESULTS.md` and `results.json`.
- Corpus provenance and licence were checked and recorded before use
  (`corpus/LICENCE-NOTE.md`) — MIT-licensed FastAPI documentation, fetched
  from the upstream repository, attribution and source URLs recorded.
- No application code was touched this session — `backend/` and
  `frontend/` are unchanged from Session 0. `privacy-forge`,
  `laravel-consent-guard`, and `bookslot` were not touched.
- Docker spike resources were torn down after the run (`docker rm -f`,
  `docker network rm`) — verified nothing was left running.

## Open questions and risks
- **Risk carried forward from Session 0, now partially informed:** the RAG
  evaluation methodology learning objective's actual difficulty is now
  somewhat de-risked by this spike (the mechanics of hybrid retrieval +
  recall measurement are proven tractable), but a CI-gated, golden-dataset
  harness at realistic corpus scale is still unbuilt — Session 5's actual
  lift is not yet known.
- **New risk, from Finding 2:** the refusal mechanism now has a firm
  requirement (groundedness/entailment check, not a similarity threshold)
  but no design yet — this is real, not hypothetical, scope for Session 2's
  architecture (`03-architecture.md`) and should not be underestimated as
  "just add a threshold."
- **New risk, from Finding 1:** any future contributor's instinct to reach
  for Postgres's default `plainto_tsquery` will silently reintroduce the
  0%-recall failure mode measured this session. Worth a code comment or
  lint-level guard at implementation time, not just a memory-pack note.
- **No blockers.** Session 2 can start immediately.

## Next recommended session
- Proposed session title: **Session 2 — Requirements & Architecture**
- Single objective: Turn this session's validated discovery (problem,
  RAG-vs-alternatives decision, feasibility findings, success metrics,
  MVP boundary, non-goals) into concrete functional/non-functional
  requirements and a real system architecture — specifically resolving the
  two firm inputs this session produced: (1) hybrid retrieval must use
  OR-semantics keyword search, and (2) the refusal mechanism needs an
  explicit groundedness/entailment check design, not a similarity
  threshold.
- Inputs required: this handoff; `00-project-brief.md`;
  `00b-rag-vs-alternatives.md`; `01-scope-and-non-goals.md`;
  `docs/spikes/session1-hybrid-retrieval/RESULTS.md`.
- Expected deliverables: `02-requirements.md` (functional/non-functional
  requirements traceable to the MVP boundary and success metrics);
  `03-architecture.md` (system architecture, including a concrete design
  for the groundedness check); `04-data-model.md`; `05-api-contracts.md`.
- Definition of done: requirements and architecture written and reasoned
  (not templated), the groundedness-check design is concrete enough to
  implement against, and neither the stack nor the deep-SDLC-phase count
  nor the learning budget has been silently changed.

## Paste-into-new-session context

**Project:** lexicon — grounded document Q&A system; every answer is
citation-backed or refused
**Track:** public flagship
**Repository state:** branch `main`, unreleased (pre-v0.1.0), Session 1
complete

**Problem being solved (validated Session 1, not just asserted):** teams
with a bounded, changing, authoritative document corpus need answers they
can act on without independently re-reading the source — a general
chatbot has no access to the corpus and doesn't know it doesn't know; pure
keyword search measurably fails on natural-language phrasing (0% recall@3
with default AND semantics, this session's spike); a fine-tuned model
can't cheaply track a changing corpus or produce real citations. See
`00-project-brief.md` and `00b-rag-vs-alternatives.md`.

**Current stack:**
- Backend: FastAPI, Python 3.12
- Frontend: Next.js 15 (App Router)
- Data: PostgreSQL + pgvector, Redis, S3-compatible object storage (MinIO)
- Infra: Docker Compose (built and verified booting at Session 0), GitHub
  Actions (real CI from Session 0)
- Testing: pytest (backend), Vitest (frontend) — both currently cover only
  the health-check skeleton; no application logic exists yet

**Architecture decisions that must not be reversed:**
- Licence is AGPL-3.0 (hostable app, not a library).
- Primary frontend/backend framework pair is fixed (Next.js 15 + FastAPI/
  Python 3.12) — frozen against the portfolio-wide framework allocation
  ledger.
- Exactly two deep SDLC phases for this repo: Discovery & Planning
  (complete, Session 1), Verification & Testing. Do not let a third phase
  creep in.
- Learning budget is exactly 2 (RAG evaluation methodology, LLM
  guardrails/prompt-injection defence) — already at cap.
- RAG (hybrid retrieval + grounded generation), not fine-tuning or
  keyword-only search — `00b-rag-vs-alternatives.md`.
- Hybrid keyword search must use OR semantics, not `plainto_tsquery`'s
  default AND semantics — measured, Session 1 spike Finding 1.
- Refusal cannot be a bare retrieval-similarity threshold — must include a
  groundedness/entailment check — measured, Session 1 spike Finding 2.

**Implementation state:**
- Done: repository skeleton, licence, governance docs, minimal real
  backend/frontend skeletons, docker-compose proven to boot, real CI
  pipeline, full discovery/planning documentation, an executed feasibility
  spike with honestly-reported results.
- In progress: nothing mid-flight.
- Not started: everything product-related — no ingestion, retrieval,
  generation, or evaluation harness exists as application code yet (the
  spike script is throwaway and lives under `docs/spikes/`, not `backend/`).

**Constraints and non-goals:**
- Full non-goals table with rationale and reconsideration triggers:
  `docs/project-memory/01-scope-and-non-goals.md`. Includes the permanent
  boundaries (no fine-tuning, no agentic tool use, no multi-modal input,
  not a general chatbot, not an LLM gateway, no autonomous action-taking)
  plus two new ones from this session (no retrieval-quality guarantees
  beyond harness-evidenced scale; no similarity-threshold-only refusal).

**Task for the next session (single objective):**
Requirements & Architecture: turn Session 1's discovery into concrete
functional/non-functional requirements and a system architecture,
including a concrete design for the groundedness/entailment refusal check
that Session 1 proved is required but did not design.

**Definition of done:**
- `02-requirements.md` written with requirements traceable to the MVP
  boundary and success metrics.
- `03-architecture.md` written with a concrete groundedness-check design,
  not a placeholder.
- `04-data-model.md`, `05-api-contracts.md` written.
- Stack, deep-phase count, and learning budget unchanged.

**Files to attach or paste:**
- `docs/project-memory/12-session-handoff.md` (this file)
- `docs/project-memory/00-project-brief.md`
- `docs/project-memory/00b-rag-vs-alternatives.md`
- `docs/project-memory/01-scope-and-non-goals.md`
- `docs/spikes/session1-hybrid-retrieval/RESULTS.md`

**Ground rules:** Do not change the stack. Do not introduce a third new
technology. Do not expand the deep-SDLC-phase count beyond two. Do not
touch `privacy-forge`, `laravel-consent-guard`, or `bookslot`. Ask before
introducing any new dependency or scope item not already anticipated
above.
