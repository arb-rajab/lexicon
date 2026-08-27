# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Session completed
- Session number and title: **Session 5 — Evaluation Harness & Methodology
  (reframed scope, per ADR-0004)**
- Objective, stated exactly as reframed before this session started
  (Session 4.5's handoff, `docs/adr/ADR-0004-real-llm-verification-
  descoped.md`): prove the evaluation *methodology* is sound and would
  produce meaningful, trustworthy numbers the moment real credentials
  exist — not claim to have measured real retrieval, generation, or
  verification quality, which remains structurally impossible against
  `StubLLMClient`. Status: **complete**, at the scope the project owner
  explicitly set for this session (see "Scope narrowed further this
  session" below) — narrower than ADR-0004's full Session 5 Definition of
  Done, which also named the four-category adversarial injection corpus as
  in-scope; that corpus was not built this session, by explicit instruction,
  and remains open (see Open questions and risks).

## Credential status — unchanged, restated briefly

No Anthropic API key (or any other LLM provider credential) exists in this
environment, and none ever will in this project's current lifecycle, by the
project owner's deliberate, permanent choice (ADR-0004). Nothing this
session did changes that. `llm.factory.get_llm_client()`'s tier-selection
seam is unchanged and untouched — this session's harness calls it exactly
the way the application and `test_proof_session1_oauth2_case.py` already do
(see "The swap point" below), never hardcoding a tier.

## Scope narrowed further this session

The project owner's task for this session was more specific than ADR-0004's
full Session 5 Definition of Done: build a committed golden dataset with
real, executed metrics (recall@k, refusal-correctness, citation-accuracy)
against the existing 8-document spike corpus, CI-gate it with a real
threshold, make the stub-tier-vs-real-quality distinction explicit in the
harness's own output (not only in docs), and document the exact code-level
swap point for real credentials. **The full four-category adversarial
injection corpus (`06-security-threat-model.md` — direct override,
authority-spoofing, verifier-targeted always-true patterns, negative-control
legitimate imperative text) was explicitly not part of this session's task**
and was not built. This is a real, tracked gap against ADR-0004's original
Session 5 Definition of Done and against `06-security-threat-model.md`'s own
"Session 4/5" attribution for that corpus — not silently dropped, recorded
here and in `07-testing-strategy.md`'s Known gaps so a future session
doesn't assume it already exists.

## Work completed

- **Read `docs/project-memory/12-session-handoff.md` (Session 4.5's
  version) and `docs/adr/ADR-0004-real-llm-verification-descoped.md`
  first**, per this session's own explicit instruction, to keep this
  session's scope from drifting back toward claiming real-model quality was
  measured.
- **Built a committed, hand-authored golden dataset**
  (`backend/tests/eval/golden_dataset.py`) — 16 cases against the real
  Session 1 spike corpus (8 documents, unchanged; see "Why the corpus was
  not expanded" below):
  - **9 LEGITIMATE cases**, reused verbatim from the Session 1 spike's own
    `TEST_QUERIES` (the same set `test_ingestion_and_retrieval.py`'s
    NFR-001 regression test already measures recall@3 against), so this
    dataset's retrieval numbers are directly comparable to that existing
    baseline rather than introducing a new, uncalibrated one.
  - **5 ADJACENT_WRONG cases**, in Session 1 Finding 2's exact spirit —
    topically close enough to plausibly retrieve, factually unsupported.
    Includes Finding 2's canonical case verbatim (OAuth2/"Sign in with
    Google", required as the harness's first test case by ADR-0001's own
    Consequences section) plus 4 freshly authored cases, each against a
    *different* corpus document (Celery/Redis background jobs, Kubernetes
    autoscaling, per-client-IP rate limiting, per-role CORS headers) — so
    the dataset's discriminating power is tested across the corpus, not
    only replicated on one document's failure mode.
  - **2 OUT_OF_CORPUS cases** (Session 1's tungsten negative control,
    verbatim, plus one fresh case), for contrast against the harder
    adjacent-wrong cases.
- **Built the metric computations** (`backend/tests/eval/metrics.py`) —
  pure, tier-agnostic functions: `recall_at_k` (LEGITIMATE cases only,
  matching NFR-001's convention that recall is undefined for a query with
  no correct document), `refusal_correctness` (does `answered` match the
  dataset's `expected_answered`), `citation_accuracy` (of cases actually
  answered, does the citation's source document match — any citation on an
  ADJACENT_WRONG/OUT_OF_CORPUS case is inaccurate by construction, since no
  document supports those claims).
- **Built and ran the harness for real**
  (`backend/tests/eval/run_evaluation.py`) — against a real Postgres+
  pgvector instance (this repo's existing `docker-compose.yml` Postgres
  service), through the real pipeline
  (`ingest -> hybrid_retrieve -> run_query_pipeline`), via
  `llm.factory.get_llm_client()` (stub tier, as always in this
  environment). **Real, executed numbers from this actual run,
  2026-08-27:**
  - **Retrieval recall@3: 9/9 (100%)** — real for any LLM tier, since
    retrieval never calls a provider; matches the existing NFR-001
    baseline exactly.
  - **Refusal-correctness: 11/16 (68.75%)**, stub-tier self-check.
    Mismatches: `legit-websocket-broadcast` and `legit-dependencies-shared`
    (the stub's keyword-overlap heuristic false-negatived two genuinely
    correct queries — refused when it should have answered);
    `adv-celery-redis-background-jobs`, `adv-middleware-rate-limiting`, and
    `adv-cors-per-role-headers` (the stub false-positived three
    adjacent-but-wrong queries — answered, with a citation, when it should
    have refused). The canonical `adv-oauth2-google-signin` case and both
    `OUT_OF_CORPUS` cases were correctly refused by the stub.
  - **Citation-accuracy: 7/10 (70%)**, of the 10 cases the stub actually
    answered — the same 3 adjacent-wrong false-positives account for every
    mismatch; all 7 answered LEGITIMATE cases cited their correct source
    document.
  - **Why these numbers matter beyond the raw percentages**: the 3
    adjacent-wrong false-positives, spanning 3 different corpus documents,
    are a live, reproduced demonstration of exactly the failure shape
    Session 1 Finding 2 predicted (a crude relevance signal — here, word
    overlap, there, vector similarity — cannot distinguish "topically close"
    from "actually correct") — not only on the one canonical OAuth2 case,
    but on a dataset built to test that discriminating power broadly. This
    is real evidence the *golden dataset itself* is doing its job (it is
    not all easy cases), even though it says nothing about real
    verification quality.
- **CI-gated the harness with real thresholds set exactly at this measured
  baseline** (`run_evaluation.py`'s module constants, `RECALL_AT_K_THRESHOLD
  = 1.0`, `REFUSAL_CORRECTNESS_THRESHOLD = 11/16`,
  `CITATION_ACCURACY_THRESHOLD = 7/10`), zero slack, each documented with
  exactly which cases produced it — so a future change that regresses
  either the pipeline's wiring or this dataset's own correctness fails CI
  immediately, without asserting a quality bar this project cannot honestly
  claim. Wired into `.github/workflows/ci.yml` two ways: the existing
  `pytest -q` step now also runs `test_evaluation_harness.py`, and a new,
  separate CI step runs `python -m tests.eval.run_evaluation` directly so
  the full labeled report prints unconditionally in every CI run's logs,
  not only on failure.
- **Made the stub-tier-vs-real-quality distinction part of the harness's
  own output, not only this document or ADR-0004.** Every report
  `run_evaluation.py` renders opens with a banner naming the active tier;
  for the stub tier (the only tier this environment can ever produce) it
  states in the harness's own printed text that the numbers describe
  `StubLLMClient`'s deterministic behavior and are not a measurement of
  real model quality, cites ADR-0004 by name, and names the exact swap
  point. `test_evaluation_harness.py` asserts that banner text is actually
  present in the rendered report — a structural check, not a convention
  that could silently erode on a future edit.
- **Documented the exact code-level swap point** (item 5 of this session's
  scope) — `run_evaluation.py`'s own "THE SWAP POINT" docstring, verified
  against the actual code, not just asserted: the harness imports only
  `lexicon.llm.factory.get_llm_client`, never `StubLLMClient` or
  `AnthropicLLMClient` directly for execution (`run_evaluation()`, line ~192
  as written this session). `get_llm_client()` (`llm/factory.py`, unchanged
  this session) already branches on `Settings.anthropic_api_key`
  (`config.py`) — this is the identical seam
  `test_proof_session1_oauth2_case.py` and `api/deps.py`'s `get_llm`
  dependency already use. Setting `ANTHROPIC_API_KEY` is the entire change
  required to produce real-tier numbers from this exact script; zero lines
  of `golden_dataset.py`, `metrics.py`, or `run_evaluation.py` would need to
  change. The `_tier_caveat()` function's `real` branch (written, not yet
  exercisable in this environment) proves this was designed for the swap,
  not merely compatible with it by accident.
- **Wrote `docs/project-memory/07-testing-strategy.md`** — was an empty
  template; now filled in with the stub-tier-only caveat for
  generation/verification built into its framing from the start (per
  ADR-0004's own Consequences section), a real Levels table naming every
  existing test file, and a Known gaps section naming the adversarial
  corpus and realistic-scale-corpus gaps explicitly.
- **Updated `docs/SDLC-EVIDENCE.md`'s Phase 5 row** with this session's real
  evidence — the golden dataset, the three real numbers above, the CI gate,
  and the explicit "what remains permanently unverified" and "what was
  deliberately not built this session" statements.
- **Rewrote this file.**
- `privacy-forge`, `laravel-consent-guard`, and `bookslot` were not
  touched, read, or modified this session.

## Files created or changed

- `backend/tests/eval/__init__.py` (new)
- `backend/tests/eval/golden_dataset.py` (new) — the committed golden
  dataset, 16 cases
- `backend/tests/eval/metrics.py` (new) — recall@k, refusal-correctness,
  citation-accuracy computations
- `backend/tests/eval/run_evaluation.py` (new) — the CI-gated harness,
  runnable standalone (`python -m tests.eval.run_evaluation`) or via pytest
- `backend/tests/eval/test_evaluation_harness.py` (new) — wires the harness
  into `pytest -q`, asserts the stub-tier caveat is present in the
  harness's own rendered output
- `.github/workflows/ci.yml` — added a dedicated evaluation-harness CI step
  after `pytest`
- `docs/project-memory/07-testing-strategy.md` — written in full (was an
  empty template)
- `docs/SDLC-EVIDENCE.md` — Phase 5 row rewritten with this session's real
  evidence
- `docs/project-memory/12-session-handoff.md` (this file, rewritten)

## Decisions made

- **The golden dataset stays against the existing 8-document Session 1
  spike corpus, not expanded to a larger "realistic-scale" corpus** —
  `00-project-brief.md`'s Success metric #1 names a 500+ chunk/20+ document
  future target, and the project owner's instruction for this session left
  that choice explicitly to this session's judgment. Reasoning: this
  session's task is proving the evaluation *methodology* is sound, not
  maximizing retrieval-quality realism; reusing the already-licence-clean,
  already-validated corpus kept the new recall@3 number directly comparable
  to the existing NFR-001 baseline instead of introducing an unrelated
  variable (a different corpus, at a different scale, with newly hand-
  labeled golden answers, all changing at once). Recorded as a deliberate,
  reasoned choice in `07-testing-strategy.md`'s Test data strategy section,
  not an oversight — a future session that wants a realistic-scale
  recall@k number should treat corpus expansion as its own scoped task.
- **CI-gate thresholds are set exactly at this session's measured baseline,
  not at a rounder or more comfortable-looking number.** Setting
  `REFUSAL_CORRECTNESS_THRESHOLD` at, say, 75% (a number that sounds more
  like a quality target) would have been dishonest twice over: it doesn't
  match what was actually measured, and it would silently permit a real
  regression down to that number without failing CI. The exact-baseline
  choice means the gate's only job is regression detection, which is the
  only claim ADR-0004 permits this session to make.
- **The full adversarial injection corpus was not built this session**, by
  the project owner's explicit scope for this session (see "Scope narrowed
  further this session" above) — a conscious choice to keep this session
  from silently drifting into a second body of work beyond what was asked,
  not a judgment that it is unimportant. It remains named, in the same
  place it always was (`06-security-threat-model.md`), as real, valuable,
  not-yet-done work.

## Validation performed

- **The full existing 33-test suite still passes** against real
  Postgres+pgvector, unchanged by this session's additions (confirmed by
  running `pytest -q` before making any change, and the eval harness's own
  test — `test_evaluation_harness.py` — passes alongside the other 33 as a
  34th test).
- **The evaluation harness was executed for real**, twice — once to
  establish the real baseline numbers above, once after setting the CI-gate
  thresholds to that exact baseline, to confirm the harness reports
  `OVERALL: PASS` against its own committed thresholds rather than shipping
  a gate that would fail on the very commit that introduced it.
- Confirmed `privacy-forge`, `laravel-consent-guard`, and `bookslot` were
  not modified this session.

## Open questions and risks

- **The full four-category adversarial injection corpus remains
  unbuilt** — explicitly out of this session's scope (see above), not
  forgotten. A future session should treat it as its own scoped task,
  following `06-security-threat-model.md`'s existing design (Categories
  1–4, generator- and verifier-targeted suites scored separately, pass
  criteria already stated there).
- **Retrieval quality at realistic scale remains unmeasured** — this
  session's golden dataset is against the same 8-document corpus as the
  original spike; `00-project-brief.md`'s 500+ chunk/20+ document target
  for Success metric #1 is still open, by this session's own deliberate
  choice (see Decisions made above).
- **Real entailment/injection-resistance quality is permanently
  unverified** (ADR-0004, unchanged) — the single largest, permanent gap in
  this project's evidence base. This session adds real, executed evidence
  that the *measurement machinery* around that gap is sound; it does not
  and cannot narrow the gap itself.
- **Rate limiting (NFR-007), PDF ingestion, MinIO upload, async ingestion,
  and instance-level authentication** remain unimplemented, unchanged from
  prior sessions, unaffected by this session's work.

## Next recommended session

- Proposed session title: **Session 6 — Adversarial Injection Corpus**
  (the remaining piece of ADR-0004's original Session 5 Definition of Done
  that this session's narrower scope deliberately left for later), or, at
  the project owner's discretion, whatever the portfolio's next priority is
  — this repository's two deep SDLC phases (Discovery & Planning,
  Verification & Testing) are both now real and substantively evidenced,
  even though Verification & Testing's adversarial-corpus piece specifically
  remains open.
- If Session 6 is the adversarial corpus: build
  `docs/security/adversarial-corpus/` (or equivalent) per
  `06-security-threat-model.md`'s existing Categories 1–4 design, scored
  through the same `llm.factory.get_llm_client()` seam this session's
  harness already demonstrates is provider-agnostic, with the identical
  stub-tier-vs-real-quality labeling this session's harness output enforces
  structurally (a good candidate: extend `run_evaluation.py`'s
  `EvaluationReport`/`_tier_caveat` pattern rather than inventing a new
  reporting shape).
- Inputs required: this handoff; `docs/adr/ADR-0004`;
  `06-security-threat-model.md`'s "Indirect prompt injection via ingested
  documents" and "The committed adversarial test corpus" sections;
  `backend/tests/eval/` (this session's harness, as the pattern to extend);
  `backend/tests/test_injection_hardening.py` (existing structural tests,
  not to be duplicated).

## Paste-into-new-session context

**Project:** lexicon — grounded document Q&A system; every answer is
citation-backed or refused
**Track:** public flagship
**Repository state:** branch `main`, unreleased (pre-v0.1.0), Session 5
(evaluation harness & methodology, reframed/narrowed scope) complete on top
of Session 4's implementation and Session 4.5's ADR-0004 descoping decision

**Problem being solved (validated Session 1):** teams with a bounded,
changing, authoritative document corpus need answers they can act on
without independently re-reading the source. See `00-project-brief.md` and
`00b-rag-vs-alternatives.md`.

**The central design decision from Session 2 (unchanged, implemented
Session 4):** refusal cannot rely on retrieval similarity alone. An
independent, post-generation groundedness/entailment verification call
gates every answer before release. See
`docs/adr/ADR-0001-groundedness-refusal-check.md` and
`backend/src/lexicon/pipeline/query_pipeline.py`.

**Session 3's finding, hardened in real code Session 4:** the verifier is a
first-class attack target (T-02), structurally different from the generator
(T-01) and requiring a structurally different defense (ADR-0003). Both are
real, tested, and provably different implementations
(`test_injection_hardening.py`).

**Session 4.5's finding (permanent, not a temporary gap):** real LLM
provider credentials are permanently descoped for this project by deliberate
owner choice (ADR-0004) — this project's central, original differentiating
claim (real entailment reasoning correctly separating grounded answers from
topically-adjacent fabrications) is permanently unprovable in this project's
current lifecycle.

**This session's (5's) central finding, and the one that must not be lost
in any future summary of this project:** the evaluation *methodology* is now
real, executed, and CI-gated — a committed 16-case golden dataset
(9 legitimate, 5 adjacent-but-wrong across 5 different corpus documents, 2
out-of-corpus), real recall@3 (9/9, 100%, unaffected by ADR-0004), and
real, reproducible refusal-correctness (11/16) and citation-accuracy (7/10)
numbers against `StubLLMClient`'s known heuristic — with the adjacent-wrong
false-positives concretely reproducing Session 1 Finding 2's failure shape
across multiple documents, not just the one canonical case. **Every one of
those numbers is stub-tier self-check evidence, not real-model-quality
evidence, and that distinction is now enforced inside the harness's own
printed output** (`backend/tests/eval/run_evaluation.py`'s tier-caveat
banner, asserted present by `test_evaluation_harness.py`), not only in this
document or in ADR-0004. The exact code-level swap point for real
credentials is documented and verified: `run_evaluation.py` calls only
`llm.factory.get_llm_client()`, the same seam the application already uses;
setting `ANTHROPIC_API_KEY` is the entire change needed to produce
real-tier numbers from this same script.

**Current stack:** unchanged from Session 4.5 — FastAPI/Python 3.12
backend, Next.js 15 frontend (still Session 0 skeleton), PostgreSQL +
pgvector, Redis (provisioned, unused), MinIO (provisioned, unused), Docker
Compose, GitHub Actions CI (now with an added evaluation-harness step).
`StubLLMClient` remains the permanent evaluation substrate (ADR-0004);
`AnthropicLLMClient` remains real, unexercised code.

**Architecture decisions that must not be reversed:** all of Session 4.5's,
unchanged (AGPL-3.0; Next.js 15 + FastAPI/Python 3.12; exactly two deep
SDLC phases; learning budget at cap; OR-semantics keyword search; post-
generation groundedness verification, never a similarity threshold; ADR-0003's
exact hardening contract; DB-permission-enforced audit-trail append-only
property; `llm.factory.get_llm_client()`'s tier-selection seam must not be
hard-wired away; real LLM credentials remain permanently descoped absent an
explicit ADR-0004 revisit). **New this session, do not reverse without a
documented reason:** the Session 5 evaluation harness's CI-gate thresholds
(`run_evaluation.py`'s module constants) are regression floors set at a
measured baseline, not quality targets — a future session must not raise
them to a "nicer" number without a new real measurement backing it, and must
not read a passing gate as evidence of real verification quality.

**Implementation state:**
- Done: everything from Session 4.5, plus Session 5's golden-dataset
  evaluation harness (`backend/tests/eval/`), CI-gated with real,
  measured-baseline thresholds, its stub-tier caveat enforced in the
  harness's own output.
- In progress: nothing mid-flight.
- Not started / explicitly deferred: rate limiting (NFR-007), PDF
  ingestion, MinIO object-storage upload, async ingestion worker,
  instance-level authentication, the full four-category adversarial
  injection corpus (explicitly out of this session's narrowed scope — see
  Next recommended session), retrieval quality at realistic corpus scale.
- **Permanently descoped, not merely deferred:** real-model verification of
  ADR-0001's entailment mechanism and ADR-0003's injection hardening
  (ADR-0004, unchanged).

**Constraints and non-goals:**
- Full non-goals table: `docs/project-memory/01-scope-and-non-goals.md`.
- Real LLM provider credentials — see ADR-0004.
- **New:** the adversarial injection corpus's design already exists
  (`06-security-threat-model.md`) but its build was deliberately excluded
  from this session's scope, not from any newly discovered constraint.

**Task for the next session (single objective, if Session 6 is the
adversarial corpus):** build the committed, four-category adversarial
injection test corpus, scored through the same tier-agnostic seam this
session's harness already proves works, with the same structural
stub-tier-vs-real-quality labeling enforced in its own output.

**Definition of done (if Session 6 is the adversarial corpus):**
- The corpus exists under `docs/security/adversarial-corpus/` (or
  equivalent), covering all four categories `06-security-threat-model.md`
  names, with generator- and verifier-targeted cases scored as separate,
  distinctly-labeled groups.
- Results are real, executed, and CI-gated, with the same stub-tier caveat
  enforced inside the harness's own output that this session's harness
  established as the pattern.
- No output describes injection-resistance as "proven" or "validated"
  against real model behavior.

**Files to attach or paste:**
- `docs/project-memory/12-session-handoff.md` (this file)
- `docs/adr/ADR-0004-real-llm-verification-descoped.md`
- `docs/project-memory/06-security-threat-model.md`
- `docs/project-memory/07-testing-strategy.md`
- `backend/tests/eval/` (this session's harness — the pattern to extend)
- `backend/tests/test_injection_hardening.py`

**Ground rules:** Do not change the stack. Do not introduce a third new
technology. Do not expand the deep-SDLC-phase count beyond two. Do not
touch `privacy-forge`, `laravel-consent-guard`, or `bookslot`. Do not report
or remember a stub-tier test or harness result as if it were evidence about
real model behavior. Do not reintroduce "obtain a real API key" as an open
or blocking item without first explicitly revisiting ADR-0004. Do not raise
`run_evaluation.py`'s CI-gate thresholds without a new real measurement
backing the new number. Ask before introducing any new dependency or scope
item not already anticipated above.
