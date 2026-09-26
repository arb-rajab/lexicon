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

**Real instance-level authentication, per ADR-0005.** Every endpoint below
requires an authenticated request; there is no unauthenticated/public
surface in v1 (unlike `privacy-forge`'s public DSAR portal — this product
has no equivalent external, unauthenticated actor per its stakeholder
model). A caller authenticates by registering (`POST /api/v1/auth/register`)
or logging in (`POST /api/v1/auth/login`) with a username/password, and
receives a signed session token (JWT) to present as
`Authorization: Bearer <token>` on every subsequent request. This is a
real, cryptographically verified identity boundary — not a trusted-header
convention a caller can spoof.

**History, for context on why this looks different from earlier sessions'
documentation of this section:** T-04's ownership enforcement
(`lexicon.api.ownership`) was built, correctly, against a caller identity
sourced from a client-supplied `X-User-Id` header, on the stated assumption
that a real deployment would terminate and verify that header at an
external, trusted reverse-proxy/gateway boundary before traffic reached
this service. That gateway was never built, in dev or in prod compose —
this application has always been the network edge in every deployable form
of this stack. The result was a full, live-reachable impersonation
vulnerability (any caller could set `X-User-Id: <anyone>` and be treated as
that person by every ownership check). **ADR-0005 closes this**: `X-User-Id`
is no longer read anywhere in the application. `GET /api/v1/corpora` remains
scoped to the caller's own corpora, exactly as before — only the source of
the caller's identity changed, from an unverified header to a verified
token's `sub` claim.

### Auth endpoints

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Create an account and receive a session token | `{ "username": string, "password": string }` | `201` `{ "access_token": string, "token_type": "bearer", "username": string }`; `409` `username_taken`; `429` `rate_limited` with `Retry-After` (global instance-wide window, not per-username — see below) |
| `POST` | `/api/v1/auth/login` | Authenticate and receive a session token | `{ "username": string, "password": string }` | `200` `{ "access_token", "token_type", "username" }`; `401` `invalid_credentials` (identical body *and* identical response time for unknown username vs. wrong password — see below); `429` `rate_limited` (T-12) with `Retry-After` |
| `GET` | `/api/v1/auth/me` | Confirm the caller's own identity | — (bearer token) | `200` `{ "username": string }` |

**On "no username enumeration":** this guarantee applies to `/login`
specifically, and to both its response body and its timing — a prior
version of this endpoint returned the identical `401 invalid_credentials`
body for both cases but only ran the ~600,000-iteration PBKDF2 comparison
when the username existed, so the *unknown-username* case was measurably
faster; that timing gap was itself a username-enumeration oracle even
though the response body never differed. Fixed by always running the
comparison (against a fixed dummy hash when no user row exists) so the
two cases cost the same regardless of outcome.

This guarantee does **not** extend to `/register`: a `409 username_taken`
response is an inherent, unavoidable signal that the submitted username is
already registered — that is what the endpoint's job (rejecting duplicate
usernames) requires it to reveal, not a side-channel to close. Treat this
as an accepted, standard trade-off of the registration flow itself, not an
open enumeration gap of the kind `/login` closes.

Every other endpoint below requires `Authorization: Bearer <token>`;
missing or invalid (unsigned, forged, expired, wrong-algorithm) → `401`
`unauthenticated`. `{corpus_id}`-scoped endpoints additionally check the
verified caller against `CORPUS.owner_id` (mismatch → `403`; nonexistent
corpus → `404`) exactly as T-04 originally specified.

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
  returned as `429` with a `Retry-After` header — **implemented this
  session** (`lexicon.api.rate_limit`, T-05), alongside a second, separate
  daily per-corpus spend-ceiling circuit breaker (also `429`, distinct
  error code `spend_ceiling_exceeded`, same `Retry-After` contract): the
  per-minute limit stops a fast burst, the daily ceiling stops
  slow-and-steady abuse that never trips it. Both gate the query endpoint
  *before* any real LLM call, and both fail open on a Redis outage
  (an availability tradeoff, not a correctness invariant — see the
  module's docstring). No rate limit on ingestion endpoints in v1 beyond
  the implicit queue-depth backpressure of the ingestion worker —
  ingestion doesn't carry the same per-request LLM cost risk that made
  query-path rate limiting a real cost-control requirement; it does now
  have a `413` file-size bound (T-06, `lexicon.api.documents`), also
  implemented this session — previously documented in this file but not
  enforced anywhere in code.

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
