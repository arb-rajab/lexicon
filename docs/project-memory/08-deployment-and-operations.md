# Deployment and Operations
> Purpose: how this runs, and how someone else keeps it running
> Project: lexicon (public)
> Last updated: 2026-08-28 (Session 7 — release readiness: production-shaped
> images, a local production-shape stack proof, structured logging,
> liveness/readiness endpoints, and three real bugs found and fixed while
> proving it. Sessions 1-6 had left this file almost entirely as an empty
> template beyond the Configuration and secrets section below.)

## Environments

| Environment | Purpose | Status |
|---|---|---|
| Local dev | `docker-compose.yml` (`postgres`/`redis`/`minio`/`backend`/`frontend`, dev Dockerfiles, bare `uvicorn --reload` / `next start`) | Exists since Session 0, used every session |
| CI | `.github/workflows/ci.yml` — ruff/mypy/bandit/pip-audit/pytest (real Postgres service), eslint/build/vitest/npm-audit, gitleaks, CodeQL | Exists since Session 0/4 |
| Production-shape local proof | `docker-compose.prod.yml` + `backend/docker/Dockerfile.prod` + `frontend/docker/Dockerfile.prod`, run locally | **Built and verified, Session 7** — see Deployment procedure below |
| A real, live, publicly-reachable instance | N/A | **Out of scope, by the same portfolio-wide precedent as privacy-forge's live-demo descoping and bookslot's cloud-provisioning descoping** (see `12-session-handoff.md`). No cloud account, VPS, DNS, or domain exists or is planned for lexicon. Unlike privacy-forge, lexicon's own project memory has never contained a decision to stand up any public demo instance in the first place — there is no prior commitment being narrowed here, only a precedent this session doesn't relitigate. |

There is no staging environment and none is planned, for the same reason
privacy-forge has none: a single-operator, not-currently-hosted-anywhere
product has no shared environment of its own to stage changes against.

## Build and release pipeline

- CI (`.github/workflows/ci.yml`) is the release gate for the *codebase* —
  lint/type-check/security-scan/test on every push and PR to `main`. It
  says nothing about deployment; nothing it runs builds or exercises the
  production images below (a real gap, not silently papered over — see
  Known gaps in `07-testing-strategy.md` for whether a future session
  should add that).
- **`backend/Dockerfile` and `frontend/Dockerfile` are dev images**
  (`docker-compose.yml` builds both) — bare `uvicorn lexicon.main:app`
  with no `--reload` flag but also no worker process model, and
  `npm install && npm run build && npm start` respectively. Neither was
  ever a production image; this was already implicitly true from Session 0
  but is stated explicitly now that a real one exists to contrast with.
- **Real production images now exist, Session 7:**
  - `backend/docker/Dockerfile.prod` — two-stage build. Stage 1 installs
    `.[prod]` (adds `gunicorn`; the `.[dev]` lint/test toolchain never
    ships). Stage 2 copies only the installed packages + `src`/`alembic`
    into a slim runtime image, creates and runs as a non-root user
    (`lexicon`, uid 1000), and — found necessary this session, see below —
    **pre-warms the `BAAI/bge-small-en-v1.5` fastembed/ONNX embedding
    model into a fixed image-baked cache directory
    (`EMBEDDING_CACHE_DIR=/app/.cache/fastembed`) at build time**, so no
    container's first real request pays a live HuggingFace download.
    `backend/docker/entrypoint.prod.sh` runs `alembic upgrade head` (as
    `DATABASE_ADMIN_URL`, same as the dev image) then execs `gunicorn
    lexicon.main:app --worker-class uvicorn.workers.UvicornWorker
    --workers "${WEB_CONCURRENCY:-4}" ...` — real multi-worker ASGI
    serving, not bare `uvicorn`, and no `--reload`.
  - `frontend/docker/Dockerfile.prod` — three-stage build using Next.js
    "standalone" output (`next.config.ts`'s `output: "standalone"`,
    Session 7): `deps` (`npm ci`), `builder` (`next build`, with
    `NEXT_PUBLIC_API_URL` baked in via a build arg — Next.js inlines
    `NEXT_PUBLIC_*` values into the client bundle at build time, not
    read at container start), and `runner` (only the traced runtime
    dependencies plus `server.js`, running as the `node:22-slim` base
    image's existing non-root `node` user — reused rather than creating
    a second uid-1000 user, which collides and fails the build).
  - Both verified to build successfully and to boot as a real,
    healthy stack — see Deployment procedure below for the full account,
    including three real bugs this session found and fixed while proving
    it, none of which were visible under either dev image or under CI.
