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
- Current version or branch: `main`, tagged **`v1.0.0`** at Session 9.

## Session completed
- Session number and title: **Session 9 — Tag v1.0.0 (closeout, not new
  work).**
- Objective, as given at the start of this session: re-confirm the full
  backend suite (ruff, mypy `--strict`, bandit, pytest — all 35 tests) and
  frontend suite (lint, build, test) are genuinely green on current `main`
  right now, not assumed from Session 7/8's prior green state; add a real
  `v1.0.0` entry to `CHANGELOG.md` stating plainly what v1.0.0 represents,
  including the ADR-0004 boundary as part of the release description, not
  omitted from it; tag the current commit `v1.0.0` (annotated, matching
  `privacy-forge`'s convention) and push the tag; update this file and
  `README.md`'s status line to reflect the tagged state. Ground rules: no
  application code changes; `privacy-forge`, `laravel-consent-guard`, and
  `bookslot` untouched. Status: **complete.**

## A gap found before the rest of this session's work

Session 8 (`802c412`, "write the case study, refresh README status,
finalize SDLC evidence") changed `README.md`, added `docs/CASE-STUDY.md`,
and extended `docs/SDLC-EVIDENCE.md` — but never touched this file.
`git log --oneline -- docs/project-memory/12-session-handoff.md` confirmed
its most recent entry was still Session 7's, with no Session 8 record at
all. Not backfilled this session (out of this session's stated scope,
which is the v1.0.0 tag closeout, not auditing Session 8's own omissions)
— named here so a future reader doesn't mistake the jump from "Session 7"
directly to "Session 9" below for data loss rather than a known, real gap.

## Work completed

- **Re-ran the full backend check suite from scratch against a fresh,
  disposable Postgres instance** — not the long-running dev stack's
  database, and not assumed from Session 7's recorded result. Started an
  isolated `pgvector/pgvector:pg16` container on the project's Docker
  network, then ran `pip install '.[dev,prod]'`, `ruff check .`, `mypy
  src`, `bandit -r src`, `alembic upgrade head`, and `pytest -q` inside a
  fresh `python:3.12-slim` container with the full repo mounted (the spike
  corpus regression/proof tests resolve `docs/spikes/...` relative to the
  repo root, so the whole repo — not just `backend/` — has to be mounted
  for them to pass). Result: `ruff` — all checks passed; `mypy --strict` —
  no issues in 33 source files; `bandit` — no issues (1468 lines scanned);
  `pytest` — **35 passed** in 1042.72s. The disposable Postgres container
  was removed afterward.
- **Re-ran the full frontend check suite from scratch** — `npm ci` (fresh
  install, not reusing `node_modules`), `npm run lint`, `npm run build`,
  `npm test`. All green: eslint clean, `next build` compiled and generated
  all 5 pages successfully, 1/1 vitest test passed.
- **Added a real `## [1.0.0] - 2026-08-29` entry to `CHANGELOG.md`**,
  above which sits a fresh, empty `## [Unreleased]`. The entry summarizes
  what v1.0.0 actually represents — the full ingest → hybrid retrieval →
  generation → groundedness verification → answer/refusal pipeline
  (ADR-0001), the tamper-evident audit trail (ADR-0002), the structural,
  tier-independent injection hardening with its 18/18 adversarial-corpus
  evidence (ADR-0003), the CI-gated evaluation harness and methodology,
  and the real production-shaped local deployment proof (Session 7's
  three real bugs found and fixed) — under `### Added`, with the ADR-0004
  boundary stated as its own `### Security` entry, in the same terms
  `README.md` and `docs/CASE-STUDY.md` already use, not softened for a
  release note.
- **Tagged the current commit `v1.0.0`** (annotated tag, `git tag -a`),
  matching `privacy-forge`'s own `v1.0.0` tag convention (checked
  directly: `git -C ../privacy-forge show v1.0.0 --stat`), and pushed the
  tag to `origin`.
- **Updated `README.md`'s status banner and Project status section** to
  say `v1.0.0` is tagged, keeping the existing ADR-0004 boundary language
  intact rather than trimming it for brevity — this portfolio's stated
  rule is that the boundary is part of what the release honestly is, not
  a footnote.
- `privacy-forge`, `laravel-consent-guard`, and `bookslot` were not
  touched, read, or modified this session, except `privacy-forge`'s own
  `CHANGELOG.md`, `README.md`, and `v1.0.0` tag metadata, which were read
  (never written to) purely to confirm this portfolio's tagging
  convention before applying it here.

## Files created or changed

- `CHANGELOG.md` — new `## [1.0.0] - 2026-08-29` entry; fresh, empty
  `## [Unreleased]` above it
- `README.md` — status banner and Project status section updated to
  reflect the tagged `v1.0.0` state
- `docs/project-memory/12-session-handoff.md` (this file, rewritten)
- Git: new annotated tag `v1.0.0`, pushed to `origin`

## Decisions made

- **`CHANGELOG.md` gets a real `## [1.0.0]` version heading**, not another
  `Unreleased`-only session bullet. `privacy-forge`'s own `CHANGELOG.md`
  was checked directly and, despite carrying a real `v1.0.0` git tag,
  never gained a version heading — its changelog stays permanently under
  `Unreleased`, grouped by session. That is read here as an inconsistency
  in that repository, not a portfolio convention worth reproducing: this
  session's own instructions explicitly asked for "a v1.0.0 entry," Keep a
  Changelog's own format is built around version headings, and a
  changelog that never versions itself despite a tagged release would
  misstate what actually shipped.
- **The full check suite was re-run against fresh, disposable
  infrastructure** (a new Postgres container, a fresh `npm ci`) rather
  than reusing the long-running dev stack's database or its already-
  installed `node_modules` — closer to what CI actually does, and avoids
  a false-green result from state the dev stack accumulated across
  earlier sessions' manual testing.
- **Session 8's own handoff gap was named, not silently patched over or
  silently ignored.** Consistent with this project's standing discipline
  (Session 7's own "correction made before the rest of this session's
  work" section) of stating what's actually true about the record rather
  than smoothing over it.

## Validation performed

- Backend: `ruff check .` (all checks passed), `mypy src` (strict; no
  issues, 33 source files), `bandit -r src` (no issues, 1468 lines),
  `alembic upgrade head` (clean), `pytest -q` (**35 passed**, 1042.72s) —
  all run together, fresh, against a disposable Postgres container created
  for this session and removed afterward.
- Frontend: `npm ci` (fresh), `npm run lint` (clean), `npm run build`
  (succeeded, 5/5 pages generated), `npm test` (1/1 passed).
- `git -C ../privacy-forge show v1.0.0 --stat` and
  `git -C ../privacy-forge log --oneline` read directly to confirm the
  annotated-tag convention and message format before tagging here.
- Confirmed `privacy-forge`, `laravel-consent-guard`, and `bookslot` were
  not modified this session (`git status` in each, before and after).
- Tag push confirmed against `origin` after `git push origin v1.0.0`.

## Open questions and risks

Carried forward from Session 7, unaffected by this session's
documentation-and-tagging-only scope — none of the following were
addressed or claimed to be addressed by tagging v1.0.0:

- No CI job builds or exercises either production image or
  `docker-compose.prod.yml` — all deployment evidence remains from local,
  manual verification.
- `WEB_CONCURRENCY=4` and the production stack's resource footprint remain
  unmeasured placeholders; no load-testing was performed or claimed.
- Metrics, tracing, dashboards, and alerting remain genuinely unbuilt.
- The central ADR-0004 boundary is permanent for this project's current
  lifecycle: real LLM provider verification quality (refusal recall,
  citation accuracy, injection resistance under a real model) is not, and
  cannot be, part of what v1.0.0 proves — stated here once more, plainly,
  as it is in `CHANGELOG.md` and `README.md`.
