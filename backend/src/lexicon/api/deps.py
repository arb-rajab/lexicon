from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.orm import Session

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


__all__ = ["get_db", "get_llm"]
