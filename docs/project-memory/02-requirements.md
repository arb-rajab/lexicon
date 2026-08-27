# Requirements
> Purpose: testable statements of what the system must do and how well
> Project: lexicon (public)
> Last updated: 2026-08-27
> Depth: baseline (this repo's two deep SDLC phases are Discovery & Planning
> and Verification & Testing — see `00a-ledger-confirmation.md`). Requirements
> and Architecture are produced together this session per the Session 1
> handoff, at real reasoning depth, but are not one of the two deep-evidence
> phases themselves.

## Roles and permissions matrix

There is no multi-tenant or multi-role authorisation model in v1 — the MVP
boundary (`01-scope-and-non-goals.md`) is a single-corpus, single-deployment
tool, and "who can log in and administer this instance at all" is an
operator/deployment concern, not a product feature this session designs.
This table records the two functional roles the product itself
distinguishes, not an access-control system.

| Role | Can | Cannot |
|---|---|---|
| **Corpus owner/admin** | Upload, re-upload (incremental re-index), and remove documents from the corpus; view ingestion status; view query logs (audit trail — see Data classification) | Bypass the citation-or-refusal invariant for their own queries — an admin's question is answered under the same refusal rules as anyone else's, since accountability for a wrong answer (`00-project-brief.md`'s stakeholder section) requires the invariant to hold uniformly |
| **Knowledge worker (end user)** | Ask questions against a corpus; receive a cited answer or an explicit refusal; view their own query history | Upload/modify/remove corpus documents; view other users' raw query logs (see Data classification — query logs are operator-visible for audit, not end-user-visible to each other) |

Instance-level authentication (who may access this deployment at all) is
deferred to `08-deployment-and-operations.md` as an operator concern — not
tracked here as a functional requirement, consistent with the MVP boundary's
"minimal web UI... enough to demonstrate the invariant end-to-end" framing.

## User stories with acceptance criteria

### Ingestion

**US-001 — Upload a document into a corpus**
As a corpus owner, I want to upload a text-based document into a named
corpus, so that its content becomes queryable.
**Acceptance criteria:**
- Given a supported file type (plain text, Markdown, or a PDF with a text
  layer), when I upload it to a corpus, then the document is chunked
  heading/section-aware (matching the spike's method), each chunk is stored
  with provenance (source document, section/heading, position), and both a
  keyword (full-text) index entry and a vector embedding are created per
  chunk.
- Given an unsupported file type (e.g. a scanned-image PDF with no text
  layer, an audio file), when I attempt to upload it, then the system
  rejects it with an explicit, specific error — not a silent partial
  ingest.

**US-002 — Re-upload a changed document without reprocessing the corpus**
As a corpus owner, I want updating one document to only re-embed that
document, so that keeping the corpus current is cheap (this is the concrete
mechanism behind the "cheap freshness" claim against fine-tuning in
`00b-rag-vs-alternatives.md` — without it, that claim is aspirational, not
real).
**Acceptance criteria:**
- Given a document already exists in a corpus, when I upload a new version
  of it, then only that document's chunks are deleted and replaced — no
  other document in the corpus is re-chunked, re-embedded, or re-indexed.
- Given a document is removed from a corpus, when the removal completes,
  then none of its chunks are retrievable by any subsequent query, and this
  takes effect before the next query is served (not eventually).

### Asking a question

**US-003 — Ask a question and receive a citation-backed answer**
As a knowledge worker, I want to ask a natural-language question against a
corpus, so that I get a synthesized answer I can act on without re-reading
the source documents myself.
**Acceptance criteria:**
- Given a corpus contains the information needed to answer a question, when
  I submit the question, then I receive an answer where every factual claim
  is attached to a specific cited chunk (source document + section), and
  that citation has passed the independent groundedness verification step
  (ADR-0001) before being shown to me.
- Given the retrieved passages do not actually support a full answer, when
  generation and verification run, then no partial or hedged answer is
  shown — the system returns the explicit refusal path (US-004) instead of
  a lower-confidence answer.

**US-004 — Receive an explicit refusal when the corpus doesn't answer the question**
As a knowledge worker, I want an honest "the supplied documents don't answer
this" instead of a fluent guess, so that I never act on an answer that
looks confident but isn't grounded (`00-project-brief.md`, "cost of a wrong
answer").
**Acceptance criteria:**
- Given a query with no true answer in the corpus — including a
  **topically-adjacent-but-absent** query (per spike Finding 2, e.g. a
  question about a feature the docs never cover but that shares vocabulary
  with something the docs do cover) — when the query is processed, then the
  system refuses rather than answering, regardless of how high the raw
  retrieval similarity score was.
- Given the generator itself signals it cannot support an answer from the
  retrieved passages (self-refusal, ADR-0001), when this occurs, then the
  system returns the refusal path directly without invoking the
  verification step (nothing to verify).
- Given the generator produces a candidate answer but the independent
  verification step finds any cited claim is not entailed by its cited
  passage, when this occurs, then the draft answer is discarded and the
  refusal path is returned — the unverified draft is never shown to the
  user, even partially.

### Audit and accountability

**US-005 — Trace how an answer or refusal was reached**
As the accountable party for a wrong answer (`00-project-brief.md`'s
stakeholder model), I want the system to log what was retrieved, generated,
and verified for each query, so that a disputed answer can be traced rather
than trusted blindly.
**Acceptance criteria:**
- Given any query is processed (answered or refused), when it completes,
  then a log entry is written recording: the query text, the retrieved
  chunk IDs and their fusion ranks, the generated answer (if any), the
  verification verdict per cited claim, and the final answered/refused
  decision.
- Given a query log entry exists, when queried by a corpus owner, then it is
  retrievable for audit purposes (see Data classification for retention).

## Functional requirements

| ID | Requirement | Priority | Verified by |
|---|---|---|---|
| FR-001 | Ingestion accepts plain text, Markdown, and PDF-text-layer documents; rejects unsupported types explicitly | Must | US-001, feature test |
| FR-002 | Documents are chunked heading/section-aware; each chunk stores provenance (source document, section, position) | Must | US-001, feature test |
| FR-003 | Each chunk gets both a full-text search index entry and a vector embedding at ingest time | Must | US-001, feature test |
| FR-004 | Re-uploading or removing a document only affects that document's chunks — no full-corpus reprocessing | Must | US-002, feature test |
| FR-005 | Keyword retrieval uses OR-semantics full-text search (`to_tsquery` joined with `\|`, ranked by `ts_rank`) — AND-semantics (`plainto_tsquery`) must not be used anywhere in the retrieval path | Must | spike Finding 1; code-level guard (Session 4/5, see `12-session-handoff.md` risk note) |
| FR-006 | Retrieval fuses keyword and vector result lists via Reciprocal Rank Fusion (or an equivalent ranked-fusion method) before passing candidates to generation | Must | US-003, feature test |
| FR-007 | Generation is conditioned only on retrieved passages, must cite specific chunk IDs for every factual claim, and must self-refuse when passages don't support an answer | Must | US-003, US-004, ADR-0001 |
| FR-008 | An independent groundedness/entailment verification step checks each cited claim against its cited passage text before an answer is released | Must | US-003, US-004, ADR-0001 |
| FR-009 | An answer is shown to the user only if every cited claim passes verification; otherwise the refusal path is returned, discarding the draft answer entirely | Must | US-004, ADR-0001 |
| FR-010 | Refusal is never based on a bare retrieval-similarity threshold alone | Must | spike Finding 2, ADR-0001 |
| FR-011 | Every query (answered or refused) is logged with: query text, retrieved chunk IDs + fusion ranks, generated answer (if any), per-claim verification verdicts, final decision | Must | US-005, feature test |
| FR-012 | Corpus owners can view query logs for their corpus for audit purposes | Must | US-005, feature test |
| FR-013 | A minimal web UI supports: selecting a corpus, submitting a question, viewing an answer with citations or an explicit refusal message | Must | US-003, US-004, e2e test |
| FR-014 | The system supports exactly one corpus concept without cross-corpus retrieval leakage — a query against corpus A never retrieves chunks from corpus B | Must | Architecture review; feature test |

## Non-functional requirements (numeric targets only)

| ID | Category | Requirement | Target | Verified by |
|---|---|---|---|---|
| NFR-001 | Retrieval quality (regression floor) | Recall@3 on the existing spike corpus (108 chunks / 9 documents, `docs/spikes/session1-hybrid-retrieval/`) using OR-semantics keyword, vector, and hybrid retrieval — must not regress below the spike's measured baseline once implemented as application code | 100% recall@3 (matching spike baseline) | Regression test using the committed spike corpus as fixture data, Session 4/5 |
| NFR-002 | Retrieval quality (production target) | Recall@3 on a realistic-scale golden query set (target corpus: 500+ chunks / 20+ documents, per `00-project-brief.md` success metric #1) | **Not set here** — no fabricated number. To be measured and recorded by the Session 5 CI-gated evaluation harness against real data at that scale; this NFR row is a placeholder for that measurement, not a target invented ahead of evidence | CI-gated evaluation harness, Session 5 |
| NFR-003 | Refusal correctness | Refusal recall on a labeled negative-query set that includes topically-adjacent-but-absent queries (spike Finding 2 class), not just fully-unrelated queries | **Not set here** — same reasoning as NFR-002; this is the metric ADR-0001's verification step exists to make measurable, not a number to guess before the mechanism has been evaluated | CI-gated evaluation harness, Session 5 |
| NFR-004 | Citation accuracy | Of answers given (not refused), fraction where a human reviewer confirms the cited passage supports the stated answer, spot-checked | **Not set here** — same reasoning; this directly measures the verification step's real-world accuracy, which ADR-0001 explicitly states is unmeasured until Session 5 | Spot-check review process, Session 5 |
| NFR-005 | Latency (provisional working budget) | End-to-end query latency, p95, for an answered (non-refused) query — accounting for retrieval + generation + independent verification (2 LLM calls, ADR-0001) | ≤ 6 seconds p95 (provisional; a working design budget, not a measured value — no generation surface exists yet to measure against, matching `00-project-brief.md` success metric #4's own honesty note). Revisit once a real provider/model is wired up in Session 4 | Load test once generation exists, Session 4/5 |
| NFR-006 | Latency (refused query) | End-to-end latency for a self-refused query (generation only, no verification call needed) | ≤ 4 seconds p95 (provisional, same caveat as NFR-005) | Load test, Session 4/5 |
| NFR-007 | Cost control | Per-query LLM spend budget (generation + verification combined), to bound runaway cost for a self-hosted operator | **Not set as a dollar figure here** — no provider contract or real pricing has been wired up yet (see Architecture's open item on API credentials). Cost-control *mechanisms* (cheaper model tier for verification, bounded top-k chunks, prompt caching) are architectural requirements now (`03-architecture.md`); the numeric budget itself is a Session 4 implementation decision made against real pricing | Cost tracking once a real provider is integrated, Session 4 |
| NFR-008 | Ingestion performance | Time to ingest and index a single document of typical size (~10 pages / ~50 chunks) | ≤ 30 seconds p95 | Feature/load test, Session 4 |
| NFR-009 | Security | Critical/high findings from CI-gated static analysis (matching the existing CI pipeline from Session 0) | 0 | CI gate, every PR from implementation onward |
| NFR-010 | Prompt-injection resistance | Pass rate on the adversarial prompt-injection test suite (`01-scope-and-non-goals.md` MVP boundary item) | 0 successful injections in the committed suite | Adversarial test suite, Session 5 |

**Why NFR-002 through NFR-004 and NFR-007 are deliberately left without a
fixed number:** the task that produced this document was explicit that
retrieval-quality targets must be "informed by Session 1's real spike
numbers, not invented ones." The spike's real numbers exist only for a
9-document toy corpus (100% recall@3) and say, in their own "does not
prove" section, that this is not evidence of production-scale quality.
Writing a specific percentage for NFR-002–004 or a specific dollar figure
for NFR-007 without that evidence would be exactly the fabrication this
document is instructed to avoid. These rows exist as placeholders with a
named owner (Session 5's harness, Session 4's real pricing) rather than
being silently omitted.

## Data classification

| Data element | Classification | Retention | Encryption | Lawful basis |
|---|---|---|---|---|
| Document content (uploaded corpus files) | Confidential — organisation-owned, per `00-project-brief.md`'s business assumption that the corpus is "owned/controlled by the deploying organisation" | Retained until explicitly removed by a corpus owner; no automatic expiry (the corpus is meant to be authoritative and current, not ephemeral) | At rest (object storage / DB) | Not modeled as personal data by this system — if an operator's corpus contains personal data, that operator's own data-governance obligations apply; this product does not classify or manage that on their behalf (out of scope, see `01-scope-and-non-goals.md`) |
| Chunk text + provenance (source doc, section, position) | Same classification as its source document | Deleted immediately on document removal or re-upload (FR-004) | At rest | Same as source document |
| Chunk embeddings (vector representations) | Same classification as source content — embeddings can leak information about source text (embedding-inversion risk is a known, general property of dense embeddings), so treating them as "just numbers" would understate their sensitivity | Deleted immediately alongside their chunk (FR-004) | At rest | Same as source document |
| Query text (user questions) | Confidential — may reveal what an internal team is worried about or investigating (e.g. a compliance question), independent of the corpus's own sensitivity | Retained per query-log retention policy (operator-configurable; no default assumed here — a deployment concern for `08-deployment-and-operations.md`) | At rest | Legitimate interest — necessary for the audit/accountability requirement (US-005, FR-011/012) |
| Generated answers | Same classification as the source content they cite, since they are derived from it | Same as query log retention (answers are stored as part of the query log entry, not separately) | At rest | Same as query text |
| Query log entry (query + retrieved chunk IDs + verification verdicts + decision) | Confidential, elevated importance as an audit/evidentiary record — this is the artifact that lets a wrong answer be traced (US-005) | Retained per operator-configured policy; not auto-deleted on a schedule assumed by this document (an operations decision, not a product-behavior one) | At rest | Legitimate interest — accountability for the "who is responsible for a wrong answer" stakeholder question |
| LLM provider API credentials | Restricted/secret | N/A — configuration, not data | At rest (secrets manager / env, never logged) | N/A |

## Integration requirements

- **LLM provider API** (generation + verification calls) — the single
  required external integration. Provider/model choice, cost-control
  approach, and the open item that real credentials do not yet exist in
  this environment are covered in `03-architecture.md`.
- **No other inbound or outbound integrations required for v1** — ingestion
  is a direct upload (no connector framework, unlike `privacy-forge`'s
  connector contract; this product has no equivalent need, per
  `01-scope-and-non-goals.md`'s "agentic tool use" non-goal, which rules out
  the system calling external tools/APIs beyond the one LLM provider call).

## Constraints

- Must not answer without a citation that has passed independent
  verification (ADR-0001) — this is the hard invariant the entire
  requirements set exists to make checkable, not a preference.
- Must not use AND-semantics full-text search (`plainto_tsquery`) anywhere
  in the retrieval path (FR-005, spike Finding 1).
- Must not treat retrieval similarity score as sufficient grounds to answer
  (FR-010, spike Finding 2, ADR-0001).
- Single-corpus-per-query isolation (FR-014) — no cross-corpus retrieval
  leakage, even though multi-corpus/multi-tenant support itself is deferred
  to backlog (`01-scope-and-non-goals.md`).
- Stack is fixed: FastAPI (Python 3.12), Next.js 15 (App Router),
  PostgreSQL + pgvector, Redis, S3-compatible object storage (MinIO) — per
  `00a-ledger-confirmation.md`; this document introduces no new technology
  beyond the two already-budgeted learning objectives.
