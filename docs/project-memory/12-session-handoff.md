# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Session completed
- Session number and title: **Session 3 — Security & Threat Model**
- Objective: Produce `06-security-threat-model.md` for this RAG-specific
  system at the depth `privacy-forge`'s own Session 4 established (STRIDE
  threats with real mitigations and test references, a dedicated section
  for the domain-specific highest-risk category, explicit accepted risks
  with revisit triggers), covering three prioritised threat categories:
  (1) indirect prompt injection via ingested documents, on **both** LLM
  call surfaces this architecture has — the generator and, named
  explicitly as its own first-class threat, the independent verifier
  ADR-0001 depends on; (2) embedding inversion / information leakage; and
  (3) resolving the audit-trail tamper-evidence question Session 2 left
  explicitly open in `04-data-model.md`. Status: **complete**.

## Work completed
- **Read `12-session-handoff.md` and `03-architecture.md` first, as
  instructed, and located the exact Session 2 tamper-evidence question**
  before any design work — quoted verbatim in both
  `04-data-model.md`'s Revisit trigger section and this session's
  `06-security-threat-model.md` (Audit trail tamper-evidence section), not
  paraphrased or assumed.
- **Wrote `docs/adr/ADR-0002-audit-trail-tamper-evidence.md`** — resolves
  Session 2's open question. Reasoned fresh against `lexicon`'s own
  stakeholder model rather than reused from `privacy-forge` by default, per
  this session's explicit ground rule: `privacy-forge`'s ADR-0003
  hash-chain-plus-anchoring answer was built against a named driver (an
  internal actor covering up a *compliance violation*, for a product whose
  audit log is a legal-evidentiary artifact) that no document in
  `lexicon`'s own discovery/requirements work names. Three options
  considered: (A) full hash-chain + anchoring matching `privacy-forge`
  exactly — rejected as disproportionate to a threat this project hasn't
  actually established, and outside the fixed two-slot learning budget;
  (B) status-quo append-only-by-convention — rejected as not actually a
  control, just re-deferring the question; (C, **chosen**) DB-level
  permission enforcement — the application's runtime database role
  restricted to `INSERT`/`SELECT` on `QUERY_LOG`/`RETRIEVED_CHUNK`/
  `CITATION_VERDICT`, `UPDATE`/`DELETE` reserved to the migration/admin
  role — mirroring `privacy-forge`'s own T-16 mitigation for the
  structurally equivalent realistic-threat class (a compromised
  app-layer credential or buggy app code), not its ADR-0003 hash-chain,
  which targets a different, stronger threat this project doesn't
  currently have. Residual limit stated honestly: does not resist a fully
  privileged/insider actor holding the migration-level credential itself —
  named as an accepted risk with a concrete revisit trigger, not hidden.
- **Wrote `docs/adr/ADR-0003-verification-injection-hardening.md`** — a
  new, distinct architectural decision this session's threat model
  surfaced: hardening the verification call (ADR-0001) against
  passage-embedded prompt injection specifically, since the verifier's
  input (one specific, attacker-guaranteed-verbatim passage per claim) is
  structurally more concentrated and consequential to hijack than the
  generator's noisier, backstopped context. Three options considered:
  (A) rely on instruction-priority alone — rejected as an unverified
  assumption, the exact pattern this project's own discipline (Session 1's
  similarity-score finding) rejects elsewhere; (B) pre-ingestion content
  filtering — rejected as unreliable and prone to corrupting legitimate
  documents whose real content is lexically imperative (e.g. compliance
  policy text); (C, **chosen**) four-part structural hardening of the
  verification call itself — forced structured output (no free-text
  surface), sandwiched untrusted-content delimiting (warning stated both
  before *and* after the passage), an explicit `injection_suspected`
  self-report that auto-fails entailment regardless of the model's own
  `entailed` value, and fail-closed on any unparseable/ambiguous verifier
  response. Consequences recorded for Session 4: `CITATION_VERDICT` should
  gain an `injection_suspected` column (small, additive schema change);
  the verification-call contract ADR-0001 already required Session 4 to
  define must implement this exact schema and prompt structure.
