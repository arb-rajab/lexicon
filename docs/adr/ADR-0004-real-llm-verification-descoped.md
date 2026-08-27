# ADR-0004 — Real LLM Provider Verification: Permanently Descoped by Deliberate Portfolio-Scope Choice

- **Date:** 2026-08-27
- **Status:** accepted (recorded as fact, not a design choice)

## Context

Every session since Session 2 has flagged the same gap: no
`ANTHROPIC_API_KEY` (or any other LLM provider credential) exists in this
environment. Session 4's `12-session-handoff.md` went further than simply
re-flagging it — it explicitly argued this repository's version of the gap
is *structurally different* from `bookslot`'s permanently-descoped Stripe
gap (`bookslot`'s decision log, D-0036), on the reasoning that ADR-0001's
entire premise is that similarity scores cannot be trusted and an
independent verification step is required *instead* — and proving that
step actually works requires observing a real model's real behavior on the
adversarial case Session 1 measured (the 0.701-scoring OAuth2/JWT query).
Session 4 therefore called obtaining a real key "an urgent, cheap-to-clear
blocker" and named it as the single gating action before Session 5 could
produce any evidence at all.

That framing has not changed technically. What has changed is that the
project owner has now made an explicit, deliberate choice: **a real
Anthropic API key will not be obtained for this project, for
portfolio/skill-proof reasons, within this project's current lifecycle.**
This mirrors two existing precedents elsewhere in this developer's
portfolio — `bookslot`'s D-0036 (real Stripe test-mode credentials
permanently declined) and `privacy-forge`'s Session 24 decision (a live,
publicly-reachable demo instance permanently declined) — but the reasoning
below is worked out fresh for this repository's own situation, not copied
from either. The two precedents share a shape (a recurring "obtain real
X before the next session" item, closed by deliberate choice rather than
left open indefinitely or quietly stopped being mentioned) but not a
severity. That difference is the point of this ADR.

This ADR formally closes the recurring "obtain a real key before Session 5"
item that has been carried forward, unresolved, since Session 2 — the same
kind of repeatedly-re-raised-without-resolution pattern `bookslot`'s own
decision log (D-0034, re-raised at D-0035) named as worth closing outright
rather than perpetuating across further sessions.

## Why this is not the same severity as bookslot's Stripe decision

This distinction matters enough to state before anything else in this ADR,
because understating it would misrepresent what this repository can now
claim.

**In `bookslot`,** the undemonstrated piece (real Stripe API responses,
real webhook delivery, real decline codes) was necessary integration
surface, but it was not the differentiating technical claim that project
was built to prove. `bookslot`'s actual point — that a database exclusion
constraint plus row-locking prevents double-booking under genuine
concurrent load — was proven independently of Stripe entirely, by a real
two-process concurrency test that never touches a payment gateway. Stripe
was one untested integration inside an otherwise-validated system.

