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
