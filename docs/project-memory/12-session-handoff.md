# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Session completed
- Session number and title: **Session 2 — Requirements & Architecture**
- Objective: Turn Session 1's validated discovery into concrete
  functional/non-functional requirements and a real system architecture —
  specifically resolving the two firm inputs Session 1 produced: (1) hybrid
  retrieval must use OR-semantics keyword search, and (2) the refusal
  mechanism needs an explicit groundedness/entailment check design, not a
  similarity threshold. Flagged explicitly as one of the most important
  design decisions this repository will make.
- Status: **complete**

## Work completed
- **Wrote `docs/adr/ADR-0001-groundedness-refusal-check.md`** — this
  repository's first ADR, and the centerpiece deliverable of this session.
  Designed directly against Session 1's spike Finding 2 (cited by exact
  numbers in the ADR's Context section: a topically-adjacent-but-wrong query
  scored 0.701 top similarity, inside the 0.706–0.848 range of genuinely
  correct retrievals in the same run), not as a generic "add safety checks"
  deferral. Considered three real options with stated trade-offs:
  (A) cross-encoder reranking — rejected as the *primary* mechanism because
  it still answers "is this topically relevant," the same question
  similarity already answers, not "does this passage support this specific
  claim"; (B) pre-generation LLM-as-judge gating — rejected because without
  a candidate answer to check against, the judge is vulnerable to the same
  topical-adjacency trap; (C, **chosen**) post-generation
  groundedness/entailment verification — generation is conditioned on
  retrieved passages with mandatory chunk-scoped citations and a
  self-refusal instruction, followed by an **independent** LLM call
  (different model, blind to the generator's own reasoning) that checks
  each cited claim against its exact passage text before the answer is
  released. Reranking (A) is retained as a secondary, non-decisive
  retrieval-quality improvement, not as a stand-in for verification.
  Real trade-offs stated and accepted: two LLM calls per answered query
  instead of one (cost, latency), and the verification step's own accuracy
  is unmeasured until Session 5's evaluation harness — not claimed as
  solved by this ADR alone.
- **Wrote `docs/project-memory/02-requirements.md`** in full, matching
  `privacy-forge`'s `02-requirements.md` rigor: a roles/permissions note
  (this product has no multi-role auth model in v1, stated explicitly
  rather than a padded fake matrix), 5 user stories with Given/When/Then
  acceptance criteria across ingestion, querying, refusal, and audit flows,
  14 functional requirements traceable to the MVP boundary
  (`01-scope-and-non-goals.md`), 10 non-functional requirements — where the
  spike provides real numbers they're used (NFR-001, a 100% recall@3
  regression floor on the actual spike corpus); where it doesn't, the
  target is explicitly marked "not set here — no fabricated number" with a
  named owner (NFR-002–004 retrieval/refusal/citation quality at scale →
  Session 5's harness; NFR-007 per-query cost budget → Session 4's real
  pricing) rather than inventing a plausible-looking figure — and a full
  data-classification table covering document content, chunk embeddings
  (explicitly flagged as carrying source-content-level sensitivity via
  embedding-inversion risk, not "just numbers"), query text, generated
  answers, and query logs.