- **Wrote `docs/project-memory/06-security-threat-model.md`** in full,
  matching `privacy-forge`'s Session 4 rigor: a 6-boundary trust-boundary
  diagram (Mermaid) that deliberately draws the generation call (B3) and
  verification call (B4) as **two distinct boundaries**, not one
  "talks to the LLM" boundary, since this session's central finding is
  that they carry structurally different risk; a 12-row STRIDE table with
  real mitigations and test references for every threat, not descriptions
  alone; a dedicated "Indirect prompt injection via ingested documents"
  section (the domain-specific highest-risk category, matching
  `privacy-forge`'s "Demo Instance Data Safety" precedent for giving its
  own highest-risk category a named section) that treats generator hijack
  (T-01) and verifier hijack (T-02) as two distinct, separately-mitigated
  threats and specifies a committed adversarial test corpus design (4
  categories: direct override, authority-spoofing, verifier-targeted
  always-true patterns, and legitimate-imperative-text negative controls
  to measure the false-positive rate, not just the true-positive rate); a
  dedicated "Embedding inversion / information leakage" section that
  checked directly against `05-api-contracts.md` (not assumed) that no
  current endpoint serialises `CHUNK.embedding`, and that the one
  score-bearing endpoint is RBAC-scoped to the role that already has
  plaintext document access; a dedicated "Audit trail tamper-evidence"
  section quoting the Session 2 question verbatim and resolving it via
  ADR-0002; a "Cost-abuse / denial-of-wallet" section recommending two
  additions beyond the already-specified per-caller rate limit (NFR-007)
  — an absolute per-window spend-ceiling circuit breaker, and a
  question-text length cap, both currently unspecified gaps; baseline
  auth/authz, secrets management, and dependency/supply-chain sections;
  and a 5-row Accepted risks table with real reasoning and revisit
  triggers per risk, not a blanket "fully mitigated" claim.
- **Re-confirmed, not silently dropped:** instance-level authentication
  mechanics remain deferred to `08-deployment-and-operations.md` (Session
  2's decision) — this session adds two new *requirements* on that future
  mechanism (T-04: per-corpus-scoped authorisation on every
  `{corpus_id}`-scoped endpoint; T-12: standard session/credential
  hardening) rather than inventing the mechanism itself, which would have
  gone beyond this session's scope.
- Updated `docs/SDLC-EVIDENCE.md`'s Architecture & Design row (Phase 3)
  with this session's evidence, extending rather than replacing Session
  2's entry — security/threat modelling is categorised under Architecture
  & Design in this portfolio's convention (confirmed against
  `privacy-forge`'s own `SDLC-EVIDENCE.md`, which states this explicitly:
  "3. Architecture & Design (includes security/threat modelling)").
- No implementation code was touched — `backend/` and `frontend/` are
  unchanged from Session 0/2, per this session's ground rules.
- `privacy-forge`, `laravel-consent-guard`, and `bookslot` were not
  touched, except to **read** `privacy-forge/docs/project-memory/06-security-threat-model.md`
  as the explicit format/depth reference this session's task named.

## Files created or changed
- `docs/adr/ADR-0002-audit-trail-tamper-evidence.md` — new: resolves
  Session 2's open tamper-evidence question.
- `docs/adr/ADR-0003-verification-injection-hardening.md` — new:
  hardens the verification call against passage-embedded prompt injection
  (the verifier-hijack threat, T-02).
- `docs/project-memory/06-security-threat-model.md` — written in full
  (was an empty template).
- `docs/SDLC-EVIDENCE.md` — Architecture & Design row extended with
  Session 3's evidence.
- `docs/project-memory/12-session-handoff.md` — this file.

