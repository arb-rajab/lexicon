# lexicon

> **Status:** 🚧 Session 3 complete — security and threat model, including
> two new ADRs (audit-trail tamper-evidence, and hardening the independent
> verification call against passage-embedded prompt injection). No
> application feature code yet. See
> [`docs/project-memory/12-session-handoff.md`](docs/project-memory/12-session-handoff.md)
> for current state and next steps.

A grounded document Q&A system: every answer is citation-backed against the
supplied documents, or the system refuses to answer. Retrieval quality is
measured by a committed, CI-gated evaluation harness — not eyeballed.
Prompt-injection defences are tested as real security controls, not assumed.

## What this demonstrates

- **Discovery & Planning (deep):** the "why RAG, not fine-tuning or search
  alone" reasoning, with an explicit failure-cost analysis, is written down
  and validated — not assumed.
- **Verification & Testing (deep):** a golden-dataset-driven, CI-gated
  evaluation harness for retrieval/answer quality, and an adversarial
  prompt-injection test suite treated as a real security control.
- Citation-or-refusal as a hard product invariant, not a prompt suggestion.

Stack: FastAPI (Python 3.12) · Next.js 15 (App Router) · PostgreSQL +
pgvector · Redis · S3-compatible storage (MinIO).

## Project status

This repository is built through a session-based workflow. Current phase:
**Session 3 (Security & Threat Model) — complete.** Next: Session 4.

Full portfolio context: this is a flagship repository in a broader
public/private software portfolio. See `docs/project-memory/` for the
complete project memory pack, and `docs/SDLC-EVIDENCE.md` for the
phase-by-phase evidence map (deep-phase rows populated as the work lands).

## Non-goals

These are permanent scope boundaries for this project, not placeholders to
fill in later:

- No model training or fine-tuning.
- No agentic tool use.
- No multi-modal input.
- Not a general-purpose chatbot.
- Not an LLM gateway product.
- No autonomous action-taking.

The full non-goals table, with rationale and reconsideration conditions for
each row (including two new ones this session's analysis surfaced) is in
[`docs/project-memory/01-scope-and-non-goals.md`](docs/project-memory/01-scope-and-non-goals.md).

## Quickstart

```
cp .env.example .env
docker compose up
```

Boots PostgreSQL (pgvector), Redis, MinIO, the backend
(`http://localhost:8010/health`) and the frontend
(`http://localhost:3001/api/health`). No document ingestion, retrieval, or
generation exists yet — those are later sessions.

Host ports are deliberately non-default (8010, 3001, 5433, 6380) to avoid
colliding with other local projects; internal service-to-service
communication is unaffected.

## Documentation

- [`docs/project-memory/`](docs/project-memory/) — brief, requirements,
  architecture, security, testing, operations, decisions, risks, backlog,
  handoff, release notes, maintenance/retirement plan
- [`docs/SDLC-EVIDENCE.md`](docs/SDLC-EVIDENCE.md) — phase-by-phase evidence map
- [`SECURITY.md`](SECURITY.md) — vulnerability disclosure policy

## Licence

AGPL-3.0 — see [`LICENSE`](LICENSE). Rationale: this is a hostable
application, not a library; AGPL ensures modifications to a hosted version
remain shareable.
