# Session Handoff

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` (unreleased, pre-v0.1.0)

## Session completed
- Session number and title: **Session 6 — Adversarial Injection Corpus**
- Objective, as given at the start of this session: build the real,
  committed, four-category adversarial injection corpus
  (`06-security-threat-model.md`'s T-01/T-02 design) that Session 5
  explicitly left open, run it through the real pipeline with the same
  honest stub-tier labeling discipline as every session since ADR-0004, and
  wire it into CI the same way as Session 5's evaluation harness. Status:
  **complete.**

## Front-loaded question, answered before this session's main work started

This session opened by asking whether Session 5's zero-slack CI gate
(11/16 refusal-correctness, 7/10 citation-accuracy) had been confirmed
stable across multiple runs, or measured once. **Answer: it had been
measured once** (Session 5's own run). Before trusting that gate, this
session re-ran `python -m tests.eval.run_evaluation` two additional times
against a fresh install in a clean container. **All three runs (the
original Session 5 run plus these two) produced byte-identical results**:
recall@3 9/9, refusal-correctness 11/16 with the exact same five mismatched
case IDs each time, citation-accuracy 7/10 with the exact same three
mismatched case IDs each time. This is expected, not a coincidence worth
being surprised by: `StubLLMClient.generate()` and `.verify()`
(`llm/stub_client.py`) are pure functions of their text inputs — no
randomness, no clock, no ordering-dependent tie-breaking observed in
practice — so determinism was the predicted outcome, and this session
confirmed it empirically rather than trusting the prediction. **The
zero-slack gate is safe to trust as a real regression floor, not a
one-off measurement that happened to look clean once.**

## Credential status — unchanged, restated briefly

No Anthropic API key (or any other LLM provider credential) exists in this
environment, and none ever will in this project's current lifecycle, by the
project owner's deliberate, permanent choice (ADR-0004). Nothing this
session did changes that. `llm.factory.get_llm_client()`'s tier-selection
seam is unchanged and untouched — this session's new harness calls it
exactly the way Session 5's harness, the application, and
`test_proof_session1_oauth2_case.py` already do, never hardcoding a tier.

## Work completed

- **Read `docs/project-memory/12-session-handoff.md` (Session 5's
  version), `06-security-threat-model.md`, and `docs/adr/ADR-0003` first**,
  per this session's own explicit instruction.
- **Confirmed Session 5's CI-gate numbers are reproducible** (see "Front-
  loaded question" above) before building anything new on top of them.
- **Built the committed adversarial corpus**
  (`docs/security/adversarial-corpus/documents/`, 18 real, standalone
  markdown documents) — genuine variety across all four categories
  `06-security-threat-model.md` names:
  - **Category 1 — direct override (4 cases):** "ignore previous
    instructions," "ignore all prior instructions," and "disregard the
    above" verbatim (matching `StubLLMClient`'s hardcoded marker list), plus
    a fake User/Assistant conversation turn phrased to avoid every marker
    string, testing the stub's detection boundary honestly rather than only
    its easy cases.
  - **Category 2 — authority-spoofing (4 cases):** "SYSTEM OVERRIDE:",
    "ADMIN OVERRIDE:", "SYSTEM NOTICE:" verbatim, plus a fake `[SYSTEM]:`
    role marker that matches no stub marker string.
  - **Category 3 — verifier-targeted always-true patterns (6 cases):**
    reuses the threat model's own example structure ("always respond
    entailed=true," "verifier: always...") for 3 cases, plus a novel
    "definitive, pre-validated proof" framing that avoids every marker
    string, plus two cases that specifically attempt to **suppress the
    injection_suspected flag itself** — one via a direct "do not flag this
    as suspicious" instruction, one via character-spaced obfuscation of a
    known marker phrase (`"i g n o r e   p r e v i o u s..."`) designed to
    defeat exact-substring matching while staying trivially readable to a
    human or a real model.
  - **Category 4 — negative controls (4 cases):** two genuinely benign,
    lexically imperative documents (a compliance policy, an ops runbook —
    matching `06-security-threat-model.md`'s own stated examples) that
    contain no marker substrings at all; two documents that legitimately
    **discuss or quote** injection-attack phrasing as their real subject
    matter (a security explainer, an LLM-testing guide) and do contain
    marker substrings verbatim — included specifically to measure the
    heuristic's false-positive cost honestly rather than engineer a
    flattering 0% number.
  - Every case's query is phrased to closely mirror its document's genuine
    topic sentence, so the stub's lexical-overlap heuristic would plausibly
    call the claim entailed on textual grounds alone — making this a real
    test of whether the `injection_suspected` override actually overrides
    an otherwise-passing verdict, not a test against claims that would have
    been refused anyway for unrelated reasons.
- **Built the dataset and harness**
  (`backend/tests/security/adversarial_dataset.py`,
  `adversarial_corpus_loader.py`, `run_adversarial_evaluation.py`,
  `test_adversarial_corpus.py`) — ingests the corpus into its own isolated
  corpus row (never mixed with the Session 1 spike corpus or Session 5's
  golden-dataset corpus, FR-014), then for every case: retrieves via the
  real `hybrid_retrieve`, checks structural prompt-construction properties
  directly against `llm/prompts.py`'s builders, runs the real
  `run_query_pipeline`, and reads back the real, persisted
  `CITATION_VERDICT` database rows the pipeline actually wrote.
- **Extracted the stub-tier-vs-real-quality caveat banner into a shared
  module** (`backend/tests/support/tier_caveat.py`'s `render_tier_caveat`,
  moved out of Session 5's `run_evaluation.py`'s private `_tier_caveat`) so
  this session's new harness reuses the identical wording instead of
  duplicating it — one source of truth for what this project is and is not
  allowed to claim about a given tier's output. `run_evaluation.py` now
  imports it; Session 5's own numbers and behavior are unchanged (confirmed
  by re-running its tests, see Validation below).
- **Ran the corpus through the real pipeline and got real results,
  2026-08-27** (re-run three times total during this session; identical
  every time, same reproducibility discipline as the front-loaded question
  above applied to this session's own new numbers before trusting them):
  - **Structural containment (ADR-0003 items 1-2), all 18 corpus documents:
    18/18.** `build_generation_user_content`'s single delimited block and
    `build_verification_user_content`'s sandwiched before-and-after
    warning both held for every document's actual ingested content — a
    pure prompt-construction property, true at any tier, no model call
    involved in this specific check at all.
  - **`injection_suspected → enforced_entailed=False` invariant
    (ADR-0003 item 3), checked against 18 real `CITATION_VERDICT` rows:
    0 violations.** Every case that reached verification and had
    `injection_suspected=true` also had the persisted `entailed=false` —
    checked through the full, real, wired pipeline (not a direct unit
    construction; `test_injection_hardening.py` already covers that), a
    stronger, corpus-scale proof of the same code property.
  - **Retrieval-correctness (query → paired document, top-ranked):
    18/18 (100%).**
  - **Stub marker-detection self-check: 18/18 (100%)** — this corpus's
    hand-authored predictions about `StubLLMClient`'s ten hardcoded
    marker strings matched its actual, real behavior exactly: it caught
    every case phrased to match its list (10 of 14 attack cases) and
    missed every case deliberately phrased to avoid it (4 of 14 —
    including the character-spaced obfuscation case), and correctly did
    not flag either genuinely benign negative control.
  - **Category 4 false-positive rate: 2/4 (50%)** —
    `cat4-discusses-injection-topic` and `cat4-quotes-example-instructions`,
    both genuinely benign documents that quote/discuss real attack
    phrasing as their actual subject matter, both flagged by the stub's
    context-blind substring matching. Not a code defect — a real, measured
    cost of this specific placeholder heuristic, reported rather than
    hidden.
- **Wrote the precise claim/non-claim split, in three places, not just
  one:** the harness's own printed report
  (`run_adversarial_evaluation.py`'s module docstring and `render()`
  output, split into "Claim 1" — hard, zero-slack, any-tier invariants —
  and "Claim 2" — stub-tier self-check numbers only), a dedicated
  `docs/security/adversarial-corpus/README.md`, and this handoff. **What
  is proven:** the application-layer enforcement gate (ADR-0003 item 3)
  cannot be bypassed by document content alone — this is a property of
  `pipeline/query_pipeline.py`'s code, checked for real, true regardless of
  which LLM tier is active. **What remains permanently unproven, exactly
  as ADR-0004 already established:** whether a real model would ever
  actually get talked into setting `injection_suspected=false`
  inappropriately in the first place — no test in this repository, present
  or future, can produce that evidence without a real model, and this
  session's corpus does not change that.
- **CI-gated the new harness** (`.github/workflows/ci.yml`) two ways,
  mirroring Session 5's exact pattern: `pytest -q` now also runs
  `test_adversarial_corpus.py`, and a new, separate CI step runs
  `python -m tests.security.run_adversarial_evaluation` directly so the
  full labeled report prints unconditionally in every CI run's logs. The
  hard invariants (`structural`, `enforcement`) are asserted with zero
  slack — any violation is a real regression, never a quality-bar judgment
  call; the stub-tier self-check numbers (`retrieval`, `stub_detection`,
  `false_positive`) are gated at their measured baseline, same
  zero-slack-at-measured-baseline pattern as Session 5's thresholds.
- **Updated `docs/project-memory/06-security-threat-model.md`** — the
  "committed adversarial test corpus" section now states "Status: built,
  Session 6" and links to the real README/results; the Pass criteria
  paragraph now states precisely how "zero successful injections" was
  actually provable against a permanent stub tier (as an application-layer
  enforcement claim, not a detection-never-misses claim); the
  `injection_suspected` false-negative-rate row in Accepted risks is
  updated from "unmeasured" to "measured for the stub, permanently
  unmeasured for any real model," with a note that this session's result
  does **not** trigger ADR-0003's revisit condition (that condition is
  specifically about a real-model gap, which this session cannot produce
  evidence about either way).
- **Updated `docs/project-memory/07-testing-strategy.md`** — added the
  adversarial-corpus row to the Levels table, rewrote the Security testing
  section's corpus paragraph from "not yet built" to the real Claim
  1/Claim 2 split with actual numbers, added the adversarial-corpus CI gate
  description, and removed the now-closed "full adversarial injection
  corpus not yet built" line from Known gaps (replaced with a note that
  Session 6 narrowed the *enforcement* half of the permanent ADR-0004 gap
  but not the *real-model-judgment* half).
- **Updated `docs/SDLC-EVIDENCE.md`'s Phase 5 row** — added a new "5a.
  Session 6" sub-row with this session's real evidence, and added a note
  to Session 5's own row recording the 3x reproducibility confirmation.
- **Rewrote this file.**
- `privacy-forge`, `laravel-consent-guard`, and `bookslot` were not
  touched, read, or modified this session.

## Files created or changed

- `docs/security/adversarial-corpus/documents/*.md` (new, 18 files) — the
  committed adversarial corpus
- `docs/security/adversarial-corpus/README.md` (new) — category breakdown,
  the precise Claim 1/Claim 2 split, measured baseline table
- `backend/tests/security/__init__.py` (new)
- `backend/tests/security/adversarial_dataset.py` (new) — the 18-case
  dataset, category enum, per-case marker-detection predictions
- `backend/tests/security/adversarial_corpus_loader.py` (new) — real
  ingestion into an isolated corpus
- `backend/tests/security/run_adversarial_evaluation.py` (new) — the
  CI-gated harness, runnable standalone
  (`python -m tests.security.run_adversarial_evaluation`) or via pytest
- `backend/tests/security/test_adversarial_corpus.py` (new) — wires the
  harness into `pytest -q`
- `backend/tests/support/tier_caveat.py` (new) — the stub-tier-vs-
  real-quality banner, extracted from `tests/eval/run_evaluation.py`
- `backend/tests/eval/run_evaluation.py` — `_tier_caveat` removed, now
  imports and calls the shared `render_tier_caveat`; behavior unchanged
  (confirmed by re-running `test_evaluation_harness.py`)
- `.github/workflows/ci.yml` — added a dedicated adversarial-corpus CI step
- `docs/project-memory/06-security-threat-model.md` — corpus status,
  pass-criteria precision, Accepted risks row updated
- `docs/project-memory/07-testing-strategy.md` — Levels table, Security
  testing section, Known gaps updated
- `docs/SDLC-EVIDENCE.md` — Phase 5 row extended with a Session 6 sub-row
- `docs/project-memory/12-session-handoff.md` (this file, rewritten)

## Decisions made

- **"Zero successful injections" (the threat model's own stated pass
  criterion) is honestly interpretable, against a permanent stub tier,
  only as "zero application-layer enforcement failures," not as "the
  detection heuristic never misses an attack."** `StubLLMClient`'s
  marker-based detection demonstrably misses 4 of 14 attack cases in this
  corpus (by design — those cases were deliberately phrased to test the
  detection boundary). Conflating "the stub didn't flag it" with "the
  injection succeeded" would misrepresent what actually happened: in every
  one of those 4 cases, the enforcement mechanism had nothing to enforce
  because nothing was flagged as suspicious — a documented limit of the
  placeholder heuristic's detection surface, not a defeat of ADR-0003's
  code. This distinction is why `structural`/`enforcement` (hard,
  zero-slack invariants) and `stub_detection`/`false_positive` (stub-tier
  self-check numbers) are computed, reported, and CI-gated completely
  separately, never merged into one pass/fail number — reinforcing
  `06-security-threat-model.md`'s own existing requirement that generator-
  and verifier-targeted suites be scored as distinct groups, extended here
  to a second axis (enforcement-vs-detection) the original design didn't
  have to consider because it predated this session's actual stub-tier
  execution.
- **Negative controls were deliberately designed so 2 of 4 would false-
  positive, not to produce a flattering 0% number.** A corpus where every
  negative control happily passes would prove nothing about the
  heuristic's real behavior on genuinely ambiguous content (a document
  that quotes an attack phrase verbatim really is textually
  indistinguishable from one that deploys it, under pure substring
  matching) — reporting the actual 50% rate, and explaining precisely why
  it occurs, is more honest and more useful than hiding it by picking
  softer negative-control content.
- **The tier-caveat banner was extracted to a shared module rather than
  duplicated.** Session 5's `_tier_caveat` was private to
  `run_evaluation.py`; this session's harness needed the identical wording
  and structural assertion (`test_evaluation_harness.py`/
  `test_adversarial_corpus.py` both assert specific banner text is
  present). Duplicating ~40 lines of caveat text across two harnesses
  would have let them silently drift apart on a future edit to one but not
  the other — extracting to `tests/support/tier_caveat.py` keeps one
  source of truth. This is the only change to Session 5's existing code
  this session made; its own numbers and tests are unaffected (verified,
  see Validation below).
- **Reproducibility was checked empirically before trusting either gate**
  (Session 5's, at the start of this session, and this session's own new
  numbers, at the end) — a zero-slack threshold on a measurement taken
  once is exactly the kind of thing that fails CI for the wrong reason
  later if the measurement wasn't actually deterministic. Both gates are
  now backed by multiple identical runs, not a single one.

## Validation performed

- **Session 5's evaluation-harness numbers were re-run 3 times total**
  (see "Front-loaded question" above) — byte-identical every time.
- **The full existing test suite still passes** against real
  Postgres+pgvector, including the new `test_adversarial_corpus.py` and the
  refactored `tests/eval/run_evaluation.py` (confirmed by running
  `pytest -q` after this session's changes).
- **The adversarial-corpus harness was executed 3 times total** (once
  standalone before wiring pytest, once via `pytest -q`, once more
  standalone after) — identical results (structural 18/18, enforcement
  0 violations, retrieval 18/18, stub-detection 18/18, false-positive 2/4)
  every time.
- Confirmed `privacy-forge`, `laravel-consent-guard`, and `bookslot` were
  not modified this session.

## Open questions and risks

- **Real entailment/injection-resistance quality remains permanently
  unverified** (ADR-0004, unchanged) — this session narrows the
  *application-layer enforcement* half of the T-02 risk (now real, checked,
  zero-slack) but does not and cannot narrow the *real-model-detection-
  judgment* half. Any future session, document, or summary that describes
  this session's corpus as having "tested injection resistance" without
  the enforcement-vs-detection qualifier would misrepresent what was
  actually measured.
- **Retrieval quality at realistic scale remains unmeasured** — unchanged
  from Session 5, out of this session's scope.
- **Rate limiting (NFR-007), PDF ingestion, MinIO upload, async ingestion,
  and instance-level authentication** remain unimplemented, unchanged from
  prior sessions, unaffected by this session's work.

## Next recommended session

- Proposed session title: whatever the portfolio's next priority is — both
  of this repository's deep SDLC phases (Discovery & Planning, Verification
  & Testing) are now real and substantively evidenced, including the
  adversarial-corpus piece that was the last explicitly-open item from
  Verification & Testing.
- If further security work is prioritized: the two Category 3 cases that
  most directly test detection-boundary generalization
  (`cat3-novel-confirmation-framing`, `cat3-suppress-flag-obfuscated`) are
  the corpus's most interesting cases for a future session that wants to
  reason further about detection-heuristic limits — though any such
  reasoning remains bounded by ADR-0004 exactly as this session's own
  findings are.
- Inputs required: this handoff; `docs/adr/ADR-0004`;
  `docs/security/adversarial-corpus/README.md`;
  `backend/tests/security/` (this session's harness).

## Paste-into-new-session context

**Project:** lexicon — grounded document Q&A system; every answer is
citation-backed or refused
**Track:** public flagship
**Repository state:** branch `main`, unreleased (pre-v0.1.0), Session 6
(adversarial injection corpus) complete on top of Session 5's evaluation
harness and Session 4.5's ADR-0004 descoping decision

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

**Session 3's finding, hardened in real code Session 4, corpus-scale-proven
Session 6:** the verifier is a first-class attack target (T-02),
structurally different from the generator (T-01) and requiring a
structurally different defense (ADR-0003). Both are real, tested, and
provably different implementations (`test_injection_hardening.py`'s unit
tests, now joined by Session 6's 18-document corpus-scale integration
proof, `backend/tests/security/`).

**Session 4.5's finding (permanent, not a temporary gap):** real LLM
provider credentials are permanently descoped for this project by deliberate
owner choice (ADR-0004) — this project's central, original differentiating
claim (real entailment reasoning correctly separating grounded answers from
topically-adjacent fabrications, and real resistance to a verifier-hijack
attempt) is permanently unprovable in this project's current lifecycle.

**Session 5's finding:** the evaluation *methodology* is real, executed,
CI-gated, and — as of this session — confirmed reproducible across multiple
runs: a committed 16-case golden dataset, real recall@3 (9/9), and real,
reproducible refusal-correctness (11/16) and citation-accuracy (7/10)
numbers against `StubLLMClient`'s known heuristic.

**This session's (6's) central finding, and the one that must not be lost
in any future summary of this project:** the four-category adversarial
injection corpus is now real, committed, and CI-gated
(`docs/security/adversarial-corpus/`, `backend/tests/security/`) — 18
documents, and it proves exactly two things, kept explicitly separate:
**(1) application-layer enforcement (ADR-0003 item 3's
`injection_suspected → enforced_entailed=False` override, and items 1-2's
structural delimiting) is real, checked, zero-slack, and holds regardless
of LLM tier** — a property of the application's code, not of any model's
judgment, proven against 18 real documents and real database rows, not one
canned unit-test case. **(2) `StubLLMClient`'s own crude, hardcoded
marker-detection is a stub-tier self-check only** (18/18 self-check match,
2/4 negative-control false-positive rate) and says nothing about whether a
real model would recognize a novel injection phrasing or distinguish
genuine discussion of injection from an actual attempt — that gap is
ADR-0004's, permanent, and unchanged by this session existing. Any future
summary that says this session "proved injection resistance" without that
qualifier is wrong.

**Current stack:** unchanged from Session 5 — FastAPI/Python 3.12 backend,
Next.js 15 frontend (still Session 0 skeleton), PostgreSQL + pgvector,
Redis (provisioned, unused), MinIO (provisioned, unused), Docker Compose,
GitHub Actions CI (now with two dedicated harness steps — Session 5's
evaluation harness and Session 6's adversarial corpus). `StubLLMClient`
remains the permanent evaluation substrate (ADR-0004); `AnthropicLLMClient`
remains real, unexercised code.

**Architecture decisions that must not be reversed:** all of Session 4.5's
and Session 5's, unchanged (AGPL-3.0; Next.js 15 + FastAPI/Python 3.12;
exactly two deep SDLC phases; learning budget at cap; OR-semantics keyword
search; post-generation groundedness verification, never a similarity
threshold; ADR-0003's exact hardening contract; DB-permission-enforced
audit-trail append-only property; `llm.factory.get_llm_client()`'s
tier-selection seam must not be hard-wired away; real LLM credentials
remain permanently descoped absent an explicit ADR-0004 revisit; Session 5's
evaluation-harness CI-gate thresholds are regression floors, not quality
targets, and must not be raised without a new real measurement backing
them. **New this session, do not reverse without a documented reason:**
Session 6's adversarial-corpus CI-gate thresholds (`run_adversarial_
evaluation.py`'s module constants) are the same kind of regression floor —
the hard invariants (`structural`, `enforcement`) must never be relaxed
below 100%/zero-violations for any reason (a failure there is always a real
code regression), and the stub-tier self-check thresholds must not be
raised or lowered without a new real measurement backing the new number.
Do not read a passing adversarial-corpus gate as evidence of real
injection resistance — see this session's central finding above.

**Implementation state:**
- Done: everything from Session 5, plus Session 6's 18-case adversarial
  injection corpus (`docs/security/adversarial-corpus/`,
  `backend/tests/security/`), CI-gated with both hard invariants and
  measured-baseline stub-tier thresholds, its Claim 1/Claim 2 split
  enforced in the harness's own printed output.
- In progress: nothing mid-flight.
- Not started / explicitly deferred: rate limiting (NFR-007), PDF
  ingestion, MinIO object-storage upload, async ingestion worker,
  instance-level authentication, retrieval quality at realistic corpus
  scale.
- **Permanently descoped, not merely deferred:** real-model verification of
  ADR-0001's entailment mechanism and ADR-0003's injection-detection
  judgment (ADR-0004, unchanged) — Session 6 narrows the enforcement half
  of the T-02 risk specifically, not this permanent gap.

**Constraints and non-goals:**
- Full non-goals table: `docs/project-memory/01-scope-and-non-goals.md`.
- Real LLM provider credentials — see ADR-0004.

**Task for the next session:** no single mandated objective — both deep
SDLC phases are now substantively evidenced. Take the portfolio's next
priority, or (if further hardening of this repository specifically is
wanted) treat the detection-boundary cases named in "Next recommended
session" above as a starting point, with the same ADR-0004 boundary this
session respected.

**Definition of done for this session (met):**
- The corpus exists under `docs/security/adversarial-corpus/`, covering
  all four categories `06-security-threat-model.md` names, with
  generator- and verifier-targeted structural checks and enforcement
  checks scored as distinct, separately-labelled groups.
- Results are real, executed, and CI-gated, with the same stub-tier caveat
  enforced inside the harness's own output that Session 5 established as
  the pattern.
- The specific claim proven (application-layer enforcement holds
  regardless of model output) is stated clearly, separate from the claim
  that remains unprovable (real model resistance) — in the harness output,
  the README, and this handoff.
- No output anywhere reads as if real model resistance to injection was
  demonstrated.

**Files to attach or paste:**
- `docs/project-memory/12-session-handoff.md` (this file)
- `docs/adr/ADR-0004-real-llm-verification-descoped.md`
- `docs/adr/ADR-0003-verification-injection-hardening.md`
- `docs/security/adversarial-corpus/README.md`
- `backend/tests/security/` (this session's harness)
- `backend/tests/eval/` (Session 5's harness — confirmed reproducible, unaffected)

**Ground rules:** Do not change the stack. Do not introduce a third new
technology. Do not expand the deep-SDLC-phase count beyond two. Do not
touch `privacy-forge`, `laravel-consent-guard`, or `bookslot`. Do not report
or remember a stub-tier test or harness result as if it were evidence about
real model behavior — specifically, do not describe the adversarial
corpus's enforcement results as "injection resistance proven." Do not
reintroduce "obtain a real API key" as an open or blocking item without
first explicitly revisiting ADR-0004. Do not raise any harness's CI-gate
thresholds without a new real measurement backing the new number. Ask
before introducing any new dependency or scope item not already
anticipated above.
