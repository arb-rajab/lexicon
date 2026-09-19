import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lexicon.api.auth import CallerContext, get_caller
from lexicon.api.deps import get_db
from lexicon.api.ownership import require_owned_corpus
from lexicon.api.schemas import CorpusCreate, CorpusDetailOut, CorpusOut
from lexicon.db import models

router = APIRouter(prefix="/api/v1/corpora", tags=["corpora"])


@router.post("", status_code=201, response_model=CorpusOut)
def create_corpus(
    payload: CorpusCreate,
    db: Session = Depends(get_db),
    caller: CallerContext = Depends(get_caller),
) -> models.Corpus:
    corpus = models.Corpus(name=payload.name, owner_id=caller.user_id)
    db.add(corpus)
    db.commit()
    db.refresh(corpus)
    return corpus


@router.get("", response_model=list[CorpusOut])
def list_corpora(
    db: Session = Depends(get_db),
    caller: CallerContext = Depends(get_caller),
) -> list[models.Corpus]:
    # T-04 (06-security-threat-model.md): a caller only ever sees corpora
    # they own — this endpoint previously listed every corpus in the
    # deployment to any caller, unscoped.
    return (
        db.query(models.Corpus)
        .filter_by(owner_id=caller.user_id)
        .order_by(models.Corpus.created_at.desc())
        .all()
    )


@router.get("/{corpus_id}", response_model=CorpusDetailOut)
def get_corpus(
    corpus_id: uuid.UUID,
    db: Session = Depends(get_db),
    caller: CallerContext = Depends(get_caller),
) -> CorpusDetailOut:
    corpus = require_owned_corpus(db, corpus_id, caller)
    document_count = db.query(models.Document).filter_by(corpus_id=corpus_id).count()
    return CorpusDetailOut(
        id=corpus.id,
        name=corpus.name,
        created_at=corpus.created_at,
        document_count=document_count,
    )
