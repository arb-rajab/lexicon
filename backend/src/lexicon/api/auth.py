"""Caller identity extraction — ADR-0005.

Before ADR-0005, this module trusted whatever `X-User-Id` value a caller
supplied directly, on the stated assumption that a real deployment would
terminate and verify that header at an external, trusted reverse-proxy/
gateway boundary before traffic ever reached this service. That gateway was
never built, in dev or in prod compose (docker-compose.yml,
docker-compose.prod.yml) — this application has always been the network
edge in every deployable form of this stack. The result was a full,
live-reachable impersonation vulnerability: any caller could set
`X-User-Id: <anyone>` and be treated as that person by every corpus-
ownership check (`lexicon.api.ownership`), which is otherwise correct,
real access-control logic — it just had an attacker-controlled identity
feeding it. See `docs/adr/ADR-0005-instance-level-authentication.md` for
the full reasoning and the options considered.

This module now performs real authentication itself: a caller identity is
only ever accepted from a cryptographically verified session token (a
`lexicon.security.tokens`-issued JWT, obtained from a real password login
at `POST /api/v1/auth/login` or `/register`, `lexicon.api.auth_routes`),
presented as `Authorization: Bearer <token>`. `X-User-Id` is no longer read
anywhere in this application — a request cannot influence its own caller
identity by any header it sends.
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from lexicon.config import Settings, get_settings
from lexicon.security.tokens import InvalidToken, verify_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CallerContext:
    user_id: str


def _unauthenticated() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={
            "code": "unauthenticated",
            "message": "A valid Authorization: Bearer <token> header is required",
            "field": None,
        },
    )


def get_caller(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> CallerContext:
    if credentials is None or not credentials.credentials:
        raise _unauthenticated()
    try:
        user_id = verify_access_token(credentials.credentials, settings)
    except InvalidToken as exc:
        raise _unauthenticated() from exc
    return CallerContext(user_id=user_id)