- No image registry is configured; no CD pipeline exists; nothing
  publishes either image anywhere beyond the local Docker image store used
  to prove this session's claims.

## Deployment procedure

**What this actually is:** a real, complete, locally-verified procedure
for what this project can currently prove about deployment — not a stub
awaiting a real host. `docker-compose.prod.yml` (repo root) builds and
runs `backend`/`frontend` from the production Dockerfiles above alongside
the same `postgres`/`redis`/`minio` images `docker-compose.yml` already
uses (those were never the dev-only part of that file).

```
docker compose -f docker-compose.prod.yml -p lexicon-prod up -d --build
```

Host ports are deliberately different from `docker-compose.yml`'s dev
stack (`8011`/`3002`/`5434`/`6381`/`9010`-`9011`, vs dev's
`8010`/`3001`/`5433`/`6380`/`9000`-`9001`) so both stacks can run at once
without colliding, mirroring the same convention privacy-forge's own
`docker-compose.prod.yml` uses for the same reason. `-p lexicon-prod`
keeps volumes/networks separate from the dev stack's too.

**Verified, Session 7, against this exact stack (not assumed from the dev
environment already working):**

1. Both images build successfully (`docker build -f
   backend/docker/Dockerfile.prod backend`,
   `docker build -f frontend/docker/Dockerfile.prod frontend`).
2. `docker compose -f docker-compose.prod.yml -p lexicon-prod up -d`
   brings up all five services; all five reach Docker's own `healthy`
   status (`postgres`, `redis`, `minio` via their existing healthchecks;
   `backend` via the new `/ready` endpoint — see Observability below;
   `frontend` via `/api/health`).
3. `GET /health` and `GET /ready` on the published backend port both
   return real 200s; `GET /api/health` and `GET /` on the published
   frontend port both return real 200s (the frontend page itself — no
   chat UI exists yet, Session 0's placeholder page only, so this proves
   the production Next.js server serves real traffic, not that a
   feature works).
