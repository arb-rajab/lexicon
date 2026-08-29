# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-08-29

First tagged release. `lexicon` is a self-hostable, citation-or-refusal
document Q&A (RAG) system: the full ingest → hybrid retrieval → generation
→ independent groundedness verification → answer/refusal pipeline is real,
wired end-to-end, and tested — proven through a real, production-shaped
local deployment, not just unit tests. See
[`docs/CASE-STUDY.md`](docs/CASE-STUDY.md) for the full engineering account
and [`docs/project-memory/12-session-handoff.md`](docs/project-memory/12-session-handoff.md)
for session-by-session detail.

### Added
- **Real pipeline, end to end:** heading-aware ingestion with real
  embeddings; hybrid retrieval (OR-semantics keyword search + pgvector
  cosine search + Reciprocal Rank Fusion); generation with mandatory
  chunk-scoped citations; an independent groundedness/entailment
  verification call that gates every answer — citation-backed or refused,
  never a bare guess ([ADR-0001](docs/adr/ADR-0001-groundedness-refusal-check.md)).
  Built after a real feasibility spike measured that a similarity threshold
  alone cannot separate a correct answer (0.706-0.848 top similarity) from
  a topically-adjacent-but-wrong one (0.701) — the finding that shaped the
  whole architecture.
- **Tamper-evident audit trail** (`QUERY_LOG`/`RETRIEVED_CHUNK`/
  `CITATION_VERDICT`) with a database-enforced, least-privilege application
  role that cannot alter or delete its own audit rows
  ([ADR-0002](docs/adr/ADR-0002-audit-trail-tamper-evidence.md)).
- **Structural, tier-independent prompt-injection hardening** for the
  verification call — forced structured output, sandwiched delimiting, a
  self-reported `injection_suspected` field, and an application-enforced
  fail-closed override — with a committed, CI-gated adversarial corpus
  proving 18/18 structural containment across four attack categories,
  regardless of LLM tier
  ([ADR-0003](docs/adr/ADR-0003-verification-injection-hardening.md),
  [`docs/security/adversarial-corpus/`](docs/security/adversarial-corpus/)).
- **A CI-gated evaluation harness and methodology**: a golden-dataset-driven
  suite whose retrieval recall@k measurement is fully real (9/9, never
  calls an LLM provider) and whose refusal/citation-scoring methodology is
  proven sound against a documented, deterministic stub substrate.
- **Real production deployment proof**: a production-shaped, two-stage
  Docker build for both services (non-root, gunicorn, pre-warmed embedding
  model), a five-service `docker-compose.prod.yml`
  (Postgres+pgvector/Redis/MinIO/backend/frontend), structured JSON
  operational logging, and a real liveness/readiness split (`/health`,
  `/ready`) — booted and proven against real HTTP traffic locally, catching
  and fixing three real bugs (an event-loop-blocking upload path, a
  live model download on the request path, a container-healthcheck
  binding bug) in the process.
- Repository governance: framework allocation ledger row confirmed
  (`UNIQUE` — FastAPI (Python 3.12) + Next.js 15, no flagship collision).
- Project Memory Pack (15-file structure under `docs/project-memory/`), a
  full ADR set, a case study, and a phase-by-phase SDLC evidence map.
- A real CI pipeline from the start: lint, type-check, security scan, and
  tests for both backend and frontend, plus the evaluation harness and
  adversarial corpus, gitleaks, CodeQL, and dependency auditing
  (`pip-audit`, `npm audit`).

### Security
- **Permanent scope boundary, stated plainly as part of this release, not
  omitted from it:** no Anthropic API key (or any other LLM provider
  credential) exists in this project's environment, by deliberate,
  permanent choice
  ([ADR-0004](docs/adr/ADR-0004-real-llm-verification-descoped.md)). The
  full pipeline, the injection-hardening design, and the evaluation
  methodology are all real and proven against `StubLLMClient`, a
  documented, deterministic stand-in — not against a real model. Any
  number in this repository that looks like a quality measurement
  (refusal recall, citation accuracy, injection-detection rate) measures
  the harness correctly scoring that known stub behavior, not real model
  quality. Retrieval recall@k is the one exception: it never calls an LLM
  provider, so it is measured for real. `llm/factory.py`'s credential-swap
  seam means closing this gap, if ever revisited, is a config change, not
  a rewrite.
