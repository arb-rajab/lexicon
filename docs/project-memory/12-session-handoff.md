# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Session completed
- Session number and title: **Session 7 — Release Readiness (Production
  Images, Local Deployment Proof)**
- Objective, as given at the start of this session: build a production-shaped
  Docker image for both services, a `docker-compose.prod.yml` proving the
  real stack (Postgres+pgvector, Redis, MinIO, backend, frontend) boots and
  serves real traffic locally, basic honestly-scoped observability, and a
  real end-to-end proof of the ingest/query/answer-or-refusal pipeline
  against that production-shaped stack — mirroring privacy-forge's own
  "Deployment Session A" pattern (real production Dockerfile, proven
  end-to-end locally, no real cloud spend), applying this portfolio's
  already-established precedent (privacy-forge's live-demo descoping,
  bookslot's cloud-provisioning descoping) without relitigating it. Status:
  **complete.**

## A correction made before the rest of this session's work

This session's own task framing described "structured logging" as
"already partially present given the audit-table work from Session 6."
That was checked first, before building on it, and found **not accurate**:
`QUERY_LOG`/`RETRIEVED_CHUNK`/`CITATION_VERDICT` (`db/models.py`,
ADR-0002) are a permanent, tamper-evident **audit trail** of pipeline
decisions, stored in Postgres — not operational log lines, and never
routed through Python's `logging` module. `grep -r "import logging"
backend/src` matched nothing outside `alembic/env.py` before this session.
`backend/src/lexicon/logging_config.py` is what actually adds structured
**operational** logging this session — a distinct, complementary concern,
documented as such in that module's own docstring so a future reader
doesn't re-make the same conflation. Stated here per this project's
own discipline of correcting assumptions rather than quietly building on
top of them.

## Credential status — unchanged, re-confirmed against a new artifact

No Anthropic API key (or any other LLM provider credential) exists in
this environment, and none ever will in this project's current lifecycle,
by the project owner's deliberate, permanent choice (ADR-0004). **What
this session added:** the credential-swap claim (Session 4's original —
"setting `ANTHROPIC_API_KEY` is a config change, not a rewrite") had only
ever been demonstrated against the dev image or in-process. This session
re-ran it against the actual production image, `lexicon-backend-prod:latest`,
using the same image both times, no rebuild between runs:

```
$ docker run --rm lexicon-backend-prod:latest \
    python -c "from lexicon.llm.factory import get_llm_client; \
               c = get_llm_client(); print(type(c).__name__, c.tier)"
StubLLMClient stub

$ docker run --rm -e ANTHROPIC_API_KEY=sk-ant-placeholder-not-a-real-credential \
    lexicon-backend-prod:latest \
    python -c "from lexicon.llm.factory import get_llm_client; \
               c = get_llm_client(); print(type(c).__name__, c.tier)"
AnthropicLLMClient real
```

Safe to run with no real key and no real spend: `anthropic.Anthropic()`'s
constructor (`llm/anthropic_client.py`) makes no network call — it only
builds the SDK client object. The placeholder value above is not a real
credential and was never sent anywhere.

## Work completed

- **Read `docs/project-memory/12-session-handoff.md` (Session 6's
  version) and `08-deployment-and-operations.md` first**, per this
  session's own explicit instruction. Found the latter almost entirely
  empty template beyond a Configuration-and-secrets section Session 4
  had written.
- **Surveyed the existing repo state** before writing anything: the dev
  Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`), the dev
  `docker-compose.yml`, `llm/factory.py`/`config.py`'s credential-swap
  seam, and confirmed (via `grep`) that Redis is declared in config but
  never imported anywhere in `backend/src` outside a comment, and MinIO
  is likewise provisioned but unused — `ingestion/service.py`'s own
  docstring already said as much for MinIO; this session confirmed the
  same is true of Redis and recorded it in `08-deployment-and-operations.md`
  so `/ready`'s scope (Postgres only, below) doesn't read as an oversight.
- **Built `backend/docker/Dockerfile.prod`** — two-stage build. Stage 1
  installs a new `prod` extras group (`pyproject.toml`, adds `gunicorn`
  only). Stage 2 is a slim runtime image, non-root `lexicon` user (uid
  1000), and pre-warms the `BAAI/bge-small-en-v1.5` fastembed/ONNX model
  into a fixed, image-baked cache directory at build time (added after
  finding the first-request live-download problem below).
  `backend/docker/entrypoint.prod.sh` runs the same `alembic upgrade head`
  (as `DATABASE_ADMIN_URL`) the dev image's CMD already does, then execs
  `gunicorn lexicon.main:app --worker-class uvicorn.workers.UvicornWorker
  --workers "${WEB_CONCURRENCY:-4}" ...` instead of bare `uvicorn`.
