"""Caller identity extraction.

T-04 (06-security-threat-model.md) requires every corpus_id-scoped
endpoint to authorise the caller against that specific corpus — but
05-api-contracts.md deliberately does not invent an instance-level
session mechanism (cookie vs. bearer token) ahead of that operational
decision, which `08-deployment-and-operations.md` still defers to a
future operator/deployment choice. This module bridges that gap the same
way a reverse-proxy/gateway pattern does in production (Envoy,
oauth2-proxy, an API gateway — something already authenticated the caller
and forwards their verified identity via a trusted header, stripping any
caller-supplied value first): it trusts a caller identity supplied via the
`X-User-Id` header, and this application layer is responsible only for
what T-04 actually asks for — authorising that identity against a specific
`corpus_id`, not for verifying who they are in the first place. This app
cannot itself distinguish a header set by a trusted proxy from one set by
the caller directly, which is exactly why instance-level authentication
stays out of this layer's scope; a real deployment must terminate
`X-User-Id` at that trusted boundary before traffic reaches this service.
"""

from dataclasses import dataclass

from fastapi import Header, HTTPException


@dataclass(frozen=True)
class CallerContext:
    user_id: str


def get_caller(x_user_id: str | None = Header(default=None)) -> CallerContext:
    if x_user_id is None or not x_user_id.strip():
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthenticated",
                "message": "X-User-Id header is required",
                "field": None,
            },
        )
    return CallerContext(user_id=x_user_id.strip())
