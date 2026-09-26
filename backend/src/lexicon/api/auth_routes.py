"""ADR-0005 — real login. The only place in this application a caller
identity is ever established from anything other than a previously issued,
verified session token (`lexicon.api.auth.get_caller` verifies; this module
issues).
"""

import logging

import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from lexicon.api.auth import CallerContext, get_caller
from lexicon.api.deps import get_db, get_redis
from lexicon.api.rate_limit import RateLimitExceeded, enforce_login_rate_limit
from lexicon.api.schemas import LoginRequest, MeOut, RegisterRequest, TokenOut
from lexicon.config import get_settings
from lexicon.db import models
from lexicon.security.passwords import hash_password, verify_password
from lexicon.security.tokens import issue_access_token

logger = logging.getLogger("lexicon.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _invalid_credentials() -> HTTPException:
    # Deliberately identical whether the username doesn't exist or the
    # password is wrong — distinguishing the two would let a caller
    # enumerate registered usernames.
    return HTTPException(
        status_code=401,
        detail={
            "code": "invalid_credentials",
            "message": "Invalid username or password",
            "field": None,
        },
    )


@router.post("/register", status_code=201, response_model=TokenOut)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenOut:
    # Called directly, not via FastAPI's Depends(get_settings) — same
    # pattern api/documents.py and api/query.py already use, specifically
    # so a test can monkeypatch this module's `get_settings` name to
    # exercise a different threshold without wiring a dependency override.
    settings = get_settings()
    username = payload.username.strip()
    if not username:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_username",
                "message": "Username cannot be blank",
                "field": "username",
            },
        )

    user = models.AppUser(username=username, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "username_taken",
                "message": "That username is already registered",
                "field": "username",
            },
        ) from exc

    token = issue_access_token(username, settings)
    return TokenOut(access_token=token, username=username)


@router.post("/login", response_model=TokenOut)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> TokenOut:
    settings = get_settings()
    try:
        enforce_login_rate_limit(redis_client, settings, payload.username)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail={"code": "rate_limited", "message": "Too many login attempts", "field": None},
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc

    username = payload.username.strip()
    user = db.execute(select(models.AppUser).filter_by(username=username)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise _invalid_credentials()

    token = issue_access_token(user.username, settings)
    return TokenOut(access_token=token, username=user.username)


@router.get("/me", response_model=MeOut)
def me(caller: CallerContext = Depends(get_caller)) -> MeOut:
    return MeOut(username=caller.user_id)