- **Built `frontend/docker/Dockerfile.prod`** — three-stage build using
  Next.js "standalone" output (`next.config.ts`'s new `output:
  "standalone"`). Final stage runs as `node:22-slim`'s existing non-root
  `node` user (an earlier attempt to `useradd --uid 1000` a new user
  failed — that uid already exists in the base image; fixed by reusing
  it instead).
- **Built `docker-compose.prod.yml`** (repo root) — real
  Postgres+pgvector/Redis/MinIO (same images `docker-compose.yml` already
  uses) plus `backend`/`frontend` built from the two Dockerfiles above.
  Distinct host ports from the dev stack (`8011`/`3002`/`5434`/`6381`/
  `9010`-`9011`) so both can run at once, mirroring privacy-forge's own
  `docker-compose.prod.yml` convention for the identical reason.
  **TLS was deliberately not added** — reasoned explicitly in
  `08-deployment-and-operations.md` rather than either copying
  privacy-forge's Caddy/`tls internal` setup by default or silently
  omitting it: privacy-forge's TLS work exists because that project's
  brief made an explicit decision to stand up a public demo instance;
  lexicon has no equivalent decision anywhere in its own project memory,
  and `06-security-threat-model.md`'s trust boundaries don't name public
  exposure at all. Adding TLS here would prove a capability nothing in
  lexicon's own scope has asked for.
- **Added structured operational logging** (`backend/src/lexicon/
  logging_config.py`) — JSON-lines to stdout, `LOG_LEVEL`-controlled,
  uvicorn's/gunicorn's own loggers routed through the same formatter —
  plus a request-logging middleware in `main.py` (`request_id`, `method`,
  `path`, `status_code`, `duration_ms` per request, `X-Request-ID`
  response header).
- **Added `GET /ready`** (`main.py`) alongside the existing `GET /health`
  — a real split, not two names for one check. `/health` stays
  liveness-only (unchanged since Session 4); `/ready` runs a real
  `SELECT 1` against Postgres and returns 503 on failure. Deliberately
  does not check Redis/MinIO (see the survey finding above — no code path
  depends on either yet, so asserting readiness against them would be
  dishonest). `docker-compose.prod.yml`'s `backend` healthcheck targets
  `/ready`, not `/health`.
- **Built and booted the full production-shape stack, iteratively, fixing
  three real bugs found in the process** (all detailed with full
  reasoning in `08-deployment-and-operations.md`'s Deployment procedure
  section; summarized here):
  1. `api/documents.py`'s `upload_document` (an `async def` route) called
     the synchronous, CPU-bound `ingest_document` inline, blocking the
     event loop for the duration of every real upload. Invisible under
     dev's bare `uvicorn --reload`; under `docker/Dockerfile.prod`'s
     gunicorn, this blocked the worker's heartbeat to the arbiter, which
     killed the worker mid-upload (`WORKER TIMEOUT`, `SIGABRT`) —
     observed for real, twice, in this session's own container logs
     before being diagnosed. **Fixed** via
     `starlette.concurrency.run_in_threadpool`. Full 35-test backend
     suite re-run and confirmed still passing after this change.
  2. The same first real embedding call also triggered a live ~20-30s
     HuggingFace model download inside the request (observed directly in
     container logs — `Fetching 5 files: 100%|...`), compounding bug 1 and
     adding a live external network dependency to the request path.
     **Fixed** by pre-warming the model into the image at build time
     (`EMBEDDING_CACHE_DIR`, `backend/docker/Dockerfile.prod`) —
     confirmed by re-running the full 8-document ingestion with no
     further worker timeouts and no HuggingFace fetch log lines.
  3. The `frontend` container reported Docker-health `unhealthy`
     continuously (`FailingStreak: 132` observed after 31 hours) despite
     serving real traffic correctly over its published port. Root cause:
     Docker auto-injects `HOSTNAME=<container id>` into every container;
     Next's standalone `server.js` binds to `process.env.HOSTNAME` if
     set, resolving it via `/etc/hosts` to the container's one assigned
     IP rather than all interfaces — so the healthcheck's own
     loopback-based `fetch('http://localhost:3000/...')`, run from
     inside that same container, connection-refused every cycle.
     **Fixed** by pinning `HOSTNAME=0.0.0.0` explicitly, both in
     `docker-compose.prod.yml`'s `frontend.environment` (what actually
     takes effect under compose) and in `frontend/docker/Dockerfile.prod`
     itself (a `docker run`-without-compose fallback) — confirmed by
     recreating the container and watching Docker's own reported health
     status flip from `unhealthy` to `healthy`.
- **Proved the full pipeline through the production images, for real,
  reusing the Session 1 spike corpus** (as Session 5's golden dataset and
  Session 6's own harness both already do) — created a corpus via
  `POST /api/v1/corpora`, uploaded all 8 spike documents via
  `POST .../documents`, ran two real queries via `POST .../query`:
  - `"How do I check a plaintext password against a stored hash at
    login?"` (golden dataset's `legit-oauth2-password-check`) →
    ```json
    {"query_log_id":"d2d211b8-73ba-4f73-a61a-e7a41dba758a","answered":true,
     "answer":"How do I check a plaintext password against a stored hash at login.",
     "citations":[{"chunk_id":"e1dfe1a9-a0c8-4f61-ab4c-aac21b47293b",
       "document_id":"5ef1998b-334b-4e1b-80ce-5d3716c19148",
       "source_filename":"oauth2-jwt.md",
       "section_heading":"Hash and verify the passwords { #hash-and-verify-the-passwords }",
       "claim_text":"How do I check a plaintext password against a stored hash at login"}],
     "refusal_reason":null,"retrieved_chunk_count":5}
    ```
  - `"How do I set up 'Sign in with Google' as an OAuth2 identity
    provider?"` (the canonical Session 1/ADR-0001 adjacent-but-wrong
    case) →
    ```json
    {"query_log_id":"9bae560f-2af7-419e-bb0e-cbc482fb035b","answered":false,
     "answer":null,"citations":[],"refusal_reason":"verification_failed",
     "retrieved_chunk_count":5}
    ```

  **Same stub-tier-vs-real-quality caveat as every session since
  ADR-0004: this is real evidence the production images serve the real,
  wired pipeline correctly end-to-end — it is not evidence of real model
  entailment quality**, since `ANTHROPIC_API_KEY` is unset in this
  environment (see Credential status above).
- **Re-confirmed the credential-swap point against the production image
  specifically** — see Credential status above for the exact commands and
  output.
- **Rewrote `docs/project-memory/08-deployment-and-operations.md`** — was
  almost entirely an empty template (only Configuration and secrets had
  real content, from Session 4); now has real content in every section,
  including the three bugs above, the TLS reasoning, and an honest
  Observability split between what's real today and what's genuinely
  future work (metrics, tracing, log aggregation, dashboards/alerting —
  none built, none silently assumed).
- **Updated `docs/SDLC-EVIDENCE.md`'s Phase 6 row** — extended with this
  session's real evidence; kept at **Baseline** depth per
  `07-testing-strategy.md`'s existing deep-phase budget rule (exactly
  two deep phases: Discovery, Verification/Testing) — this session adds
  real evidence within that budget, not a request to expand it.
