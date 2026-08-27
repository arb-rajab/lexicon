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
| 1. Discovery & Planning | **Deep** | **Produced, Session 1 (2026-08-27):** validated problem statement, failure-cost analysis, and target-user reasoning (`00-project-brief.md`); explicit options-considered "why RAG, not fine-tuning or search alone" comparison (`00b-rag-vs-alternatives.md`); a real, executed feasibility spike against a real corpus — hybrid retrieval technically proven end-to-end, plus two honestly-reported findings (naive AND-semantics keyword search scored 0% recall@3; retrieval-similarity-only refusal is unsafe — a topically-adjacent-but-wrong query scored inside the correct-answer similarity range) — see `docs/spikes/session1-hybrid-retrieval/RESULTS.md`; 5 concrete success metrics; full non-goals table with reconsideration conditions | `docs/project-memory/00-project-brief.md`, `docs/project-memory/00b-rag-vs-alternatives.md`, `docs/project-memory/01-scope-and-non-goals.md`, `docs/spikes/session1-hybrid-retrieval/` |
| 2. Requirements Analysis | Baseline | **Produced, Session 2 (2026-08-27):** user stories with acceptance criteria for ingestion, querying, refusal, and audit flows; functional requirements traceable to the MVP boundary; non-functional requirements with real targets where the spike provides evidence and explicit "not set — no fabricated number" placeholders where it doesn't (retrieval quality at scale, refusal recall, citation accuracy, per-query cost); a full data-classification pass | `docs/project-memory/02-requirements.md` |
| 3. Architecture & Design | Baseline | **Produced, Session 2 (2026-08-27):** system context and container diagrams (Mermaid); the refusal-mechanism decision as this repo's first ADR — post-generation groundedness/entailment verification, chosen over reranking-only and pre-generation LLM-as-judge gating, directly against Session 1 spike Finding 2's measured numbers (`docs/adr/ADR-0001-groundedness-refusal-check.md`); the ingestion pipeline and hybrid-retrieval architecture (OR-semantics keyword + vector + RRF, fixed by the spike); LLM provider choice (Anthropic Claude, model-tier asymmetry for cost control) with the missing-API-credentials open item stated explicitly; a full data model (ERD) and API contract | `docs/project-memory/03-architecture.md`, `docs/project-memory/04-data-model.md`, `docs/project-memory/05-api-contracts.md`, `docs/adr/ADR-0001-groundedness-refusal-check.md` |
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
