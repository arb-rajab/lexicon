# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Repository governance: framework allocation ledger row confirmed
  (`UNIQUE` — FastAPI (Python 3.12) + Next.js 15, no flagship collision).
- Project Memory Pack scaffolded (15-file structure under
  `docs/project-memory/`).
- Minimal, real FastAPI backend skeleton with a passing health-check test.
- Minimal, real Next.js 15 (App Router) frontend skeleton with a passing
  build and test.
- `docker-compose.yml` booting PostgreSQL (pgvector), Redis, MinIO, and both
  application services, with both health checks returning 200.
- A real CI pipeline from the start: lint, type-check, security scan, and
  tests for both backend and frontend, plus gitleaks and CodeQL.
- Session 0 deliverables: ledger confirmation, project brief stub,
  repository skeleton, licence, contribution/security/conduct policies.

Nothing has shipped yet — this project is pre-v0.1.0.
