# ADR-0001 — Refusal Mechanism: Post-Generation Groundedness/Entailment Verification

- **Date:** 2026-08-27
- **Status:** accepted

## Context

`00-project-brief.md`'s hard product invariant is "cited or refused" — an
answer is only shown to the user alongside the specific passage(s) it was
grounded in, or the system explicitly declines to answer. The entire
argument for choosing RAG over a general chatbot or a fine-tuned model
(`00b-rag-vs-alternatives.md`) depends on refusal actually working: RAG's
advantage is that "a refusal decision has something concrete to be based
on," but choosing RAG does not automatically produce a *correct* refusal
decision — it only produces the retrieved passages a refusal decision could
be based on.

Session 1's feasibility spike measured this directly rather than assuming
it (`docs/spikes/session1-hybrid-retrieval/RESULTS.md`, Finding 2). Two
negative-control queries had no correct answer anywhere in the corpus:

| Query | Kind | Top vector similarity |
|---|---|---|
| "How do I set up 'Sign in with Google' as an OAuth2 identity provider?" | topically adjacent, but absent from the corpus | **0.701** |
| "What is the boiling point of tungsten?" | fully out-of-corpus | 0.515 |

The nine genuinely answerable queries in the same run scored **0.706–0.848**
top similarity. The fully-unrelated query is cleanly separable from the
correct-answer range; **the topically-adjacent query is not** — 0.701 sits
squarely inside 0.706–0.848. A system that refused only below a fixed
similarity threshold (e.g. "refuse if top score < 0.6") would have handed
the OAuth2/JWT password-flow chunk to generation with high confidence and
risked a fabricated-but-plausible answer about a feature the documentation
never covers — precisely the failure mode `00-project-brief.md`'s "cost of a
wrong answer" section exists to prevent (a wrong-but-confident answer acted
on without independent verification).

**This is a measured finding, not a hypothesis:** retrieval-similarity
score, on its own, cannot separate "topically close but wrong" from
"actually correct." A real refusal mechanism — something that checks
whether a passage actually supports a specific answer, not merely whether
it is topically related to the query — is required. This ADR is that
design decision, made explicitly with real trade-offs stated, not defaulted
into by whichever approach was easiest to wire up first.

A second constraint shapes every option below: **this is a self-hostable
application where every query costs real money against an LLM API**
(`00-project-brief.md`'s stakeholder model has no captive infrastructure
budget). A refusal mechanism that doubles or triples LLM spend per query
without a stated reason is not a free choice — the cost has to be justified
against what it buys.

## Options considered

### A — Reranking (cross-encoder) as the refusal signal

Replace or supplement the bi-encoder cosine-similarity score with a
cross-encoder reranker: a model that jointly attends to the query and each
candidate passage together, rather than comparing two independently
computed embeddings. Refuse below a tuned score threshold, as before, but
on the reranker's score instead of raw vector similarity.

