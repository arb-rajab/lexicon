# Testing Strategy
> Purpose: what we test, at which level, and why that is sufficient
> Project: lexicon (public)
> Last updated: 2026-08-27 (Session 5)

**Read `docs/adr/ADR-0004-real-llm-verification-descoped.md` before this
document's Security testing section below.** This project's central,
original differentiating claim — that real entailment reasoning correctly
separates grounded answers from topically-adjacent fabrications
(`00-project-brief.md`'s Finding 2) — is permanently unprovable in this
project's current lifecycle, by the project owner's deliberate choice not to
obtain a real LLM provider credential. That constraint is built into this
document's framing from the start, not appended as an afterthought: every
section below states plainly which layer it tests for real and which layer
it can only self-check against `StubLLMClient`'s known, deterministic
behavior (`backend/src/lexicon/llm/stub_client.py`).

## Testing philosophy for this project

Two things are tested, and they require structurally different evidence:

1. **Is the pipeline wired correctly?** (ingestion, hybrid retrieval,
   generation, verification, the refusal gate, the audit trail, the
   ADR-0002 permission split.) This is fully real and fully testable today,
   against a real Postgres+pgvector instance, with no LLM provider
   credential required — retrieval never calls one, and the pipeline's
   *shape* (does a self-refusal short-circuit verification, does
   `injection_suspected` force `enforced_entailed=False`, does a failed
   verification withhold the answer) is testable against any client that
   implements the `LLMClient` protocol, real or stub.
2. **Does the verification mechanism actually work — does it correctly
   judge entailment and resist a hijack attempt?** This requires observing
   a real model's real reasoning on genuinely adversarial input. Per
   ADR-0004, this project has no path to that evidence and will not for the
   duration of the current lifecycle. Every test or harness below that
   touches generation or verification is therefore a **methodology
   self-check** against `StubLLMClient`'s crude keyword-overlap heuristic —
   real, executed, and useful for catching a wiring or scoring regression —
   never evidence of real answer quality. This distinction is enforced in
   the evaluation harness's own printed output, not left to a reader to
   infer (`backend/tests/eval/run_evaluation.py`).

## Levels

| Level | Tool | Scope | Gate |
|---|---|---|---|
| Unit / structural | pytest | Chunking, RRF fusion math, injection-hardening prompt/schema structure (`test_injection_hardening.py`), the FR-005 keyword-guard regex check (`test_retrieval_guard.py`) | `pytest -q`, every PR |
| Integration (real DB) | pytest + real Postgres/pgvector service | Ingestion → retrieval → pipeline → refusal-gate → audit-trail, end to end, against a real database (no mocked DB anywhere in this suite) — `test_ingestion_and_retrieval.py`, `test_pipeline_refusal_paths.py`, `test_api_query.py`, `test_adr0002_grants.py` | `pytest -q`, every PR |
| Retrieval quality (real, unaffected by ADR-0004) | pytest, real embeddings | NFR-001 recall@3 regression against the Session 1 spike corpus baseline (`test_ingestion_and_retrieval.py`); recall@k inside the Session 5 golden-dataset evaluation harness (`tests/eval/`) | `pytest -q`; `python -m tests.eval.run_evaluation`, both every PR |
| Evaluation-methodology self-check (stub-tier, ADR-0004) | Session 5's golden-dataset harness (`backend/tests/eval/`) | Refusal-correctness and citation-accuracy scoring logic, exercised against a committed golden dataset (9 legitimate + 5 adjacent-but-wrong + 2 out-of-corpus cases, `golden_dataset.py`) through the real pipeline via whichever tier `llm.factory.get_llm_client()` selects | `pytest -q` (`test_evaluation_harness.py`) **and** a dedicated CI step that prints the full labeled report unconditionally (`ci.yml`) |
| Proof test (ADR-0001-mandated) | pytest | Reproduces Session 1's exact 0.701-similarity OAuth2/Google adjacent-but-wrong case through the real pipeline (`test_proof_session1_oauth2_case.py`) — the harness's required first test case per ADR-0001's own Consequences section | `pytest -q`, every PR |
| End-to-end (frontend) | Vitest | Health-check skeleton only — the frontend has not progressed past Session 0's scaffold | `npm test`, every PR |

## Security testing

- **Structural injection-hardening tests are real** (`test_injection_hardening.py`):
  the generator (T-01) and verifier (T-02) carry genuinely different
  defenses, asserted directly against the prompt-builders and output
  schemas — sandwiched delimiting, the `injection_suspected` self-report
  field's existence, the schema shape difference, and the
  application-enforced auto-fail (`_ClaimVerdict.__post_init__`,
  `query_pipeline.py`) are all checked as real code structure, not by
  asking a model whether it resisted anything.
- **A committed, adversarial injection test corpus** (`06-security-threat-
  model.md`'s four categories — direct override, authority-spoofing,
  verifier-targeted always-true patterns, and negative-control legitimate
  imperative text) is **not yet built** — this was named in the Session 4.5
  handoff as Session 5/future scope, and this session's own scope (see
  `docs/project-memory/12-session-handoff.md`) was narrowed by the project
  owner to the golden-dataset evaluation harness specifically, not the full
  injection suite. It remains a real, tracked gap, not silently dropped —
  see Known gaps below.
