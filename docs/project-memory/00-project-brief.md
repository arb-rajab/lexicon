# Project Brief
> Purpose: the single source of truth for what this project is and why it exists.
> Project: lexicon (public)
> Last updated: 2026-08-27
> Status: **Session 1 — Discovery & Planning, complete.** This replaces the
> Session 0 draft stub in full; no section below is carried over unvalidated.

## One-line description

A grounded document Q&A system: every answer is citation-backed against the
supplied documents, or the system refuses to answer.

## Problem statement

**Who has this problem.** A team with a bounded, authoritative, *changing*
document corpus — engineering runbooks and API references, internal policy
or compliance documents, product/config documentation — where people need
answers fast, but the answer has to be trustworthy enough to act on without
re-reading the source document themselves every time. The realistic persona
this brief reasons about: a software engineer or support/compliance analyst
who currently either (a) pastes questions into a general-purpose chatbot
that has never seen their internal docs, (b) greps or full-text-searches the
doc set and has to reconcile several partial matches by hand, or (c) asks a
senior colleague who happens to remember the answer — a pattern that does
not scale and does not leave an audit trail.

**Honesty note on "target users."** This is a portfolio flagship project
with no live customers or user interviews conducted. The persona above is
reasoned from direct, first-hand familiarity with the actual failure modes
of the three existing options — it is a grounded hypothesis, stated as one,
not empirical user research dressed up as validated fact. What *is*
empirical is the feasibility spike below, which tests the retrieval
mechanism against a real corpus and real queries.

### Why the existing options fall short

**1. A general-purpose chatbot (no retrieval).** It has no access to the
org's actual documents — private runbooks, unpublished policy revisions,
anything created or changed after its training cutoff — so it cannot
possibly ground an answer in them. Critically, it does not *know that it
doesn't know*: it produces a plausible, confident answer anyway, because
plausibility, not correctness, is what its training optimizes for on
out-of-distribution questions. There is no citation to check, because it
never had a source document to cite in the first place.

**2. Pure keyword/full-text search.** This spike measured this directly
rather than asserting it (see `docs/spikes/session1-hybrid-retrieval/RESULTS.md`,
Finding 1): naive AND-semantics Postgres full-text search
(`plainto_tsquery`) scored **0/9 (0%) recall@3** against natural-language
questions phrased the way a real user would phrase them, because it
requires every content word in the *question* to co-occur with the answer
in one chunk — something ordinary question phrasing rarely satisfies. Even
after fixing that (OR semantics), keyword search only works when the
query and the answer share vocabulary; it has no mechanism for synonymy or
paraphrase, and — even when it retrieves the right document — it returns
*documents*, not a synthesized, cited answer. The user still has to read
and reconcile the results themselves.

**3. A fully fine-tuned model.** Full comparison and cost analysis is in
[`00b-rag-vs-alternatives.md`](00b-rag-vs-alternatives.md). Summary: fine-
tuning bakes facts into diffuse model weights with no mechanism to point at
"this exact passage, this exact document version" — so it cannot produce a
real citation — and every time the corpus changes (which, per the problem
statement, it routinely does), the fix is a full retraining cycle rather
than re-embedding one changed document. It also does not remove the
confident-fabrication risk; it just moves where the fabrication comes from.

### The cost of a wrong answer (why refuse rather than hallucinate)

This is the crux of the project, made concrete rather than asserted:

- An engineer asks "what's the default value of this config parameter?" A
  wrong-but-confident answer gets shipped into code and causes a production
  incident that takes hours to trace back to a hallucinated default.
- A compliance analyst asks "does our retention policy allow deleting this
  record category after 90 days?" A wrong-but-confident "yes" causes data to
  be destroyed that should have been kept under a legal hold — a real
  regulatory and legal exposure, not a hypothetical one.
- A wrong-but-confident answer claiming a deprecated auth flag is still
  supported becomes a security misconfiguration someone ships on trust.