**For:** Cross-encoders are well understood to be more precise than
bi-encoder similarity for relevance ranking, precisely because they can
attend to specific token overlap and mismatch (e.g. "this passage never
mentions Google or third-party sign-in") rather than comparing two fixed
vectors in isolation. Cheaper than a full LLM call — rerankers are
typically small, fast models. Would also likely improve retrieval ranking
quality generally, independent of refusal.

**Against:** A reranker still produces the same *shape* of signal Finding 2
disproved — a soft numeric relevance score with a threshold. It narrows the
gap but does not change the fundamental question being asked: "is this
passage relevant to the query's topic," not "does this passage contain the
specific fact needed to answer this specific question." Those are different
questions — the OAuth2/JWT chunk *is* topically relevant to "OAuth2
identity provider," which is exactly why it scored high; a reranker
evaluating topical relevance has no obvious reason to fail differently on
this case. Nothing in the spike measured whether a reranker would have
actually separated 0.701 from the true positives — building that evidence
would require another spike, which is out of scope for an architecture
session (Ground rules: no implementation this session, and the ADR must
decide from evidence already in hand, not defer the decision pending a new
experiment). Rejected as the **primary** refusal mechanism; retained as a
retrieval-quality improvement, addressed below.

### B — Pre-generation LLM-as-judge groundedness gate

Before running generation, ask an LLM: "given these retrieved passages, do
they contain the specific information needed to answer this question?" If
no, refuse immediately without generating an answer.

**For:** Can save a full generation call in the common case where retrieval
clearly missed — cheaper than always running generation first. Operates on
a semantic judgment rather than a numeric score, so it isn't structurally
identical to the mechanism Finding 2 disproved.

**Against:** The judge is asked to evaluate topical fit against the
*question*, not against any specific claim — it has nothing concrete to
check the passages against yet, because no candidate answer exists. A judge
prompted only with "is this passage related to this question" is
vulnerable to the same topical-adjacency trap a human skimming the chunk
would be: the OAuth2/JWT chunk visibly discusses "OAuth2" and "identity
provider," the exact phrase in the query. Without a specific claim to
verify against, the judge is reasoning about the same fuzzy relevance
question as Option A, just with a more expensive model. Rejected as the
primary mechanism for the same structural reason as A, though the
underlying idea (a dedicated LLM call whose only job is to gate the
answer) carries forward into the decision below in a more precise form.

### C — Post-generation groundedness/entailment verification (chosen)

Generation is conditioned strictly on the retrieved passages and required
to attach a citation (a specific chunk ID) to every factual claim, with an
explicit instruction to self-refuse ("I cannot answer this from the
supplied documents") when the passages do not support an answer. This
self-refusal is a first, cheap filter — but it is **not trusted alone**: an
independent verification step, run by a separate LLM call that does not
see the generator's reasoning, takes the generated answer's claims and
their cited passages and checks entailment claim-by-claim — "does the exact
text of this cited passage actually support this exact claim?" If any
required claim fails entailment, or the generator itself self-refused, the
system discards the draft answer and returns an explicit refusal.

**For:** This operates on the question Finding 2 actually shows matters —
not "is this passage topically related" but "does this specific passage
support this specific claim." The OAuth2/JWT chunk can score however high
it wants on topical similarity; a claim like "you can sign in with Google"
checked against a passage that only ever discusses password-flow JWT
issuance fails entailment cleanly, because entailment asks a narrower,
factual question that topical similarity structurally cannot answer.
Running verification as a separate call, blind to the generator's own
reasoning, avoids the same model "grading its own homework" inside one
context window, which would let a hallucinated justification
cross-contaminate the check. This composes as defense in depth: cheap
self-refusal catches the obvious cases without invoking a second model call
question-by-question; independent verification is what actually enforces
the invariant when self-refusal fails to fire (a generator can be wrong
about its own certainty).

**Against:** Real, stated cost: an answered (non-self-refused) query costs
two LLM calls instead of one — added latency (one more round trip) and
added spend. The verification step's own accuracy is not yet measured — a
verifier that is too lenient rubber-stamps wrong claims (defeats the
purpose); a verifier that is too strict produces false refusals on
genuinely correct answers (defeats usability, and would itself need
measuring against success metric #3, citation accuracy). This ADR commits
to the mechanism's existence and shape; it explicitly does **not** claim
the verification step's accuracy is proven — that is Session 5's
evaluation-harness job (refusal recall and citation accuracy, success
metrics #2–#3), using the same adjacent-but-wrong query class Finding 2
surfaced, not just fully-unrelated negative controls.

## Decision

**Option C — post-generation groundedness/entailment verification —
combined with Option A retained as a secondary, non-decisive retrieval-
quality improvement.**

- **Primary refusal mechanism:** generation with mandatory chunk-scoped
  citations and a self-refusal instruction, followed by an independent
  entailment-verification LLM call over the generated claims against their
  cited passage text. The system returns an answer only if verification
  passes for every cited claim; otherwise it returns an explicit refusal.
  This is the mechanism the "cited or refused" invariant is actually
  enforced by.
- **Reranking (Option A)** is retained as a future retrieval-ranking
  improvement — worth pursuing because the spike's own "does not prove"
  section flags that this corpus never tested vector search's known
  weakness on exact-token queries, where a reranker or hybrid signal could
  plausibly help — but it is explicitly **not** load-bearing for the
  refusal decision, so a later choice to add, tune, or drop it cannot
  quietly relitigate whether verification is needed.
- **Option B is rejected outright**, not merely deprioritised: asking a
  judge to assess passage-to-question relevance before a candidate answer
  exists reproduces the same structural blind spot as similarity
  thresholding, just at higher cost.

## Trade-offs accepted

- **Cost and latency:** two LLM calls per answered query (generation +
  verification) instead of one. Verification is skipped only when
  generation self-refuses, since there is nothing to verify — the added
  cost is scoped to the case where an answer is actually being considered
  for release, not every query. Cost-control approach (model tier choice,
  prompt caching, chunk-count bounding) is addressed in `03-architecture.md`.
- **Unmeasured verifier accuracy:** the verification step's own false-accept
  and false-refuse rates are not known yet and cannot be known without a
  generation surface to test — Session 5's evaluation harness carries this
  forward as a first-class metric, not an afterthought.
- **More moving parts than a single-call design:** a distinct pipeline
  stage, a distinct prompt/schema (per-claim entailment judgments), and a
  distinct failure mode (the verifier itself being wrong) to design,
  implement, and evaluate — accepted because Finding 2 shows the single-call
  designs (A, B, or a bare similarity threshold) share the same structural
  blind spot regardless of which scoring model produces the number.

## Consequences

- `03-architecture.md`'s pipeline must implement generation and
  verification as two distinct stages with two distinct model calls — not
  a single call asked to "answer and also rate your own confidence," which
  would reintroduce the self-grading problem this decision explicitly
  avoids.
- Session 4 (Implementation) must define a concrete verification
  input/output contract: per-claim citations in, per-claim
  entailment pass/fail out, with the overall answer gated on all claims
  passing — this is a real interface, not a vague "double-check it" step.
- Session 5's evaluation harness must specifically include the
  adjacent-but-wrong query class Finding 2 surfaced (not just fully
  unrelated negative controls) when measuring refusal recall — a harness
  that only tests obviously-unrelated queries would not actually validate
  that this mechanism solves the problem it was built for.
- Provider/model choice (`03-architecture.md`) is shaped by this decision:
  the verification call is a bounded, narrow classification-style task
  (does this text support this claim, yes/no) and does not need the same
  model tier as open-ended generation — this is the basis for the
  cost-control approach in the architecture doc.

## Revisit triggers

- If Session 5's harness shows reranking (Option A) alone achieves
  comparable refusal precision to the two-call verification design at
  materially lower cost, reconsider collapsing to a single-call design —
  but only on measured evidence from the harness, not on the general
  reputation of rerankers.
- If the verification step's measured false-refusal rate (correct answers
  wrongly refused) is too high in harness data, consider a compound signal
  (verification result plus retrieval score together) rather than reverting
  to similarity alone — reverting to a bare threshold would silently
  re-introduce the exact failure this ADR exists to close.
- If per-query LLM cost proves materially unsustainable for a self-hosted
  deployment once real usage data exists, revisit the verification-model
  tier choice before revisiting whether verification happens at all —
  cost-tuning the mechanism is preferable to removing it.
