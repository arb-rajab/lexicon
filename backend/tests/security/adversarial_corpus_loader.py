"""Loads Session 6's committed adversarial injection corpus (docs/security/
adversarial-corpus/documents/) through the real ingestion pipeline
(lexicon.ingestion.service.ingest_document — real heading-aware chunking,
real embeddings, no LLM call), into its own corpus row, kept separate from
the Session 1 spike corpus (tests/support/spike_corpus.py) so retrieval
isolation (FR-014) keeps this suite's results independent of
golden_dataset.py's.
"""

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from lexicon.db import models
from lexicon.ingestion.service import ingest_document

ADVERSARIAL_CORPUS_DIR = (
    Path(__file__).resolve().parents[3] / "docs" / "security" / "adversarial-corpus" / "documents"
)


def load_adversarial_corpus(db: Session, filenames: tuple[str, ...]) -> uuid.UUID:
    corpus = models.Corpus(name="session6-adversarial-injection-corpus")
    db.add(corpus)
    db.commit()
    db.refresh(corpus)

    for filename in filenames:
        raw_bytes = (ADVERSARIAL_CORPUS_DIR / filename).read_bytes()
        ingest_document(db, corpus.id, filename, raw_bytes)

    return corpus.id
