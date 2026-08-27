# Scope and Non-Goals
> Purpose: prevent scope creep by writing down what this will never do
> Project: lexicon (public)
> Last updated: 2026-08-27

## MVP boundary (in scope)

A reviewer-checkable list of what v1 actually delivers. Nothing here is
built yet (Session 1 is discovery, not implementation) — this is the
target Session 2+ builds against, derived from `00-project-brief.md` and
the feasibility spike's findings.

- [ ] **Ingestion:** upload a bounded set of text-based documents (plain
      text, Markdown, PDF-text-layer) into a named corpus; chunk them
      (heading/section-aware, as the spike did) and store chunks with
      provenance (source document, section/heading, position).
- [ ] **Incremental re-indexing:** re-embedding a single changed or added
      document does not require reprocessing the whole corpus — this is
      the concrete mechanism behind the "cheap freshness" claim in
      `00b-rag-vs-alternatives.md` versus fine-tuning; without it, that
      claim would be aspirational rather than real.
- [ ] **Hybrid retrieval:** Postgres full-text search (OR-semantics —
      `00b-rag-vs-alternatives.md` and the spike found AND-semantics
      (`plainto_tsquery`) unusable, 0% recall@3) fused with pgvector
      cosine similarity search, via a ranked fusion method (RRF or
      equivalent).
- [ ] **Grounded generation with mandatory citation:** an answer is only
      emitted alongside the specific passage(s) it was grounded in.
- [ ] **Refusal path:** the system declines to answer when the retrieved
      passages don't actually ground an answer. Per the spike's Finding 2,
      this must be a groundedness/entailment check between the retrieved
      passage and the candidate answer — a bare similarity-score threshold
      is explicitly ruled insufficient by measured evidence, not by
      preference.
- [ ] **CI-gated evaluation harness:** a committed, golden-dataset-driven
      suite that measures retrieval recall and refusal correctness
      (success metrics #1–#3 in `00-project-brief.md`) automatically on
      every change — this is the Verification & Testing deep phase's
      central deliverable.
- [ ] **Adversarial prompt-injection test suite:** committed tests that
      attempt to subvert the citation-or-refusal invariant via injected
      instructions inside document content or user queries, treated as a
      real security control, not an assumption.
- [ ] **Minimal web UI:** ask a question against a corpus, see the answer
      with its citation(s) or an explicit refusal message — enough to
      demonstrate the invariant end-to-end, not a polished product surface.

## Explicit non-goals

| Non-goal | Why excluded | Would reconsider if |
|---|---|---|
| Model training or fine-tuning | Full comparison in `00b-rag-vs-alternatives.md`: fine-tuning cannot cheaply track a changing corpus, cannot produce real citations (facts are diffused across weights, not tied to a retrievable passage), and does not remove hallucination risk — it relocates it. Also outside the two-slot learning budget (`00a-ledger-confirmation.md`), which is spent on RAG evaluation methodology and LLM guardrails. | A specific deployment has a genuinely frozen, non-changing corpus *and* a measured RAG-based approach demonstrably underperforms on it — would need its own ledger conversation (a third learning objective), not a quiet local decision. |
| Agentic tool use (the model taking actions, calling external tools/APIs beyond retrieval) | Every action surface is a place a wrong-but-confident decision can cause real-world harm, which is precisely the failure mode this project exists to prevent (`00-project-brief.md`, "cost of a wrong answer"). Retrieval is a read-only, inspectable step; arbitrary tool use is not. | The product's scope deliberately expands beyond read-only Q&A — a decision big enough to need a new ledger row/portfolio conversation, not an incremental feature add. |
| Multi-modal input (images, audio, video, scanned-image PDFs requiring OCR) | The MVP's ingestion path (above) is text-only; multi-modal retrieval and grounding is a materially different, unbudgeted problem (different embedding models, different chunking, different citation semantics — "cite this region of this image" is not "cite this passage"). Not free to add on top of the current learning budget. | A specific, demonstrated user need for image/audio-grounded citation arises and is worth its own learning-budget slot in a future session's ledger review. |
| General-purpose chatbot (open-ended conversation not grounded in a supplied corpus) | The product's entire value proposition is "answers restricted to what a specific document set actually supports." An open-ended chat mode would let users get ungrounded answers from the same system that promises grounding elsewhere — undermining the "cited or refused" invariant by giving it an escape hatch. | Never, for this product's identity — an open-ended mode would be a different product, not a feature of this one. |
| LLM gateway / general model-proxy product | Scope is a specific application (document Q&A), not infrastructure for routing arbitrary LLM traffic. Building a generic gateway is a different, much larger problem with its own portfolio slot. | Never for this repository; would be a separate portfolio entry if ever pursued. |
| Autonomous action-taking (the system acting on its own conclusions without a human in the loop) | Same reasoning as agentic tool use, specifically for the "who is accountable for a wrong answer" question in `00-project-brief.md`'s stakeholder section — accountability requires a human deciding whether to act on a cited answer, not the system acting for them. | Not anticipated; would require rethinking the accountability model from scratch. |
| Retrieval-quality guarantees on unbounded or very-large corpora without harness evidence at that scale | This session's feasibility spike (`docs/spikes/session1-hybrid-retrieval/RESULTS.md`) explicitly and honestly does not prove retrieval quality beyond a 108-chunk/9-document corpus, and says so in its own "does not prove" section. Claiming otherwise would be asserting an untested guarantee. | Once the Session 5 CI-gated evaluation harness produces real recall numbers on a realistic-scale corpus (target: 500+ chunks/20+ documents per `00-project-brief.md` success metric #1), this row should be updated with the actual measured boundary, not removed on faith. |
| Similarity-threshold-only refusal (treating retrieval confidence as sufficient grounds to answer) | Measured, not assumed: the spike's Finding 2 found a topically-adjacent-but-wrong query scoring inside the same similarity range (0.701) as genuinely correct retrievals (0.706–0.848). A fixed-threshold refusal gate would have answered it confidently and wrongly. | If a future groundedness-check design (Session 2+ architecture) is proven, via the eval harness, to be reliably approximated by a similarity threshold alone on this project's actual corpora — i.e. the extra check is shown to add no measured refusal-precision benefit — this could be simplified. Not assumed in advance. |

## Deferred to backlog

- Multi-corpus / multi-tenant support (one corpus per deployment is the
  MVP assumption; see `00-project-brief.md`'s business assumptions).
- Answer streaming, conversational follow-up questions with retained
  context, and any UI polish beyond the minimal demonstration surface
  listed in the MVP boundary.
- Non-English corpora / multilingual retrieval and generation.
- Vector-only or keyword-only "fast path" optimisations — not worth
  building until the Session 5 evaluation harness shows hybrid's extra
  cost isn't earning its keep (see `00b-rag-vs-alternatives.md`'s revisit
  triggers).

## Definition of "v1 complete"

Every unchecked box in "MVP boundary (in scope)" above is checked and
demonstrated working end-to-end (not merely present in code), the CI-gated
evaluation harness is committed and passing against its defined success
metrics (`00-project-brief.md`), and the adversarial prompt-injection suite
is committed and passing with zero successful injections. None of the rows
in "Explicit non-goals" have been silently absorbed into scope without a
recorded reconsideration decision.