- **Ran the full existing backend test suite (35 tests) plus ruff/mypy
  strict/bandit against a real Postgres**, after all source changes
  (`api/documents.py`, `config.py`, `ingestion/embeddings.py`,
  `logging_config.py`, `main.py`) — see Validation below for the exact
  result.
- **Ran the frontend's existing `lint`/`build`/`test` scripts locally**
  after `next.config.ts`'s `output: "standalone"` change — all three
  still pass; the standalone output only adds an extra build artifact,
  it doesn't change `next dev`, `eslint`, or `vitest`'s behavior.
- `privacy-forge`, `laravel-consent-guard`, and `bookslot` were not
  touched, read, or modified this session (privacy-forge's own
  `docker-compose.prod.yml` and `08-deployment-and-operations.md` were
  read for reference on the established pattern, per this session's own
  instruction to mirror it — never written to).

## Files created or changed

- `backend/docker/Dockerfile.prod` (new) — production backend image
- `backend/docker/entrypoint.prod.sh` (new) — migrate-then-serve entrypoint
- `frontend/docker/Dockerfile.prod` (new) — production frontend image
- `frontend/public/.gitkeep` (new) — the standalone build's runner stage
  expects a `public/` directory to exist; none did before this session
- `docker-compose.prod.yml` (new, repo root) — the production-shape stack
- `backend/pyproject.toml` — new `prod` optional-dependencies group (`gunicorn`)
- `backend/src/lexicon/config.py` — new `log_level`, `embedding_cache_dir` settings
- `backend/src/lexicon/logging_config.py` (new) — structured JSON logging
- `backend/src/lexicon/main.py` — logging configured at import time,
  request-logging middleware, new `GET /ready` endpoint
- `backend/src/lexicon/api/documents.py` — `upload_document`'s ingestion
  call moved through `run_in_threadpool` (bug 1 above)
- `backend/src/lexicon/ingestion/embeddings.py` — `_model()` now passes
  `cache_dir=settings.embedding_cache_dir` through to `TextEmbedding`
- `frontend/next.config.ts` — `output: "standalone"`
- `docs/project-memory/08-deployment-and-operations.md` — rewritten from
  an almost-empty template to real content in every section
- `docs/SDLC-EVIDENCE.md` — Phase 6 row extended
- `docs/project-memory/12-session-handoff.md` (this file, rewritten)

