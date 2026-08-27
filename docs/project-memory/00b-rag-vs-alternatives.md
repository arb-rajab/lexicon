# Session 1 — Why RAG, Not Fine-Tuning or Search Alone

> Purpose: the explicit options-considered comparison this repository's
> central design question requires (per `00a-ledger-confirmation.md`'s
> Discovery deep-phase rationale). Written in the same rigor as this
> portfolio's ADRs (see `privacy-forge/docs/adr/`), but deliberately kept
> out of `docs/adr/` and unnumbered: `00a-ledger-confirmation.md` records
> that formal ADRs begin at Session 3 (architecture), and this is Session 1
> (discovery) reasoning. If Session 3 needs to formalise or revise this
> decision as an architecture ADR, it should reference this file rather
> than re-run the comparison from scratch.
>
> Project: lexicon (public) · Last updated: 2026-08-27 · Status: decided

## Context

The problem statement (`00-project-brief.md`) establishes: a bounded,
*changing* document corpus; users who need answers they can act on without
re-reading the source; and a failure-cost profile where a confident wrong
answer is worse than a refusal. Three mechanisms could plausibly deliver
"answer questions about our documents": full-text/keyword search, a fully
fine-tuned model, and retrieval-augmented generation (RAG — retrieve
relevant passages, generate an answer grounded in them, cite the source).
This file compares them against that specific failure-cost profile, not
against RAG's general reputation.

## Options considered

### A — Pure keyword / full-text search

A search index (e.g. Postgres full-text search, Elasticsearch) over the
corpus; the user reads the returned documents themselves.

**For:** Cheap, exact, fully explainable — a match is a match, there is
nothing to hallucinate. No model cost at all.

**Against, measured directly by this session's feasibility spike** (not
asserted — see `docs/spikes/session1-hybrid-retrieval/RESULTS.md`, Finding
1): naive AND-semantics keyword search scored **0/9 (0%) recall@3** against
natural-language questions phrased the way a real user actually asks them
("How do I check a plaintext password against a stored hash at login?"
shares almost no vocabulary with the answer's actual terms —
`verify_password`, `pwd_context`, `CryptContext`). Fixing the query
semantics (OR instead of AND) recovered full recall on this small corpus,
but the fundamental limit remains: **keyword search can only find what
shares vocabulary with the query.** It has no mechanism for synonymy,
paraphrase, or conceptual similarity, and it never fails silently in the
dangerous direction — it either matches or it plainly doesn't, so it can't
even partially satisfy the "give me a synthesized, cited answer" requirement
the problem statement asks for; it always defers reading and reconciliation
back to the human.

**Verdict:** necessary but not sufficient. Kept as one half of the hybrid
mechanism (see Decision), not as a standalone answer.

### B — Fully fine-tuned model

Fine-tune a base model on the document corpus so the facts live in its
weights; answer questions by generating directly, no retrieval step.

**Cost of keeping the corpus current.** The problem statement establishes
the corpus is not static — documents get added, edited, deprecated. Under
RAG, absorbing a change means re-embedding one document (seconds, no GPU
training run) and it takes effect immediately. Under fine-tuning, every
material corpus change requires a new fine-tuning run: real compute cost, a
real turnaround delay (the answer set is stale until the run completes and
is deployed), and real engineering process (dataset curation, eval,
re-deployment) repeated on every meaningful change. For a bounded corpus
that changes routinely — the exact shape this project targets — that
recurring cost compounds; for a corpus that never changed, it might be
tolerable, but that isn't this project's premise.

**Citability is not an add-on gap, it's structural.** A fine-tuned model's
"knowledge" is distributed across weight updates gradient descent made
during training; there is no artifact inside the model that corresponds to
"this exact passage, in this exact document, as of this version." Citation
requires pointing at a specific retrievable source, which is only possible
if a specific source was explicitly looked up as part of answering — i.e.
you need a retrieval step regardless, at which point you have reinvented
half of RAG anyway, just without the grounding-check benefit of actually
conditioning generation on the retrieved text.

**Staleness is actively dangerous here, not just inconvenient.** When a
document is edited or deprecated, a fine-tuned model may keep answering
from the old, now-wrong fact baked into its weights — with no clean way to
force it to forget. Given this project's stated failure-cost profile
("what does a wrong answer cost," `00-project-brief.md`), *silently
continuing to give a stale-but-confident answer after the source document
changed* is close to the worst-case failure mode: it looks exactly as
confident as a correct answer, and there is no separate "did the source
change" signal a downstream check could catch it with. Under RAG, deleting
or re-embedding the stale chunk removes it from what can be retrieved at
all — the failure mode is structurally closed, not just mitigated.

**Fine-tuning does not remove the hallucination risk either** — it just
relocates where fabrication can come from (the model still generates from
its own learned distribution, and can still fill gaps with plausible
invented specifics). It trades one hallucination surface for another while
giving up citability and cheap freshness, which is a strictly worse
trade for this project's requirements.

