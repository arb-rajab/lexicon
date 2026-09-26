# Session Handoff

## Retroactive entry — Session 8 (backfilled by Session 10)

Session 8 (`802c412`, "Session 8: write the case study, refresh README
status, finalize SDLC evidence") never wrote its own entry to this file —
first noticed and named by Session 9 (see below), left unbackfilled at
the time as out of Session 9's stated scope. Verified retroactively:
`git show --stat 802c412` and `git diff 363cf7b 802c412 --stat` both
confirm the commit changed exactly `README.md` (+92/-23 area),
`docs/CASE-STUDY.md` (new, 324 lines), and `docs/SDLC-EVIDENCE.md` (+55),
matching the commit message's own description — the case study's honest
account of Session 1's spike finding, ADR-0003's injection-hardening
results, the ADR-0004 descoping decision, and Session 7's four real bugs;
the README status-banner refresh; and SDLC-EVIDENCE.md's Phase 1/5/7
corrections. `main` was confirmed up to date with `origin/main` at the
time of this check, so the commit was genuinely pushed, not merely
committed locally. No work is missing — only this handoff paragraph was
skipped at the time.

## Retroactive entry — Session 12 (backfilled by Session 13)

Session 12 (`72a21a0`, "Build real frontend UI: corpus browse, upload,
query with X-User-Id auth (#2)") also never wrote its own entry to this
file — found while this session (13) was reading history to understand the
frontend's current auth model before changing it. `git show --stat 72a21a0`
confirms the commit replaced the empty frontend skeleton with a working
Next.js/React app (corpus list/create, document upload with client- and
server-side `413` handling, a query panel surfacing citations/refusals and
`401`/`403`/`422`/`429`/`502` error states) plus Vitest/Testing-Library
component tests, and a same-PR follow-up fixing a CI `npm ci` peer-dependency
conflict (`@types/node` bump for vite 8). Per that commit's own message, the
frontend's auth model was a deliberate, correct reflection of the backend's
*then-actual* mechanism: a client-side identity switcher
(`frontend/lib/identity.tsx`, persisted to `localStorage`) sending whatever
`X-User-Id` the visitor typed, proxied server-side by Next.js route handlers
(`app/api/**`) since the backend has no CORS middleware. This was not a
frontend defect — it correctly matched Session 11's own explicit, reasoned
decision (this file's prior revision: "Caller identity is a trusted header
(`X-User-Id`), not a new session/login system") — but see Session 13's entry
below for why that backend decision, and therefore this frontend's identity
switcher built against it, both needed to change. No other work from Session
12 is missing; only this handoff paragraph was skipped at the time.

## Project
- Repository: `lexicon`
- Public or private: public (flagship)
- Product/domain: Grounded document Q&A (RAG) system
- Current version or branch: `main` history is tagged `v1.0.0` at
  Session 9; Sessions 11 and 12 each landed as their own PR (#1, #2),
  continuing the PR-per-session convention Session 11 adopted (see that
  session's Decisions made, preserved below); this session's work follows
  the same convention.

## Session completed
- Session number and title: **Session 13 — Build a real auth boundary for
  the `X-User-Id` header: it was full, live-reachable impersonation.**
- Objective, as given at the start of this session: Session 11's own
  documented decision — "caller identity is a trusted header (`X-User-Id`),
  not a new session/login system," modeled on an external reverse-proxy/
  gateway that would terminate and verify it — had never actually been made
  true. Neither `docker-compose.yml` nor `docker-compose.prod.yml` (Session
  7's own "production-shaped, verified locally" stack) puts anything in
  front of `backend`. Live-verified: any caller could set
  `X-User-Id: <anyone>` and be treated as that identity by every T-04
  ownership check — full impersonation, no credential required. Ground
  rule: fix this for real (implement real authentication or actually deploy
  a verifying gateway — pick based on this project's actual deployment
  shape), not re-document the caveat again; do not touch T-04's ownership/
  scoping logic itself. Status: **complete** — real password authentication
  now replaces the trusted header entirely; T-04 is unchanged.

## Work completed

- **Decision: real authentication inside the FastAPI app, not an OIDC
  gateway** (`docs/adr/ADR-0005-instance-level-authentication.md`, full
  reasoning and options considered there). A gateway (`oauth2-proxy`)
  would need a real external identity provider this project has never had
  a relationship with, and a stable HTTPS callback URL — this project has
  no cloud deployment and has explicitly, separately decided against TLS
  (`08-deployment-and-operations.md`) for the same "no session has ever
  committed to public exposure" reason. Standing up a gateway without also
  reversing that TLS decision would have been the same "assumed, not real"
  failure mode this task exists to close, just with an extra container
  around it. Real login, self-contained in the app that already exists,
  actually fits this project's dev/prod-compose-only, no-cloud shape.
- **New `app_user` table** (migration `0004_app_user.py`), granted the
  ADR-0002 application role's ordinary mutable-table CRUD. New
  `lexicon.security` package: `passwords.py` (salted PBKDF2-HMAC-SHA256,
  600,000 iterations, OWASP 2023 minimum — not `bcrypt`/`argon2`, to avoid
  a new native-extension dependency in an otherwise pure-Python-wheel
  project), `tokens.py` (HS256 JWTs, `algorithms=` pinned explicitly on
  verify — defeats `alg:none`-style confusion attacks).
- **New `lexicon.api.auth_routes`**: `POST /api/v1/auth/register` and
  `/login` (issue a signed session token; identical `401 invalid_credentials`
  for unknown username vs. wrong password — no enumeration surface),
  `GET /api/v1/auth/me`. Login is rate-limited per username
  (`lexicon.api.rate_limit.enforce_login_rate_limit`, Redis-backed,
  fail-open on Redis outage, same availability posture as T-05's existing
  controls) — T-12's "rate-limited login" requirement, carried forward
  since Session 2, closed alongside the header fix rather than left open
  a second time.
- **`lexicon.api.auth.get_caller` rewritten**: verifies
  `Authorization: Bearer <token>` via `lexicon.security.tokens`.
  `X-User-Id` is read nowhere in the application — not checked, not
  preferred, not a fallback. `lexicon.api.ownership` (T-04) is **byte-for-
  byte unchanged**; only what feeds it a caller identity changed.
- **The regression proof** (`backend/tests/test_auth.py`): reproduces the
  exact pre-fix attack — a bare `X-User-Id` header, no credential — and
  asserts it now gets `401`, not access. Also: forged-signature tokens,
  `alg:none` confusion, expired tokens, wrong-claim-type tokens, a real
  token for one account never authenticating as another even with a forged
  `X-User-Id` alongside it, and the login rate limit.
  `test_corpus_authorization.py` gained the same proof at the ownership-
  boundary level (`test_forged_x_user_id_header_no_longer_grants_access`).
  Every pre-existing test that authenticated via a raw `X-User-Id` header
  (`test_corpus_authorization.py`, `test_api_query.py`,
  `test_document_upload_size_limit.py`, `test_query_rate_limit.py`) now
  goes through the real register/login endpoints
  (`tests/support/auth.py:bearer_headers_for`) — deliberately, so a
  regression in the real auth boundary can't hide behind a test-only
  shortcut back to the old header.
- **A real test-isolation bug found and fixed while building the login-
  rate-limit test**: Redis state wasn't flushed between tests (only
  Postgres was, `conftest.py`'s existing `_clean_tables`) — T-05's
  per-corpus counters never collided because each test uses a fresh
  corpus UUID, but T-12's login limiter is keyed by a small set of
  *reused* literal usernames across tests, so leftover attempt counts
  from an earlier test or run bled into a later one, reproduced directly
  (a test passing alone, failing in the full suite). Fixed by flushing
  Redis in `_clean_tables` alongside the existing Postgres truncate — a
  general test-isolation improvement, not a workaround local to one test.
- **Frontend: the `localStorage` identity switcher replaced with real
  sign-in.** `lib/identity.tsx`/`IdentityBar.tsx` were a correct reflection
  of the backend's then-actual (and it turned out spoofable) auth model,
  not a frontend defect — see the Session 12 backfill above. New
  `lib/auth.tsx` (`AuthProvider`/`useAuth`), `components/AuthForm.tsx`
  (login/register), `components/AuthGate.tsx` (gates the app behind a real
  session), `components/AuthBar.tsx` (signed-in username + sign-out). The
  session token itself never reaches page JavaScript: `app/api/auth/*`
  route handlers set/read an `httpOnly` cookie (`lib/session-cookie.ts`)
  server-side; `lib/backend.ts`'s proxy reads that cookie and attaches
  `Authorization: Bearer` when forwarding to the backend — the browser
  never has a readable token to leak, unlike the old localStorage string.
  `lib/api-client.ts`'s functions no longer take a `userId` parameter at
  all; there is nothing client-side left to forge.
- **A real bug found and fixed while end-to-end-verifying the frontend
  against a running backend, not just unit tests**: the session cookie's
  `secure` flag was initially tied to `NODE_ENV === "production"` — but
  `next start` (`docker-compose.prod.yml`'s production build) sets
  `NODE_ENV=production` regardless of whether TLS terminates in front of
  it, and neither compose stack in this repository ever does. A `Secure`
  cookie served over the plain HTTP this stack actually serves is silently
  dropped by the browser — this would have broken login specifically on
  the "production-shaped" stack while looking fine in dev. Fixed with an
  explicit `COOKIE_SECURE` env var (default `false`, matching this
  project's actual, current no-TLS reality), verified by rebuilding and
  re-running the full register → cookie → `/me` → create-corpus →
  forged-header-has-no-effect chain against a real running Next.js server
  and real running FastAPI backend, not assumed from reading the diff.
- **Docs reconciled**: `05-api-contracts.md`'s Authentication section
  rewritten (real endpoints, real contract); `06-security-threat-model.md`
  T-12 row moved from "mechanism undesigned" to implemented, T-04 row's
  wording updated to note the identity source change, Accepted-risks table
  gained the honest no-TLS-with-real-credentials residual gap;
  `08-deployment-and-operations.md` gained `JWT_SECRET_KEY`/
  `LOGIN_RATE_LIMIT_PER_5_MINUTES` documentation; `.env.example` and both
  compose files gained the same, with `JWT_SECRET_KEY`'s labeled dev-only
  default matching the existing `POSTGRES_PASSWORD`-style convention.

## Files created or changed

- `backend/src/lexicon/security/` (new package) — `passwords.py`,
  `tokens.py`
- `backend/src/lexicon/api/auth.py` — rewritten: verifies a bearer token,
  no longer reads `X-User-Id`
- `backend/src/lexicon/api/auth_routes.py` (new) — register/login/me
- `backend/src/lexicon/api/rate_limit.py` — `enforce_login_rate_limit`
- `backend/src/lexicon/api/schemas.py` — `RegisterRequest`, `LoginRequest`,
  `TokenOut`, `MeOut`
- `backend/src/lexicon/config.py` — `jwt_secret_key`, `jwt_algorithm`,
  `jwt_access_token_expire_minutes`, `login_rate_limit_per_5_minutes`
- `backend/src/lexicon/db/models.py` — `AppUser`; `Corpus.owner_id`
  comment updated
- `backend/src/lexicon/main.py` — `auth_router` included
- `backend/alembic/versions/0004_app_user.py` (new)
- `backend/pyproject.toml` — `pyjwt` dependency
- `backend/tests/test_auth.py` (new), `tests/support/auth.py` (new)
- `backend/tests/test_corpus_authorization.py`, `test_api_query.py`,
  `test_document_upload_size_limit.py`, `test_query_rate_limit.py` —
  real register/login instead of raw `X-User-Id` headers
- `backend/tests/conftest.py` — Redis flush added to `_clean_tables`
- `docker-compose.yml`, `docker-compose.prod.yml`, `.env.example` —
  `JWT_SECRET_KEY`, `LOGIN_RATE_LIMIT_PER_5_MINUTES`, `COOKIE_SECURE`
- `docs/adr/ADR-0005-instance-level-authentication.md` (new)
- `docs/project-memory/05-api-contracts.md`,
  `06-security-threat-model.md`, `08-deployment-and-operations.md` —
  reconciled with implementation, per Work completed above
- `CHANGELOG.md` — new `## [Unreleased]` entry
- `frontend/lib/identity.tsx`, `components/IdentityBar.tsx` — deleted
- `frontend/lib/auth.tsx`, `lib/auth-server.ts`, `lib/session-cookie.ts`,
  `components/AuthForm.tsx`, `components/AuthGate.tsx`,
  `components/AuthBar.tsx` (all new)
- `frontend/app/api/auth/register/route.ts`, `login/route.ts`,
  `logout/route.ts`, `me/route.ts` (all new)
- `frontend/lib/backend.ts` — cookie-based bearer forwarding, not
  `X-User-Id` passthrough
- `frontend/lib/api-client.ts`, `lib/hooks.ts`,
  `components/CorpusCreateForm.tsx`, `DocumentList.tsx`, `QueryPanel.tsx`,
  `UploadForm.tsx` — `userId`/`useIdentity` removed
- `frontend/app/layout.tsx` — `AuthProvider`/`AuthGate` wiring
- `frontend/app/globals.css` — `.identity-bar` styles replaced with
  `.auth-bar`/`.auth-form`/`.auth-page`
- `frontend/components/__tests__/QueryPanel.test.tsx`,
  `UploadForm.test.tsx` — `IdentityProvider` wrapper removed (components no
  longer need it)

## Decisions made

- **Real authentication in the app, not an OIDC gateway** — see ADR-0005;
  the gateway option was seriously evaluated and rejected as disproportionate
  to, and not actually compatible with, this project's current no-cloud,
  no-external-IdP, no-TLS deployment shape, not skipped for convenience.
- **PBKDF2-HMAC-SHA256 over the standard library, not `bcrypt`/`argon2`.**
  Avoids a new native-extension dependency in a project whose dependency
  set (`pyproject.toml`) is otherwise pure-Python-wheel-friendly; 600,000
  iterations matches OWASP's 2023 minimum recommendation for this
  algorithm specifically, not an arbitrary number.
- **Symmetric HS256 JWTs, not asymmetric RS256/JWKS.** This process is
  both the only issuer and the only verifier of its own tokens — there is
  no separate trusted gateway to hand a public key to, so key-distribution
  machinery would add complexity this deployment shape has no use for. If
  horizontal scaling is ever introduced, this becomes a revisit trigger
  (ADR-0005) since every replica would then need the same shared secret.
- **The session cookie's `secure` flag is an explicit `COOKIE_SECURE` env
  var, not tied to `NODE_ENV`.** Found and reasoned about directly (see
  Work completed) — `NODE_ENV=production` and "served over HTTPS" are two
  different facts this codebase must not conflate, and conflating them
  here would have silently broken login on the one stack
  (`docker-compose.prod.yml`) most likely to be judged "the real one."
- **No TLS added this session.** `08-deployment-and-operations.md`
  already reasoned explicitly about why this stack has none (no session
  has ever committed to public exposure); ADR-0005 accepts that reasoning
  rather than bundling an unrelated TLS decision into an auth-boundary
  fix, but names the resulting residual gap explicitly (real passwords now
  travel the same plaintext-over-local-network path everything else
  already did) rather than silently inheriting the old document's
  reasoning for a materially different kind of data.
- **T-04's ownership/scoping logic was not touched**, per this session's
  own ground rule — confirmed by inspection and by
  `test_corpus_authorization.py`'s unchanged (bar the auth-header
  mechanics) assertions all still passing.

## Validation performed

Real local Postgres 16 + pgvector 0.6.0 and Redis were provisioned in this
session's own sandbox (no Docker daemon available here; pgvector installed
via `apt-get install postgresql-16-pgvector` since it wasn't already
present) to run the suite against real infrastructure, matching this
project's standing "no ADR-0002/NFR-001-style test against a mock" rule:

- `ruff check .` (backend) — all checks passed, after fixing line-length
  and import-order issues in the new files.
- `mypy src` (strict) — no issues, 40 source files.
- `bandit -r src` — no issues, 1936 lines scanned (one false positive on a
  `_TOKEN_TYPE = "access"` constant — bandit's hardcoded-password
  heuristic matching on the name, not the value — fixed by renaming to
  `_ACCESS_CLAIM_TYPE` rather than suppressing the finding).
- `alembic upgrade head` — clean, migration `0004` applies without error.
- `pytest tests/ -q --ignore=tests/security --ignore=tests/eval` —
  **51 passed, 10 failed. Every failure is the same pre-existing root
  cause as prior sessions' recorded runs**, confirmed by traceback, not
  assumed: this sandbox's outbound network policy blocks `huggingface.co`,
  so `fastembed`'s first-run ONNX model download fails for every test that
  exercises real ingestion/retrieval — unrelated to and unaffected by this
  session's change. All 15 of this session's own `test_auth.py` cases,
  all of `test_corpus_authorization.py` (including the new forged-header
  regression test), and every other auth-touching test pass cleanly.
- **Full end-to-end verification against real running servers**, not just
  the test suite: started the real backend (`uvicorn`) and a real built
  Next.js frontend (`next build && next start`) against the same local
  Postgres/Redis, then via `curl` — registered a user through the frontend
  proxy, confirmed the `Set-Cookie` response never exposes the raw token
  in the JSON body, confirmed `/api/auth/me` round-trips the identity from
  the cookie alone, created a corpus through the cookie-authenticated
  proxy, confirmed a bare forged `X-User-Id` header (no cookie) gets `401`
  through the real frontend proxy (the exact pre-fix attack, reproduced
  and closed at the browser-facing layer, not only the backend's own test
  suite), and confirmed a valid cookie plus a forged `X-User-Id` claiming
  a different identity is still scoped to the cookie's real owner only.
- Frontend: `npx tsc --noEmit`, `npx eslint .`, `npx vitest run` (10/10
  passed), and `npm run build` all clean.

## Open questions and risks

Carried forward, still true, unaffected by this session's scope:

- No CI job builds or exercises either production image or
  `docker-compose.prod.yml` — all deployment evidence remains from local,
  manual verification (Session 7, and this session's own end-to-end check
  above, both still manual).
- Metrics, tracing, dashboards, and alerting remain genuinely unbuilt.
- The central ADR-0004 boundary is permanent for this project's current
  lifecycle: real LLM provider verification quality is not, and cannot
  be, proven in this environment.
- T-06's soft per-corpus document-count warning is still not built.
- The daily spend ceiling's query-count proxy has never been validated
  against real provider spend (ADR-0004).

New from this session:

- **This stack still has no TLS.** Real password credentials now travel
  the same plaintext-over-local-network path query text and document
  content already did — an accepted trade-off (ADR-0005), not an oversight,
  but a materially higher-stakes one than before this session, since a
  credential is now on that wire, not just query content. Hard revisit
  trigger: TLS becomes non-optional the moment this stack is ever exposed
  anywhere beyond localhost.
- **No refresh tokens, no server-side session revocation.** A stolen valid
  token remains valid for its full lifetime (24h default,
  `jwt_access_token_expire_minutes`) — "logout" (frontend) only stops this
  browser from sending it. Acceptable for this session's actual threat
  (closing unauthenticated impersonation), not a complete session-security
  design.
- **`login_rate_limit_per_5_minutes`'s threshold (10) is an unmeasured
  placeholder**, same honesty standard as this project's other T-05/T-06
  placeholders — not validated against real credential-stuffing traffic.
- **`JWT_SECRET_KEY`'s dev-only default is, by construction, public.**
  Anyone who has read this repository can forge a token signed with it;
  every real deployment overriding this is a hard requirement (documented
  in three places: `config.py`, both compose files, `.env.example`), not
  merely a suggestion — this is the single most load-bearing secret in the
  application now, more so than any credential before it.

## Session completed

- Session number and title: **Session 14 — Fix login timing side-channel
  (username enumeration); rate-limit `/register`.**
- Objective, as given at the start of this session: Session 13 built real
  auth (T-12) but was re-inspected and found to have two smaller gaps left
  in it: (1) `/login`'s `401 invalid_credentials` response, while
  body-identical for an unknown username vs. a wrong password, differed
  measurably in *timing* between the two — the PBKDF2 comparison only ran
  when a matching user row existed — which is a classic username-
  enumeration side-channel and directly undercut this codebase's own
  documented "no enumeration" claim; (2) `/register` had no rate limiting
  at all, an open account-creation endpoint with no throttle. Ground rule:
  fix both, correct the "no enumeration" doc claim if it doesn't hold in
  full, don't touch the core auth mechanism (PBKDF2/session tokens)
  itself. Status: **complete**.

## Work completed

- **Login timing side-channel closed**
  (`backend/src/lexicon/api/auth_routes.py`): a fixed dummy password hash
  (`_DUMMY_PASSWORD_HASH`, same `pbkdf2_sha256$<iterations>$...` format as
  a real stored hash, computed once at import time) is now compared
  against whenever the submitted username doesn't match a row, so
  `verify_password`'s ~600,000-iteration PBKDF2 comparison always runs
  exactly once per login attempt regardless of outcome — the two cases
  now cost the same, not just return the same body.
- **`/register` rate-limited**
  (`backend/src/lexicon/api/rate_limit.py:enforce_register_rate_limit`,
  wired into `auth_routes.register`): a **global**, instance-wide 5-minute
  bucket, not per-submitted-username like login's limiter — the identity
  being throttled here doesn't exist yet, so a per-username key would be
  trivially evaded by varying the username on every request. Same
  fail-open-on-Redis-outage posture as every other control in this module.
  New setting `register_rate_limit_per_5_minutes` (default `20`,
  conservative placeholder, same honesty standard as this project's other
  thresholds), new `REGISTER_RATE_LIMIT_PER_5_MINUTES` env var
  (`.env.example`).
- **Docs corrected, not just re-asserted**: `05-api-contracts.md`'s
  "no username enumeration" claim was accurate as stated (scoped to
  `/login`'s response body) but incomplete — it didn't call out that the
  guarantee also depends on timing, which the code didn't actually
  provide until this session. Rewrote that section to state the timing
  fix explicitly and to draw an explicit line around `/register`: a `409
  username_taken` response is an inherent, accepted signal that a
  registration flow's job requires it to reveal, not an open enumeration
  gap of the kind `/login` closes — checked deliberately per this
  session's scope, and not something a code change can close without
  changing the endpoint's actual contract (e.g. always returning `201`
  with a "check your email" style response, which is a product decision
  out of scope here, not a security bug fix). `06-security-threat-model.md`'s
  T-12 row updated to describe both fixes and both new tests.
- **Tests**: `test_login_does_equivalent_work_for_unknown_vs_known_username`
  — deliberately a structural assertion (verify_password runs exactly
  once, at the same iteration count, in both the known- and unknown-
  username cases), not a wall-clock timing assertion, since the latter
  would be flaky on shared CI runners; the docstring states this
  trade-off explicitly. `test_register_is_rate_limited_after_repeated_attempts`
  — proves the limiter trips across *different* usernames (it must, since
  it's a global bucket), not just repeated attempts at one.

## Files created or changed

- `backend/src/lexicon/api/auth_routes.py` — `_DUMMY_PASSWORD_HASH`,
  timing-equalised `login`, `enforce_register_rate_limit` wired into
  `register`
- `backend/src/lexicon/api/rate_limit.py` — `enforce_register_rate_limit`
- `backend/src/lexicon/config.py` — `register_rate_limit_per_5_minutes`
- `backend/tests/test_auth.py` — the two new tests above
- `.env.example` — `REGISTER_RATE_LIMIT_PER_5_MINUTES`
- `docs/project-memory/05-api-contracts.md`,
  `06-security-threat-model.md`, `08-deployment-and-operations.md` —
  reconciled with implementation, per Work completed above

## Decisions made

- **Structural test over wall-clock timing test for the side-channel
  proof.** A real timing assertion (`assert elapsed_known ≈
  elapsed_unknown`) is the more literal proof but is genuinely flaky on
  shared/virtualized CI runners; the code-path invariant that actually
  *causes* equal timing (same comparison, same iteration count, run
  exactly once either way) is deterministic and just as strong a
  guarantee, so it's what's asserted.
- **Register's rate limit is a global bucket, not per-username**, unlike
  login's. Deliberate, not an oversight: the whole point of rate-limiting
  registration is to bound an attacker who is *choosing a new username on
  every request* — a per-username key would never trip for that attacker
  at all.
- **`/register`'s `409 username_taken` is not treated as a bug to fix.**
  Considered and rejected: this session's scope was closing enumeration
  vectors that are implementation bugs (a timing leak, a missing
  throttle), not redesigning `/register`'s contract to also hide whether
  a username is taken, which is a different, larger product/UX decision
  (e.g. always-succeeds-with-email-confirmation registration flows) this
  session's ground rule ("don't touch the core auth mechanism") puts out
  of scope.

## Validation performed

Real local Postgres 16 + pgvector 0.6.0 and Redis provisioned in this
session's own sandbox (no Docker daemon available here), matching this
project's standing "no test against a mock" rule for auth/rate-limit
tests:

- `ruff check`, `mypy src` (strict), `bandit -r src` — all clean on the
  changed files.
- `alembic upgrade head` — unaffected, no migration in this session.
- `pytest tests/test_auth.py -q` — **17 passed** (15 pre-existing + 2 new).
- `pytest -q` (full suite) — 53 passed, 12 failed; every failure is the
  same pre-existing root cause as prior sessions' recorded runs (this
  sandbox's outbound network policy blocks the real LLM/embedding calls
  those tests exercise) — none touch auth, none regressed by this
  session's change.

## Open questions and risks

Carried forward, still true, unaffected by this session's scope: see
Session 13's entry above (no TLS, no refresh tokens/session revocation,
unmeasured rate-limit thresholds, `JWT_SECRET_KEY`'s public dev default).

New from this session:

- **`register_rate_limit_per_5_minutes`'s threshold (20) is an unmeasured
  placeholder**, same honesty standard as this project's other
  thresholds — not validated against real signup-abuse traffic.
- **A global registration rate limit is a single shared bucket across
  every legitimate concurrent signup on the instance**, not just
  attackers — a burst of real, unrelated signups can trip it. Accepted
  for this deployment's actual scale (no cloud deployment, no measured
  production signup volume), same honesty standard as this project's
  other conservative placeholders; a hard revisit trigger if real traffic
  ever approaches the threshold.
