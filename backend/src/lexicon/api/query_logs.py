import base64
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from lexicon.api.deps import get_db
from lexicon.api.errors import not_found
from lexicon.api.schemas import (
    CitationVerdictOut,
    QueryLogDetailOut,
    QueryLogListItem,
    QueryLogListOut,
    RetrievedChunkOut,
)
from lexicon.db import models

router = APIRouter(prefix="/api/v1/corpora/{corpus_id}/query-logs", tags=["query-logs"])


def _require_corpus(db: Session, corpus_id: uuid.UUID) -> models.Corpus:
    corpus = db.get(models.Corpus, corpus_id)
    if corpus is None:
        raise not_found("Corpus not found")
    return corpus


def _encode_cursor(created_at: datetime, log_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{log_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    created_at_str, id_str = raw.split("|", 1)
    return datetime.fromisoformat(created_at_str), uuid.UUID(id_str)


@router.get("", response_model=QueryLogListOut)
def list_query_logs(
    corpus_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = None,
    db: Session = Depends(get_db),
) -> QueryLogListOut:
    _require_corpus(db, corpus_id)
    q = db.query(models.QueryLog).filter_by(corpus_id=corpus_id)
    if cursor:
        created_at, log_id = _decode_cursor(cursor)
        q = q.filter(
            (models.QueryLog.created_at < created_at)
            | ((models.QueryLog.created_at == created_at) & (models.QueryLog.id < log_id))
        )
    rows = (
        q.order_by(models.QueryLog.created_at.desc(), models.QueryLog.id.desc())
        .limit(limit + 1)
        .all()
    )

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last.created_at, last.id)
        rows = rows[:limit]

    items = [
        QueryLogListItem(
            id=r.id,
            query_text=r.query_text,
            answered=r.final_answered,
            refusal_reason=r.refusal_reason,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return QueryLogListOut(items=items, next_cursor=next_cursor)


@router.get("/{query_log_id}", response_model=QueryLogDetailOut)
def get_query_log(
    corpus_id: uuid.UUID, query_log_id: uuid.UUID, db: Session = Depends(get_db)
) -> QueryLogDetailOut:
    _require_corpus(db, corpus_id)
    log = (
        db.query(models.QueryLog)
        .filter_by(id=query_log_id, corpus_id=corpus_id)
        .one_or_none()
    )
    if log is None:
        raise not_found("Query log not found")

    return QueryLogDetailOut(
        id=log.id,
        corpus_id=log.corpus_id,
        query_text=log.query_text,
        generated_answer=log.generated_answer,
        self_refused=log.self_refused,
        final_answered=log.final_answered,
        refusal_reason=log.refusal_reason,
        created_at=log.created_at,
        retrieved_chunks=[
            RetrievedChunkOut(
                chunk_id=rc.chunk_id,
                keyword_rank=rc.keyword_rank,
                vector_rank=rc.vector_rank,
                fusion_rank=rc.fusion_rank,
                fusion_score=rc.fusion_score,
            )
            for rc in log.retrieved_chunks
        ],
        citation_verdicts=[
            CitationVerdictOut(
                chunk_id=cv.chunk_id,
                claim_text=cv.claim_text,
                entailed=cv.entailed,
                injection_suspected=cv.injection_suspected,
                verifier_rationale=cv.verifier_rationale,
            )
            for cv in log.citation_verdicts
        ],
    )
