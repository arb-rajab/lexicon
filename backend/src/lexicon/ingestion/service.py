"""Ingestion orchestration (FR-001–FR-004).

Deliberately synchronous within the request, not handed off to a queue +
worker — a stated simplification against 03-architecture.md's async
ingestion-worker design, scoped down to match this session's task
("Minimal document ingestion"). See docs/project-memory/12-session-
handoff.md (Session 4) for why this is flagged rather than silent: at the
corpus sizes this session actually exercises (the Session 1 spike corpus,
single-digit documents), synchronous ingestion is well within NFR-008's
30s p95 budget, and the queue/worker split is a scaling concern this
session doesn't need to solve to prove the pipeline this task is actually
about (generation + verification + refusal).

PDF-text-layer ingestion (also named in FR-001) is out of scope this
session too, for the same reason — not silently dropped, just not needed
to exercise the corpus this session reuses (Session 1's markdown corpus).
"""

import hashlib
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from lexicon.db import models
from lexicon.ingestion.chunking import chunk_markdown
from lexicon.ingestion.embeddings import embed_texts

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt"}


class UnsupportedDocumentType(Exception):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__(f"Unsupported document type: {filename}")


@dataclass
class IngestResult:
    document: models.Document
    chunk_count: int
    no_op: bool  # content_hash unchanged from the existing version (FR-004)


def _extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def ingest_document(
    db: Session, corpus_id: uuid.UUID, filename: str, raw_bytes: bytes
) -> IngestResult:
    if _extension(filename) not in SUPPORTED_EXTENSIONS:
        raise UnsupportedDocumentType(filename)

    text = raw_bytes.decode("utf-8")
    content_hash = hashlib.sha256(raw_bytes).hexdigest()

    existing = (
        db.query(models.Document)
        .filter_by(corpus_id=corpus_id, source_filename=filename)
        .one_or_none()
    )

    if existing is not None and existing.content_hash == content_hash:
        return IngestResult(document=existing, chunk_count=len(existing.chunks), no_op=True)

    if existing is not None:
        # FR-004: only this document's chunks are touched — a document_id-
        # scoped delete, never corpus-scoped.
        db.query(models.Chunk).filter(models.Chunk.document_id == existing.id).delete()
        existing.content_hash = content_hash
        existing.version += 1
        document = existing
    else:
        document = models.Document(
            corpus_id=corpus_id,
            source_filename=filename,
            content_hash=content_hash,
            version=1,
        )
        db.add(document)
        db.flush()

    candidates = chunk_markdown(text)
    embeddings = embed_texts([c.content for c in candidates])
    for candidate, embedding in zip(candidates, embeddings, strict=True):
        db.add(
            models.Chunk(
                document_id=document.id,
                section_heading=candidate.heading,
                position=candidate.position,
                content=candidate.content,
                embedding=embedding,
            )
        )

    db.commit()
    db.refresh(document)
    return IngestResult(document=document, chunk_count=len(candidates), no_op=False)


def remove_document(db: Session, corpus_id: uuid.UUID, document_id: uuid.UUID) -> bool:
    document = (
        db.query(models.Document).filter_by(id=document_id, corpus_id=corpus_id).one_or_none()
    )
    if document is None:
        return False
    db.delete(document)  # ON DELETE CASCADE removes its chunks (04-data-model.md invariant)
    db.commit()
    return True