## Decisions made
- **Audit trail tamper-evidence is enforced at the database permission
  layer (restricted `UPDATE`/`DELETE` grants), not via hash-chaining** —
  `docs/adr/ADR-0002-audit-trail-tamper-evidence.md`. Resolves Session 2's
  explicitly open question. Not a reuse of `privacy-forge`'s ADR-0003 by
  default — reasoned fresh, and explicitly rejected as disproportionate to
  this project's own, different threat driver.
- **The independent verification call (ADR-0001) gets its own,
  structurally distinct prompt-injection hardening** — forced structured
  output, sandwiched delimiting, an `injection_suspected` auto-fail
  signal, fail-closed on ambiguity — `docs/adr/ADR-0003-verification-injection-hardening.md`.
  Verifier hijack (T-02) is treated as a first-class threat, distinct from
  and more severe than generator hijack (T-01), because the verifier is
  the last check in the pipeline with no tertiary gate behind it.
- **No API surface currently exposes raw embeddings**, and the one
  score-bearing audit endpoint is already RBAC-scoped to a role with
  equivalent underlying data access — confirmed directly against the
  existing API contract, not assumed; recorded as a standing, testable
  constraint (no endpoint may ever serialise `CHUNK.embedding`) rather than
  an incidental fact that could regress silently.
- **Two cost-abuse controls recommended as additions to the
  already-specified per-caller rate limit (NFR-007):** an absolute
  per-window LLM-spend ceiling, and a maximum question-text length. Both
  are currently unspecified gaps, not yet implemented — recorded as
  Session 4 requirements, not invented numbers.
- **Instance-level authentication mechanics remain deferred**, per Session
  2's decision — re-confirmed as still open, with two new requirements
  (T-04 cross-corpus authorisation scoping, T-12 session/credential
  hardening) added onto whatever mechanism is eventually chosen.

## Validation performed
- The Session 2 tamper-evidence question was located and quoted verbatim
  from its source (`04-data-model.md`'s Revisit trigger section) before
  any design work began, per this session's explicit instruction — not
  paraphrased from the session handoff's shorter restatement, though both
  say the same thing.
- Checked `05-api-contracts.md`'s actual response schemas directly (not
  assumed) before writing the embedding-inversion finding — confirmed
  neither the `/query` citation objects nor the `/query-logs/{id}` detail
  response serialise `CHUNK.embedding`, and confirmed the score-bearing
  endpoint's existing RBAC scope, before concluding the current surface is
  sound.
- Cross-checked `privacy-forge`'s own `06-security-threat-model.md` and
  `SDLC-EVIDENCE.md` directly (read, not recalled) to confirm both the
  format/depth bar and the SDLC-phase categorisation convention (security
  under Architecture & Design) before matching them here.
- Confirmed `backend/` and `frontend/` are unchanged (no implementation
  this session, per ground rules); confirmed no files under
  `privacy-forge/`, `laravel-consent-guard/`, or `bookslot/` were modified.

## Open questions and risks
- **New risk, from this session:** the verifier-hijack mitigation
  (ADR-0003)'s `injection_suspected` signal has an unmeasured
  false-negative rate — a sufficiently subtle injection attempt might not
  be recognised as an attempt at all by the model. This is why
  fail-closed-on-ambiguity exists as an independent second layer rather
  than relying on detection alone; the real, measured answer is Session
  5's adversarial suite, specifically the verifier-targeted category
  (T-02), not an assumption made now.
- **Carried forward from Session 2, still open:** no LLM API credentials
  exist in this environment — re-confirmed, not silently dropped. Still
  not a blocker for this session (no live API calls were needed to write
  the threat model); still blocks Session 4 (Implementation) from
  starting the query-path work.
- **Carried forward from Session 2, still open:** the naive
  `plainto_tsquery` regression risk (FR-005) has no code-level guard yet —
  unchanged this session, still a Session 4 target.
