"""Initial schema — 04-data-model.md's ERD, plus ADR-0003's injection_suspected column

Revision ID: 0001
Revises:
Create Date: 2026-08-27

pgvector extension and the HNSW index type must exist before the
CHUNK.embedding column migration (04-data-model.md's Migration approach
note) — both are created here, in the same revision that introduces CHUNK.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "corpus",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "document",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "corpus_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("corpus.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_filename", sa.Text, nullable=False),
        sa.Column("object_storage_key", sa.Text, nullable=True),
        sa.Column("content_hash", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_document_corpus_id", "document", ["corpus_id"])

    op.create_table(
        "chunk",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_heading", sa.Text, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chunk_document_id", "chunk", ["document_id"])
    # FR-005: content_tsv is a DB-generated column so OR-semantics
    # to_tsquery search (see retrieval/keyword.py) always has an up-to-date
    # index without the application ever writing to this column itself.
    op.execute(
        "ALTER TABLE chunk ADD COLUMN content_tsv tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED"
    )
    op.execute("CREATE INDEX ix_chunk_content_tsv ON chunk USING GIN (content_tsv)")
    op.execute(
        "CREATE INDEX ix_chunk_embedding_hnsw ON chunk USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "query_log",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "corpus_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("corpus.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("generated_answer", sa.Text, nullable=True),
        sa.Column("self_refused", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("final_answered", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("refusal_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_query_log_corpus_id_created_at", "query_log", ["corpus_id", "created_at"])

    op.create_table(
        "retrieved_chunk",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "query_log_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("query_log.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chunk.id"),
            nullable=False,
        ),
        sa.Column("keyword_rank", sa.Integer, nullable=True),
        sa.Column("vector_rank", sa.Integer, nullable=True),
        sa.Column("fusion_rank", sa.Integer, nullable=False),
        sa.Column("fusion_score", sa.Float, nullable=False),
    )
    op.create_index("ix_retrieved_chunk_query_log_id", "retrieved_chunk", ["query_log_id"])

    op.create_table(
        "citation_verdict",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "query_log_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("query_log.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chunk.id"),
            nullable=False,
        ),
        sa.Column("claim_text", sa.Text, nullable=False),
        sa.Column("entailed", sa.Boolean, nullable=False),
        sa.Column("injection_suspected", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("verifier_rationale", sa.Text, nullable=True),
    )
    op.create_index("ix_citation_verdict_query_log_id", "citation_verdict", ["query_log_id"])


def downgrade() -> None:
    op.drop_table("citation_verdict")
    op.drop_table("retrieved_chunk")
    op.drop_table("query_log")
    op.drop_table("chunk")
    op.drop_table("document")
    op.drop_table("corpus")
