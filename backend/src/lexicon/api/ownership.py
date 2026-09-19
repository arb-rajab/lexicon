"""T-04 enforcement (06-security-threat-model.md): the row-level
ownership check every corpus_id-scoped endpoint must apply, in one place
rather than reimplemented per-router — the exact gap the threat model
named ("every {corpus_id}-scoped endpoint must independently verify the
caller's authorisation for that specific corpus_id, not merely that they
are authenticated at all") and that had no enforcement anywhere in the
API layer until this module existed.
"""

import uuid

from sqlalchemy.orm import Session

from lexicon.api.auth import CallerContext
from lexicon.api.errors import forbidden, not_found
from lexicon.db import models


def require_owned_corpus(db: Session, corpus_id: uuid.UUID, caller: CallerContext) -> models.Corpus:
    corpus = db.get(models.Corpus, corpus_id)
    if corpus is None:
        raise not_found("Corpus not found")
    if corpus.owner_id != caller.user_id:
        # 05-api-contracts.md's documented distinction: 404 for a
        # corpus_id that doesn't exist at all, 403 for one that does but
        # that this caller isn't authorised for — not collapsed into a
        # single code, matching the existing contract rather than
        # inventing a new disclosure posture here.
        raise forbidden("Not authorised for this corpus")
    return corpus