- **New risk, from this session:** two cost-abuse controls (spend-ceiling
  circuit breaker, question-length cap) are recommended but not yet
  specified as concrete numbers or implemented — a Session 4 design and
  implementation task, not a decided value.
- **New risk, from this session:** `CITATION_VERDICT` needs an additive
  schema change (`injection_suspected` boolean) before Session 4's
  verification-call implementation can match ADR-0003's design — a small
  but real dependency Session 4 must account for in its migration
  ordering, not discovered mid-build.
- **No blockers for the next session itself.** Session 4 (Implementation)
  can begin once the LLM-credentials item is resolved — that remains the
  one real gate, unchanged from Session 2's assessment.

## Next recommended session
- Proposed session title: **Session 4 — Implementation**
- Single objective: Build the ingestion and query pipelines for real,
  against this repository's now-complete requirements, architecture, data
  model, API contract, and threat model — the first session where
  `backend/`/`frontend/` change beyond the Session 0 skeleton. Must resolve
  the LLM-credentials open item first (provision a real Anthropic API key,
  or explicitly revisit the provider choice if policy prevents it), then
  implement: hybrid retrieval (OR-semantics keyword + vector + RRF), the
  two-call generate/verify pipeline per ADR-0001 and ADR-0003's exact
  schema, the two-database-role permission split per ADR-0002, and the
  code-level guard against `plainto_tsquery` regression (FR-005, carried
  since Session 1).
- Inputs required: this handoff; `02-requirements.md`; `03-architecture.md`;
  `04-data-model.md`; `05-api-contracts.md`; `06-security-threat-model.md`;
  `docs/adr/ADR-0001-groundedness-refusal-check.md`; `ADR-0002`; `ADR-0003`.
- Expected deliverables: working ingestion and query endpoints; the
  two-role database permission split (ADR-0002); the verification call
  implemented to ADR-0003's exact contract, including the
  `injection_suspected` field and its associated `CITATION_VERDICT`
  migration; the FR-005 query-builder guard; real feature tests for FR-001
  through FR-014.
- Definition of done: the ingestion → query → generate → verify → decide
  flow works end-to-end against a real (or realistically stubbed, if
  credentials remain blocked) LLM provider; the audit trail's permission
  split is proven via a real grant-assertion test, not a config review;
  no regression on the spike's 100% recall@3 baseline (NFR-001).

## Paste-into-new-session context

**Project:** lexicon — grounded document Q&A system; every answer is
citation-backed or refused
**Track:** public flagship
**Repository state:** branch `main`, unreleased (pre-v0.1.0), Session 3
complete

**Problem being solved (validated Session 1):** teams with a bounded,
changing, authoritative document corpus need answers they can act on
without independently re-reading the source. See `00-project-brief.md` and
`00b-rag-vs-alternatives.md`.

**The central design decision from Session 2 (unchanged):** refusal cannot
rely on retrieval similarity alone. The architecture requires an
independent, post-generation groundedness/entailment verification call
before any answer is released. See
`docs/adr/ADR-0001-groundedness-refusal-check.md`.

