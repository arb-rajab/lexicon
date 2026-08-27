"""Loads the Session 1 spike's real corpus (docs/spikes/session1-hybrid-
retrieval/corpus/) through the real ingestion pipeline — used by the NFR-001
recall regression test and the Session-1-adversarial-case proof test, so
both exercise real ingestion, not a synthetic fixture.
"""

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from lexicon.db import models
from lexicon.ingestion.service import ingest_document

SPIKE_CORPUS_DIR = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "spikes"
    / "session1-hybrid-retrieval"
    / "corpus"
)

# The 9 markdown source documents the spike measured against (excludes
# LICENCE-NOTE.md, which is provenance, not corpus content).
SPIKE_SOURCE_FILES = (
    "background-tasks.md",
    "cors.md",
    "dependencies.md",
    "docker.md",
    "middleware.md",
    "oauth2-jwt.md",
    "sql-databases.md",
    "websockets.md",
)


def load_spike_corpus(db: Session, filenames: tuple[str, ...] = SPIKE_SOURCE_FILES) -> uuid.UUID:
    corpus = models.Corpus(name="session1-spike-corpus")
    db.add(corpus)
    db.commit()
    db.refresh(corpus)

    for filename in filenames:
        raw_bytes = (SPIKE_CORPUS_DIR / filename).read_bytes()
        ingest_document(db, corpus.id, filename, raw_bytes)

    return corpus.id