- **Wrote `docs/project-memory/03-architecture.md`** in full, with the
  refusal-mechanism decision (ADR-0001) as its explicit centerpiece — the
  Key Flows section's "ask a question" sequence diagram is the direct
  architectural expression of the ADR (two independent refusal entry
  points: generator self-refusal, and verification failure; an answer is
  never shown to the user without passing the independent verification
  call). Also covers: the ingestion pipeline (upload → object storage →
  queued chunking/embedding → incremental per-document re-index, keeping
  the "cheap freshness" claim against fine-tuning real rather than
  aspirational); the hybrid-retrieval architecture fixed as OR-semantics
  keyword + vector + RRF fusion (Session 1's spike, now the production
  design rather than a re-litigated question); fail-closed failure handling
  (an LLM provider outage during generation or verification never falls
  back to an unverified or similarity-only answer); and LLM provider fit —
  **decision: Anthropic Claude API**, with a stated reason (native prompt
  caching directly reduces the repeated-passage cost this two-call pipeline
  incurs) and a model-tier asymmetry for cost control (mid/high tier for
  open-ended generation, small/fast tier for the narrow per-claim
  entailment check in verification — the asymmetry is what keeps "two calls
  instead of one" from doubling cost outright). System context and
  container diagrams in Mermaid, matching this portfolio's established
  C4Context/C4Container convention (`privacy-forge`'s `03-architecture.md`).
- **Checked this environment directly and confirmed no LLM API credentials
  exist** (no `ANTHROPIC_API_KEY` or equivalent) — recorded as an explicit
  open item in `03-architecture.md`'s own section, not left to surface as a
  surprise mid-Session-4 the way Stripe credentials reportedly were
  discovered mid-build in a prior portfolio project. Stated as **not** a
  blocker for this session (no live API calls are needed to write
  requirements/architecture) but as a concrete action item that must be
  resolved before Session 4 (Implementation) can begin the query-path work.
- **Wrote `docs/project-memory/04-data-model.md`** in full: ERD (Mermaid)
  covering `CORPUS`/`DOCUMENT`/`CHUNK`/`QUERY_LOG`/`RETRIEVED_CHUNK`/
  `CITATION_VERDICT`; the entity design makes the refusal gate's audit
  trail concrete (`CITATION_VERDICT` is literally the per-claim entailment
  verdict ADR-0001 requires, not an abstract "logging" placeholder);
  invariants section documents that `QUERY_LOG.final_answered` is enforced
  at the application layer (not a DB constraint, since verification is a
  multi-call process a `CHECK` constraint can't observe) and names this as
  a known single point of failure for the whole invariant, deliberately not
  hand-waved; an honest revisit-trigger note that, unlike `privacy-forge`'s
  hash-chained audit log (ADR-0003), this design is append-only-by-
  convention only, pending the not-yet-written security/threat-model
  session's judgment on whether tamper-evidence is actually required here.
- **Wrote `docs/project-memory/05-api-contracts.md`** in full: REST/JSON
  under `/api/v1/`, with the query endpoint's response schema directly
  reflecting the three-way refusal reason (`self_refused` /
  `verification_failed` / `no_candidates_retrieved`) so a corpus owner can
  distinguish "nothing relevant was found" from "something was found but
  didn't verify"; explicit error-model rule that a provider-call failure
  (`502`) is never represented as a successful refusal response, so an
  operational failure can't be mistaken for the refusal mechanism working
  correctly.
- Updated `docs/SDLC-EVIDENCE.md`'s Requirements Analysis and Architecture &
  Design rows with real evidence citations, replacing "Not yet produced."
- Updated `README.md`'s status banner and project-status line (Session 1 →
  Session 2 complete).
- No implementation code was touched — `backend/` and `frontend/` are
  unchanged from Session 0, per this session's ground rules.
- `privacy-forge`, `laravel-consent-guard`, and `bookslot` were not touched.

## Files created or changed
- `docs/adr/ADR-0001-groundedness-refusal-check.md` — new: this
  repository's first ADR, the refusal-mechanism decision.
- `docs/project-memory/02-requirements.md` — written in full (was an empty
  template).
- `docs/project-memory/03-architecture.md` — written in full (was an empty
  template).
- `docs/project-memory/04-data-model.md` — written in full (was an empty
  template).
- `docs/project-memory/05-api-contracts.md` — written in full (was an empty
  template).
- `docs/SDLC-EVIDENCE.md` — Requirements Analysis and Architecture & Design
  rows updated with real evidence citations.
- `README.md` — status banner, project-status line.
- `docs/project-memory/12-session-handoff.md` — this file.

## Decisions made
- **Refusal mechanism is post-generation groundedness/entailment
  verification, run as an independent LLM call, not a retrieval-similarity
  threshold, not reranking alone, and not a pre-generation relevance
  gate** — `docs/adr/ADR-0001-groundedness-refusal-check.md`. This is this
  session's central decision and the one flagged as most important; it is
  now a fixed architectural input, not an open question.
- **LLM provider: Anthropic Claude API**, with model-tier asymmetry
  (mid/high tier for generation, small/fast tier for verification) as the
  primary cost-control lever — `03-architecture.md`. Specific model IDs are
  deliberately not pinned (a Session 4 configuration decision against
  whatever the current lineup is then), to avoid this document going stale.
- **Hybrid retrieval architecture (OR-semantics keyword + vector + RRF) is
  fixed as the production design**, not re-derived — carried forward from
  Session 1's spike per the handoff's stated input.
- **No numeric target is invented for retrieval quality at scale, refusal
  recall, citation accuracy, or per-query cost** (`02-requirements.md`
  NFR-002–004, NFR-007) — each is explicitly marked as pending real
  evidence (Session 5's harness or Session 4's real provider pricing)
  rather than filled with a plausible-sounding guess.
- **Instance-level authentication/authorisation is explicitly deferred as
  an operator/deployment concern**, not designed this session — the two
  functional roles this product itself distinguishes (corpus owner,
  knowledge worker) are recorded, but login/session mechanics are not
  invented ahead of `08-deployment-and-operations.md`.

## Validation performed
- No application code exists yet for this session's deliverables to be
  tested against — this session's own "definition of done" is that the
  documents are written and reasoned, not templated, which was checked by
  re-reading each document against `01-scope-and-non-goals.md`'s MVP
  boundary and `00-project-brief.md`'s success metrics for traceability
  (every FR maps to a user story; every "not yet built" claim in the spike
  is respected rather than quietly overstated).
- Confirmed directly (not assumed) that no LLM API credentials exist in
  this environment before writing the architecture doc's open-item section,
  so the claim is a checked fact, not a guess.
- Confirmed `backend/` and `frontend/` are unchanged from Session 0 (no
  implementation this session, per ground rules).

## Open questions and risks
- **Carried forward from Session 1, still open:** any future contributor's
  instinct to reach for Postgres's default `plainto_tsquery` will silently
  reintroduce the 0%-recall failure mode — FR-005 states the requirement in
  writing now, but no code-level guard (lint rule, wrapped query-builder
  function that doesn't expose the AND path) exists yet. Worth building at
  Session 4 (Implementation), not deferred indefinitely.
- **New risk, from this session:** ADR-0001's verification step is a real,
  concrete design, but its actual accuracy (false-accept and false-refuse
  rates) is completely unmeasured — the ADR states this honestly rather
  than claiming the refusal problem is solved. Session 5's evaluation
  harness must treat this as a first-class thing to measure, specifically
  using the adjacent-but-wrong query class Finding 2 surfaced, not only
  fully-unrelated negative controls — if the harness only tests the easy
  case, it will not actually validate the mechanism this session designed.
- **New risk, from this session:** `04-data-model.md`'s
  `QUERY_LOG.final_answered` gate is enforced at the application layer, not
  the database layer, because a DB constraint can't observe multi-call LLM
  verification results. This is named as a single point of failure for the
  entire "cited or refused" invariant — a bug in that one piece of
  application logic breaks the product's core promise silently. Should be
  a priority target for the exhaustive feature-test coverage Session 4/5
  build, not treated as "probably fine."
- **Blocker for Session 4 (Implementation), not for Session 3:** no LLM API
  credentials exist in this environment. Must be resolved (a real
  Anthropic API key provisioned, and how it's supplied recorded in
  `08-deployment-and-operations.md`) before the query pipeline can be built
  and actually run. Named now, not discovered mid-build.
- **Open, not yet decided:** whether `lexicon`'s audit trail
  (`QUERY_LOG`/`CITATION_VERDICT`) needs tamper-evidence (hash-chaining,
  matching `privacy-forge`'s ADR-0003) or whether append-only-by-convention
  is sufficient — explicitly left to the next session's threat model rather
  than decided by default in the data model doc.
- **No blockers for the next session itself.** Session 3 can start
  immediately; the LLM-credentials item blocks Session 4, not Session 3.

## Next recommended session
- Proposed session title: **Session 3 — Security & Threat Model**
- Single objective: Produce `06-security-threat-model.md` for this
  RAG-specific system — the prompt-injection/LLM-guardrails learning
  objective (`00a-ledger-confirmation.md`) needs a real threat model before
  Session 4 implements anything, not an afterthought bolted on at Session
  5's testing phase. Must cover: prompt-injection via document content
  (a malicious instruction embedded inside an ingested document attempting
  to override the "cited or refused" invariant or exfiltrate other corpus
  content) and via query text; the embedding-inversion risk this session's
  data-classification table flagged for chunk embeddings; and resolve the
  open tamper-evidence question this session left explicitly undecided in
  `04-data-model.md`.
- Inputs required: this handoff; `02-requirements.md`; `03-architecture.md`
  (especially the fail-closed failure-handling section and the LLM
  provider integration surface); `04-data-model.md`'s revisit-trigger note;
  `docs/adr/ADR-0001-groundedness-refusal-check.md`.
- Expected deliverables: `06-security-threat-model.md`, written at real
  reasoning depth (STRIDE or an equivalent structured method, applied to
  the actual query and ingestion flows in `03-architecture.md`, not a
  generic checklist); a decision on the audit-trail tamper-evidence
  question; any resulting ADRs (e.g. ADR-0002 if the threat model concludes
  something needs a distinct architectural decision).
- Definition of done: the threat model is reasoned against this session's
  real architecture (specific flows, specific data), not written in the
  abstract; the tamper-evidence question is explicitly resolved one way or
  the other; the LLM-credentials open item is either resolved or explicitly
  re-confirmed as still blocking Session 4, not silently dropped.

## Paste-into-new-session context

**Project:** lexicon — grounded document Q&A system; every answer is
citation-backed or refused
**Track:** public flagship
**Repository state:** branch `main`, unreleased (pre-v0.1.0), Session 2
complete

**Problem being solved (validated Session 1):** teams with a bounded,
changing, authoritative document corpus need answers they can act on
without independently re-reading the source. See `00-project-brief.md` and
`00b-rag-vs-alternatives.md`.

**The central design decision made this session:** refusal cannot rely on
retrieval similarity alone (Session 1 spike Finding 2: a
topically-adjacent-but-wrong query scored 0.701, inside the
0.706–0.848 range of genuinely correct answers). The architecture now
requires an independent, post-generation groundedness/entailment
verification call — a second LLM call, separate from generation, checking
each cited claim against its exact source passage — before any answer is
released. See `docs/adr/ADR-0001-groundedness-refusal-check.md`.

**Current stack:**
- Backend: FastAPI, Python 3.12
- Frontend: Next.js 15 (App Router)
- Data: PostgreSQL + pgvector, Redis, S3-compatible object storage (MinIO)
- Infra: Docker Compose, GitHub Actions CI
- LLM provider (decided this session, not yet wired up): Anthropic Claude
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
  alone, not a pre-generation relevance gate.** (`ADR-0001`, this session.)
- LLM provider is Anthropic Claude, with model-tier asymmetry for cost
  control (this session's decision — revisit only with a stated reason, not
  by default).

**Implementation state:**
- Done: repository skeleton, licence, governance docs, minimal
  backend/frontend skeletons, docker-compose, CI, full discovery/planning
  documentation, executed feasibility spike, full requirements and
  architecture documentation including the first ADR, data model, and API
  contracts.
- In progress: nothing mid-flight.
- Not started: security/threat model (next session); everything
  product-related as code — no ingestion, retrieval, generation, or
  verification exists as application code yet.

**Constraints and non-goals:**
- Full non-goals table: `docs/project-memory/01-scope-and-non-goals.md`.
- New this session: no numeric target invented for retrieval quality at
  scale, refusal recall, citation accuracy, or per-query cost — each is an
  explicit placeholder pending Session 5's harness or Session 4's real
  provider pricing, not a guess.

**Task for the next session (single objective):**
Security & Threat Model: produce `06-security-threat-model.md` covering
prompt-injection via document content and query text, the embedding-
inversion risk on chunk embeddings, and resolve the audit-trail
tamper-evidence question left open in `04-data-model.md`.

**Definition of done:**
- `06-security-threat-model.md` written at real reasoning depth against
  this session's actual architecture and flows, not a generic checklist.
- Tamper-evidence question explicitly resolved.
- LLM-credentials open item explicitly re-confirmed as still blocking
  Session 4, or resolved.

**Files to attach or paste:**
- `docs/project-memory/12-session-handoff.md` (this file)
- `docs/adr/ADR-0001-groundedness-refusal-check.md`
- `docs/project-memory/03-architecture.md`
- `docs/project-memory/04-data-model.md`
- `docs/project-memory/02-requirements.md`

**Ground rules:** Do not change the stack. Do not introduce a third new
technology. Do not expand the deep-SDLC-phase count beyond two. Do not
touch `privacy-forge`, `laravel-consent-guard`, or `bookslot`. Ask before
introducing any new dependency or scope item not already anticipated above.
