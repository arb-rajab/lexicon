# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Credential status — stated plainly, first, per this session's explicit instruction

**No Anthropic API key (or any other LLM provider credential) exists in
this environment.** Checked directly before any other work: no
`ANTHROPIC_API_KEY` in `.env`, `.env.example`, `docker-compose.yml`, or the
shell environment. This is unchanged from Sessions 2 and 3, which both
already flagged it — this session re-confirms it by direct inspection
rather than assuming the prior note still holds.

**This is explicitly not being treated the way `bookslot`'s D-0036
permanently descoped real Stripe credentials.** The reason is structural,
not a preference for "nice to have real infra": ADR-0001's entire premise
is that similarity scores can't be trusted and an independent verification
step is required *instead* — proving that verification step actually works
requires observing a real model's real behavior on the adversarial case
(Session 1's 0.701-scoring OAuth2/JWT query). A stub can prove the pipeline
is wired correctly end-to-end; it cannot prove the claim this repository
exists to prove. Session 5's entire evaluation harness is meaningless
without a real provider — **the human operator should obtain an Anthropic
API key before Session 5 starts.** Unlike cloud/VPS provisioning, this is
a signup and a few dollars of credit — an urgent but cheap-to-clear
blocker, not a structural one.

Everything in this session was built against a clearly-labeled stub/fake
LLM client tier instead, using the same seam shape as `bookslot`'s
`PaymentIntentGateway`/`FakePaymentIntentGateway` split
(`backend/src/lexicon/llm/base.py`'s `LLMClient` protocol,
`llm/anthropic_client.py`'s real implementation, `llm/stub_client.py`'s
fake one, selected by `llm/factory.py` based on whether
`ANTHROPIC_API_KEY` is set). Swapping in a real key is a config change
(set the env var, restart), not a rewrite — see
`docs/project-memory/08-deployment-and-operations.md`'s new Configuration
and secrets section.

## Session completed
- Session number and title: **Session 4 — Implementation**
- Objective: build the ingestion and query pipelines for real, against
  this repository's complete requirements, architecture, data model, API
  contract, and threat model — the first session where `backend/` changes
  beyond the Session 0 skeleton. Status: **complete**, against the stub
  LLM tier; the generation/verification code itself is real and untested
  against a live provider (see Credential status above and Validation
  performed below).

## Work completed

- **Read `12-session-handoff.md`, ADR-0001, and ADR-0003 first**, as
  instructed, before any implementation — the exact hardening contract
  (forced structured output, sandwiched delimiting, `injection_suspected`
  auto-fail, fail-closed-on-ambiguity) and the exact proof-test requirement
  (ADR-0001's Consequences section) were read from source, not
  paraphrased from the shorter session-handoff restatement.
- **Checked for real LLM credentials before any other work** and reported
  the result plainly — see Credential status above.
- **Minimal document ingestion** (`ingestion/`): heading/section-aware
  chunking (`chunking.py`, adapted directly from Session 1's
  `spike.py:chunk_markdown` — same method, now application code) and
  `BAAI/bge-small-en-v1.5` embeddings via `fastembed`
  (`embeddings.py`, matching the spike's model exactly). `service.py`
  orchestrates ingest/re-upload/removal (FR-001–FR-004): content-hash-based
  no-op detection, a `document_id`-scoped chunk delete-then-reinsert on
  re-upload (never corpus-scoped), and explicit `415` rejection for
  unsupported types. **Two deliberate, stated scope reductions**, not
  silent ones: ingestion runs synchronously within the request rather than
  via the async worker/Redis-queue design in `03-architecture.md` (a
  scaling concern this session's actual focus — the generate/verify
  pipeline — doesn't need to solve, well within NFR-008's 30s budget at
  the corpus sizes exercised here); PDF-text-layer ingestion (also named in
  FR-001) is not implemented, since the reused Session 1 spike corpus is
  entirely Markdown. Original files are not uploaded to MinIO object
  storage this session — `DOCUMENT.object_storage_key` exists in the
  schema but is unused, since the task's ingestion scope item didn't
  require it and ingestion needed to stay minimal to leave room for the
  session's actual point (the security-hardened generate/verify pipeline).
- **Hybrid retrieval** (`retrieval/`), matching `03-architecture.md` and
  the spike exactly: OR-semantics keyword search (`keyword.py`,
  `to_tsquery` joined with `|`, never `plainto_tsquery` — FR-005, applied
  correctly from the start, not rediscovered), pgvector cosine HNSW search
  (`vector.py`), and Reciprocal Rank Fusion (`fusion.py`, k=60).
  `tests/test_retrieval_guard.py` is the permanent code-level regression
  guard against `plainto_tsquery` reappearing, requested since Session 1.
- **Generation with inline citations** (`llm/prompts.py`'s
  `build_generation_*`, `llm/anthropic_client.py`'s `generate()`), matching
  `05-api-contracts.md`'s contract: schema-constrained output
  (`self_refused`, `answer_text`, per-claim `claims` with `chunk_id`
  citations), reference material delimited as untrusted data (T-01
  mitigation).
- **The groundedness verifier as a real, separate LLM call** — a distinct
  method (`LLMClient.verify()`), distinct prompt (`build_verification_*`),
  distinct schema (`VerificationOutput`), and a distinct pipeline stage
  (`pipeline/query_pipeline.py` calls it once per claim, never folded into
  generation), exactly matching ADR-0001's explicit "not a single call
  asked to answer and also rate your own confidence" design.
- **ADR-0003's injection-hardening measures applied to both call sites as
  two genuinely different defenses**, not one mitigation copy-pasted:
  - **Generator (T-01):** a single delimited `<reference_material>` block,
    stated once, backstopped by independent verification rather than
    needing to be the actual defense on its own.
  - **Verifier (T-02):** the untrusted-content warning is **sandwiched**
    (stated both before and after the passage, inside
    `<<<PASSAGE_START>>>`/`<<<PASSAGE_END>>>` markers), the output schema
    adds an `injection_suspected` field the generator's schema doesn't
    have, and the application layer (not the prompt) enforces
    `injection_suspected: true` → `entailed: false` regardless of the
    model's own value (`pipeline/query_pipeline.py`'s `_ClaimVerdict`).
  - `tests/test_injection_hardening.py` asserts these structural
    differences directly (sandwiching, schema field sets, the enforced-
    entailed override) — a regression that merged the two defenses into
    one would fail here even if no other test caught it.
  - Fail-closed on ambiguity (ADR-0003 item 4) is implemented precisely:
    a provider-call failure (`LLMProviderError`) propagates and becomes a
    `502`, per `05-api-contracts.md`; a technically-successful-but-
    unparseable verifier response fails closed to `entailed=False` inside
    `verify()` itself, without raising — these are deliberately different
    code paths, matching the ADR's distinction between "the call failed"
    and "the call succeeded but was ambiguous."
- **The refusal path**: `pipeline/query_pipeline.py`'s `run_query_pipeline`
  implements the deterministic gate (`final_answered` = not self-refused
  AND every claim's enforced `entailed`), returning one of
  `self_refused` / `verification_failed` / `no_candidates_retrieved` per
  `05-api-contracts.md`, never a confident wrong answer. The unverified
  draft answer is retained in the audit log (`QUERY_LOG.generated_answer`)
  for US-005 traceability but withheld from the API response whenever
  `final_answered` is false — tested explicitly
  (`test_pipeline_refusal_paths.py`).
- **ADR-0002's database permission split** implemented as Alembic
  migration `0002`: creates a restricted `lexicon_app` role
  (`INSERT`/`SELECT` only on `QUERY_LOG`/`RETRIEVED_CHUNK`/
  `CITATION_VERDICT`; full CRUD on `CORPUS`/`DOCUMENT`/`CHUNK`, since
  ingestion/removal need `DELETE` there — FR-004). The application's
  `DATABASE_URL` connects as this role; migrations run as a separate
  admin role (`DATABASE_ADMIN_URL`). **Proven via a real grant-assertion
  test** (`tests/test_adr0002_grants.py`) against a live Postgres
  connection using the actual runtime role — `UPDATE`/`DELETE` attempts on
  all three audit tables raise `permission denied`; `SELECT` succeeds
  (a positive control, so the denial tests can't pass vacuously against a
  role with no grants at all).
- **One reconciliation between `04-data-model.md` (pre-ADR-0003) and
  ADR-0003 (post), recorded explicitly rather than silently resolved**:
  `CITATION_VERDICT.verifier_rationale` still exists for human audit
  (US-005), but ADR-0003 gives the verifier model no free-text field to
  write into. It is now populated by application code from a small fixed
  set of strings (`pipeline/query_pipeline.py`'s `_rationale_for`), never
  from model output — see `db/models.py`'s module docstring.
- **`QUERY_LOG` gained a `refusal_reason` column**, not in the original
  Session 2 ERD — needed so the API layer can serve
  `05-api-contracts.md`'s three-value `refusal_reason` field without
  re-deriving it from child rows on every read. A small, additive schema
  decision made during implementation, recorded here rather than silently
  present only in the migration diff.
- **The non-negotiable proof test** (`tests/test_proof_session1_oauth2_case.py`):
  ingests the real, full 8-document Session 1 spike corpus, retrieves for
  the real query ("How do I set up 'Sign in with Google' as an OAuth2
  identity provider?" — spike Finding 2's 0.701-scoring case), and runs it
  through the real pipeline (`llm.factory.get_llm_client()`, so it
  automatically uses whichever tier is actually configured). **Passed —
  against the stub tier.** Per the task's explicit instruction and
  bookslot's Claim-A/Claim-B precedent, this is stated with full honesty
  in the test's own module docstring, in `SDLC-EVIDENCE.md`, and here: a
  passing result against `StubLLMClient` proves the pipeline **wiring**
  (ingestion → retrieval → generation → verification → refusal-gate all
  executed and reached a well-formed terminal decision) — it does **not**
  prove a real LLM verifier would correctly resist this case, because
  `StubLLMClient.verify()` is a crude keyword-overlap heuristic, not
  entailment reasoning. The test is written so that once a real
  `ANTHROPIC_API_KEY` exists, `llm.tier == "real"` and it automatically
  asserts the actual claim ADR-0001 requires evidence for
  (`answered is False`) instead of the wiring-only assertion.
- **Full backend CI wired to run against real infrastructure**, not
  mocked: `.github/workflows/ci.yml`'s `backend` job now provisions a real
  `pgvector/pgvector:pg16` service container and runs `alembic upgrade
  head` before `pytest` — the ADR-0002 grant-assertion test and the
  NFR-001 recall regression test are both meaningless against a mock
  database, so CI had to gain real Postgres to keep enforcing them. `ruff`,
  `mypy --strict`, `bandit`, and `pip-audit` all pass clean.
- **Verified `docker compose up` boots the real service end-to-end**, not
  just the ad-hoc test harness: built and started the actual `backend`
  container, confirmed migrations ran automatically on startup, and issued
  a live `POST /api/v1/corpora` smoke-test request against it successfully.
- `privacy-forge`, `laravel-consent-guard`, and `bookslot` were touched
  only to **read** `bookslot`'s `PaymentIntentGateway`/
  `FakePaymentIntentGateway`/`StripePaymentIntentGateway` files as the
  explicit pattern reference this session's task named — no files under
  those three repositories were modified.

## Files created or changed

**Backend application code (new):**
`backend/src/lexicon/config.py`; `db/{session,models}.py`;
`ingestion/{chunking,embeddings,service}.py`;
`retrieval/{keyword,vector,fusion,service}.py`;
`llm/{base,schemas,prompts,anthropic_client,stub_client,factory}.py`;
`pipeline/query_pipeline.py`;
`api/{schemas,deps,errors,corpora,documents,query,query_logs}.py`;
`main.py` rewritten to wire all routers plus the `{"error": ...}`
exception-handler shape `05-api-contracts.md` specifies.

**Migrations (new):** `backend/alembic.ini`, `alembic/env.py`,
`alembic/script.py.mako`, `alembic/versions/0001_initial_schema.py`
(full ERD plus ADR-0003's `injection_suspected` column),
`alembic/versions/0002_adr0002_app_role.py` (the restricted role).

**Tests (new, 33 total, all passing against real Postgres+pgvector):**
`conftest.py`, `support/spike_corpus.py`, `test_retrieval_guard.py`,
`test_chunking.py`, `test_ingestion_and_retrieval.py`,
`test_injection_hardening.py`, `test_pipeline_refusal_paths.py`,
`test_adr0002_grants.py`, `test_api_query.py`,
`test_proof_session1_oauth2_case.py`.

**Infra:** `backend/pyproject.toml` (new deps: `pgvector`, `fastembed`,
`anthropic`, `python-multipart`; `flake8-bugbear` immutable-calls
exception for FastAPI's `Depends()` pattern); `backend/Dockerfile`
(runs `alembic upgrade head` before `uvicorn`); `docker-compose.yml`
(backend service gains `DATABASE_ADMIN_URL`/`APP_DB_ROLE`/
`APP_DB_PASSWORD`/`ANTHROPIC_API_KEY`/`GENERATION_MODEL`/
`VERIFICATION_MODEL`); `.env`/`.env.example` (same additions, credential
left empty); `.github/workflows/ci.yml` (real Postgres service for the
`backend` job).

**Docs:** `docs/SDLC-EVIDENCE.md` (Implementation row filled in; new `4a`
row for the proof test's honest result); `docs/project-memory/08-
deployment-and-operations.md` (Configuration and secrets section — the
env-var wiring `03-architecture.md`'s open item asked Session 4 to
record; rest of that document remains an empty template, out of scope);
`docs/project-memory/12-session-handoff.md` (this file).

## Decisions made

- **Credentials: build against a labeled stub/real LLM client seam, not a
  permanent fake tier and not a blocked session** — reasoned explicitly
  above and in `08-deployment-and-operations.md`; structurally different
  from `bookslot`'s D-0036 because ADR-0001's whole premise requires real
  model behavior to prove, not just infra to reach.
- **Ingestion is synchronous this session, not async-worker-based** — a
  stated, scoped-down simplification against `03-architecture.md`'s design
  (see Work completed), not a silent deviation. Revisit when corpus scale
  or latency actually demands it.
- **PDF ingestion and MinIO object-storage upload are not implemented this
  session** — FR-001 and the data model still name them; this session's
  actual point was the generate/verify security pipeline, and the reused
  Markdown spike corpus didn't require either. Both remain real, tracked
  gaps against FR-001/the data model, not abandoned scope.
- **`CITATION_VERDICT.verifier_rationale` is application-generated, not
  model free text** — the explicit reconciliation between `04-data-model.md`
  (predates ADR-0003) and ADR-0003's "no free-text surface" hardening
  requirement. Recorded in `db/models.py` and here so it isn't rediscovered
  as a surprise inconsistency.
- **A concrete `max_question_length` (1000 chars) is set** — T-05's cost-
  abuse control, `06-security-threat-model.md` recommended this and
  explicitly deferred the number to a "Session 4 configuration decision,"
  which this session made. Not a measured value against real pricing (no
  provider integration exists yet) — a conservative placeholder, same
  honesty standard as NFR-007.
- **`QUERY_LOG.refusal_reason` added as a column** beyond Session 2's
  original ERD, for the reason stated in Work completed.

## Validation performed

- **33 tests pass against a real Postgres 16 + pgvector instance** (not
  mocked) — `docker exec`'d into a throwaway container on the project's own
  `docker-compose.yml` network, running `alembic upgrade head` then
  `pytest`. Re-run clean from scratch after every fix, not just once.
- **NFR-001 regression test**: recall@3 on the real Session 1 spike corpus,
  ingested through real application code (not the spike's throwaway
  script) — 100%, matching the spike's baseline exactly.
- **ADR-0002 grant-assertion test**: real `UPDATE`/`DELETE` attempts against
  all three audit tables via the actual application runtime role fail with
  `permission denied`; `SELECT` succeeds (positive control).
- **The proof test** (see Work completed) — passed against the stub tier
  only; this is wiring evidence, explicitly not entailment evidence. No
  claim is made here that ADR-0001's mechanism has been shown to work
  against a real model, because it hasn't been, and can't be until a real
  key exists.
- **`ruff check .`, `mypy --strict src`, `bandit -r src`, `pip-audit`** all
  pass clean. `pip-audit`'s only finding was the base image's bundled `pip`
  tool itself (7 known CVEs, none in an actual application dependency) —
  an environment artifact, not something this session's dependency
  additions introduced.
- **`docker compose up --build backend`** boots the real service: migrations
  ran automatically, `/health` returned `200`, and a live
  `POST /api/v1/corpora` request against the running container succeeded.
- Confirmed `privacy-forge`, `laravel-consent-guard`, and `bookslot` were
  not modified — `bookslot`'s Payment*Gateway files were read only, as the
  explicit pattern reference.

## Open questions and risks

- **The single largest open risk, unchanged in kind since Session 2/3,
  now sharper**: the verifier's real accuracy is still completely
  unmeasured. This session built the mechanism and its hardening
  correctly per the ADRs and proved the wiring works — it did not and
  could not measure whether a real model actually resists the OAuth2/JWT
  case or any adversarial injection pattern. **Getting a real
  `ANTHROPIC_API_KEY` is the single gating action before Session 5 can
  produce any real evidence at all** — restated here as plainly as
  possible so it cannot be missed.
- **Ingestion is synchronous and PDF/MinIO are unimplemented** — real,
  tracked gaps against `03-architecture.md`/FR-001, not forgotten. Revisit
  when corpus scale, latency, or a PDF-bearing corpus actually requires
  them; not needed for Session 5's evaluation harness, which can reuse the
  existing Markdown spike corpus and its successor golden set.
- **Rate limiting (NFR-007) is not implemented** — `03-architecture.md`
  and the threat model named Redis-backed per-corpus/per-caller rate
  limiting and a spend-ceiling circuit breaker as required controls; this
  session implemented the question-length cap (T-05's other named control)
  but not the rate limiter itself, since it wasn't necessary to exercise
  the generate/verify pipeline this session's task centered on. A real gap
  against the threat model's stated requirements, not a silent drop —
  needs to close before any real-traffic deployment.
- **Instance-level authentication remains undesigned**, carried forward
  unchanged from Sessions 2/3 — T-04/T-12's requirements on it are
  unaddressed, and this session added no auth/authz enforcement to any
  endpoint (every corpus/document/query endpoint is currently reachable by
  any caller who can reach the API). Still an explicit, pre-existing scope
  boundary, not a new gap this session introduced.
- **The adversarial injection test corpus (`06-security-threat-model.md`'s
  4-category design) was not built this session** — `test_injection_hardening.py`
  proves the *structural* difference between the two defenses (schema
  shape, sandwiching, enforced auto-fail), but does not run actual
  injection-attempt passages through a real model. That is explicitly
  Session 5's job, per ADR-0003's own Consequences section.

## Next recommended session

- Proposed session title: **Session 5 — Evaluation & Adversarial Testing**
  (this repository's second deep SDLC phase, Verification & Testing)
- Single objective: with a real `ANTHROPIC_API_KEY` provisioned, build the
  CI-gated evaluation harness — golden query set including the adjacent-
  but-wrong query class (Finding 2), refusal recall and citation accuracy
  measurement (NFR-002–004), and the committed adversarial injection test
  corpus (`06-security-threat-model.md`'s 4 categories, generator- and
  verifier-targeted suites scored separately, NFR-010's "0 successful
  injections" target) — and, as its first required test case, re-run
  `test_proof_session1_oauth2_case.py` against `llm.tier == "real"` and
  record the actual result.
- Inputs required: this handoff; `docs/adr/ADR-0001`, `ADR-0003`;
  `06-security-threat-model.md`; `07-testing-strategy.md` (currently an
  empty template — Session 5 is where it should actually get written);
  `backend/src/lexicon/llm/` and `pipeline/query_pipeline.py`
  (what's being evaluated); `backend/tests/test_proof_session1_oauth2_case.py`.
- Expected deliverables: a real Anthropic API key configured (blocking
  everything else); `eval/` or equivalent CI-gated harness; the committed
  adversarial corpus under `docs/security/adversarial-corpus/` or
  equivalent; NFR-002–004/NFR-010 measured for the first time with real
  numbers, replacing their current "not set — no fabricated number"
  placeholders; the proof test's real-tier result recorded honestly,
  whatever it is.
- Definition of done: the proof test passes against `llm.tier == "real"`
  (or, if it doesn't, that failure is itself the headline finding,
  investigated rather than hidden); the adversarial suite's pass/fail
  numbers are real, not assumed; refusal recall and citation accuracy have
  actual measured values.

## Paste-into-new-session context

**Project:** lexicon — grounded document Q&A system; every answer is
citation-backed or refused
**Track:** public flagship
**Repository state:** branch `main`, unreleased (pre-v0.1.0), Session 4
complete

**Problem being solved (validated Session 1):** teams with a bounded,
changing, authoritative document corpus need answers they can act on
without independently re-reading the source. See `00-project-brief.md` and
`00b-rag-vs-alternatives.md`.

**The central design decision from Session 2 (unchanged, now implemented):**
refusal cannot rely on retrieval similarity alone. An independent,
post-generation groundedness/entailment verification call gates every
answer before release. See `docs/adr/ADR-0001-groundedness-refusal-check.md`
and, as of this session, `backend/src/lexicon/pipeline/query_pipeline.py`
for the real implementation.

**Session 3's central finding, now hardened in real code:** the verifier
is a first-class attack target (T-02), structurally different from the
generator (T-01) and requiring a structurally different defense
(sandwiched delimiting, `injection_suspected` self-report, application-
enforced auto-fail, fail-closed-on-ambiguity — ADR-0003). Both are now
real, tested, and provably different implementations
(`llm/prompts.py`, `tests/test_injection_hardening.py`).

**This session's central finding:** the pipeline is real, correct against
the ADRs, and wired end-to-end (33 real-database tests, real CI, a real
`docker compose` boot) — but **every piece of evidence about whether the
verifier actually works against real model behavior is still zero**,
because no LLM provider credential exists in this environment. The proof
test ADR-0001 requires exists and passes, but only against a stub
heuristic — stated with total honesty, not allowed to read as more than it
is. Getting a real Anthropic API key is the one blocking action before any
real evidence can exist.

**Current stack:**
- Backend: FastAPI, Python 3.12 — now with real application code (see
  Files created or changed)
- Frontend: Next.js 15 (App Router) — still Session 0 skeleton, untouched
  this session (out of scope: task was backend pipeline only)
- Data: PostgreSQL + pgvector (real schema via Alembic, two-role
  permission split per ADR-0002), Redis (provisioned, not yet used —
  ingestion queue and rate limiting are both deferred), S3-compatible
  object storage (MinIO, provisioned, not yet wired into ingestion)
- Infra: Docker Compose (verified booting end-to-end), GitHub Actions CI
  (now runs against a real Postgres service)
- LLM provider: Anthropic Claude API, mid/high tier (`claude-sonnet-5`)
  for generation, small/fast tier (`claude-haiku-4-5`) for verification —
  **real client code exists and is believed correct against the
  documented SDK surface, but is unexercised: no API key in this
  environment.** Stub tier (`llm/stub_client.py`) is what actually ran
  every test this session.
- Testing: pytest (backend) — 33 tests, all against real Postgres+pgvector,
  no mocked database anywhere in the suite. Vitest (frontend) — still only
  the health-check skeleton.

**Architecture decisions that must not be reversed:**
- Licence AGPL-3.0.
- Next.js 15 + FastAPI/Python 3.12, frozen against the portfolio ledger.
- Exactly two deep SDLC phases: Discovery & Planning (complete),
  Verification & Testing (Session 5, next).
- Learning budget exactly 2 (RAG evaluation methodology; LLM
  guardrails/prompt-injection defence) — at cap.
- Hybrid keyword search must use OR semantics, never `plainto_tsquery` —
  now a permanent code-level test guard, not just a written rule.
- Refusal is post-generation groundedness/entailment verification, a real
  separate LLM call, never a similarity threshold — now real code, not
  just a design decision.
- The verification call implements ADR-0003's exact hardening contract —
  now real code (`llm/prompts.py`, `llm/schemas.py`), proven structurally
  distinct from the generator's defense by a dedicated test file.
- The audit trail's append-only property is enforced by database
  permission grants (ADR-0002) — now real, migrated, and proven by a
  grant-assertion test against a live connection, not a config review.
- LLM provider is Anthropic Claude, with model-tier asymmetry for cost
  control — real client code exists for this; a real key is the only
  thing missing to exercise it.
- **New this session, do not reverse without a documented reason:**
  `llm.factory.get_llm_client()`'s tier-selection seam
  (`ANTHROPIC_API_KEY` set → real client; unset → stub) is the mechanism
  that makes "add a real key" a config change instead of a rewrite —
  don't hard-wire either client concretely anywhere application code
  (`pipeline/query_pipeline.py`, `api/*.py`) depends on `LLMClient`.

**Implementation state:**
- Done: full discovery/planning/architecture/security documentation
  (Sessions 1–3); repository skeleton, licence, governance docs,
  docker-compose, CI; **and now (Session 4)**: real ingestion, real hybrid
  retrieval, the real two-call generate/verify pipeline with ADR-0003
  hardening, the ADR-0002 database permission split, 33 passing tests
  against real infrastructure, and the ADR-0001-mandated proof test
  (passing at the wiring-evidence level only).
- In progress: nothing mid-flight.
- Not started / explicitly deferred: rate limiting (NFR-007), PDF
  ingestion, MinIO object-storage upload, async ingestion worker, instance-
  level authentication, the Session 5 evaluation harness and adversarial
  corpus, anything requiring a real LLM call to actually happen.

**Constraints and non-goals:**
- Full non-goals table: `docs/project-memory/01-scope-and-non-goals.md`.
- `max_question_length` (1000 chars, T-05) is a Session 4 placeholder
  number against no real pricing data, same discipline as NFR-007's
  existing "not set here — no fabricated number" pattern for the rest of
  cost control.

**Task for the next session (single objective):**
Evaluation & Adversarial Testing: provision a real Anthropic API key first
(the one gating action), then build the CI-gated evaluation harness and
adversarial injection corpus, and record the proof test's real-tier result
honestly.

**Definition of done:**
- A real `ANTHROPIC_API_KEY` is configured.
- `test_proof_session1_oauth2_case.py` passes (or its real failure is the
  headline finding) against `llm.tier == "real"`.
- NFR-002–004 and NFR-010 have actual measured values, not placeholders.
- The adversarial corpus is committed, with generator- and verifier-
  targeted results scored and reported separately.

**Files to attach or paste:**
- `docs/project-memory/12-session-handoff.md` (this file)
- `docs/adr/ADR-0001-groundedness-refusal-check.md`
- `docs/adr/ADR-0002-audit-trail-tamper-evidence.md`
- `docs/adr/ADR-0003-verification-injection-hardening.md`
- `docs/project-memory/06-security-threat-model.md`
- `backend/src/lexicon/llm/` (the client seam being evaluated)
- `backend/src/lexicon/pipeline/query_pipeline.py`
- `backend/tests/test_proof_session1_oauth2_case.py`

**Ground rules:** Do not change the stack. Do not introduce a third new
technology. Do not expand the deep-SDLC-phase count beyond two. Do not
touch `privacy-forge`, `laravel-consent-guard`, or `bookslot`. Do not let
a stub-tier test result be reported or remembered as if it were evidence
about real model behavior — that distinction must survive into every
future session's understanding of what Session 4 actually proved. Ask
before introducing any new dependency or scope item not already
anticipated above.