**In `lexicon`, the undemonstrated piece *is* the differentiating claim
this flagship exists to prove.** `00-project-brief.md`'s central bet is
that retrieval confidence alone cannot safely gate a refusal decision
(Session 1's Finding 2, measured), and that an independent,
model-driven entailment check can do what a similarity threshold cannot.
ADR-0001 chose that mechanism specifically because it is the one design
that engages the actual question — "does this passage entail this claim,"
not "is this passage topically close to this query" — and made explicit,
in its own Consequences section, that the verifier's real accuracy would
remain unproven until a real model could be observed reasoning about the
exact adversarial case the spike surfaced. ADR-0003 then hardened that same
call against a named, first-class attack (T-02, verifier hijack) and
likewise deferred proof of the hardening's real effectiveness to a real
model's behavior under adversarial passages.

Without a real provider key, **neither of those two things can ever be
observed in this project's lifecycle.** This is not "one integration
boundary is untested while the rest of the system is proven." It is: *the
specific, original, differentiating claim this flagship was built to
demonstrate — that real entailment reasoning, not retrieval confidence, can
correctly separate grounded answers from topically-adjacent fabrications,
and can resist a passage that tries to talk the verifier into agreeing with
a false claim — is now permanently unprovable.* Any future session,
document, or summary that describes this repository's verification
mechanism as "proven" or "validated" is describing something this decision
makes impossible to claim honestly, absent a scope change (see Revisit
triggers).

## What remains real, tested, and provable — stated so this ADR is not read as pure loss

This decision costs this repository its central evidentiary claim. It does
not cost it everything built so far, and conflating the two would be its
own kind of dishonesty:

- **The full pipeline is real, correctly wired, and tested end-to-end.**
  Ingestion (heading-aware chunking, real embeddings), hybrid retrieval
  (OR-semantics keyword search + pgvector cosine search + RRF fusion,
  Session 1's `plainto_tsquery` finding fixed and permanently
  regression-guarded), generation with mandatory chunk-scoped citations,
  the independent verifier call, and the refusal gate all execute for
  real, against a real Postgres+pgvector instance, in 33 passing tests —
  proven against `StubLLMClient`, a client whose behavior is deterministic
  and fully known (a keyword-overlap heuristic, documented as such in its
  own module docstring), not against a black box. That proves the
  *architecture* is sound and the *wiring* is correct — a real
  precondition for the verification claim to ever be checkable, even
  though it is not the claim itself.
- **ADR-0003's injection-hardening design is real architecture with real
  structural tests**, independent of model quality. Forced structured
  output, sandwiched delimiting, the `injection_suspected` self-report
  field, and the application-enforced fail-closed override are all
  implemented exactly as designed, and `test_injection_hardening.py`
  proves the generator and verifier carry genuinely different defenses
  (not one mitigation copy-pasted twice) by inspecting the actual schema
  and prompt structure — not by asking a model whether it resisted
  anything. This is real, checkable evidence about the *shape* of the
  defense.
- **ADR-0002's audit-trail permission split is proven against a live
  database connection** (`test_adr0002_grants.py`), a control that has
  nothing to do with which LLM tier is bound.
- **What is permanently missing, precisely:** evidence that a real model's
  entailment reasoning actually catches the class of failure ADR-0001
  exists to prevent (a topically-adjacent-but-wrong claim, reusing
  Session 1's 0.701-scoring OAuth2/JWT case), and evidence that ADR-0003's
  hardening actually resists the class of attack it was designed against
  (a passage that attempts to direct the verifier's own judgment). Nothing
  else in this repository's evidence base changes as a result of this
  decision.

## Options considered

### A — Continue carrying "obtain a real key" as a recurring blocking precondition

Keep re-raising it at the start of every future session, as Sessions 2
through 4 each did, until a key eventually appears.

**Against:** This is the exact pattern `bookslot`'s own decision log
explicitly named as a problem worth closing, not perpetuating — an item
re-raised without resolution stops being a live open question and starts
being a standing fiction that the gap is temporary when, in practice, it
has never once been closed across four sessions. It also leaves Session 5
free to start without a settled scope, risking the accidental overclaim
this ADR exists to prevent: a harness that quietly measures against the
stub tier while its own language implies it measures real model quality.
Rejected.

### B — Obtain a real Anthropic API key now

Unblock full validation by simply provisioning the credential Session 4
asked for.

**Against:** Not a technical rejection — a stated scope choice by the
project owner. `lexicon`, like `bookslot` and `privacy-forge`, is
portfolio/skill-proof work, not a system being operated for real, and the
project owner has explicitly declined to obtain a real key for it. One
asymmetry worth naming against the `bookslot` precedent: Stripe test-mode
credentials are free, so `bookslot`'s equivalent decision was purely about
scope, not money; a real Anthropic API key requires actual, ongoing spend
per query, which sharpens rather than weakens the case for a deliberate
"no" here rather than an assumed "yes, eventually." Rejected, by explicit
owner decision, not by this ADR's own argument.

### C — Formally descope: close the recurring ask, state precisely what this leaves unprovable, and reframe Session 5 around what is actually achievable without real credentials (chosen)

## Decision

**Option C.**

- The recurring "obtain a real key before Session 5" item, carried in
  every session's handoff since Session 2, is closed with status
  **descoped by deliberate choice** — not "resolved," and not "the real
  proof was achieved by another means." No placeholder or
  real-looking-but-fake value is written anywhere (`.env`, `.env.example`)
  — `ANTHROPIC_API_KEY` stays exactly as absent as it already was; there
  was nothing to clean up, since no session wrote a fake value there.
- `llm/factory.py`'s tier-selection seam (`ANTHROPIC_API_KEY` set → real
  client; unset → `StubLLMClient`) is **unchanged and stays exactly as
  built.** `StubLLMClient` becomes this project's **permanent** evaluation
  substrate for its current lifecycle, not a temporary stand-in awaiting
  Session 5 — the same status `bookslot`'s `FakePaymentIntentGateway`
  holds for Stripe validation, and for the identical reason: a real client
  already exists, is believed correct against the documented provider SDK
  surface, and remains real code, permanently unexercised against live
  provider traffic, by choice rather than by gap.
- `test_proof_session1_oauth2_case.py`'s real-tier branch (asserting
  `answered is False` once `llm.tier == "real"`) is not removed — it
  remains real, correct, dead code, exercisable only if a future scope
  change reopens this decision (see Revisit triggers).
- Session 5 is reframed, not cancelled — see below.

## Session 5, reframed

Session 5's originally-planned objective — "build the CI-gated evaluation
harness and measure real retrieval/generation/verification quality" —
cannot be carried forward unchanged: the second half of that sentence is
now structurally impossible to deliver, per this ADR. Session 5's actual,
achievable objective is narrower and must be stated as such going in, not
discovered mid-session:

**Session 5's purpose is to prove the evaluation *methodology* is sound
and would produce meaningful, trustworthy numbers the moment real
credentials exist — not to claim it has measured real retrieval,
generation, or verification quality, which it cannot do against a stub.**
Concretely, still real and still worth building:

- **Retrieval recall@k measurement is unaffected by this decision** and
  remains a fully real, fully measurable metric — retrieval never calls an
  LLM provider at all. Success metric #1 can and should be measured for
  real, at realistic scale, exactly as originally planned.
- **Refusal-correctness measurement design** — the golden query set
  construction (including the adjacent-but-wrong query class Finding 2
  surfaced), the labeling methodology, the scoring logic — is real
  engineering work whose soundness does not depend on which LLM tier
  produces the answers being scored. Running it against the stub proves
  the harness *works* (it correctly scores a known, deterministic
  behavior) — it does not and cannot prove anything about real refusal
  quality, and Session 5's own documentation must say so explicitly rather
  than let a passing harness run read as more than it is.
- **The adversarial injection corpus itself** — the four attack
  categories, the generator- and verifier-targeted cases,
  `06-security-threat-model.md`'s design — is real, valuable authorship
  work independent of which tier ultimately runs against it.
- **What Session 5 must not claim:** any pass/fail number produced by
  running this harness against `StubLLMClient` is not evidence about real
  retrieval, generation, or verification quality, and must not be reported
  using language that implies otherwise (no "refusal recall: 94%" framed
  as a real quality measurement — framed instead, explicitly, as
  "harness self-check against the stub tier: N/N behaves as the stub's
  known, documented logic predicts").

## Trade-offs accepted

- **This repository's central original thesis — that real entailment
  reasoning can do what retrieval confidence cannot — is permanently
  unprovable within this project's current lifecycle.** This is the real
  cost of this decision, stated once more, plainly, so it cannot be missed
  by skimming only the Decision section.
- **Session 5's evidentiary ceiling is lower than originally planned** for
  everything downstream of a real generation/verification call (refusal
  recall, citation accuracy, prompt-injection resistance) — those success
  metrics (`00-project-brief.md`) can no longer be described as "not yet
  measured, pending Session 5" without qualification; they must be
  described as "not measurable against real model behavior in this
  project's current lifecycle," a different and more permanent claim.
- **Retrieval quality and pipeline-wiring evidence are unaffected** — this
  trade-off is scoped precisely to the generation/verification half of the
  system, not the whole evaluation harness.

## Consequences

- `docs/SDLC-EVIDENCE.md`'s Phase 5 (Verification & Testing) row must
  state this precisely: the depth Session 5 produces is real
  (methodology design, structural tests, pipeline-wiring proof against a
  known stub), but any claim of having measured real AI quality must be
  stated as permanently unverified, not merely "not yet."
- `docs/project-memory/00-project-brief.md`'s success metrics #2, #3, and
  #5 (refusal recall, citation accuracy, prompt-injection resistance) must
  be corrected to state plainly that they can be measured only in
  methodology/self-check form against the stub tier, not as real quality
  measurements, for the duration of this decision. Metric #1 (retrieval
  recall@k) is unaffected and should be measured for real, as planned.
  Metric #4 (latency p95) must note that stub-tier latency is not
  representative of real provider round-trip latency and cannot stand in
  for it.
- `docs/project-memory/12-session-handoff.md` must stop naming "obtain a
  real Anthropic API key" as the blocking action before Session 5 can
  proceed — Session 5 is now unblocked, at its reframed, narrower scope.
- Any future session, README, case study, or summary describing this
  repository's verification mechanism must not describe it as "proven,"
  "validated," or "measured against real model behavior" — the accurate
  description is "designed, implemented, and structurally tested; real
  entailment accuracy against a live model is a permanently accepted gap
  in this project's current lifecycle, by deliberate choice, per
  ADR-0004."

## Revisit triggers

- If `lexicon`'s scope changes from portfolio/skill-proof work to a system
  actually intended to be operated for real — mirroring the identical
  clause in `bookslot`'s D-0036 — this decision is revisited and a real
  key sought at that time. This ADR closes the recurring *ask*; it does
  not close the technical *possibility*. `llm/factory.py`'s seam exists
  precisely so that reopening this decision is a config change, not a
  rewrite.
- If a future portfolio ledger conversation allocates dedicated budget or
  learning-objective scope specifically to real-model RAG evaluation
  (distinct from this project's current two-slot budget, which is already
  spent on RAG evaluation methodology and LLM guardrails design per
  `00a-ledger-confirmation.md`), that conversation — not a unilateral
  in-session choice — is the correct place to reopen this decision.
