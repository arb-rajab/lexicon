from collections.abc import Generator
from functools import lru_cache

import redis
from sqlalchemy.orm import Session

from lexicon.config import get_settings
from lexicon.db.session import get_db
from lexicon.llm.base import LLMClient
from lexicon.llm.factory import get_llm_client

DbDep = Generator[Session, None, None]


@lru_cache
def _cached_llm_client() -> LLMClient:
    # Constructed once per process: cheap for the stub client, avoids
    # rebuilding an anthropic.Anthropic() client per request for the real
    # one. Selection itself (real vs stub) is re-evaluated only on process
    # restart — matches how DATABASE_URL/REDIS_URL are already resolved
    # once at startup.
    return get_llm_client()


def get_llm() -> LLMClient:
    return _cached_llm_client()


@lru_cache
def _cached_redis_client() -> redis.Redis:
    # Same one-per-process rationale as _cached_llm_client above — a
    # single connection pool, not one client per request. Used by
    # api/rate_limit.py's T-05 controls.
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    return _cached_redis_client()


__all__ = ["get_db", "get_llm", "get_redis"]
