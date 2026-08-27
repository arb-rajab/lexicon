"""SQLAlchemy models for 04-data-model.md's ERD.

One deliberate reconciliation with ADR-0003 (written after 04-data-model.md):
`CitationVerdict.verifier_rationale` is populated by application code, not by
the verifier LLM's own free-text output — ADR-0003's structured-output
hardening gives the verifier model exactly two fields to respond with
(`entailed`, `injection_suspected`), no free-text surface. The rationale
column still exists for human audit (US-005) but is written from a small,
fixed set of application-generated strings (see pipeline/query_pipeline.py),
never from model output. See docs/project-memory/12-session-handoff.md
(Session 4) for the explicit note on this.
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBEDDING_DIM = 384  # BAAI/bge-small-en-v1.5, matching the Session 1 spike


class Base(DeclarativeBase):
    pass


class Corpus(Base):
    __tablename__ = "corpus"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(
        back_populates="corpus", cascade="all, delete-orphan"
    )
    query_logs: Mapped[list["QueryLog"]] = relationship(
        back_populates="corpus", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "document"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    corpus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("corpus.id", ondelete="CASCADE"), nullable=False
    )
    source_filename: Mapped[str] = mapped_column(Text, nullable=False)
    # Unused this session — Session 4's ingestion scope is minimal (chunk +
    # embed + store in pgvector, per this session's task); wiring uploads to
    # MinIO object storage is deferred, not silently dropped. See handoff.
    object_storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    corpus: Mapped[Corpus] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunk"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    section_heading: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    # content_tsv is a DB-generated column (GENERATED ALWAYS AS ... STORED,
    # created in the migration) — not written to by the application, so it
    # is intentionally not mapped as a settable ORM attribute here.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="chunks")


class QueryLog(Base):
    __tablename__ = "query_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    corpus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("corpus.id", ondelete="CASCADE"), nullable=False
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    self_refused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    final_answered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Not in the original 04-data-model.md ERD — needed so the API layer
    # (05-api-contracts.md) can distinguish the three refusal_reason values
    # (self_refused / verification_failed / no_candidates_retrieved) without
    # re-deriving it from retrieved-chunk/verdict rows on every read.
    refusal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    corpus: Mapped[Corpus] = relationship(back_populates="query_logs")
    retrieved_chunks: Mapped[list["RetrievedChunk"]] = relationship(
        back_populates="query_log", cascade="all, delete-orphan"
    )
    citation_verdicts: Mapped[list["CitationVerdict"]] = relationship(
        back_populates="query_log", cascade="all, delete-orphan"
    )


class RetrievedChunk(Base):
    __tablename__ = "retrieved_chunk"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("query_log.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chunk.id"), nullable=False
    )
    keyword_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vector_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fusion_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    fusion_score: Mapped[float] = mapped_column(Float, nullable=False)

    query_log: Mapped[QueryLog] = relationship(back_populates="retrieved_chunks")


class CitationVerdict(Base):
    __tablename__ = "citation_verdict"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("query_log.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chunk.id"), nullable=False
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    entailed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # ADR-0003 consequence: additive column alongside `entailed`. True when
    # the verifier's own self-report (or a fail-closed default, see
    # llm/anthropic_client.py) flagged the cited passage as attempting to
    # direct the verifier's behavior. The application layer treats this as
    # an automatic entailed=False regardless of the model's own value —
    # enforced in pipeline/query_pipeline.py, not trusted to the prompt alone.
    injection_suspected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Application-generated, not model free text — see module docstring.
    verifier_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    query_log: Mapped[QueryLog] = relationship(back_populates="citation_verdicts")
