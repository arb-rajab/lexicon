"""ADR-0002 — restricted application database role

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-27

Creates the runtime role the application connects as (DATABASE_URL) and
grants it exactly what ADR-0002 specifies: full CRUD on the corpus/document/
chunk tables (ingestion and document removal need DELETE there — FR-004),
but only INSERT/SELECT on QUERY_LOG/RETRIEVED_CHUNK/CITATION_VERDICT.
UPDATE/DELETE on those three tables is reserved to the migration/admin role
this script itself runs as. This is what T-07's grant-assertion test
(tests/test_adr0002_grants.py) asserts against a real connection.
"""
import os
from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = os.environ.get("APP_DB_ROLE", "lexicon_app")
APP_PASSWORD = os.environ.get("APP_DB_PASSWORD", "lexicon_app_dev_only")

AUDIT_TABLES = ("query_log", "retrieved_chunk", "citation_verdict")
MUTABLE_TABLES = ("corpus", "document", "chunk")


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_PASSWORD}';
            END IF;
        END
        $$;
        """
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")

    for table in MUTABLE_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")

    for table in AUDIT_TABLES:
        # ADR-0002's actual control: no UPDATE, no DELETE. Append-only from
        # the application's point of view — enforced by Postgres grants,
        # not application-layer discipline alone.
        op.execute(f"GRANT SELECT, INSERT ON {table} TO {APP_ROLE}")


def downgrade() -> None:
    for table in (*MUTABLE_TABLES, *AUDIT_TABLES):
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {APP_ROLE}")
