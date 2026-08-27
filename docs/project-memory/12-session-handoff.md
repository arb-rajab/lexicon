# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Credential status — superseded this session, stated plainly, first

**No Anthropic API key (or any other LLM provider credential) exists in
this environment, and — as of this session — none ever will, by deliberate
choice.** Sessions 2 through 4 each flagged the missing key as a temporary
gap; Session 4 went further and argued this repository's version of the
gap was *not* the kind bookslot permanently closed with D-0036, because
ADR-0001's verification mechanism can only be proven against real model
behavior. That argument is now moot, not wrong: the project owner has
made the same kind of decision bookslot's owner made for Stripe and
privacy-forge's owner made for a live demo instance — **a real Anthropic
API key will not be obtained for this project, for portfolio/skill-proof
reasons, within this project's current lifecycle.**

**This session's full reasoning, worked out fresh for this repository
rather than copied from either precedent, is
`docs/adr/ADR-0004-real-llm-verification-descoped.md`. Read it before
starting Session 5 — it changes Session 5's actual objective, not just its
inputs.** The short version: unlike bookslot's Stripe gap (one untested
integration boundary around an otherwise independently-proven core claim),
this decision makes **this repository's central, original, differentiating
claim — that real entailment reasoning can correctly separate grounded
answers from topically-adjacent fabrications, where retrieval confidence
alone measurably cannot (Session 1's Finding 2) — permanently unprovable**
in this project's current lifecycle. What remains real and unaffected: the
full pipeline (ingestion, hybrid retrieval, generation, verification,
refusal gate) is correctly wired and tested end-to-end against a real
database, using a stub LLM client whose behavior is deterministic and
known; ADR-0003's injection-hardening design is real, structurally tested
architecture; retrieval recall@k is measurable for real, since retrieval
never calls an LLM provider at all.

Everything in Session 4 was, and remains, built against the same
clearly-labeled stub/fake LLM client tier this note previously described
(`backend/src/lexicon/llm/base.py`'s `LLMClient` protocol,
`llm/anthropic_client.py`'s real implementation, `llm/stub_client.py`'s
fake one, selected by `llm/factory.py`). That seam is unchanged by this
decision and stays exactly as built — `StubLLMClient` is now this
project's **permanent** evaluation substrate, not a temporary stand-in,
and a real key remains a config change rather than a rewrite, should a
future scope change reopen this decision (ADR-0004's Revisit triggers).

## Session completed
- Session number and title: **Session 4.5 — Real LLM Verification
  Descoped (documentation-and-scope session)**
- Objective: formally record the project owner's decision not to obtain
  real LLM provider credentials, state honestly and precisely what that
  costs this repository's evidentiary value, identify what remains real
  and provable, and reframe Session 5's scope before it starts rather than
  let it discover the constraint mid-session. Status: **complete.**
- **No application code was changed this session** — matching bookslot's
  own MVP-checkpoint session pattern (D-0045): documentation and
  scope-accounting only. `backend/`, `frontend/`, and all 33 of Session 4's
  passing tests are untouched; nothing here required re-running CI.

## Work completed

- **Read `12-session-handoff.md` (Session 4's version), ADR-0001, and
  ADR-0003 first**, to ground this decision in the exact claims those
  documents make about what the verification mechanism is for and what
  evidence it still needed.
- **Wrote `docs/adr/ADR-0004-real-llm-verification-descoped.md`** — the
  formal decision record. States the decision plainly; explains precisely
  why this repository's version of "no real provider credential" is more
  consequential than bookslot's Stripe descoping (D-0036) rather than
  treating the two as equivalent; states exactly what remains real,
  tested, and provable (full pipeline wiring, ADR-0003's structural
  hardening, retrieval quality); reframes Session 5's objective around
  evaluation *methodology* proof rather than real quality measurement;
  records trade-offs, consequences, and revisit triggers.
- **Corrected `docs/project-memory/00-project-brief.md`'s success
  metrics.** Metrics #2 (refusal recall), #3 (citation accuracy), and #5
  (prompt-injection resistance) each depend on real generation or
  verification behavior and are now annotated as permanently measurable
  only as a stub-tier harness self-check, not as real quality evidence,
  for this project's current lifecycle. Metric #4 (latency) gained a note
  that stub-tier latency was never going to be representative of real
  provider latency either. Metric #1 (retrieval recall@3) is explicitly
  called out as unaffected, since retrieval never calls an LLM provider.
- **Updated `docs/SDLC-EVIDENCE.md`'s Phase 5 (Verification & Testing)
  row** to state, with the same precision as privacy-forge's R-08 and
  bookslot's frontend-verification gap, exactly which parts of this deep
  phase remain real (methodology design, structural tests, wiring proof)
  and exactly which claim is now permanently unverified (real
  entailment/injection-resistance quality against a live model) — rather
  than leaving the row's original "not yet produced" phrasing to imply a
  temporary gap Session 5 would simply close.
- **Rewrote this file** to carry the corrected picture forward, since the
  prior version's Credential status section and Next recommended session
  both explicitly argued the opposite of what is now true.
- `privacy-forge`, `laravel-consent-guard`, and `bookslot` were not
  touched, read, or modified this session beyond recalling their existing,
  already-recorded decisions (D-0036, the Session 24 demo-hosting
  decision) as the explicit precedents this task named — no files under
  those three repositories were opened this session.

## Files created or changed

**Docs only, no application code:**
- `docs/adr/ADR-0004-real-llm-verification-descoped.md` (new)
- `docs/SDLC-EVIDENCE.md` (Phase 5 row rewritten)
- `docs/project-memory/00-project-brief.md` (Success metrics section
  amended)
- `docs/project-memory/12-session-handoff.md` (this file, rewritten)

## Decisions made

- **Real LLM provider credentials are permanently descoped for this
  project, by deliberate portfolio-scope choice** — full reasoning in
  ADR-0004. Structurally distinct from bookslot's D-0036 in severity: this
  is not one untested integration boundary, it is this repository's
  central, original differentiating claim becoming permanently unprovable.
- **Session 5 is reframed, not cancelled.** Its objective is now proving
  the evaluation *methodology* is sound and would produce trustworthy
  numbers the moment real credentials exist — golden query set design
  (including the adjacent-but-wrong query class), refusal-correctness and
  citation-accuracy measurement design, the adversarial injection corpus
  itself — rather than claiming to measure real retrieval, generation, or
  verification quality, which is structurally impossible against a stub.
  Retrieval recall@k is the one metric Session 5 can and should still
  measure for real, at realistic scale, exactly as originally planned.
- **`StubLLMClient` is now this project's permanent evaluation substrate**,
  not a temporary stand-in — matching the permanent status
  `FakePaymentIntentGateway` holds in bookslot for Stripe validation.
- **No placeholder or real-looking-but-fake credential value is written
  anywhere.** `ANTHROPIC_API_KEY` stays absent from `.env`/`.env.example`,
  exactly as before — there was nothing to change, since no prior session
  wrote a fake value there.

## Validation performed

- **None required or performed against application code** — this session
  changed only documentation. Session 4's validation record (33 tests
  passing against real Postgres+pgvector, `ruff`/`mypy --strict`/`bandit`/
  `pip-audit` clean, `docker compose up` boot confirmed) is unchanged and
  still accurately describes the current state of `backend/`.
- Confirmed `privacy-forge`, `laravel-consent-guard`, and `bookslot` were
  not modified this session.

## Open questions and risks

- **The single largest risk is now stated as permanent, not open.** Prior
  handoffs listed "the verifier's real accuracy is unmeasured" as the
  single largest *open* risk, gated on obtaining a real API key. As of
  this session, per ADR-0004, that risk is a **permanently accepted
  limitation of this project's current lifecycle**, not an open item
  Session 5 will close. Any future session must describe it that way —
  "permanently unverified, by deliberate choice," not "pending
  credentials."
- **Ingestion is synchronous and PDF/MinIO are unimplemented** — unchanged
  from Session 4, unaffected by this decision, still real tracked gaps
  against `03-architecture.md`/FR-001.
- **Rate limiting (NFR-007) is not implemented** — unchanged from
  Session 4, unaffected by this decision.
- **Instance-level authentication remains undesigned** — unchanged from
  Session 4, unaffected by this decision.
- **The adversarial injection test corpus has still not been built** —
  unaffected in *what* it is (Session 5's job, per ADR-0003's own
  Consequences section), but affected in *what running it can prove*: per
  ADR-0004, it will exist and be real authored work, but its pass/fail
  numbers against `StubLLMClient` will be a harness self-check, not
  evidence of real injection resistance.

## Next recommended session

- Proposed session title: **Session 5 — Evaluation Harness & Methodology
  (reframed scope)** (this repository's second deep SDLC phase,
  Verification & Testing)
- Single objective: build the CI-gated evaluation harness as a proof of
  **methodology**, not real-model quality — golden query set construction
  including the adjacent-but-wrong query class (Finding 2), a real,
  measured retrieval recall@k number at realistic scale (unaffected by
  ADR-0004), refusal-correctness and citation-accuracy measurement logic
  exercised and self-checked against `StubLLMClient`'s known behavior, and
  the committed adversarial injection corpus (`06-security-threat-model.md`'s
  4 categories, generator- and verifier-targeted suites scored separately)
  — all explicitly reported as stub-tier self-checks where generation or
  verification is involved, never as real quality measurements. Re-run
  `test_proof_session1_oauth2_case.py` only to confirm it still passes at
  the wiring-evidence level; do **not** attempt or imply a real-tier run,
  since no credential exists or will exist.
- Inputs required: this handoff; `docs/adr/ADR-0001`, `ADR-0003`,
  **`ADR-0004` (read this one first — it changes the objective)**;
  `06-security-threat-model.md`; `07-testing-strategy.md` (currently an
  empty template — Session 5 is where it should actually get written, with
  the stub-tier-only caveat built into its own framing from the start);
  `backend/src/lexicon/llm/` and `pipeline/query_pipeline.py` (what's being
  evaluated); `backend/tests/test_proof_session1_oauth2_case.py`.
- Expected deliverables: `eval/` or equivalent CI-gated harness measuring
  real retrieval recall@k; refusal-correctness and citation-accuracy
  measurement logic, proven correct against `StubLLMClient`'s known
  behavior and clearly labeled as a methodology self-check, not a quality
  measurement; the committed adversarial corpus under
  `docs/security/adversarial-corpus/` or equivalent, with generator- and
  verifier-targeted results scored and reported separately, and reported
  with the same stub-tier caveat.
- Definition of done: retrieval recall@k has a real, measured number at
  realistic scale; the refusal-correctness, citation-accuracy, and
  adversarial-suite harnesses are built, pass their stub-tier self-checks,
  and are documented — every place a number appears — as evidence the
  harness works, explicitly not as evidence about real model quality; no
  new claim anywhere in Session 5's output describes verification or
  injection-resistance as "proven" or "validated."

## Paste-into-new-session context

**Project:** lexicon — grounded document Q&A system; every answer is
citation-backed or refused
**Track:** public flagship
**Repository state:** branch `main`, unreleased (pre-v0.1.0), Session 4.5
(documentation/scope only) complete on top of Session 4's implementation

**Problem being solved (validated Session 1):** teams with a bounded,
changing, authoritative document corpus need answers they can act on
without independently re-reading the source. See `00-project-brief.md` and
`00b-rag-vs-alternatives.md`.

**The central design decision from Session 2 (unchanged, implemented
Session 4):** refusal cannot rely on retrieval similarity alone. An
independent, post-generation groundedness/entailment verification call
gates every answer before release. See
`docs/adr/ADR-0001-groundedness-refusal-check.md` and
`backend/src/lexicon/pipeline/query_pipeline.py` for the real
implementation.

**Session 3's finding, hardened in real code Session 4:** the verifier is
a first-class attack target (T-02), structurally different from the
generator (T-01) and requiring a structurally different defense
(sandwiched delimiting, `injection_suspected` self-report,
application-enforced auto-fail, fail-closed-on-ambiguity — ADR-0003). Both
are real, tested, and provably different implementations.

**This session's (4.5's) central finding, and the one that must not be
lost in any future summary of this project:** the pipeline is real,
correct against the ADRs, and wired end-to-end (33 real-database tests,
real CI, a real `docker compose` boot) — but **whether the verifier
actually works against real model behavior is now a permanently
unanswerable question for this project, by the project owner's own
deliberate choice, not a temporary gap awaiting a credential.** This is
this repository's central, original differentiating claim, and it is
permanently unprovable in this project's current lifecycle. Full reasoning
and precise severity comparison against bookslot's Stripe descoping:
`docs/adr/ADR-0004-real-llm-verification-descoped.md`.

**Current stack:**
- Backend: FastAPI, Python 3.12 — unchanged since Session 4.
- Frontend: Next.js 15 (App Router) — still Session 0 skeleton, untouched.
- Data: PostgreSQL + pgvector (real schema via Alembic, two-role
  permission split per ADR-0002), Redis (provisioned, not yet used),
  S3-compatible object storage (MinIO, provisioned, not yet wired in).
- Infra: Docker Compose (verified booting end-to-end), GitHub Actions CI
  (runs against a real Postgres service).
- LLM provider: Anthropic Claude API — real client code
  (`llm/anthropic_client.py`) exists, is believed correct against the
  documented SDK surface, and is now **permanently unexercised** against
  live provider traffic in this project's current lifecycle, by deliberate
  choice (ADR-0004), not by a temporary missing credential.
  `StubLLMClient` is the **permanent** evaluation substrate.
- Testing: pytest (backend) — 33 tests, all against real Postgres+pgvector,
  unaffected by this session. Vitest (frontend) — still only the
  health-check skeleton.

**Architecture decisions that must not be reversed:**
- Licence AGPL-3.0.
- Next.js 15 + FastAPI/Python 3.12, frozen against the portfolio ledger.
- Exactly two deep SDLC phases: Discovery & Planning (complete),
  Verification & Testing (Session 5, next, reframed scope).
- Learning budget exactly 2 (RAG evaluation methodology; LLM
  guardrails/prompt-injection defence) — at cap.
- Hybrid keyword search must use OR semantics, never `plainto_tsquery`.
- Refusal is post-generation groundedness/entailment verification, a real
  separate LLM call, never a similarity threshold.
- The verification call implements ADR-0003's exact hardening contract.
- The audit trail's append-only property is enforced by database
  permission grants (ADR-0002).
- LLM provider is Anthropic Claude, with model-tier asymmetry for cost
  control — real client code exists for this.
- `llm.factory.get_llm_client()`'s tier-selection seam
  (`ANTHROPIC_API_KEY` set → real client; unset → stub) must not be
  hard-wired away — it is what keeps "add a real key" a reversible config
  change, should ADR-0004 ever be revisited.
- **New this session, do not reverse without a documented reason:** real
  LLM provider credentials are permanently descoped
  (ADR-0004). No future session may reintroduce "obtain a real API key" as
  a blocking precondition for Session 5 or beyond without first
  explicitly revisiting ADR-0004 itself, per its own Revisit triggers.
  No future document may describe this project's verification or
  injection-resistance mechanism as "proven" or "validated" against real
  model behavior.

**Implementation state:**
- Done: full discovery/planning/architecture/security documentation
  (Sessions 1–3); real ingestion, real hybrid retrieval, the real two-call
  generate/verify pipeline with ADR-0003 hardening, the ADR-0002 database
  permission split, 33 passing tests against real infrastructure, and the
  ADR-0001-mandated proof test, all from Session 4 and unchanged; the
  formal descoping decision and its documentation consequences (Session
  4.5, this handoff).
- In progress: nothing mid-flight.
- Not started / explicitly deferred: rate limiting (NFR-007), PDF
  ingestion, MinIO object-storage upload, async ingestion worker,
  instance-level authentication, the Session 5 evaluation harness and
  adversarial corpus (now reframed as methodology-proof, not
  real-quality-proof).
- **Permanently descoped, not merely deferred:** real-model verification
  of ADR-0001's entailment mechanism and ADR-0003's injection hardening —
  per ADR-0004, this will not become available in this project's current
  lifecycle absent a scope change.

**Constraints and non-goals:**
- Full non-goals table: `docs/project-memory/01-scope-and-non-goals.md`.
- `max_question_length` (1000 chars, T-05) is a Session 4 placeholder
  number against no real pricing data.
- **New:** real LLM provider credentials — see ADR-0004.

**Task for the next session (single objective):**
Session 5 — Evaluation Harness & Methodology: build the CI-gated harness
and adversarial corpus at their now-reframed, achievable scope (real
retrieval recall@k; methodology self-checks, not quality measurements, for
everything downstream of a generation/verification call), and document
every number produced with the precision ADR-0004 requires.

**Definition of done:**
- Retrieval recall@k has a real, measured number at realistic scale.
- The refusal-correctness, citation-accuracy, and adversarial-injection
  harnesses are built and pass their stub-tier self-checks, each
  explicitly labeled as methodology evidence, not real-model-quality
  evidence.
- `docs/project-memory/07-testing-strategy.md` is written, with the
  stub-tier-only caveat for generation/verification built into its framing
  from the start, not appended as an afterthought.
- No output from this session describes verification or
  injection-resistance as "proven" or "validated" against real model
  behavior.

**Files to attach or paste:**
- `docs/project-memory/12-session-handoff.md` (this file)
- `docs/adr/ADR-0001-groundedness-refusal-check.md`
- `docs/adr/ADR-0002-audit-trail-tamper-evidence.md`
- `docs/adr/ADR-0003-verification-injection-hardening.md`
- `docs/adr/ADR-0004-real-llm-verification-descoped.md`
- `docs/project-memory/06-security-threat-model.md`
- `backend/src/lexicon/llm/` (the client seam being evaluated)
- `backend/src/lexicon/pipeline/query_pipeline.py`
- `backend/tests/test_proof_session1_oauth2_case.py`

**Ground rules:** Do not change the stack. Do not introduce a third new
technology. Do not expand the deep-SDLC-phase count beyond two. Do not
touch `privacy-forge`, `laravel-consent-guard`, or `bookslot`. Do not
report or remember a stub-tier test or harness result as if it were
evidence about real model behavior — that distinction must survive into
every future session's understanding of what this project can and cannot
claim. Do not reintroduce "obtain a real API key" as an open or blocking
item without first explicitly revisiting ADR-0004. Ask before introducing
any new dependency or scope item not already anticipated above.