**This session's central finding:** the independent verifier ADR-0001
depends on is itself a first-class attack target — a poisoned document's
passage text can be engineered to hijack the verification call into
reporting false entailment, which would defeat ADR-0001's entire purpose
while looking, from every other vantage point, like the system working
correctly. `docs/adr/ADR-0003-verification-injection-hardening.md` designs
the defense (forced structured output, sandwiched delimiting, an
`injection_suspected` auto-fail signal, fail-closed on ambiguity). The
audit-trail tamper-evidence question Session 2 left open is resolved by
`docs/adr/ADR-0002-audit-trail-tamper-evidence.md` (DB-level permission
enforcement, not hash-chaining — reasoned as a deliberate, justified
scope difference from `privacy-forge`'s ADR-0003, not an oversight).

**Current stack:**
- Backend: FastAPI, Python 3.12
- Frontend: Next.js 15 (App Router)
- Data: PostgreSQL + pgvector, Redis, S3-compatible object storage (MinIO)
- Infra: Docker Compose, GitHub Actions CI
- LLM provider (decided Session 2, not yet wired up): Anthropic Claude
  API — mid/high tier for generation, small/fast tier for verification.
  **No API credentials exist in this environment yet — this blocks Session
  4 (Implementation), not Session 3.**
- Testing: pytest (backend), Vitest (frontend) — still only the health-check
  skeleton; no application logic exists yet.

**Architecture decisions that must not be reversed:**
- Licence AGPL-3.0.
- Next.js 15 + FastAPI/Python 3.12, frozen against the portfolio ledger.
- Exactly two deep SDLC phases: Discovery & Planning (complete), Verification
  & Testing. No third deep phase.
- Learning budget exactly 2 (RAG evaluation methodology; LLM
  guardrails/prompt-injection defence) — at cap.
- RAG (hybrid retrieval + grounded generation), not fine-tuning or
  keyword-only search.
- Hybrid keyword search must use OR semantics, never `plainto_tsquery`.
- **Refusal must be post-generation groundedness/entailment verification —
  an independent LLM call — not a similarity threshold, not reranking
  alone, not a pre-generation relevance gate.** (`ADR-0001`.)
- **The verification call must implement ADR-0003's exact hardening
  contract** — forced structured output with `entailed`/`injection_suspected`,
  sandwiched delimiting, fail-closed on ambiguity — not a simplified
  "just ask yes/no" version.
- **The audit trail's append-only property is enforced by database
  permission grants** (ADR-0002) — the application's runtime DB role must
  never receive `UPDATE`/`DELETE` on `QUERY_LOG`/`RETRIEVED_CHUNK`/
  `CITATION_VERDICT`.
- LLM provider is Anthropic Claude, with model-tier asymmetry for cost
  control.

**Implementation state:**
- Done: repository skeleton, licence, governance docs, minimal
  backend/frontend skeletons, docker-compose, CI, full discovery/planning
  documentation, executed feasibility spike, full requirements and
  architecture documentation including ADR-0001, data model, API
  contracts, and now a full security/threat model with ADR-0002 and
  ADR-0003.
- In progress: nothing mid-flight.
- Not started: everything product-related as code — no ingestion,
  retrieval, generation, or verification exists as application code yet
  (Session 4).

**Constraints and non-goals:**
- Full non-goals table: `docs/project-memory/01-scope-and-non-goals.md`.
- New this session: two cost-abuse controls (spend ceiling, question-length
  cap) are recommended but not yet given concrete numbers — a Session 4
  decision against real pricing, same discipline as NFR-007's existing
  "not set here — no fabricated number" pattern.

**Task for the next session (single objective):**
Implementation: build the ingestion and query pipelines for real, resolve
the LLM-credentials blocker first, implement ADR-0001/0002/0003 as working
code with real feature tests.

**Definition of done:**
- Working ingestion and query endpoints, end-to-end.
- ADR-0002's database permission split proven via a real grant-assertion
  test.
- ADR-0003's verification contract implemented exactly, including
  `injection_suspected`.
- No regression on NFR-001's 100% recall@3 baseline.

**Files to attach or paste:**
- `docs/project-memory/12-session-handoff.md` (this file)
- `docs/adr/ADR-0001-groundedness-refusal-check.md`
- `docs/adr/ADR-0002-audit-trail-tamper-evidence.md`
- `docs/adr/ADR-0003-verification-injection-hardening.md`
- `docs/project-memory/03-architecture.md`
- `docs/project-memory/04-data-model.md`
- `docs/project-memory/05-api-contracts.md`
- `docs/project-memory/06-security-threat-model.md`

**Ground rules:** Do not change the stack. Do not introduce a third new
technology. Do not expand the deep-SDLC-phase count beyond two. Do not
touch `privacy-forge`, `laravel-consent-guard`, or `bookslot`. Ask before
introducing any new dependency or scope item not already anticipated above.
