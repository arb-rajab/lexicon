"""ADR-0005 — real instance-level authentication: the app_user table

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-23

Creates `app_user` (password-authenticated accounts issuing real session
tokens, lexicon.security.tokens) and grants the ADR-0002 application
runtime role ordinary CRUD on it — the same mutable-table treatment
`corpus`/`document`/`chunk` already get, not the audit tables' restricted
INSERT/SELECT-only grant, since this table has real update/delete needs
(e.g. a future password-change/account-deletion path) and carries no
audit-trail tamper-evidence requirement (ADR-0002 was reasoned specifically
against QUERY_LOG/RETRIEVED_CHUNK/CITATION_VERDICT, not this table).

No backfill: `08-deployment-and-operations.md`/`12-session-handoff.md`
confirm this project has never had a real, persisted deployment, so there
is no pre-existing X-User-Id-header-string data to reconcile into real
accounts. Every existing `CORPUS.owner_id`/`QUERY_LOG` row from prior
sessions' local testing is disposable local-dev data, matching this
project's established precedent (docker-compose down -v between sessions).
"""

import os
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = os.environ.get("APP_DB_ROLE", "lexicon_app")


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON app_user TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON app_user FROM {APP_ROLE}")
    op.drop_table("app_user")
