"""Session-token issuance/verification for ADR-0005.

HS256 JWTs, symmetric-key signed with `Settings.jwt_secret_key`. This
process is both the issuer (`/api/v1/auth/login`, `/register`) and the only
verifier (`lexicon.api.auth.get_caller`) — there is no separate trusted
gateway to hand a public key to, so RS256/JWKS would add asymmetric-key
management this deployment shape has no use for (see ADR-0005, Option
considered B).
"""

from datetime import UTC, datetime, timedelta

import jwt

from lexicon.config import Settings

_ACCESS_CLAIM_TYPE = "access"


class InvalidToken(Exception):
    """Raised for any token that must not be trusted: bad signature,
    expired, wrong algorithm/type, or missing the expected claims — the
    caller (api/auth.py) always maps this to a single 401, never
    distinguishing *why* the token was rejected, to avoid handing an
    attacker a signature-forging oracle."""


def issue_access_token(user_id: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": _ACCESS_CLAIM_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_access_token(token: str, settings: Settings) -> str:
    """Returns the verified `sub` (user id) claim, or raises InvalidToken."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidToken(str(exc)) from exc

    if payload.get("type") != _ACCESS_CLAIM_TYPE:
        raise InvalidToken("unexpected token type")

    sub = payload["sub"]
    if not isinstance(sub, str) or not sub:
        raise InvalidToken("empty subject claim")
    return sub
