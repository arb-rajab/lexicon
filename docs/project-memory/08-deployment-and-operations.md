# Deployment and Operations
> Purpose: how this runs, and how someone else keeps it running
> Project: lexicon (public)
> Last updated: 2026-08-27

## Environments
## Build and release pipeline
## Deployment procedure
## Migration and rollback procedure

## Configuration and secrets

**Partial — only the piece Session 4's implementation actually needed to
resolve is recorded here** (`03-architecture.md`'s open item: "record how
[the LLM API key] is supplied to the application... in this document").
Instance-level authentication and the rest of this document's sections
remain unwritten — not this session's scope.

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
key and restarting the `backend` service is the entire migration path to
the real tier; no code change is required. See
`docs/project-memory/12-session-handoff.md` (Session 4) for why this
absence is flagged as an urgent, cheap-to-clear blocker rather than a
permanent design choice, unlike the stub tier itself, which stays.

## Observability: logs, metrics, traces, health checks
## Dashboards and alerts (each links a runbook)
## Runbooks
## Backup and restore (last verified: NEVER — update this)
## Capacity and cost notes
