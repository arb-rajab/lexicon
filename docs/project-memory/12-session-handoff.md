# Session Handoff

## Retroactive entry — Session 8 (backfilled by Session 10)

Session 8 (`802c412`, "Session 8: write the case study, refresh README
status, finalize SDLC evidence") never wrote its own entry to this file —
first noticed and named by Session 9 (see below), left unbackfilled at
the time as out of Session 9's stated scope. Verified retroactively:
`git show --stat 802c412` and `git diff 363cf7b 802c412 --stat` both
confirm the commit changed exactly `README.md` (+92/-23 area),
`docs/CASE-STUDY.md` (new, 324 lines), and `docs/SDLC-EVIDENCE.md` (+55),
matching the commit message's own description — the case study's honest
account of Session 1's spike finding, ADR-0003's injection-hardening
results, the ADR-0004 descoping decision, and Session 7's four real bugs;
the README status-banner refresh; and SDLC-EVIDENCE.md's Phase 1/5/7
corrections. `main` was confirmed up to date with `origin/main` at the
time of this check, so the commit was genuinely pushed, not merely
committed locally. No work is missing — only this handoff paragraph was
skipped at the time.

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` history is tagged `v1.0.0` at
  Session 9; this session's work lands on a feature branch, opened as a
  PR rather than pushed direct-to-main — the first PR this repository has
  ever had (see Decisions made).

## Session completed
- Session number and title: **Session 11 — Close the T-04/T-05/T-06
  security-threat-model gaps: real multi-corpus authorisation, query
  rate-limit/spend-ceiling/length-cap, and upload size bound.**
- Objective, as given at the start of this session: the API had grown a
  full multi-corpus surface with **zero** authorisation between a caller
  and a `corpus_id` — top priority, fix first and don't let the other two
  crowd it out. Second: no rate limit, spend ceiling, or length cap on the
  query endpoint, a real cost-DoS surface the moment a real
  `ANTHROPIC_API_KEY` is ever configured. Third: the upload endpoint is
  unbounded despite `05-api-contracts.md` documenting a `413` response
  that no code enforced. Ground rule: scope to these three surfaces, don't
  rearchitect the app, don't touch the LLM-stub/real-key selection logic
  itself. Status: **complete** for all three, with one pre-existing gap
  (T-06's soft per-corpus document-count warning) explicitly still open,
  not claimed done.

## Work completed

- **T-04 — real per-corpus ownership scoping (the priority item).**
  Confirmed directly, not assumed, that `ANTHROPIC_API_KEY` is still unset
  in this environment (`llm/factory.py` still selects `StubLLMClient`) —
  the cost-DoS surface below is real risk on activation, not present risk
  today. Added `CORPUS.owner_id` (migration `0003`), a trusted-header
  caller identity (`lexicon/api/auth.py`: `X-User-Id`, modeled on a
  reverse-proxy/gateway-injected-identity pattern, since instance-level
  authentication itself stays explicitly deferred to
  `08-deployment-and-operations.md` — this session did not reverse that
  boundary, only built the per-resource authorisation T-04 always required
  on top of whatever identity eventually arrives there), and a single
  shared ownership check (`lexicon/api/ownership.py:require_owned_corpus`)
  applied to every `{corpus_id}`-scoped endpoint across all four routers
  (corpora, documents, query, query-logs). `GET /api/v1/corpora` is now
  scoped to the caller's own corpora, not the whole deployment's.
  Regression proof: `backend/tests/test_corpus_authorization.py` — two
  distinct callers, cross-corpus access attempted against every scoped
  endpoint (read, upload, delete, query, audit-log read), each asserted
  `403`; missing-identity requests asserted `401`; `GET /corpora` listing
  scoping asserted directly.
- **T-05 — query-endpoint rate limit, spend ceiling, and length cap.**
  The question-length cap (`max_question_length`) already existed from
  Session 4 and was left as-is. Added, Redis-backed
  (`lexicon/api/rate_limit.py`), both enforced in `api/query.py` *before*
  the pipeline makes any real LLM call: a per-corpus fixed one-minute
  request-rate limit and a separate daily per-corpus spend ceiling (a
  query-count proxy for spend — no real per-call cost feed exists in this
  environment, ADR-0004 — stated as a conservative placeholder, not a
  silently assumed dollar figure). Both return `429` with a real
  `Retry-After` header; a Redis outage fails *open* (logged), a
  deliberate availability tradeoff distinct from ADR-0003's fail-closed
  verifier gate — argued explicitly in the module docstring, not left
  implicit. **A real bug found and fixed while proving this**:
  `main.py`'s custom `StarletteHTTPException` handler built its
  `JSONResponse` without forwarding `exc.headers`, silently dropping
  `Retry-After` (and any other header a route ever attaches to an error
  response) — never manifested before because no prior route set response
  headers on an exception. Fixed by passing `headers=exc.headers` through.
  Regression proof: `backend/tests/test_query_rate_limit.py` — burst
  triggers the rate limit, sustained-but-under-burst triggers the spend
  ceiling once reached, and per-corpus scoping is asserted directly (one
  corpus hitting its limit does not affect another's).
- **T-06 — real upload size enforcement.** `05-api-contracts.md` has
  named a `413` "exceeds the configured size limit" response since
  Session 2; nothing in `api/documents.py` ever produced it —
  `await file.read()` buffered an unbounded body into memory
  unconditionally. Replaced with a bounded chunked read
  (`_read_bounded`, 1 MiB chunks, checked against a running total, not
  against the client-supplied and untrustworthy `Content-Length` header)
  that aborts with a real `413` as soon as the configured
  `max_upload_size_bytes` (conservative placeholder, 10 MiB) is crossed,
  before the oversized body is ever fully buffered. The soft
  per-corpus document-count warning T-06's mitigation also names is
  **not** built this session — named here as still open, not silently
  dropped. Regression proof: `backend/tests/test_document_upload_size_limit.py`.
- **Test-fixture fallout from the new non-nullable `CORPUS.owner_id`
  column**: `tests/support/spike_corpus.py`, `tests/security/
  adversarial_corpus_loader.py`, and `tests/test_pipeline_refusal_paths.py`
  each construct a `models.Corpus` directly (bypassing the API layer, so
  no `X-User-Id` header applies) — all three updated to pass a fixed
  `owner_id="test-fixture"`. `tests/test_api_query.py`'s existing suite
  updated to send `X-User-Id` on every call now that it's required, plus
  one new `401`-on-missing-identity case.
- **CI gained a Redis service** (`.github/workflows/ci.yml`) — the
  backend job had never provisioned one; T-05's controls need a real
  instance for the same reason the existing Postgres service does
  (`conftest.py`'s own ground rule: no ADR-0002/NFR-001-style test is
  honest against a mock). Host port `6380` matches `docker-compose.yml`'s
  dev port so `config.py`'s `REDIS_URL` default resolves with no CI-side
  override.
- **Docs reconciled with what the code actually does, not left stale
  behind it**: `05-api-contracts.md`'s Authentication/authorisation
  section and rate-limit bullet, `06-security-threat-model.md`'s T-04/
  T-05/T-06 table rows and the Cost-abuse/Authentication sections, and
  `02-requirements.md`'s Roles-and-permissions note (which had literally
  stated "no multi-tenant... model in v1" for a product whose real API
  was already a full multi-corpus surface) all updated in place, each
  naming what changed and why rather than quietly rewriting history.
- `.env.example` documents the four new settings
  (`MAX_QUESTION_LENGTH` restated for completeness,
  `QUERY_RATE_LIMIT_PER_MINUTE`, `QUERY_DAILY_SPEND_CEILING`,
  `MAX_UPLOAD_SIZE_BYTES`).

## Files created or changed

- `backend/src/lexicon/api/auth.py` (new) — `CallerContext`, `get_caller`
- `backend/src/lexicon/api/ownership.py` (new) — `require_owned_corpus`
- `backend/src/lexicon/api/rate_limit.py` (new) — rate limit + spend
  ceiling
- `backend/src/lexicon/api/corpora.py`, `documents.py`, `query.py`,
  `query_logs.py` — ownership checks wired in; `query.py` gets the
  rate-limit/spend-ceiling gate; `documents.py` gets the bounded upload
  read
- `backend/src/lexicon/api/deps.py` — `get_redis`
- `backend/src/lexicon/api/errors.py` — `forbidden()`
- `backend/src/lexicon/main.py` — `Retry-After`/header-forwarding fix in
  the `StarletteHTTPException` handler
- `backend/src/lexicon/config.py` — four new settings
- `backend/src/lexicon/db/models.py` — `Corpus.owner_id`
- `backend/alembic/versions/0003_corpus_ownership.py` (new)
- `backend/tests/test_corpus_authorization.py` (new)
- `backend/tests/test_query_rate_limit.py` (new)
- `backend/tests/test_document_upload_size_limit.py` (new)
- `backend/tests/test_api_query.py`, `tests/support/spike_corpus.py`,
  `tests/security/adversarial_corpus_loader.py`,
  `tests/test_pipeline_refusal_paths.py` — fixture/auth-header updates
- `.github/workflows/ci.yml` — Redis service added to the backend job
- `.env.example` — new settings documented
- `docs/project-memory/05-api-contracts.md`,
  `06-security-threat-model.md`, `02-requirements.md` — reconciled with
  implementation, per Work completed above
- `CHANGELOG.md` — new `## [Unreleased]` entries

## Decisions made

- **Ownership scoping is per-corpus, uniformly, rather than adding the
  corpus-owner/knowledge-worker RBAC split within a shared corpus.** The
  task's own ground rule ruled out rearchitecting the app, and there is no
  membership/grant table for a non-owner caller to share access to
  someone else's corpus — building one is exactly the kind of new
  multi-user data model this session was scoped away from. Every corpus
  is therefore its own tenant, scoped to its creator; the
  owner/knowledge-worker distinction `02-requirements.md` describes
  remains a real but *unenforced-within-a-corpus* distinction, named as
  such in that document's own updated note rather than silently
  conflated with what this session actually built.
- **Caller identity is a trusted header (`X-User-Id`), not a new session/
  login system.** `05-api-contracts.md` has always deliberately declined
  to invent an instance-level auth mechanism ahead of an operator
  decision that still doesn't exist; inventing one now to close T-04
  would have been a bigger scope change than the gap itself warranted.
  The header-trust model is the same one a reverse-proxy/gateway sits in
  front and performs in production (already how this document frames the
  operator/deployment boundary) — this session's contribution is the
  authorisation *check* T-04 always required, not a new authentication
  *mechanism*.
- **The spend ceiling counts queries, not dollars.** No live per-call
  token-cost feed exists in this environment (ADR-0004's permanent
  boundary) — inventing a fabricated per-token dollar estimate would have
  been less honest than a stated, conservative count-based proxy. Matches
  this project's existing precedent (`max_question_length`'s own
  "conservative placeholder, not a measured value" framing).