In every case, the damage comes specifically from the answer being **acted
on without independent verification** — which is exactly what a citation-
backed answer is supposed to enable, and exactly what a fluent, wrong,
uncited answer defeats. A refusal ("the supplied documents don't answer
this") is recoverable: the human goes and checks manually, which is slower
but safe. A confident wrong answer is not self-announcing as wrong, so nobody
checks. **This is why the product's hard invariant is "cited or refused,"
not "answered, with a confidence score attached."**

The spike found direct evidence that a naive confidence-threshold approach
is not sufficient to make this invariant hold — see
`docs/spikes/session1-hybrid-retrieval/RESULTS.md`, Finding 2: a query that
was topically adjacent to the corpus but not actually answered by it
(*"How do I set up 'Sign in with Google' as an OAuth2 identity provider?"*
against a corpus that only documents password-flow JWT auth) scored a top
vector similarity of **0.701** — squarely inside the 0.706–0.848 range of
the nine genuinely correct retrievals in the same run. A system that refused
only below a fixed similarity threshold would have handed this passage to
the generator with high confidence and risked a fabricated-but-plausible
answer about a feature the documentation never covers. **Retrieval
confidence alone cannot carry the refusal decision** — this is a concrete,
measured finding, not a hypothesis, and it is now a fixed architectural
input for Session 2+ (see Finding 2's "implication for the architecture").

## Stakeholders

- **Primary user:** the knowledge worker asking the question (engineer,
  support agent, compliance analyst — see persona above).
- **Corpus owner/admin:** whoever uploads and maintains the document set;
  cares that the system stays current as documents change without a
  retraining cycle.
- **Accountable party for a wrong answer:** whoever owns the downstream
  consequence (engineering lead, compliance officer) — the actual audience
  for the "cost of a wrong answer" section above.

## Business assumptions

- The document corpus is primarily textual, bounded, and owned/controlled
  by the deploying organisation (not the open internet) — this is what
  makes grounding meaningful and citations checkable.
- The corpus changes over time — new documents, edited documents, deprecated
  documents — which is the direct justification for RAG over fine-tuning
  (see `00b-rag-vs-alternatives.md`).
- Users of this kind of system value a correct refusal over a fluent guess
  for factual questions with real consequences. This is stated as an
  assumption, not a proven fact — there is no live user base to validate it
  against. It is the product's central bet, and it is the reason "cited or
  refused" is a hard invariant rather than a nice-to-have.

## Feasibility note

A real feasibility spike was run against a real, licence-clean corpus (8
pages of official FastAPI documentation, MIT-licensed) using the project's
actual planned infrastructure (Postgres + pgvector, Docker) — not a toy
script and not a hand-wave. Full method, honest results (including the
mediocre first attempt), and their implications are in
[`docs/spikes/session1-hybrid-retrieval/RESULTS.md`](../spikes/session1-hybrid-retrieval/RESULTS.md).
Headline: hybrid retrieval is technically feasible end-to-end; naive
keyword search is not viable as shipped and must use OR semantics; retrieval
confidence alone is not a safe refusal signal (Finding 2, above). The spike
explicitly does **not** prove retrieval quality at production scale — see
its "What this spike does and does not prove" section.

## Success metrics

Defined now so later sessions have a fixed target, not a moving one. Where
the spike already produced a number, it is quoted; where it did not
(generation and security don't exist yet), the metric and methodology are
defined without a fabricated current value.

**Amended, Session 4.5 (2026-08-27):** the project owner has permanently
declined to obtain a real LLM provider credential for this project
(`docs/adr/ADR-0004-real-llm-verification-descoped.md`). Metrics #2, #3,
and #5 below depend on real generation or verification behavior and can
therefore only ever be measured against `StubLLMClient`'s known,
deterministic heuristic — not against real model quality — for this
project's current lifecycle. Each is annotated below with what it can and
cannot actually claim. Metric #1 does not depend on an LLM call at all and
is unaffected.

1. **Retrieval recall@3**, measured by the CI-gated evaluation harness
   (Session 5, Verification & Testing) against a golden query set on a
   realistic-scale corpus (target: 500+ chunks across 20+ documents — large
   enough that 3-guesses-out-of-N stops being a low bar, unlike this
   spike's 9-document corpus). *Spike baseline, honestly caveated as an easy
   corpus:* 100% recall@3 for OR-semantics keyword, vector-only, and hybrid;
   0% for AND-semantics keyword. **Unaffected by ADR-0004** — retrieval
   never calls an LLM provider, so this remains a real, fully measurable
   metric at realistic scale.
2. **Refusal recall** — of a labeled set of queries with no true answer in
   the corpus, the fraction the system correctly refuses. Per Finding 2,
   this set must include *topically-adjacent-but-absent* queries, not only
   fully-unrelated ones — the spike showed the fully-unrelated case (0.515
   similarity) is the easy case and the adjacent case (0.701 similarity) is
   the one that actually tests the refusal mechanism. **Permanently
   measurable only as a stub-tier self-check, per ADR-0004**: Session 5 can
   confirm the harness correctly scores `StubLLMClient`'s known
   keyword-overlap heuristic against this query set, which proves the
   harness works — it cannot and will not produce a real refusal-recall
   number, because that requires observing a real model's entailment
   judgment, which this project has no credential to obtain.
3. **Citation accuracy** — of the answers the system does give (not
   refused), the fraction where a human reviewer confirms the cited passage
   actually supports the stated answer, on a spot-checked labeled sample.
   This is the literal, checkable test of "citation-backed." **Permanently
   measurable only as a stub-tier self-check, per ADR-0004**, for the same
   reason as metric #2 — the answers being reviewed would be
   `StubLLMClient` output, not real generation.
4. **End-to-end query latency (p95)** — not yet measurable; no generation
   step exists. A concrete budget is set once Session 2's architecture
   fixes the generation model and infra, not invented here. **Note added,
   ADR-0004:** even once measurable, latency measured against
   `StubLLMClient` (in-process, no network round trip) will not be
   representative of real provider latency and must not be reported as if
   it were — this metric has no path to a real value in this project's
   current lifecycle either.
5. **Prompt-injection resistance** — pass rate on the adversarial
   prompt-injection test suite committed at the Verification & Testing deep
   phase (Session 5). Target: zero successful injections in the committed
   suite. Not yet measurable; no generation surface exists to attack yet.
   **Permanently measurable only as a stub-tier self-check, per ADR-0004**:
   the adversarial corpus itself (attack categories, generator- and
   verifier-targeted cases) is real, valuable work that Session 5 will
   still produce, but running it against `StubLLMClient` tests whether the
   *harness* correctly detects the stub's scripted responses — it does not
   and cannot test whether a real model actually resists an injection
   attempt, which is the metric's actual point.

## MVP boundary

See [`01-scope-and-non-goals.md`](01-scope-and-non-goals.md) for the full,
checkable MVP boundary and the non-goals table with reconsideration
conditions — this brief does not duplicate it.

## Why RAG, not fine-tuning or search alone

Full options-considered comparison, in the same rigor as this portfolio's
ADRs (`privacy-forge`'s `docs/adr/`), lives in a dedicated file because it
is genuinely a separate piece of reasoning, not a paragraph of this brief:
[`00b-rag-vs-alternatives.md`](00b-rag-vs-alternatives.md).

## Why this project exists in the portfolio

For the technology allocation, learning-objective rationale, and the "why
Discovery and Verification/Testing are the two deep SDLC phases" reasoning,
see [`00a-ledger-confirmation.md`](00a-ledger-confirmation.md) — that file
is the frozen governance record for this repository and is not duplicated
here.

## Elevator pitch (for the README)

"Every answer is citation-backed or refused."
