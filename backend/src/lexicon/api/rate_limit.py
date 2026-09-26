"""T-05 cost-abuse control (06-security-threat-model.md) — Redis-backed
per-corpus query rate limiting (NFR-007, 05-api-contracts.md: "returned as
`429` with a `Retry-After` header") plus a daily spend-ceiling circuit
breaker (the threat model's "recommended absolute spend-ceiling circuit
breaker"). Both are enforced in api/query.py *before* a query reaches the
real generate/verify pipeline — every answered query costs at least one
live generation call plus at least one live verification call per cited
claim (ADR-0001), so the whole point of this control is to sit in front of
that spend, not clean up after it.

The two layers are deliberately separate fixed windows, not one counter:
the per-minute limit stops a fast burst (a retry loop, a scripted probe);
the daily ceiling stops slow-and-steady abuse that never trips the
per-minute limit but still runs up real spend over a day.
"""

import logging
import time
import uuid

import redis

from lexicon.config import Settings

logger = logging.getLogger("lexicon.rate_limit")

_RATE_LIMIT_WINDOW_SECONDS = 60
# A day, plus slack so a window's TTL never lapses a little early relative
# to the UTC-date-keyed window below purely from clock/request latency.
_SPEND_CEILING_TTL_SECONDS = 24 * 60 * 60 + 60


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(f"query rate limit exceeded, retry after {retry_after}s")


class SpendCeilingExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(f"daily spend ceiling exceeded, retry after {retry_after}s")


def _key(prefix: str, corpus_id: uuid.UUID, window: str) -> str:
    return f"lexicon:{prefix}:{corpus_id}:{window}"


def _check_rate_limit(redis_client: redis.Redis, settings: Settings, corpus_id: uuid.UUID) -> None:
    window = int(time.time()) // _RATE_LIMIT_WINDOW_SECONDS
    key = _key("ratelimit", corpus_id, str(window))
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, _RATE_LIMIT_WINDOW_SECONDS)
    if count > settings.query_rate_limit_per_minute:
        ttl = redis_client.ttl(key)
        raise RateLimitExceeded(retry_after=ttl if ttl and ttl > 0 else _RATE_LIMIT_WINDOW_SECONDS)


def _check_spend_ceiling(
    redis_client: redis.Redis, settings: Settings, corpus_id: uuid.UUID
) -> None:
    day = time.strftime("%Y-%m-%d", time.gmtime())
    key = _key("spend", corpus_id, day)
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, _SPEND_CEILING_TTL_SECONDS)
    if count > settings.query_daily_spend_ceiling:
        ttl = redis_client.ttl(key)
        raise SpendCeilingExceeded(
            retry_after=ttl if ttl and ttl > 0 else _SPEND_CEILING_TTL_SECONDS
        )


_LOGIN_RATE_LIMIT_WINDOW_SECONDS = 5 * 60


def _login_key(username: str) -> str:
    return f"lexicon:login-attempts:{username.strip().lower()}"


def enforce_login_rate_limit(redis_client: redis.Redis, settings: Settings, username: str) -> None:
    """T-12 (06-security-threat-model.md): rate-limited login, so guessing a
    real account's password isn't just gated by real-world latency. Keyed
    by the submitted username (not caller IP, which this app never sees
    reliably behind an unknown/absent proxy layer) — same fail-open-on-
    Redis-outage posture as enforce_query_limits above, for the same
    availability reason: an unreachable rate limiter should not itself take
    login down.
    """
    key = _login_key(username)
    try:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, _LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        if count > settings.login_rate_limit_per_5_minutes:
            ttl = redis_client.ttl(key)
            raise RateLimitExceeded(
                retry_after=ttl if ttl and ttl > 0 else _LOGIN_RATE_LIMIT_WINDOW_SECONDS
            )
    except redis.RedisError:
        logger.warning("login rate limiter unreachable, failing open for this request")


_REGISTER_RATE_LIMIT_WINDOW_SECONDS = 5 * 60
_REGISTER_RATE_LIMIT_KEY = "lexicon:register-attempts:global"


def enforce_register_rate_limit(redis_client: redis.Redis, settings: Settings) -> None:
    """Found during Session N re-inspection: `/register` had no throttle at
    all — an open account-creation endpoint is both a mass-account-creation
    vector and, since a `409 username_taken` response is itself a
    registered-username oracle, an enumeration-via-registration-errors
    vector (faster to script against than login, which is already rate
    limited).

    Global bucket, not per-submitted-username like
    `enforce_login_rate_limit`: the identity being rate limited here
    doesn't exist yet, so keying on it is trivially evaded by trying a new
    username on every request. Same "this app never sees caller IP
    reliably" constraint as login applies here too, so a global fixed
    window is the available option, not a design preference. Same
    fail-open-on-Redis-outage posture as every other control in this
    module, for the same availability reason.
    """
    key = _REGISTER_RATE_LIMIT_KEY
    try:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, _REGISTER_RATE_LIMIT_WINDOW_SECONDS)
        if count > settings.register_rate_limit_per_5_minutes:
            ttl = redis_client.ttl(key)
            raise RateLimitExceeded(
                retry_after=ttl if ttl and ttl > 0 else _REGISTER_RATE_LIMIT_WINDOW_SECONDS
            )
    except redis.RedisError:
        logger.warning("register rate limiter unreachable, failing open for this request")


def enforce_query_limits(
    redis_client: redis.Redis, settings: Settings, corpus_id: uuid.UUID
) -> None:
    """Raises RateLimitExceeded or SpendCeilingExceeded if this query must
    not reach the pipeline. A Redis outage fails OPEN (logged, not raised):
    this is an availability tradeoff, not a correctness invariant like
    ADR-0003's fail-closed verifier gate — an unreachable rate-limit
    backend should not itself take query answering down, and the
    question-length cap (T-05's other, backend-independent layer,
    api/query.py) still holds regardless.
    """
    try:
        _check_rate_limit(redis_client, settings, corpus_id)
        _check_spend_ceiling(redis_client, settings, corpus_id)
    except redis.RedisError:
        logger.warning(
            "rate limiter unreachable, failing open for this request",
            extra={"extra_fields": {"corpus_id": str(corpus_id)}},
        )