- **Redis rate-limit/spend-ceiling failures fail open, not closed.**
  Unlike ADR-0003's verifier gate (a correctness invariant where
  ambiguity must fail closed), an unreachable rate limiter is an
  availability concern — failing closed here would let a Redis blip take
  down query answering entirely, a worse outcome than temporarily losing
  the cost-abuse backstop while the question-length cap (which needs no
  external dependency) still holds.
- **This session opens a PR instead of pushing to `main` directly.**
  Every prior session in this repository's history pushed straight to
  `main` (`git log` confirms zero prior PRs) — this session adopts the
  portfolio-wide PR convention going forward, per this session's own
  instructions, rather than continuing the direct-push pattern silently.

## Validation performed

Real local Postgres 16 + pgvector 0.6.0 and Redis were provisioned in
this session's own sandbox (no Docker daemon available here) to run the
suite against real infrastructure, matching this project's standing
"no ADR-0002/NFR-001-style test against a mock" rule:

- `ruff check .` — all checks passed.
- `mypy src` (strict) — no issues, 36 source files.
- `bandit -r src` — no issues, 1693 lines scanned.
- `alembic upgrade head` — clean, migration `0003` applies without error.
- `pytest -q` — **35 passed**, 12 failed. **Every failure is the same
  root cause, confirmed by traceback, not assumed**: this sandbox's
  outbound network policy blocks `huggingface.co` (`/root/.ccr/README.md`'s
  documented "do not retry or route around a policy denial"), so
  `fastembed`'s first-run ONNX model download fails for every test that
  exercises real ingestion/retrieval — a pre-existing dependency of this
  project's test suite, unrelated to and unaffected by this session's
  change, and not something this sandbox can route around. This session's
  own three new test files, plus every auth/rate-limit/upload-size case,
  pass cleanly; the four query-embedding-dependent cases in the new
  rate-limit suite were additionally made independent of that network
  call entirely (stubbing `retrieval/service.embed_query` — the rate
  limiter, not embedding quality, is what's under test there) and are
  confirmed green in this sandbox, not merely expected to pass in CI.
  CI itself has real internet access (every prior session's recorded
  `pytest` runs confirm this), so the 12 network-blocked cases are
  expected green there.
- Found and fixed one real bug while validating the `Retry-After` header
  contract directly (a monkeypatched-embedding smoke test against the
  real `TestClient`, not just the isolated `rate_limit.py` unit logic) —
  see the `main.py` fix under Work completed above; re-verified green
  after the fix.

## Open questions and risks

Carried forward, still true, unaffected by this session's scope:

- No CI job builds or exercises either production image or
  `docker-compose.prod.yml` — all deployment evidence remains from local,
  manual verification (Session 7).
- Metrics, tracing, dashboards, and alerting remain genuinely unbuilt.
- The central ADR-0004 boundary is permanent for this project's current
  lifecycle: real LLM provider verification quality is not, and cannot
  be, proven in this environment.

New from this session:

- **`X-User-Id` is only as trustworthy as whatever sits in front of this
  service in a real deployment.** This session does not and cannot verify
  that header — it authorises against it. A production deployment must
  terminate and verify caller identity at a trusted boundary (reverse
  proxy/gateway) before traffic reaches this app, exactly as
  `05-api-contracts.md`'s auth section states; this remains true, not
  newly introduced, but now has real enforcement code depending on it
  being honored.
- **T-06's soft per-corpus document-count warning is still not built** —
  named as open in the threat-model table update, not silently dropped.
- **The daily spend ceiling's query-count proxy has never been validated
  against real provider spend** — it cannot be, in an environment with no
  real `ANTHROPIC_API_KEY` (ADR-0004). Revisit the actual ceiling number
  once real usage data exists.
- **Redis is now a hard dependency of the query endpoint's cost controls**
  (fail-open, not fail-closed, so query answering itself still works
  without it) — `docker-compose.yml` already provisions it with a
  healthcheck, and CI now does too, but this is the first application
  code path that actually calls it (previously provisioned but unused,
  per Session 7's own note in `main.py`).