4. **The full ingest → query → answer/refusal pipeline, proven through
   these production images specifically**, reusing the Session 1 spike
   corpus the way Session 5/6 both did: a corpus was created
   (`POST /api/v1/corpora`), all 8 spike documents were uploaded
   (`POST .../documents`), and two real queries were run
   (`POST .../query`) — the exact same two shapes Session 5's golden
   dataset and Session 4's ADR-0001 proof test already establish meaning
   for:
   - `"How do I check a plaintext password against a stored hash at
     login?"` (golden dataset's `legit-oauth2-password-check`) →
     `answered: true`, cited `oauth2-jwt.md`'s "Hash and verify the
     passwords" section.
   - `"How do I set up 'Sign in with Google' as an OAuth2 identity
     provider?"` (the canonical Session 1/ADR-0001 adjacent-but-wrong
     case) → `answered: false`, `refusal_reason: "verification_failed"`.

   **Same stub-tier caveat as every other session since ADR-0004: this is
   real evidence that the production images serve the real, wired
   pipeline correctly end-to-end (retrieval, generation, verification,
   the refusal gate) — it is not evidence of real model quality**, since
   no `ANTHROPIC_API_KEY` exists in this environment (see Configuration
   and secrets below). Raw request/response JSON for both is preserved in
   `12-session-handoff.md`.
5. **The credential-swap point (Session 4's original claim, restated in
   every handoff since) was re-confirmed against this production image
   specifically, not assumed to carry over from dev:**
   `docker run --rm lexicon-backend-prod:latest python -c "from
   lexicon.llm.factory import get_llm_client; print(type(get_llm_client()).__name__)"`
   prints `StubLLMClient` with no `ANTHROPIC_API_KEY` set, and
   `AnthropicLLMClient` with a (placeholder, non-functional — no real key
   exists or was used) value set, **using the identical image, no
   rebuild**. `anthropic.Anthropic()`'s constructor makes no network call
   (`llm/anthropic_client.py`), so this check needed no real credential
   and made no real API request.

**Three real bugs found and fixed while producing the evidence above** —
none were visible under `docker-compose.yml`'s dev image, and none are
caught by the existing CI suite, because both dev's bare `uvicorn
--reload` and CI's pytest run lack the specific mechanism each bug needed
to manifest:

1. **A blocking-event-loop bug in `api/documents.py`'s `upload_document`.**
   `ingestion/service.py`'s `ingest_document` is synchronous, CPU-bound
   work (chunking, then ONNX embedding inference,
   `ingestion/embeddings.py`) with no async path. `upload_document` is
   `async def` (it awaits `file.read()`) and was calling
   `ingest_document` inline — which runs it directly on the event loop,
   blocking it for the full duration of a real upload. Under
   `docker-compose.yml`'s dev image (bare `uvicorn`, no process
   supervisor watching for a hung worker) this was slow but invisible.
   Under `docker/Dockerfile.prod`'s gunicorn, a blocked event loop also
   stops the worker answering the arbiter's own heartbeat — gunicorn
   concluded the worker had hung and killed it (`WORKER TIMEOUT`,
   `SIGABRT`) mid-upload. **Fixed** by moving the blocking call through
   `starlette.concurrency.run_in_threadpool` — the same offload FastAPI
   already gives a plain `def` route (`api/query.py`'s `ask_question`)
   for free; this route needed the explicit opt-in because it's
   `async def` for an unrelated reason. Full backend test suite (35
   tests) re-run and still passes after this change.
2. **The same first-request cost, compounded by a live external
   dependency.** Before this session's embedding-model pre-warming (Build
   and release pipeline above), the very first call to `embed_texts()` in
   a freshly started container downloaded fastembed's ONNX model live
   from HuggingFace (~20-30s observed) — worsening bug 1 above and adding
   a live network dependency to the request path that a real production
   deployment should not have. **Fixed** by baking the model into the
   image at build time.
3. **Next.js standalone's server binds to a single container IP, not all
   interfaces, once Docker's own `HOSTNAME` env var is present.** Docker
   auto-injects `HOSTNAME=<container id>` into every container; Next's
   standalone `server.js` reads `process.env.HOSTNAME` (falling back to
   `0.0.0.0` only when unset) and resolves it via `/etc/hosts` to the
   container's one assigned IP, binding only there. The published host
   port still worked (Docker's NAT lands traffic directly on that IP),
   which is why this went unnoticed at first — but the frontend's own
   loopback-based Docker healthcheck (`fetch('http://localhost:3000/...')`
   from inside the same container) failed every cycle, leaving the
   container permanently `unhealthy` even though it was actually serving
   real traffic correctly. **Fixed** by pinning `HOSTNAME=0.0.0.0`
   explicitly (`docker-compose.prod.yml`'s `frontend.environment` and, as
   a `docker run`-without-compose fallback, `frontend/docker/
   Dockerfile.prod`'s own `ENV`) — confirmed by re-recreating the
   container and watching Docker's own health status go from
   `unhealthy` (`FailingStreak: 132`, over 31 hours) to `healthy`.

None of these three would have been found by continuing to test only
against the dev image or against CI as it exists today — each needed the
specific production-shaped mechanism (gunicorn's heartbeat supervision;
a freshly-built, freshly-started container with no warm cache; Docker's
own `HOSTNAME` injection interacting with Next's standalone server) that
only exists once you actually build and run the production stack. This is
the concrete argument for why this session's work is real verification,
not a formality.

**TLS: deliberately not added, reasoned explicitly rather than copied
from privacy-forge by default.** privacy-forge's own production-shape
stack terminates HTTPS (Caddy, `tls internal`, a placeholder domain)
because that project's brief made an explicit, first-class decision to
stand up a public-facing demo instance — proving real HTTPS termination
was answering a question that decision actually posed. **lexicon has no
equivalent decision anywhere in `docs/project-memory/`** — no session has
ever proposed or committed to a public demo instance, and
`06-security-threat-model.md`'s trust boundaries don't name public
network exposure as one this project takes on at all. Adding a
self-signed reverse proxy here would be proving a capability nothing in
this project's own scope has ever called for. If a future session decides
otherwise, the reverse-proxy/TLS layer is what to add then; nothing about
today's stack blocks it later.

## Migration and rollback procedure

Same Alembic migrations (`alembic upgrade head`, `backend/alembic/`) apply
to any environment, dev or production-shaped — `docker/entrypoint.prod.sh`
runs the identical command `../Dockerfile`'s dev CMD does, as the same
`DATABASE_ADMIN_URL`-authenticated admin role (ADR-0002), before the
server process starts. No production-only migration step or rollback
tooling exists or was built this session — this project has never needed
one (no session has run a migration against real, durable data that would
need rolling back; every environment to date is disposable, recreated via
`docker compose down -v` + `up -d --build`, as this session did twice
while iterating on the three bugs above).

## Configuration and secrets

**Session 4's original note below is preserved as-is; Session 7 adds
what changed for the production-shaped stack specifically, without
re-litigating the credential decision (`ADR-0004`,
`12-session-handoff.md`).**

All configuration is environment-variable-sourced, matching
`docker-compose.yml`'s existing `${VAR:-default}` pattern
(`DATABASE_URL`/`REDIS_URL` were already wired this way; Session 4 extends
the same pattern rather than introducing a second mechanism):

| Variable | Purpose | Session 4 default (dev only) |
|---|---|---|
| `DATABASE_URL` | App runtime DB connection — the ADR-0002-restricted role | `lexicon_app` role, created by migration `0002` |
| `DATABASE_ADMIN_URL` | Migration/admin DB connection — the only role with `UPDATE`/`DELETE` on the audit tables | superuser (`POSTGRES_USER`) |
| `APP_DB_ROLE` / `APP_DB_PASSWORD` | Credentials migration `0002` uses to create the restricted role above | `lexicon_app` / `lexicon_app_dev_only` |
| `ANTHROPIC_API_KEY` | LLM provider credential (ADR-0001, ADR-0003) | unset — see below |
| `GENERATION_MODEL` / `VERIFICATION_MODEL` | Model-tier assignment (`03-architecture.md`) | `claude-sonnet-5` / `claude-haiku-4-5` |

**`ANTHROPIC_API_KEY` is unset in every environment this project has run in
so far, including this session's.** This is not a boot-time failure:
`lexicon.llm.factory.get_llm_client()` reads its absence as a deliberate
signal and returns `StubLLMClient` instead of `AnthropicLLMClient` — the
application starts and serves the full ingest/retrieve/generate/verify
pipeline either way, against whichever tier is configured. Setting a real
key and restarting the `backend` service remains the technical migration
path to the real tier, should that ever happen; no code change would be
required. **Superseded, Session 4.5:** this absence is no longer a
temporary blocker awaiting a credential — the project owner has
permanently declined to obtain one, by deliberate portfolio-scope choice.
See `docs/adr/ADR-0004-real-llm-verification-descoped.md` for the full
decision and `docs/project-memory/12-session-handoff.md` for its
consequences. `StubLLMClient` is now this project's permanent evaluation
substrate, not a stand-in awaiting Session 5.

**Session 7 addendum — new variables, and the production-image
re-confirmation of the row above:**

| Variable | Purpose | Default |
|---|---|---|
| `LOG_LEVEL` | Root logger level (`logging_config.py`) | `info` |
| `WEB_CONCURRENCY` | gunicorn worker-process count (`entrypoint.prod.sh`) | `4` — an unmeasured placeholder, not load-tested (no capacity data exists, see Capacity and cost notes) |
| `GUNICORN_TIMEOUT` | gunicorn worker heartbeat/request timeout (seconds) | `60` |
| `EMBEDDING_CACHE_DIR` | Fixed fastembed model cache path, baked and pre-warmed at image build time (`docker/Dockerfile.prod`) | `/app/.cache/fastembed` (prod image only; `None`/fastembed's own default in dev, unchanged) |
| `HOSTNAME` | Pinned to `0.0.0.0` for the frontend production container only — see the standalone-server bug above | `0.0.0.0` (frontend prod only) |

`ANTHROPIC_API_KEY` was re-confirmed, this session, to still be a pure
config change against `lexicon-backend-prod:latest` specifically — see
Deployment procedure step 5 above for the actual command and result. This
had never previously been checked against a production-built image; it
was previously only demonstrated against dev.

**MinIO and Redis are both provisioned in `docker-compose.prod.yml` (same
images as `docker-compose.yml`) but neither is called by any application
code path today** — `ingestion/service.py`'s own module docstring already
states the MinIO half of this (`object_storage_key` is written as `NULL`,
Session 4); Redis has never been imported anywhere in `backend/src`
outside a config field and a code comment (checked this session,
`grep -r redis backend/src` found nothing else). Both remain provisioned
because `03-architecture.md` names them as intended future components,
not because the app depends on either today — this is stated here
explicitly so a future reader doesn't assume `main.py`'s `/ready`
endpoint (below) omitting them is an oversight.

## Observability: logs, metrics, traces, health checks

**A correction to this session's own starting assumption, stated plainly
rather than quietly built on top of:** this session's task framing
described "structured logging" as already partially existing because of
"the audit-table work from Session 6." That is not accurate.
`QUERY_LOG`/`RETRIEVED_CHUNK`/`CITATION_VERDICT` (`db/models.py`,
ADR-0002) are a permanent, tamper-evident **audit trail** of pipeline
decisions, stored in Postgres and readable via `api/query_logs.py` — not
operational log lines, and never routed through Python's `logging`
module. Before this session, `grep -r "import logging" backend/src`
matched nothing outside `alembic/env.py`. `logging_config.py`
(Session 7) is what actually adds structured **operational** logging, a
distinct, complementary concern — see that module's own docstring for the
full distinction.

**What is real, today:**

- **Structured JSON logging** (`backend/src/lexicon/logging_config.py`) —
  one JSON object per log line to stdout, level controlled by
  `LOG_LEVEL`, uvicorn's and gunicorn's own loggers routed through the
  same formatter so container logs are consistently one format, not a
  mix. Configured once, at `main.py` import time, so it's active under
  `pytest`'s `TestClient`, dev `uvicorn`, and production gunicorn workers
  alike.
- **Per-request structured logging** — `main.py`'s `log_requests`
  middleware logs `request_id` (echoed back as an `X-Request-ID` response
  header — reused from the caller's own header if supplied, generated
  otherwise), `method`, `path`, `status_code`, and `duration_ms` for every
  request. Verified for real against the production stack — see
  `12-session-handoff.md` for a real captured log line.
- **`GET /health` (liveness) vs `GET /ready` (readiness) — a real split,
  not just two names for the same check.** `/health` (existed since
  Session 4) asserts only that the process is up. `/ready` (Session 7)
  additionally executes a real `SELECT 1` against Postgres and returns
  503 if it fails — the one real runtime dependency the app actually has.
  Redis/MinIO are deliberately not checked (Configuration and secrets
  above explains why: no code path calls either yet, so a readiness check
  cannot honestly assert a dependency on either). `docker-compose.prod.yml`'s
  `backend` healthcheck targets `/ready`, not `/health`, on the reasoning
  that a production healthcheck should reflect real capability to serve
  work, not merely process liveness.
- **Frontend liveness** — `GET /api/health` (existed since Session 0,
  unchanged) is what `docker-compose.prod.yml`'s `frontend` healthcheck
  targets. No frontend readiness endpoint was added: the frontend has no
  server-side runtime dependency of its own to check (it calls the
  backend API from the browser via `NEXT_PUBLIC_API_URL`, not
  server-side), so a readiness check here would either duplicate the
  backend's or check nothing real.

**What is genuinely future work, not built, stated honestly rather than
silently assumed to exist:**

- **Metrics** — no request-latency histograms, no counter of LLM calls or
  which tier served them (relevant specifically because of ADR-0004: an
  operator watching a real deployment would want to know at a glance
  whether `stub` or `real` is currently answering traffic), no retrieval
  recall/quality trend over time. Would need a real metrics backend
  (Prometheus/OpenTelemetry are the obvious choices given the stack) —
  not evaluated or chosen, since nothing here needs one yet.
- **Distributed tracing** — no spans across
  ingest → retrieve → generate → verify. The per-request `request_id`
  above is request-scoped only, not a trace correlating multiple pipeline
  stages or services.
- **Log aggregation/shipping** — stdout JSON lines, read via `docker
  logs`, is sufficient for this session's own local proof and for any
  self-hoster's single-instance deployment. A real multi-instance or
  managed-hosting deployment would need a real collector (Loki, CloudWatch,
  or equivalent) to ship and query these centrally — not needed or built
  here, since no such deployment exists.
- **Dashboards and alerting** — none exist or are planned (see below).

## Dashboards and alerts (each links a runbook)

None exist. No metrics backend exists to dashboard against (see
Observability above), and no real, running instance exists for an alert
to page anyone about — both are genuinely future work, tracked here
rather than silently absent.

## Runbooks

| Runbook | Status |
|---|---|
| Bring up the production-shape stack | `docker compose -f docker-compose.prod.yml -p lexicon-prod up -d --build` — verified, Session 7 (Deployment procedure above). |
| Tear down / reset the production-shape stack | `docker compose -f docker-compose.prod.yml -p lexicon-prod down -v` — verified, Session 7 (run twice this session while iterating on the three bugs above). |
| Rotate/set a real `ANTHROPIC_API_KEY` | Set the env var, recreate the `backend` service (`docker compose -f docker-compose.prod.yml -p lexicon-prod up -d --force-recreate backend`). No image rebuild needed — verified against the production image specifically, Session 7 (Deployment procedure step 5). |
| Diagnose a "WORKER TIMEOUT" in `backend` logs | Check whether the request in flight is CPU-bound work called synchronously from an `async def` route without `run_in_threadpool` (Deployment procedure, bug 1) — this exact class of bug already happened once and was fixed in `api/documents.py`; a recurrence elsewhere would look identical. |
| Diagnose `frontend` stuck `unhealthy` despite the page loading fine over the published port | Check whether `HOSTNAME` is set in the container's actual environment (`docker exec <container> env \| grep HOSTNAME`) — Docker's own auto-injected value silently overrides Next standalone's default bind address (Deployment procedure, bug 3). Both `docker-compose.prod.yml` and `frontend/docker/Dockerfile.prod` now pin this, but a future image variant that drops either fix would reproduce the exact same symptom. |

## Backup and restore (last verified: N/A — still not applicable)

No backup/restore procedure exists or is needed: every environment to
date, dev and this session's production-shape proof alike, is disposable
and holds no data anyone depends on — recreated from scratch via `docker
compose ... down -v && up -d --build` whenever needed (done twice this
session). This would become a real, required section the day any real,
durable instance exists; none does.

## Capacity and cost notes

No spend cap or capacity plan exists because no real infrastructure exists
or is planned to spend against (same reasoning as privacy-forge's own
Session 24 entry, and the same portfolio-wide precedent
`12-session-handoff.md` names). `WEB_CONCURRENCY=4` (gunicorn workers,
`entrypoint.prod.sh`) is a config placeholder, not a load-tested number —
no request-volume or resource-constraint data exists for this project at
any tier. If a real deployment is ever provisioned, load-testing to pick
a real worker count, and a real spend cap with alerting on approach to it,
both become required again — neither is attempted or estimated here.
