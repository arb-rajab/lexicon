# lexicon

> **Status:** Session 7 complete — ingestion, hybrid retrieval,
> generation/verification pipeline, injection hardening, evaluation
> harness, and a production-shaped local deployment are all real and
> tested. **Real LLM provider verification is permanently descoped by
> deliberate choice ([ADR-0004](docs/adr/ADR-0004-real-llm-verification-descoped.md))**
> — see [`docs/CASE-STUDY.md`](docs/CASE-STUDY.md) for the full account of
> what that means and what it cost. See
> [`docs/project-memory/12-session-handoff.md`](docs/project-memory/12-session-handoff.md)
> for session-by-session state.

A grounded document Q&A system: every answer is citation-backed against the
supplied documents, or the system refuses to answer. This is enforced by an
independent groundedness/entailment verification call, not a similarity
threshold — Session 1's feasibility spike measured that a similarity
threshold cannot tell a correct answer (0.706–0.848 top similarity) apart
from a topically-adjacent but wrong one (0.701), which is why the refusal
mechanism exists in the shape it does
([ADR-0001](docs/adr/ADR-0001-groundedness-refusal-check.md)). Retrieval
quality and the verification harness's own methodology are measured by a
committed, CI-gated evaluation suite, not eyeballed. The verification call
is hardened against passage-embedded prompt injection with a
code-level-provable guarantee (18/18 structural containment across an
18-document adversarial corpus, regardless of model tier —
[ADR-0003](docs/adr/ADR-0003-verification-injection-hardening.md)).

**Read this before trusting any quality number in this repository:** no
Anthropic API key (or any other LLM provider credential) exists in this
project's environment, by permanent, deliberate choice
([ADR-0004](docs/adr/ADR-0004-real-llm-verification-descoped.md)). The full
pipeline, the injection-hardening design, and the evaluation methodology
are all real and proven against `StubLLMClient`, a documented,
deterministic stand-in — not against a real model. Any number in this
repository that looks like a quality measurement (refusal recall, citation
accuracy, injection-detection rate) measures the harness correctly scoring
that known stub behavior, not real model quality. Retrieval recall@k is the
one exception — it never calls an LLM provider, so it is measured for real
(9/9 at Session 1 and again at Session 5). See
[`docs/CASE-STUDY.md`](docs/CASE-STUDY.md) for the full story of why this
boundary exists and what stayed real despite it.

## What this demonstrates

- **Discovery & Planning (deep):** the "why RAG, not fine-tuning or search
  alone" reasoning, with an explicit failure-cost analysis, is written down
  and validated by a real spike against real infrastructure — not assumed.
- **Verification & Testing (deep):** a golden-dataset-driven, CI-gated
  evaluation harness whose methodology is real and proven, and an
  18-document adversarial prompt-injection test suite whose code-level
  containment guarantees are proven regardless of LLM tier — both stated
  with the ADR-0004 boundary attached everywhere it applies.
- Citation-or-refusal as a hard product invariant, enforced by an
  independent verification call, not a prompt suggestion or a similarity
  threshold.
- A production-shaped local deployment (real Dockerfiles, a real
  five-service compose stack) with three real bugs found and fixed by
  actually running it under production-like conditions.

Stack: FastAPI (Python 3.12) · Next.js 15 (App Router) · PostgreSQL +
pgvector · Redis · S3-compatible storage (MinIO).

## Project status

This repository is built through a session-based workflow. Current phase:
**Session 7 (Release Readiness) — complete.**

Full portfolio context: this is a flagship repository in a broader
public/private software portfolio. See `docs/project-memory/` for the
complete project memory pack, [`docs/CASE-STUDY.md`](docs/CASE-STUDY.md)
for the narrative account of the project's real engineering arc, and
`docs/SDLC-EVIDENCE.md` for the phase-by-phase evidence map.

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
(`http://localhost:8010/health`, `/ready`) and the frontend
(`http://localhost:3001/api/health`). The full pipeline is real: create a
corpus, upload documents, and query it via the backend's
`/api/v1/corpora`/`.../documents`/`.../query` endpoints
(`docs/project-memory/05-api-contracts.md`). Answers are generated by
`StubLLMClient` unless `ANTHROPIC_API_KEY` is set (see the ADR-0004 boundary
above) — setting that variable is a config change, not a rewrite.

Host ports are deliberately non-default (8010, 3001, 5433, 6380) to avoid
colliding with other local projects; internal service-to-service
communication is unaffected. A separate, production-shaped stack
(`docker-compose.prod.yml`, gunicorn + non-root images + pre-warmed
embedding model, distinct host ports 8011/3002/5434/6381/9010-9011) is
proven to boot and serve real traffic locally — see
[`docs/project-memory/08-deployment-and-operations.md`](docs/project-memory/08-deployment-and-operations.md).

## Documentation

- [`docs/CASE-STUDY.md`](docs/CASE-STUDY.md) — the real engineering story:
  the spike finding that changed the architecture, the injection-hardening
  design, the ADR-0004 arc, and real bugs found and fixed
- [`docs/project-memory/`](docs/project-memory/) — brief, requirements,
  architecture, security, testing, operations, decisions, risks, backlog,
  handoff, release notes, maintenance/retirement plan
- [`docs/adr/`](docs/adr/) — architecture decision records (groundedness
  refusal, audit-trail tamper-evidence, verification-injection hardening,
  real-LLM-verification descoping)
- [`docs/spikes/session1-hybrid-retrieval/`](docs/spikes/session1-hybrid-retrieval/) —
  the Session 1 feasibility spike and its raw results
- [`docs/security/adversarial-corpus/`](docs/security/adversarial-corpus/) —
  the committed prompt-injection adversarial test corpus
- [`docs/SDLC-EVIDENCE.md`](docs/SDLC-EVIDENCE.md) — phase-by-phase evidence map
- [`SECURITY.md`](SECURITY.md) — vulnerability disclosure policy

## Licence

AGPL-3.0 — see [`LICENSE`](LICENSE). Rationale: this is a hostable
application, not a library; AGPL ensures modifications to a hosted version
remain shareable.