**Verdict:** rejected. (This also matches the standing portfolio non-goal
already recorded in the README — "no model training/fine-tuning" — but the
rejection above is reasoned independently of that governance rule, not
justified *by* it; the rule and the reasoning happen to agree.)

### C — Hybrid retrieval + generation (RAG)

Keyword search and vector (embedding) search both index the corpus;
results are fused (this spike used Reciprocal Rank Fusion); the top
passages are handed to a generation step that must ground its answer in
them and cite the source, or refuse.

**Why hybrid, not vector-only.** Vector search alone matched 100% recall@3
in this spike, so on this small, prose-heavy corpus it looks sufficient by
itself. But vector embeddings are comparatively weak at exact-match/rare-
token lookups — error codes, config keys, version numbers, exact function
names — precisely because semantic similarity models are trained to
generalise past exact tokens, not to memorise them. This spike's corpus
happened not to test that case (see RESULTS.md's "does not prove" section),
but it's a well-understood, structural gap in pure vector search, and
keyword search is exactly what closes it. Keeping both, fused, costs little
extra (Postgres full-text search is already available alongside pgvector in
the chosen stack) for a real robustness gain on query types this spike
didn't happen to sample.

**Why this fits the failure-cost profile better than A or B.** RAG is the
only one of the three where (1) the corpus can change cheaply and the
system reflects the change immediately (unlike B), (2) a synthesized,
citable answer is possible at all because generation is explicitly
conditioned on retrieved, inspectable passages rather than opaque weights
(unlike A's raw document list and B's non-citable weights), and (3) a
refusal decision has something concrete to be *based on* — the retrieved
passages themselves can be checked for whether they actually ground an
answer, which is what makes "cited or refused" achievable as a hard
invariant rather than a hope.

**What RAG does not solve by itself — recorded honestly.** This session's
spike Finding 2 (`RESULTS.md`) found that retrieval confidence alone is not
a safe refusal signal: a topically-adjacent-but-wrong query scored inside
the same similarity range (0.701) as genuinely correct retrievals
(0.706–0.848). RAG's retrieval step gives you something to check groundedness
*against* — it does not automatically check it. That check (a groundedness/
entailment verification between the retrieved passage and the generated
answer) is additional design work for Session 2+ (`03-architecture.md`),
not something choosing RAG solves for free. This is stated here so the
decision below isn't oversold as a complete answer to the refusal problem.

## Decision

**Option C — hybrid retrieval (keyword OR-semantics + vector, fused) with
generation grounded in the retrieved passages, citation-or-refusal as a
hard invariant.** Not vector-only, not keyword-only, not fine-tuning.

## Trade-offs accepted

- More moving parts than either alternative alone: two indexes to
  maintain (keyword + vector), a fusion step, and — per Finding 2 — a
  groundedness check beyond retrieval score that still has to be designed.
  This is accepted because A and B were each rejected for reasons specific
  to this project's requirements (vocabulary-boundedness for A; staleness
  and non-citability for B), not because C was assumed superior by default.
- RAG's answer quality is bounded by retrieval quality — if the right
  passage is never retrieved, no amount of generation quality recovers it.
  This is why retrieval recall is success metric #1 in `00-project-brief.md`
  and why the CI-gated evaluation harness (Session 5, Verification &
  Testing) exists as a deep phase rather than an afterthought.

## Consequences

- The evaluation harness (Session 5) must test retrieval recall and
  refusal correctness as two genuinely separate metrics — Finding 2 shows
  they are not the same thing and a system can score well on one while
  failing the other.
- Session 2+'s architecture must include an explicit groundedness/
  entailment check between retrieved passage and generated answer as part
  of the refusal decision — a fixed threshold on retrieval similarity score
  is ruled out by this session's measured evidence, not by preference.
- Ingestion must support incremental re-embedding of individual changed
  documents (the freshness advantage over fine-tuning is only real if the
  implementation actually does cheap incremental updates rather than
  periodic full reindexes).

## Revisit triggers

- If the target corpus turns out to be effectively static (rare document
  changes, e.g. a frozen legal archive) for a specific deployment, the
  freshness argument against fine-tuning weakens for that deployment —
  worth a note in `08-deployment-and-operations.md` if it comes up, not a
  reason to reopen this decision for the project generally.
- If a future evaluation run (Session 5, on a realistic-scale corpus) shows
  vector-only matching hybrid's recall with no measurable gap on
  exact-token queries either, the added complexity of maintaining two
  indexes should be reconsidered — this spike's small corpus could not
  actually test that gap (see RESULTS.md), so the hybrid decision should be
  re-examined against real evidence once it exists, not left as permanent
  on the strength of a plausibility argument alone.
