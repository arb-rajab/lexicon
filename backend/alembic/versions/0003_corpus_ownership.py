"""T-04 — per-corpus ownership scoping

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-19

Adds CORPUS.owner_id (06-security-threat-model.md T-04): every
corpus_id-scoped endpoint now checks the caller's identity (the X-User-Id
header, lexicon.api.auth.CallerContext) against this column before
allowing access — see lexicon/api/ownership.py. No backfill strategy is
needed beyond the placeholder default below: this project has never had a
real, persisted deployment (08-deployment-and-operations.md — no live
instance exists or has ever existed), so there is no real pre-existing
corpus data to reconcile against a caller identity that didn't exist
before this migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Only used transiently, for any row that predates this column (none in
# any real deployment — see module docstring) — removed as the column's
# default immediately after backfilling, so every corpus created from this
# point on must supply a real owner_id explicitly.
_PLACEHOLDER_OWNER = "__unowned_pre_t04__"


def upgrade() -> None:
    op.add_column(
        "corpus",
        sa.Column("owner_id", sa.Text, nullable=False, server_default=_PLACEHOLDER_OWNER),
    )
    op.alter_column("corpus", "owner_id", server_default=None)
    op.create_index("ix_corpus_owner_id", "corpus", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_corpus_owner_id", table_name="corpus")
    op.drop_column("corpus", "owner_id")
