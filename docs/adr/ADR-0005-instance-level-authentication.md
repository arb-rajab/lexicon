# ADR-0005 — Instance-Level Authentication: Real Login In the App, Not an Unbuilt Gateway

- **Date:** 2026-09-23
- **Status:** accepted

## Context

`lexicon.api.auth` (Session 4, T-04's enforcement work) was built on an
explicit, stated assumption, quoted verbatim from that module's own
docstring before this session:

> This module ... trusts a caller identity supplied via the `X-User-Id`
> header, and this application layer is responsible only for ... authorising
> that identity against a specific `corpus_id`, not for verifying who they
> are in the first place. This app cannot itself distinguish a header set by
> a trusted proxy from one set by the caller directly ... a real deployment
> must terminate `X-User-Id` at that trusted boundary before traffic reaches
> this service.

`05-api-contracts.md` and `06-security-threat-model.md` (T-12) repeated the
same assumption, each time correctly labeled as *deferred*, not *solved* —
Session 2 first named instance-level authentication as an operator/
deployment concern, and every session since carried it forward as an open
requirement on "whatever mechanism is eventually chosen," never as a gap
that had quietly become load-bearing.

**This session found that it had become load-bearing.** `docker-compose.yml`
(dev) and `docker-compose.prod.yml` (Session 7's own "production-shaped
stack, verified locally") both expose the `backend` service's port directly
to the host with nothing in front of it — no reverse proxy, no
`oauth2-proxy`, no gateway of any kind, in either file. Session 7's own
docstring in `docker-compose.prod.yml` explicitly reasoned about *not*
adding a reverse-proxy/TLS layer, on the grounds that no session had ever
committed to a public-facing instance — but that reasoning was never
connected back to the fact that the *authentication* boundary the API
contract had assumed would live at exactly that layer also did not exist.
The result, verified live against the running stack, not merely inferred
from reading the code: any HTTP client that can reach the backend at all —
which, in every deployable form of this stack today, is the same as "any
client that can reach it over the network at all" — can set
`X-User-Id: <any string>` and be treated as that identity by every
corpus-ownership check T-04 added. `lexicon.api.ownership.
require_owned_corpus` is correct, real authorisation logic; it was
authorising an attacker-chosen identity. This is a full, unauthenticated
impersonation vulnerability, not a "missing defense in depth" — it requires
no credential, no prior session, and no interaction with the victim.

The frontend's identity switcher (`frontend/lib/identity.tsx`,
`IdentityBar.tsx`) was a correct reflection of this same, then-believed-
external-to-the-app auth model at the time it was built — it is addressed
below as a consequence of this decision, not a separate defect.

## Options considered

### A — Re-document the assumption again, change nothing

Restate the "a real deployment terminates X-User-Id at a trusted boundary"
caveat somewhere more prominent (this ADR file itself, a bigger warning in
`auth.py`, a `06-security-threat-model.md` update marking T-12 "critical,
still open"). **Rejected outright.** This is the exact failure mode this
session's task exists to correct: the caveat was already stated, correctly,
in three separate documents, and remained true precisely because nothing
was ever built to make it stop being true. A fourth restatement of an
already-well-documented gap changes nothing about what a real request
against this stack can do today.

### B — Deploy a real OIDC reverse-proxy gateway (`oauth2-proxy` or equivalent) in front of the stack

Add `oauth2-proxy` (or Envoy with an OIDC filter) as a new service in both
compose files, sitting in front of `backend`, terminating and verifying
`X-User-Id` (or an equivalent trusted header it injects) before any request
reaches the FastAPI app — making `auth.py`'s original stated assumption
literally true instead of aspirational.

**For:** Matches the exact architecture `auth.py`'s original docstring
described; decouples authentication from the application entirely, which is
a real advantage if this API is ever meant to serve additional first-party
clients beyond the one Next.js frontend `05-api-contracts.md` already scopes
it to.

**Against, decisively for this project's actual shape:** `oauth2-proxy`
authenticates *against* something — a real OIDC identity provider (Google,
GitHub, Okta, a self-hosted Keycloak/Dex instance). This project has no
discovery-work-documented relationship with any external IdP, and standing
up a self-hosted one is not "adding a sidecar container," it is standing up
an entire second stateful subsystem (its own database or embedded store,
its own admin/user-provisioning flow, its own upgrade and backup surface) —
a materially larger addition than this task's scope, for a single-consumer
API `05-api-contracts.md` already explicitly ruled out designing as a
general-purpose product (`01-scope-and-non-goals.md`'s "no LLM gateway /
general model-proxy product" reasoning applies with equal force here: this
is not a project that has ever taken on being an identity platform either).
It also does not compose with this project's own, already-made, explicitly
reasoned TLS decision: `08-deployment-and-operations.md` deliberately
descopes TLS termination because no session has ever committed to exposing
this stack beyond localhost — but an OIDC gateway's redirect-based login
flow (the entire mechanism by which `oauth2-proxy` establishes a session)
depends on a real, stable callback URL and, for any non-toy IdP integration,
real HTTPS. Standing up the gateway container without also reversing the
TLS decision would produce a login flow that only plausibly works against
`localhost`, using OAuth app credentials checked into or generated fresh for
a disposable dev environment — solving the problem in form only, which is
the same "assumed, not real" failure mode as Option A, just with an extra
container around it. Rejected as disproportionate to, and not actually
compatible with, this project's current deployment shape.

### C — Real authentication inside the FastAPI application itself (chosen)

The application becomes its own identity provider for the one thing this
product actually needs: a caller can prove they are a specific account via a
password, and every subsequent request carries a signed, verifiable session
token that identity issued. Concretely: a real `AppUser` table
(username + salted/hashed password), `POST /api/v1/auth/register` and
`/login` issuing an HS256 JWT (`lexicon.security.tokens`) on successful
authentication, and `lexicon.api.auth.get_caller` rewritten to verify that
token — cryptographically, with a pinned algorithm — instead of reading
`X-User-Id` at all. `X-User-Id` is no longer read anywhere in the
application; sending it has zero effect on anything.

**For:** Actually closes the gap *today*, against the stack that actually
exists, with no new external dependency, no new stateful subsystem, and no
architectural precondition (a real IdP relationship, a stable public
callback URL) this project doesn't already have. Fully self-contained and
fully testable end-to-end through the real app (`tests/test_auth.py`) —
including the exact forged-header attack this ADR exists to close, run
against the code and proven to fail. Matches this project's `dev`/
`prod`-compose-only, no-cloud-deployment-yet deployment shape (confirmed
current per `08-deployment-and-operations.md` and this session's own
research) far better than Option B's gateway does. Symmetric HS256 signing
is sufficient and not a corner cut: this process is both the only issuer and
the only verifier of these tokens — there is no separate trusted gateway to
hand a public key to, so RS256/JWKS key distribution would add complexity
this deployment shape has no use for.

**Against:** This process is now both the identity provider and the
resource server — a real, if commonly accepted, coupling of concerns Option
B avoids. No MFA, social login, or password-reset flow exists (none is in
scope for what this vulnerability required closing). No refresh-token or
server-side revocation mechanism — a valid, unexpired token remains valid
for its full lifetime (default 24h) even if, e.g., an operator wanted to
force-logout an account; the only mitigation is a short-ish expiry, not true
revocation. Most importantly: **this stack still has no TLS** (the same
descoped-for-now decision `08-deployment-and-operations.md` already made,
reasoned about again in this ADR's Revisit triggers below) — a real
password now travels the same plaintext-over-localhost path every other
request already does, which was an accepted trade-off for query text and
document content, but is a materially different one for a credential.
Named honestly as a residual gap, not hidden.

## Decision

**Option C.** Real password authentication, implemented in the FastAPI
application itself, replaces the trusted-`X-User-Id`-header model entirely.
`X-User-Id` is removed from the application's vocabulary — it is not
checked, not preferred, not accepted as a fallback under any condition.
T-04's ownership-scoping logic (`lexicon.api.ownership`) is **unchanged** —
this decision only replaces what feeds it a caller identity, per this
session's own scope boundary.

## Trade-offs accepted

- Credentials (registration/login payloads) travel over the same
  unencrypted-by-default local stack every other request already does — see
  Revisit triggers. This is a real, if currently low-blast-radius (no
  session has ever exposed this stack beyond localhost), regression in
  what's at stake if that assumption ever stops holding silently.
- No refresh tokens, no server-side session revocation, no password-reset
  flow, no MFA. A stolen valid token is valid until its natural expiry.
- This process is both issuer and verifier of its own session tokens — a
  coupling Option B's gateway model would have avoided, accepted here
  because it is proportionate to this project's actual, current deployment
  shape rather than a shape it might have in some future the project has
  never actually committed to.
- The dev-only default `JWT_SECRET_KEY` (`config.py`, `docker-compose.yml`,
  `docker-compose.prod.yml`, `.env.example`) is, by construction, public —
  anyone who has read this repository can forge a token signed with it.
  Exactly like `POSTGRES_PASSWORD`/`MINIO_ROOT_PASSWORD`'s existing
  dev-only-default convention, this is safe **only** because it is labeled
  and only ever used as a placeholder; a real deployment overriding it is a
  hard requirement, not a suggestion.

## Consequences

- New `app_user` table (migration `0004_app_user.py`), granted the ADR-0002
  application role's ordinary mutable-table CRUD (not the audit tables'
  restricted grant — this table has real update/delete needs and carries no
  audit-tamper-evidence requirement).
- `lexicon.api.auth.get_caller` rewritten: verifies an
  `Authorization: Bearer <token>` header via `lexicon.security.tokens`;
  `X-User-Id` is read nowhere in the application.
- New `lexicon.security` package (`passwords.py`, `tokens.py`) and
  `lexicon.api.auth_routes` (`/api/v1/auth/register`, `/login`, `/me`).
- T-12 (`06-security-threat-model.md`) moves from "mechanism undesigned" to
  implemented, with this ADR as its resolution — update applied in that
  document directly, not merely cross-referenced here.
- `05-api-contracts.md`'s Authentication and authorisation model section
  rewritten to describe the real mechanism, replacing the trusted-header
  description.
- `frontend/lib/identity.tsx`'s localStorage identity switcher — a correct
  reflection of the old model — is replaced with real sign-in (register/
  login forms, an `httpOnly` session cookie the Next.js server attaches as
  the backend's bearer token, never exposed to page JavaScript) in this same
  session's frontend changes, per this ADR's own reasoning: leaving a fake
  identity-switching control in front of a now-real auth system would be
  actively misleading about what the app now does.
- `tests/test_auth.py` reproduces the pre-fix vulnerability (a bare
  `X-User-Id` header, no credential, previously sufficient for full
  impersonation) and proves it now fails closed, alongside real
  register/login/token-verification coverage (forged signatures, `alg:none`
  confusion, expired tokens, wrong-claim-type tokens). Every existing test
  that previously authenticated via a raw `X-User-Id` header
  (`test_corpus_authorization.py`, `test_api_query.py`,
  `test_document_upload_size_limit.py`, `test_query_rate_limit.py`) now goes
  through the real register/login endpoints (`tests/support/auth.py`) —
  deliberately, so a regression in the real auth boundary cannot hide behind
  a test-only shortcut back to the old header.

## Revisit triggers

- **If this stack is ever deployed anywhere reachable beyond localhost**,
  TLS is no longer optional the way `08-deployment-and-operations.md`
  reasoned it could stay descoped for query/document content — it becomes a
  hard prerequisite, because this ADR now puts real password credentials on
  the wire. This is a stronger, credential-driven version of that document's
  existing revisit trigger, not a new independent one.
- **If this API is ever meant to serve more than the one first-party
  Next.js consumer** `05-api-contracts.md` scopes it to (third-party
  integrations, a public API product), Option B's gateway/OIDC model
  becomes worth re-evaluating on its own merits — this ADR's rejection of it
  was specifically about disproportion to *today's* single-consumer,
  no-external-IdP shape, not a permanent architectural verdict.
- **If horizontal scaling (multiple backend replicas) is ever introduced,**
  `JWT_SECRET_KEY` must be provisioned via real shared secret management
  (not a compose-file env default) across every replica — HS256 verification
  requires every verifying process to hold the same key, unlike an
  asymmetric scheme where only the issuer needs the private half.
- **If an account-takeover or credential-stuffing incident is ever observed
  or reported**, the login rate limit's current placeholder threshold
  (`login_rate_limit_per_5_minutes`, unmeasured against real attack traffic,
  same honesty standard as this project's other T-05/T-06 placeholders) must
  be revisited against real data, and server-side token revocation should be
  reconsidered as a real requirement rather than an accepted gap.
