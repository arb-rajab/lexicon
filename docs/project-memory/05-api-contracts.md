# API / Event Contracts
> Purpose: the interface others depend on
> Project: lexicon (public)
> Last updated: 2026-08-27

## Style and rationale

REST over JSON, versioned under `/api/v1/`. No GraphQL, no gRPC — a small,
single-consumer API surface (the project's own Next.js frontend is the only
client planned for v1, per `01-scope-and-non-goals.md`'s "no LLM gateway /
general model-proxy product" non-goal, which also rules out designing this
as a general-purpose API product for third-party consumers) does not
justify the added complexity either would bring. This matches
`privacy-forge`'s REST choice for the same underlying reason: pick the
simplest style that fits an actually-scoped consumer set, not the most
general one available.

## Authentication and authorisation model

Instance-level authentication (who may access a deployment at all) is an
operator/deployment concern, not designed in this session — see
`02-requirements.md`'s Roles and permissions matrix note and
`08-deployment-and-operations.md` (not yet written). This document assumes
a single authenticated session type per the two functional roles
identified in `02-requirements.md` (corpus owner, knowledge worker) and
does not invent a specific auth mechanism (session cookie vs. bearer token)
ahead of that operational decision. Every endpoint below requires an
authenticated request; there is no unauthenticated/public surface in v1
(unlike `privacy-forge`'s public DSAR portal — this product has no
equivalent external, unauthenticated actor per its stakeholder model).

## Endpoints / schema summary

### Corpus management

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `POST` | `/api/v1/corpora` | Create a named corpus | `{ "name": string }` | `201` `{ "id": uuid, "name": string, "created_at": timestamp }` |
| `GET` | `/api/v1/corpora` | List corpora | — | `200` `[{ "id", "name", "created_at" }]` |
| `GET` | `/api/v1/corpora/{corpus_id}` | Get corpus detail | — | `200` `{ "id", "name", "created_at", "document_count" }` |

### Ingestion (FR-001–FR-004)

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `POST` | `/api/v1/corpora/{corpus_id}/documents` | Upload a document (create or re-upload by matching filename) | `multipart/form-data`: file | `202` `{ "document_id": uuid, "status": "queued" }` — chunking/embedding happens asynchronously (ingestion worker, `03-architecture.md`) |
| `GET` | `/api/v1/corpora/{corpus_id}/documents/{document_id}` | Ingestion status and metadata | — | `200` `{ "id", "source_filename", "version", "status": "queued"\|"processing"\|"ready"\|"failed", "chunk_count", "uploaded_at" }` |
| `DELETE` | `/api/v1/corpora/{corpus_id}/documents/{document_id}` | Remove a document (FR-004) | — | `204` — chunks deleted synchronously before response; original file removed from object storage |
| `GET` | `/api/v1/corpora/{corpus_id}/documents` | List documents in a corpus | — | `200` `[{ "id", "source_filename", "version", "status", "chunk_count" }]` |

### Query (FR-006–FR-013, ADR-0001)

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `POST` | `/api/v1/corpora/{corpus_id}/query` | Ask a question against a corpus | `{ "question": string }` | `200` — see response shape below. Synchronous: the response is only returned once retrieval, generation, and (if applicable) verification have all completed — no polling, since the latency budget (NFR-005/006) is designed around a single request/response cycle |

