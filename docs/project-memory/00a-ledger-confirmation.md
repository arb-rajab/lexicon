# Session 0 — Ledger Confirmation

> Purpose: freeze the technology allocation for this repository before any
> architecture work begins, per Portfolio Governance Rule D1 ("ledger before
> architecture").
> Last updated: 2026-08-26

## Ledger row (from master Framework Allocation Ledger)

| Field | Value |
|---|---|
| Repository | `lexicon` |
| Domain | Grounded document Q&A / retrieval-augmented generation |
| Platform | Web app |
| Primary frontend | Next.js 15 (App Router) |
| Primary backend | FastAPI (Python 3.12) |
| Primary mobile/desktop | — |
| Language(s) | Python, TypeScript |
| Key data/infra | PostgreSQL + pgvector, Redis, S3-compatible object storage (MinIO), queues |
| New learning objective | RAG evaluation methodology (golden-dataset-driven, CI-gated); LLM guardrails / prompt-injection defence |
| SDLC phases (deep) | 1. Discovery & Planning · 5. Verification & Testing |
| Overlap status | `UNIQUE` |

## Overlap check

- FastAPI (Python 3.12) as primary **backend**: not used as primary backend by
  any other public flagship repository — `privacy-forge` uses Laravel. ✅ No
  collision.
- Next.js 15 (App Router) as primary **frontend**: not used as primary
  frontend by any other public flagship repository — `privacy-forge` uses
  Vue 3 (via Inertia). ✅ No collision.
- No mobile/desktop framework claimed. N/A.

**Result: PASS.** This repository may proceed past Session 2 (per Rule D1, the
gate is actually "before Architecture," i.e. before Session 3 — recorded here
so Session 3 does not need to re-verify).

## Learning budget check (Rule D3 — max 2 new technologies)

| New technology | Genuinely new? | Counts against budget |
|---|---|---|
| RAG evaluation methodology (golden-dataset-driven, CI-gated retrieval/answer quality measurement) | Yes — first time this portfolio commits an evaluation harness to CI as a quality gate rather than ad hoc manual testing | 1 |
| LLM guardrails / prompt-injection defence (tested as a real security control, not assumed) | Yes — first adversarial-security treatment of an LLM-facing surface in this portfolio | 2 |
| Hybrid retrieval (lexical + vector), pgvector, FastAPI, Next.js, SQLAlchemy, Alembic, Redis, MinIO/S3, Docker Compose | No — established engineering patterns being applied to a new domain, not learned for the first time | 0 |

**Result: PASS.** Exactly 2 new technologies — at budget, not over.

## Deep SDLC phase check (Rule D2 — exactly two)

1. **Discovery & Planning** — chosen because the central design question this
   repository must answer with real reasoning, not assumption, is "why RAG at
   all, and not fine-tuning or search alone" — including an explicit
   failure-cost analysis (what a wrong-but-confident answer costs versus a
   refusal). That reasoning is deep discovery work, not a one-line
   justification, and belongs in Session 1.
2. **Verification & Testing** — chosen because the two claims this repository
   exists to demonstrate — "every answer is citation-backed or refused" and
   "prompt-injection defences are tested as real security controls" — are
   claims that only verification evidence can support. The committed
   evaluation harness (golden-dataset-driven, CI-gated) and adversarial
   prompt-injection test suite ARE that evidence.

No third deep phase is claimed. Architecture, Security, Implementation, and
Release are baseline; Operations and Retirement are intentionally light
(reasons to be recorded in `docs/SDLC-EVIDENCE.md` once the deep-phase work
lands).

## Ship-ability check (Rule D4)

Estimated time to credible v1: within the ≤120-hour guideline (full estimate
to be recorded against the flagship specification in Session 1, alongside the
failure-cost analysis that will size the MVP boundary).

## Governance sign-off

- [x] Ledger row confirmed against master register
- [x] Zero collisions
- [x] Learning budget ≤ 2 confirmed
- [x] Exactly two deep SDLC phases chosen
- [ ] Ship-ability check passed — full estimate deferred to Session 1
- [x] Repository added to Status Board under **Now** (see portfolio governance
      repo — action: add this row manually to `portfolio/STATUS.md`)

**This file is not modified again.** It is the frozen record Session 3 checks
before starting architecture work.