- **Dependency/static-analysis security controls are real and CI-gated**:
  `ruff`, `mypy --strict`, `bandit`, `pip-audit`, `gitleaks`, and CodeQL all
  run on every PR (`ci.yml`) — NFR-009's existing requirement, unaffected by
  ADR-0004 since none of it depends on an LLM call.
- **What security testing cannot do here, stated plainly**: no test in this
  repository, present or future, can measure whether a real model actually
  resists a verifier-hijack attempt (T-02) or correctly judges real
  entailment, because no real model is ever called. A green adversarial-
  corpus run against `StubLLMClient` would prove the corpus and the harness
  work — never that the defense works against a real adversary.

## Accessibility testing

Not yet in scope. The frontend has not progressed past Session 0's
health-check skeleton (`frontend/app/page.tsx`) — there is no real UI
surface to test yet. Tracked as a gap for whichever future session builds
the actual query/citation UI, not fabricated here.

## Performance testing and budgets

- NFR-008 (ingestion latency) and NFR-001 (retrieval recall) both have real
  regression tests against real infrastructure.
- **No query-latency (p95) budget is measurable today**, and per ADR-0004
  never will be in this project's current lifecycle: the only generation/
  verification latency this environment can observe is `StubLLMClient`'s
  in-process, no-network-round-trip response time, which is not
  representative of a real provider call and must not be reported as if it
  were (`00-project-brief.md`'s Success metrics, metric #4).

## Test data strategy (synthetic only)

- **The Session 1 spike corpus is the only real corpus used anywhere in this
  test suite** — 8 pages of MIT-licensed official FastAPI documentation
  (`docs/spikes/session1-hybrid-retrieval/corpus/`, loaded via
  `tests/support/spike_corpus.py`). No proprietary, customer, or synthetic-
  PII data is used anywhere in this repository's tests.
- **The Session 5 golden dataset is hand-authored against this same corpus**
  (`backend/tests/eval/golden_dataset.py`), not generated or sampled — every
  query's expected answer/citation/refusal was reasoned by hand against the
  actual document content, the same standard the Session 1 spike's own
  `TEST_QUERIES` were held to.
- **Why the corpus was not expanded to a larger, "realistic-scale" size this
  session** (`00-project-brief.md`'s Success metric #1 names a 500+
  chunk/20+ document target): this session's actual scope, reframed by the
  project owner (see `12-session-handoff.md`), is proving the evaluation
  *methodology* is sound — the golden-dataset design, the metric
  computations, the CI gate, and the tier-swap seam — not maximizing
  retrieval-quality realism. Sourcing, licensing, and hand-labeling a
  20+ document golden set is real, separate work with its own scope; reusing
  the already-licence-clean, already-validated 8-document spike corpus kept
  this session's new golden-dataset numbers directly comparable to the
  existing NFR-001 baseline rather than introducing an unrelated variable.
  Recorded here as a deliberate, reasoned choice, not an oversight — a
  future session that wants a realistic-scale recall@k number should treat
  corpus expansion as its own scoped task.

## Quality gates in CI

All of the following must pass on every PR against `main` (`ci.yml`):
`ruff`, `mypy --strict`, `bandit`, `alembic upgrade head` against a real
Postgres service, `pytest -q` (unit + integration + the Session 5
evaluation-harness test + the ADR-0001 proof test, all against that same
real database), a dedicated evaluation-harness CI step that prints the full
stub-tier-labeled report unconditionally, `pip-audit`, `gitleaks`, and
CodeQL (Python + JS/TS). Frontend: `eslint`, `npm run build`, `npm test`,
`npm audit --omit=dev`.

**The evaluation harness's CI gate, precisely**: `python -m
tests.eval.run_evaluation` exits non-zero if retrieval recall@3 regresses
below 100% (a real quality floor — retrieval never calls an LLM provider),
or if refusal-correctness/citation-accuracy regress below their
stub-tier-baseline thresholds (`tests/eval/run_evaluation.py`'s own module
constants document the exact measured run each threshold came from). The
latter two thresholds gate against a *regression in the stub's own known
behavior or this dataset's own correctness* — not a real quality bar — see
that file's module docstring for why that distinction matters and is not
merely asserted.

## Known gaps and why they are acceptable

- **Real entailment/injection-resistance quality is permanently unverified**
  (ADR-0004) — the single largest, and now permanent, gap in this project's
  evidence base. Accepted by explicit project-owner decision, not treated as
  temporary.
- **The full adversarial injection corpus** (`06-security-threat-model.md`'s
  four categories, generator- and verifier-targeted suites scored
  separately) is not yet built. This session's scope was explicitly narrowed
  by the project owner to the golden-dataset evaluation harness; the
  injection corpus remains real, valuable, not-yet-done work for a future
  session, tracked here rather than silently dropped.
- **Retrieval quality at realistic scale is not yet measured** — see Test
  data strategy above for why this session kept the 8-document spike
  corpus rather than expanding it.
- **Rate limiting (NFR-007), PDF ingestion, MinIO upload, async ingestion,
  and instance-level authentication** are all unimplemented, unchanged from
  prior sessions' handoffs — none of this session's work depends on or
  affects any of them.
- **Frontend testing is a health-check skeleton only** — no real UI exists
  yet to test.
