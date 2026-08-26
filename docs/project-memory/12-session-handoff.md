# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Session completed
- Session number and title: **Session 0 — Portfolio Governance & Technology Allocation**
- Objective: Confirm the ledger row, learning budget, and non-goals preview before any architecture or feature work begins; ship a real, booting repository skeleton (not a placeholder) from day one.
- Status: **complete**

## Work completed
- Confirmed framework allocation: **FastAPI/Python 3.12 (backend) + Next.js 15 App Router (frontend)** — verified `UNIQUE`, zero collisions against the sibling public flagship (`privacy-forge` uses Laravel + Vue 3/Inertia).
- Confirmed learning budget: exactly 2 new technologies (RAG evaluation methodology — golden-dataset-driven, CI-gated; LLM guardrails/prompt-injection defence) — at cap, not over. Hybrid retrieval, pgvector, FastAPI, Next.js, SQLAlchemy, Alembic, Redis, MinIO/S3, Docker Compose are established engineering patterns being applied, not new learning.
- Confirmed the two deep SDLC phases for this repo: **Discovery & Planning** and **Verification & Testing**.
- Created repository skeleton: directory structure, licence (AGPL-3.0), `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `README.md` (status: skeleton, with an explicit permanent non-goals preview).
- Scaffolded the full 15-file Project Memory Pack under `docs/project-memory/`.
- Wrote a draft `00-project-brief.md` (marked DRAFT STUB — points to `00a-ledger-confirmation.md` for the technology/learning-objective rationale; full brief is Session 1 work).
- Built a **real, minimal FastAPI backend skeleton** (`backend/`): `pyproject.toml` declaring FastAPI, Pydantic v2, SQLAlchemy, Alembic, psycopg, Redis as dependencies, plus a dev toolchain (pytest, ruff, mypy, bandit, pip-audit); a `GET /health` endpoint; one passing test.
- Built a **real, minimal Next.js 15 App Router frontend skeleton** (`frontend/`): a placeholder page, a `GET /api/health` route, a Vitest test runner with one passing test, ESLint configured, TypeScript strict mode.
- Wrote `docker-compose.yml` covering PostgreSQL (pgvector), Redis, MinIO, and both application services, and **actually booted it** — all five services reached `healthy`, and both `/health` endpoints were curled from the host and returned HTTP 200 (not assumed from config).
- Wrote a **real CI pipeline from the start** (`.github/workflows/ci.yml`): ruff, mypy, bandit, pytest, pip-audit for the backend; eslint, build, vitest, npm audit for the frontend; gitleaks; CodeQL (Python + JavaScript/TypeScript matrix). Deliberately not a placeholder — see "Decisions made" below for why.
- Added GitHub issue templates (bug, feature, security) and a PR template.
- Initialised git and made the first commit.

## Files created or changed
- `docs/project-memory/00a-ledger-confirmation.md` — frozen governance record; Session 3 checks this before starting architecture.
- `docs/project-memory/00-project-brief.md` — draft stub; **will be rewritten, not appended to, in Session 1**.
- `docs/project-memory/01-scope-and-non-goals.md` through `14-maintenance-and-retirement.md` — empty templates from the standard scaffold, ready for their respective sessions.
- `docs/SDLC-EVIDENCE.md` — deep-phase declaration filled in (Discovery & Planning, Verification & Testing); evidence rows for those phases are marked "not yet produced" (this repo's actual deep-phase deliverables land in Session 1 and the eventual testing/evaluation session).
- `README.md` — skeleton with status banner, elevator pitch, and the permanent non-goals list.
- `LICENSE` — AGPL-3.0 (rationale: hostable application, not a library — recorded so this isn't silently changed later).
- `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md` — standard governance docs.
- `backend/` — FastAPI skeleton: `pyproject.toml`, `src/lexicon/main.py` (health endpoint), `tests/test_health.py`, `Dockerfile`, `.dockerignore`.
- `frontend/` — Next.js 15 App Router skeleton: `package.json`, `app/page.tsx`, `app/layout.tsx`, `app/api/health/route.ts`, `lib/greeting.ts` + test, `vitest.config.ts`, `eslint.config.mjs`, `tsconfig.json`, `Dockerfile`, `.dockerignore`.
- `docker-compose.yml`, `.env.example` — full local stack (postgres/pgvector, redis, minio, backend, frontend), proven to boot.
- `.github/workflows/ci.yml` — real pipeline (see above), not a placeholder.
- `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/*.yml` — contribution scaffolding.
- `.gitignore` — Python/Node/Next.js exclusions plus `.env`.
- `scaffold-memory-pack.sh` — copied into the repo so future sessions can regenerate the pattern.

## Decisions made
- **Licence: AGPL-3.0**, not MIT — because this is a hostable application (per the portfolio rule: MIT for libraries/tools, AGPL for hostable apps). Should not be silently changed without a recorded reason.
- **Framework allocation is frozen** at FastAPI (Python 3.12) + Next.js 15 (App Router). Must not be silently reversed.
- **Exactly two deep SDLC phases** (Discovery & Planning, Verification & Testing) are committed. A third should not quietly creep in during later sessions.
- **CI is real from Session 0, not a placeholder.** This portfolio's own `privacy-forge` shipped a placeholder CI workflow at its Session 0 and had to replace it with a real pipeline at Session 5 — an avoidable rework cost. `lexicon`'s CI runs actual lint/type/security/test jobs against the actual (minimal) skeleton from the first commit.
- **Host ports in `docker-compose.yml` are non-default** (backend `8010`, frontend `3001`, postgres `5433`, redis `6380`) — chosen after discovering real collisions with other locally running projects (`booking-and-deposits` on 5432/6379, and unrelated native dev-server processes squatting on `127.0.0.1:8000`/`[::1]:3001`) during verification. Internal service-to-service traffic uses the standard container ports and is unaffected.
- No formal ADR yet — ADRs begin at Session 3. This session's decisions are governance decisions, not architecture decisions.

## Validation performed
- Commands run: `bash -n scaffold-memory-pack.sh` (syntax check, passed); `git status`, `git log`.
- Backend: `ruff check .`, `mypy src` (strict), `bandit -r src`, `pytest -q` (1 passed), `pip-audit` (0 known vulnerabilities after upgrading `pip` itself in the check environment — the same order CI follows) — all run inside a `python:3.12-slim` container to mirror the CI runner exactly, since no local Python is installed on this machine.
- Frontend: `npm run lint` (clean), `npm run build` (succeeds, 3 routes), `npm test` (1 passed, Vitest), `npm audit` / `npm audit --omit=dev` (0 vulnerabilities — required pinning `next`/`eslint`/`vitest` off their initially-scaffolded versions and adding a `postcss` override to clear CVEs while staying on the ledger-confirmed Next.js 15 line, not jumping to Next 16).
- `docker compose build` — both `backend` and `frontend` images build successfully.
- `docker compose up` — **all five services reached `healthy`** (postgres, redis, minio, backend, frontend). Verified for real, not assumed: `curl http://127.0.0.1:8010/health` → `200 {"status":"ok"}`; `curl http://127.0.0.1:3001/api/health` → `200 {"status":"ok"}`. (Used `127.0.0.1` explicitly rather than `localhost` after discovering the latter could resolve to an unrelated process's IPv6 listener on this machine — see port-remapping decision above.)
- Manual checks performed: verified `LICENSE` file downloaded correctly (checked header "GNU AFFERO GENERAL PUBLIC LICENSE" and footer reference to gnu.org); verified all 15 memory-pack files were created; verified `arb-rajab/lexicon` did not already exist on GitHub before creating it; verified sibling public flagship repos (`privacy-forge`, `laravel-consent-guard`) both live under the `arb-rajab` GitHub account, confirming portfolio account consistency.
- Stack was torn down (`docker compose down`) after verification, per normal practice — it is not left running.

## Open questions and risks
- **Risk:** RAG evaluation methodology and LLM guardrails/prompt-injection defence are both genuinely new to this developer. If Session 1's feasibility spike or a later architecture session reveals either is a bigger lift than expected, consider a short timeboxed spike before committing to an ADR, rather than an open-ended detour.
- **Risk (environment-specific, not repo-level):** this dev machine has several other projects' dev servers left running on nearby ports (5432, 6379, 8000, 3000/3001 all had collisions during this session). `docker-compose.yml`'s non-default host ports work around this, but a contributor on a clean machine could reasonably expect standard ports — call this out in onboarding docs if it becomes friction.
- **Risk (portfolio-level, not repo-level):** confirm with the Status Board owner that no other public-track repo is concurrently active, per the WIP-limit-of-2 governance rule.
- **No blockers.** Session 1 can start immediately.

## Next recommended session
- Proposed session title: **Session 1 — Discovery & Planning**
- Single objective: Produce the deep-phase Discovery evidence — validate the problem and users with real reasoning, the explicit "why RAG, not fine-tuning or search alone" comparison with a failure-cost analysis, and a feasibility spike proving hybrid retrieval works on a sample corpus.
- Inputs required: this handoff; `00a-ledger-confirmation.md`; the draft `00-project-brief.md`.
- Expected deliverables: finalised project brief (no "draft"/"stub" markers remaining); `01-scope-and-non-goals.md` with an explicit non-goals table (reason + reconsideration condition, expanding on the permanent boundaries already stated in the README); the RAG-vs-alternatives comparison and failure-cost analysis; a feasibility spike report; concrete, checkable success metrics; an explicit MVP boundary.
- Definition of done: Gate 1→2 checklist satisfied (problem statement, target users, stakeholders, assumptions, risks, feasibility note including the spike result, success metrics, MVP boundary, non-goals — all written and no longer marked draft).

## Paste-into-new-session context

**Project:** lexicon — grounded document Q&A system; every answer is citation-backed or refused
**Track:** public flagship
**Repository state:** branch `main`, unreleased (pre-v0.1.0), Session 0 complete, pushed to `arb-rajab/lexicon`

**Problem being solved:** (to be validated in Session 1) users need answers grounded in a specific document set, with retrieval quality measured rather than eyeballed, and with prompt-injection resistance treated as a tested security control rather than an assumption.

**Current stack:**
- Backend: FastAPI, Python 3.12
- Frontend: Next.js 15 (App Router)
- Data: PostgreSQL + pgvector, Redis, S3-compatible object storage (MinIO)
- Infra: Docker Compose (built and verified booting at Session 0), GitHub Actions (real CI from Session 0)
- Testing: pytest (backend), Vitest (frontend) — both currently cover only the health-check skeleton

**Architecture decisions that must not be reversed:**
- Licence is AGPL-3.0 (hostable app, not a library).
- Primary frontend/backend framework pair is fixed (Next.js 15 + FastAPI/Python 3.12) — frozen against the portfolio-wide framework allocation ledger; changing it requires reopening ledger governance, not just a local decision.
- Exactly two deep SDLC phases for this repo: Discovery & Planning, Verification & Testing. Do not let a third phase creep in.
- Learning budget is exactly 2 (RAG evaluation methodology, LLM guardrails/prompt-injection defence) — already at cap; do not introduce a third new technology.

**Implementation state:**
- Done: repository skeleton, licence, governance docs, empty Project Memory Pack, draft (unvalidated) project brief, minimal real backend/frontend skeletons, docker-compose proven to boot, real CI pipeline.
- In progress: nothing mid-flight.
- Not started: everything product-related — no ingestion, retrieval, generation, or evaluation harness exists yet.

**Constraints and non-goals:**
- Permanent scope boundaries (see README, not placeholders): no model training/fine-tuning, no agentic tool use, no multi-modal input, not a general chatbot, not an LLM gateway product, no autonomous action-taking.
- Full non-goals table with rationale is Session 1 work.

**Task for this session (single objective):**
Conduct project discovery: validate the problem, users, and business assumptions; produce the "why RAG, not fine-tuning or search alone" reasoning with an explicit failure-cost analysis; run a feasibility spike proving hybrid retrieval works on a sample corpus; define success metrics and the MVP boundary.

**Definition of done:**
- `00-project-brief.md` rewritten with no "draft"/"stub" markers, every section validated with actual reasoning.
- `01-scope-and-non-goals.md` produced with an explicit non-goals table.
- RAG-vs-alternatives comparison and failure-cost analysis written down.
- Feasibility spike run and its result recorded.
- 5 concrete, checkable success metrics defined.
- MVP boundary stated as a bullet list a reviewer could tick off.

**Files to attach or paste:**
- `docs/project-memory/00-project-brief.md` (current draft)
- `docs/project-memory/00a-ledger-confirmation.md`
- `docs/project-memory/12-session-handoff.md` (this file)

**Ground rules:** Do not change the stack. Do not introduce a third new technology. Do not expand the deep-SDLC-phase count beyond two. Do not touch `privacy-forge`, `laravel-consent-guard`, or `bookslot`. Ask before introducing any new dependency or scope item not already anticipated above.
