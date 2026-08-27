"""Test configuration.

Tests run against a REAL Postgres + pgvector instance (docker-compose's
`postgres` service) — no ADR-0002 grant-assertion test or NFR-001 recall
regression test can be honest against a mock. Point TEST_DATABASE_ADMIN_URL
at a real database before running pytest (defaults match docker-compose.yml
+ .env.example's dev values, using localhost:5433 since that's the port
docker-compose publishes to the host).
"""

import os
from pathlib import Path

os.environ.setdefault(
    "DATABASE_ADMIN_URL", "postgresql+psycopg://lexicon:lexicon@localhost:5433/lexicon"
)
os.environ.setdefault("APP_DB_ROLE", "lexicon_app")
os.environ.setdefault("APP_DB_PASSWORD", "lexicon_app_dev_only")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://lexicon_app:lexicon_app_dev_only@localhost:5433/lexicon",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/0")
# Deliberately never set ANTHROPIC_API_KEY here — tests must exercise the
# same stub-tier selection real app boot would make in this credential-less
# environment, not a special test-only path.
os.environ.pop("ANTHROPIC_API_KEY", None)

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402

BACKEND_ROOT = Path(__file__).resolve().parent.parent

ALL_TABLES = (
    "citation_verdict",
    "retrieved_chunk",
    "query_log",
    "chunk",
    "document",
    "corpus",
)


@pytest.fixture(scope="session", autouse=True)
def _migrated_schema() -> None:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def admin_engine():  # type: ignore[no-untyped-def]
    return create_engine(os.environ["DATABASE_ADMIN_URL"])


@pytest.fixture(autouse=True)
def _clean_tables(admin_engine, _migrated_schema):  # type: ignore[no-untyped-def]
    # Cleanup runs via the admin role, never the app role — the app role
    # cannot TRUNCATE/DELETE the audit tables by design (ADR-0002); using
    # admin privileges here is a test-isolation concern, not something the
    # application itself ever does at runtime.
    yield
    with admin_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(ALL_TABLES)} RESTART IDENTITY CASCADE"))


@pytest.fixture()
def db() -> Session:  # type: ignore[misc]
    from lexicon.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
