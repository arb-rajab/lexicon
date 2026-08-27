import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from lexicon.api.deps import get_db, get_llm
from lexicon.api.errors import not_found
from lexicon.api.schemas import CitationOut, QueryRequest, QueryResponse
from lexicon.config import get_settings
from lexicon.db import models
from lexicon.llm.base import LLMClient, LLMProviderError
from lexicon.pipeline.query_pipeline import run_query_pipeline

router = APIRouter(prefix="/api/v1/corpora/{corpus_id}/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def ask_question(
    corpus_id: uuid.UUID,
    payload: QueryRequest,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
) -> QueryResponse:
    corpus = db.get(models.Corpus, corpus_id)
    if corpus is None:
        raise not_found("Corpus not found")

    settings = get_settings()
    # T-05 cost-abuse control (06-security-threat-model.md): a maximum
    # question-text length, closing both a cost-control gap and a T-03
    # query-text injection surface.
    if len(payload.question) > settings.max_question_length:
        limit = settings.max_question_length
        raise HTTPException(
            status_code=422,
            detail={
                "code": "question_too_long",
                "message": f"Question exceeds the {limit}-character limit",
                "field": "question",
            },
        )

    try:
        result = run_query_pipeline(
            db, llm, corpus_id, payload.question, top_n=settings.top_n_chunks
        )
    except LLMProviderError as exc:
        # 05-api-contracts.md: a failed generation/verification call is
        # never represented as a successful 200 with refusal_reason — it is
        # a distinct operational failure (502).
        raise HTTPException(
            status_code=502,
            detail={
                "code": "llm_provider_error",
                "message": str(exc),
                "field": None,
            },
        ) from exc

    return QueryResponse(
        query_log_id=result.query_log_id,
        answered=result.answered,
        answer=result.answer,
        citations=[
            CitationOut(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                source_filename=c.source_filename,
                section_heading=c.section_heading,
                claim_text=c.claim_text,
            )
            for c in result.citations
        ],
        refusal_reason=result.refusal_reason,
        retrieved_chunk_count=result.retrieved_chunk_count,
    )