## Decisions made

- **TLS/reverse-proxy was deliberately not added** — see Work completed
  above and `08-deployment-and-operations.md`'s Deployment procedure
  section for the full reasoning. Not a cost-cutting shortcut: lexicon
  genuinely has no prior decision or threat-model boundary that TLS would
  be answering.
- **The embedding model is baked into the production image at build
  time, not left to download lazily.** Found necessary, not just
  nice-to-have, once bug 1 and bug 2 above were understood together — a
  production image that depends on a live third-party download during its
  very first real request is a real reliability and latency problem
  independent of the gunicorn-timeout interaction that first surfaced it.
- **`/ready` checks only Postgres, not Redis or MinIO.** A readiness
  check that asserts a dependency the application doesn't actually use
  yet would be dishonest, not merely incomplete — matching this project's
  standing discipline (ADR-0004's stub-tier labeling, `07-testing-strategy.md`'s
  Known gaps) of stating what's real precisely rather than rounding up.
- **Phase 6 stays at Baseline depth in `SDLC-EVIDENCE.md`**, not promoted
  to Deep, despite substantial new evidence — `07-testing-strategy.md`'s
  deep-phase budget (Discovery, Verification/Testing, exactly two) is an
  existing project rule this session didn't relitigate.

## Validation performed

- **Both production images build successfully** (`docker build -f
  backend/docker/Dockerfile.prod backend`, `docker build -f
  frontend/docker/Dockerfile.prod frontend`) — confirmed via direct build
  output, not assumed.
- **`docker-compose.prod.yml` brings up all five services to Docker's own
  `healthy` status** — confirmed via `docker compose ... ps`, re-checked
  after each of the three bug fixes above until all five were genuinely
  healthy simultaneously (not merely running).
- **Full ingest → query → answer/refusal pipeline proven through the
  running production containers via real HTTP calls** (`curl` against
  the published backend port) — see Work completed above for the exact
  requests and real, captured JSON responses.
- **Credential-swap point re-run against `lexicon-backend-prod:latest`
  twice, same image, no rebuild** — see Credential status above for the
  exact commands and output.
- **Full backend test suite re-run after all source changes**: `ruff
  check .`, `mypy src` (strict), `bandit -r src`, and `pytest -q` (35
  tests) run together against a real Postgres+pgvector instance — run
  once immediately after the `api/documents.py` fix (35 passed) and again
  as a combined check after every backend source change in this session
  was in place. **That combined run caught a real `ruff` failure**
  (`ingestion/embeddings.py:18` — the new `cache_dir=` argument pushed the
  line to 101 characters, over this project's 100-character limit) —
  fixed by wrapping the call across two lines. The backend prod image was
  rebuilt on the fixed code (confirmed working, including a from-scratch
  `--no-cache` rebuild), and the full combined check (`ruff`, `mypy
  --strict`, `bandit`, `pytest -q`) was re-run clean end to end afterward:
  `All checks passed!`; `Success: no issues found in 33 source files`;
  `35 passed in 715.83s`. (Two intermediate re-run attempts hit transient
  PyPI-connectivity errors and an unrelated host Docker Desktop restart
  mid-session — both environment blips, not code issues; the third
  attempt, after the host network and Docker daemon settled, passed
  clean.)
- **Frontend `npm run lint`, `npm run build`, `npm test` all still pass**
  after `next.config.ts`'s `output: "standalone"` change.
- Confirmed `privacy-forge`, `laravel-consent-guard`, and `bookslot` were
  not modified this session (git status / directory listing checked
  before and after).

## Open questions and risks

- **No CI job builds or exercises either production image or
  `docker-compose.prod.yml`.** All of this session's evidence is from
  local, manual verification — a regression in either Dockerfile, the
  compose file, or any of the three bugs' fixes would not be caught
  automatically today. Not fixed this session (out of the stated scope,
  which was proving deployability locally, not building release CI); a
  reasonable candidate for a future session if this project's release
  process is ever revisited.
- **`WEB_CONCURRENCY=4` and the general resource footprint of the
  production stack are unmeasured placeholders**, same honesty standard
  as `max_question_length` (Session 3) — no load-testing was performed or
  claimed.
- **Metrics, tracing, dashboards, and alerting remain genuinely
  unbuilt.** `08-deployment-and-operations.md`'s Observability section
  states plainly what a real deployment would still need; none of it
  exists today, and none was represented as existing.
- **This session's upload-latency observations (16-30s per document
  during one test run) were confounded by a concurrent, CPU-heavy
  background `pytest` run on the same host** — re-measured cleanly after
  that background run finished (documents uploaded promptly, no further
  worker timeouts). No throughput or latency number from this session
  should be read as a representative production figure; none is claimed
  as one.