**Query response shape** — the schema directly reflects the retrieve →
generate → verify → decide flow (`03-architecture.md`'s Key flows):

```json
{
  "query_log_id": "uuid",
  "answered": false,
  "answer": null,
  "citations": [],
  "refusal_reason": "self_refused" ,
  "retrieved_chunk_count": 3
}
```

or, when verification passes:

```json
{
  "query_log_id": "uuid",
  "answered": true,
  "answer": "string, with inline citation markers",
  "citations": [
    { "chunk_id": "uuid", "document_id": "uuid", "source_filename": "string", "section_heading": "string", "claim_text": "string" }
  ],
  "refusal_reason": null,
  "retrieved_chunk_count": 5
}
```

`refusal_reason` is one of `"self_refused"` (the generator declined —
FR-007) or `"verification_failed"` (a candidate answer existed but at
least one cited claim failed entailment — FR-008/FR-009); a third value,
`"no_candidates_retrieved"`, covers the zero-retrieval short-circuit
(`03-architecture.md`'s Failure handling section) so a client can
distinguish "nothing relevant was even found" from "something relevant was
found but couldn't be verified" — a distinction useful to a corpus owner
diagnosing whether to add missing documentation versus investigate a
verification false-refusal.

### Query log / audit (FR-011, FR-012, US-005)

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/api/v1/corpora/{corpus_id}/query-logs` | List query log entries (corpus owner only) | Query params: `limit`, `cursor` (see Pagination below) | `200` `{ "items": [{ "id", "query_text", "answered", "refusal_reason", "created_at" }], "next_cursor": string\|null }` |
| `GET` | `/api/v1/corpora/{corpus_id}/query-logs/{query_log_id}` | Full audit detail for one query — retrieved chunks with fusion ranks, generated answer, per-claim verification verdicts | — | `200` — full `QUERY_LOG` + `RETRIEVED_CHUNK[]` + `CITATION_VERDICT[]` per `04-data-model.md`'s entities, the literal data behind US-005's traceability requirement |

## Error model

Standard HTTP status codes with a consistent JSON error body:
`{ "error": { "code": string, "message": string, "field": string|null } }`.

| Status | Used for |
|---|---|
| `400` | Malformed request body |
| `401` | Unauthenticated |
| `403` | Authenticated but not authorised for this corpus/action (e.g. knowledge worker attempting document upload) |
| `404` | Corpus/document/query-log not found (or not visible to the caller) |
| `413` | Uploaded file exceeds the configured size limit |
| `415` | Unsupported document type (FR-001 — plain text/Markdown/PDF-text-layer only; explicit rejection, not silent partial ingest) |
| `422` | Well-formed but semantically invalid request (e.g. empty question text) |
| `429` | Rate limit exceeded (NFR-007 cost-control) |
| `502` | LLM provider call failed (generation or verification) — the query fails closed per `03-architecture.md`'s Failure handling; the response body distinguishes this from a normal refusal via a distinct error code, since a provider outage is an operational failure, not a "the documents don't answer this" product refusal, and a client should treat the two differently (retry vs. don't retry) |
| `503` | Ingestion or query pipeline dependency (Postgres, Redis) unavailable |

**A `502`/failed generation or verification call is never represented as a
successful `200` response with `refusal_reason: "verification_failed"`** —
conflating "the system checked and correctly declined" with "the system
couldn't complete the check" would hide operational failures inside what
looks like the product working as designed. This distinction is a direct
consequence of ADR-0001's fail-closed requirement being observable at the
API layer, not just internally.

## Versioning and deprecation policy

`/api/v1/` prefix now; a breaking change to the query response shape (e.g.
changing `refusal_reason`'s enum values) would require a `/api/v2/` prefix
rather than an in-place breaking change, since the Web UI is the only
planned consumer today but the response shape is also the literal contract
`04-data-model.md`'s audit trail is built to support — breaking it silently
would undermine the traceability guarantee US-005 exists to provide. No
formal deprecation window is defined yet (single-consumer API, no external
integrators in v1); revisit if/when a public API surface is ever
considered, which is not planned.

## Idempotency, pagination, rate limits

- **Idempotency:** document upload is keyed by `(corpus_id, filename)` —
  uploading the same filename again is treated as a re-upload (new
  `version`, FR-004's incremental re-index path), not a duplicate document.
  A client that retries an upload request after a network failure without
  changing the filename gets the same idempotent re-upload behavior rather
  than accumulating duplicate documents.
- **Pagination:** cursor-based (`limit`/`next_cursor`) on `GET
  /query-logs`, the only list endpoint expected to grow unbounded over a
  corpus's lifetime; document and corpus listing use simple unpaginated
  responses in v1, consistent with the MVP boundary's "bounded... document
  set" assumption (`01-scope-and-non-goals.md`) — pagination there is
  deferred, not designed away permanently.
- **Rate limits:** per-corpus query rate limiting (NFR-007, Redis-backed),
  returned as `429` with a `Retry-After` header. No rate limit on ingestion
  endpoints in v1 beyond the implicit queue-depth backpressure of the
  ingestion worker — ingestion doesn't carry the same per-request LLM cost
  risk that made query-path rate limiting a real cost-control requirement.

## Events published/consumed

- **Ingestion job** (`document.ingest`, internal — Redis queue, not a
  public event/webhook contract): `{ "document_id": uuid, "corpus_id": uuid,
  "object_storage_key": string }`, consumed by the ingestion worker
  (`03-architecture.md`). This is an internal implementation detail of the
  ingestion flow, not a contract external consumers depend on — unlike
  `privacy-forge`'s connector webhook contract (ADR-0004), `lexicon` has no
  external system that needs to observe or trigger these events, per
  `01-scope-and-non-goals.md`'s "agentic tool use" non-goal ruling out
  external tool/API integration beyond the one LLM provider call.
- No outbound webhooks or public event stream are planned for v1.
