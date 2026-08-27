import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lexicon.api.deps import get_db
from lexicon.api.errors import not_found
from lexicon.api.schemas import CorpusCreate, CorpusDetailOut, CorpusOut
from lexicon.db import models

router = APIRouter(prefix="/api/v1/corpora", tags=["corpora"])


@router.post("", status_code=201, response_model=CorpusOut)
def create_corpus(payload: CorpusCreate, db: Session = Depends(get_db)) -> models.Corpus:
    corpus = models.Corpus(name=payload.name)
    db.add(corpus)
    db.commit()
    db.refresh(corpus)
    return corpus


@router.get("", response_model=list[CorpusOut])
def list_corpora(db: Session = Depends(get_db)) -> list[models.Corpus]:
    return db.query(models.Corpus).order_by(models.Corpus.created_at.desc()).all()


@router.get("/{corpus_id}", response_model=CorpusDetailOut)
def get_corpus(corpus_id: uuid.UUID, db: Session = Depends(get_db)) -> CorpusDetailOut:
    corpus = db.get(models.Corpus, corpus_id)
    if corpus is None:
        raise not_found("Corpus not found")
    document_count = db.query(models.Document).filter_by(corpus_id=corpus_id).count()
    return CorpusDetailOut(
        id=corpus.id,
        name=corpus.name,
        created_at=corpus.created_at,
        document_count=document_count,
    )
