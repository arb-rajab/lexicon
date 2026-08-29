"""Application configuration.

Environment-variable-sourced, matching the existing DATABASE_URL/REDIS_URL
pattern (03-architecture.md's open item on credentials). ANTHROPIC_API_KEY
is intentionally optional: its absence is not an error at import time — it
is the signal llm.factory uses to select the stub LLM client tier instead
of failing to boot. See docs/project-memory/12-session-handoff.md (Session
4) for why that is a deliberate, labeled fallback rather than a silent one.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres. `database_url` is the application's runtime role — per
    # ADR-0002, restricted to INSERT/SELECT on QUERY_LOG/RETRIEVED_CHUNK/
    # CITATION_VERDICT. `database_admin_url` is the migration/owner role
    # that Alembic runs as, and is the only role permitted UPDATE/DELETE on
    # those three tables. Falling back to `database_url` when the admin URL
    # isn't set is a local-dev convenience only — see db/session.py.
    database_url: str = "postgresql+psycopg://lexicon:lexicon@localhost:5433/lexicon"
    database_admin_url: str | None = None

    redis_url: str = "redis://localhost:6380/0"

    # LLM provider (ADR-0001/ADR-0003). Real credentials do not exist in
    # this development environment as of Session 4 — see
    # docs/project-memory/12-session-handoff.md. When unset, llm.factory
    # selects StubLLMClient instead of AnthropicLLMClient.
    anthropic_api_key: str | None = None
    # Tier assignment per 03-architecture.md: generation gets a mid/high
    # tier model, verification gets a small/fast tier model. Specific IDs
    # are a Session 4 configuration decision (the architecture doc
    # deliberately left them unpinned), overridable per deployment.
    generation_model: str = "claude-sonnet-5"
    verification_model: str = "claude-haiku-4-5"

    # Retrieval / cost control (03-architecture.md Cost-control approach).
    top_n_chunks: int = 5
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    # Session 7 (release readiness): a fixed on-disk cache for fastembed's
    # ONNX model weights. `None` (the dev default, unchanged) leaves
    # fastembed's own default cache location in place — fine for
    # `docker-compose.yml`'s dev image, which never rebuilds mid-session.
    # docker/Dockerfile.prod sets this explicitly and pre-warms it at
    # *build* time (see that file's comment) specifically so the first
    # real request in a freshly started production container never pays
    # a live HuggingFace download — see ingestion/embeddings.py and
    # docs/project-memory/12-session-handoff.md for the real timeout this
    # was found fixing.
    embedding_cache_dir: str | None = None

    # T-05 cost-abuse control (06-security-threat-model.md) — a concrete
    # number chosen this session against no real pricing data yet, so it is
    # a conservative placeholder, not a measured value (same honesty
    # standard as NFR-007).
    max_question_length: int = 1000

    corpus_owner_role: str = Field(default="corpus_owner")
    knowledge_worker_role: str = Field(default="knowledge_worker")

    # Session 7 (release readiness) — structured logging level
    # (logging_config.py). Independent of GUNICORN's own `--log-level`
    # (docker/entrypoint.prod.sh), which controls gunicorn's own
    # worker-lifecycle log verbosity, not the application logger this
    # setting configures.
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
