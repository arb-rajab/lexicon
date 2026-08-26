# SDLC Evidence Map

**Deep phases:** 1. Discovery & Planning · 5. Verification & Testing
**Baseline phases:** 3. Architecture & Design · 4. Implementation · 6. Release & Deployment
**Intentionally light:** 7. Operations & Maintenance, 8. Retirement & Handover — because
this is a single-operator, self-hostable flagship where the deep evidence
budget is deliberately spent on proving the two claims the project exists to
demonstrate (grounded answers, tested security controls), not on operational
maturity. Reasons will be finalised once the deep-phase work lands.

| Phase | Depth | Evidence | Location |
|---|---|---|---|
| 1. Discovery & Planning | **Deep** | Not yet produced — Session 1: "why RAG, not fine-tuning or search alone" reasoning, explicit failure-cost analysis, user research, feasibility spike on a sample corpus | `docs/project-memory/00-project-brief.md`, `docs/project-memory/01-scope-and-non-goals.md` |
| 2. Requirements Analysis | Baseline | Not yet produced | `docs/project-memory/02-requirements.md` |
| 3. Architecture & Design | Baseline | Not yet produced | `docs/project-memory/03-architecture.md`, `docs/project-memory/04-data-model.md`, `docs/project-memory/05-api-contracts.md` |
| 4. Implementation | Baseline | Repository skeleton only (Session 0): minimal FastAPI backend, minimal Next.js frontend, no feature code | `backend/`, `frontend/` |
| 5. Verification & Testing | **Deep** | Not yet produced — planned: committed golden-dataset-driven, CI-gated retrieval/answer evaluation harness; adversarial prompt-injection test suite treated as a real security control | `docs/project-memory/07-testing-strategy.md` (future: `eval/`, `docs/security/`) |
| 6. Release & Deployment | Baseline | CI pipeline (lint, type-check, security scan, tests) and `docker-compose.yml` proven to boot | `.github/workflows/ci.yml`, `docker-compose.yml` |
| 7. Operations & Maintenance | Light | Not yet produced | `docs/project-memory/08-deployment-and-operations.md` |
| 8. Retirement & Handover | Light | Not yet produced | `docs/project-memory/14-maintenance-and-retirement.md` |

## Why some phases are light

Operations and Retirement/Handover are intentionally light for this
repository: the deep-evidence budget (Rule D2, exactly two phases) is
committed to Discovery and Verification/Testing, because those two phases
carry the evidence for this project's actual claims — grounded, refusal-safe
answers, and prompt-injection defences that are tested rather than assumed.
Full reasoning to be recorded once Session 1 and the Verification/Testing
deep-phase work land.
