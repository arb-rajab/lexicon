import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from lexicon.api.deps import get_db
from lexicon.api.errors import not_found
from lexicon.api.schemas import DocumentDetailOut, DocumentOut, DocumentUploadOut
from lexicon.db import models
from lexicon.ingestion.service import UnsupportedDocumentType, ingest_document, remove_document

router = APIRouter(prefix="/api/v1/corpora/{corpus_id}/documents", tags=["documents"])


def _require_corpus(db: Session, corpus_id: uuid.UUID) -> models.Corpus:
    corpus = db.get(models.Corpus, corpus_id)
    if corpus is None:
        raise not_found("Corpus not found")
    return corpus


@router.post("", status_code=201, response_model=DocumentUploadOut)
async def upload_document(
    corpus_id: uuid.UUID, file: UploadFile, db: Session = Depends(get_db)
) -> DocumentUploadOut:
    _require_corpus(db, corpus_id)
    raw_bytes = await file.read()
    try:
        # ingest_document is synchronous, CPU-bound work (chunking, then
        # ONNX embedding inference — ingestion/embeddings.py has no async
        # path). Session 7 found this out the hard way: calling it inline
        # from this `async def` handler runs it directly on the event
        # loop, blocking it for the full duration of a real upload
        # (seconds, longer on the first call while fastembed downloads and
        # caches its ONNX model). Under docker/Dockerfile.prod's gunicorn
        # (unlike dev's bare `uvicorn --reload`), a blocked event loop
        # also stops the worker from answering the arbiter's heartbeat,
        # which reliably killed the worker mid-upload with a false
        # "WORKER TIMEOUT". `run_in_threadpool` moves the blocking call
        # off the event loop, matching how FastAPI already handles a
        # plain `def` route (api/query.py's `ask_question` gets this for
        # free from FastAPI itself; this route is `async def` because it
        # also awaits `file.read()` above, so it needs the opt-in here).
        result = await run_in_threadpool(
            ingest_document, db, corpus_id, file.filename or "untitled", raw_bytes
        )
    except UnsupportedDocumentType as exc:
        raise HTTPException(
            status_code=415,
            detail={
                "code": "unsupported_document_type",
                "message": str(exc),
                "field": "file",
            },
        ) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=415,
            detail={
                "code": "unsupported_document_type",
                "message": "File is not valid UTF-8 text",
                "field": "file",
            },
        ) from exc

    return DocumentUploadOut(document_id=result.document.id, status="ready")


@router.get("/{document_id}", response_model=DocumentDetailOut)
def get_document(
    corpus_id: uuid.UUID, document_id: uuid.UUID, db: Session = Depends(get_db)
) -> DocumentDetailOut:
    _require_corpus(db, corpus_id)
    document = (
        db.query(models.Document).filter_by(id=document_id, corpus_id=corpus_id).one_or_none()
    )
    if document is None:
        raise not_found("Document not found")
    return DocumentDetailOut(
        id=document.id,
        source_filename=document.source_filename,
        version=document.version,
        status="ready",
        chunk_count=len(document.chunks),
        uploaded_at=document.uploaded_at,
    )


@router.get("", response_model=list[DocumentOut])
def list_documents(corpus_id: uuid.UUID, db: Session = Depends(get_db)) -> list[DocumentOut]:
    _require_corpus(db, corpus_id)
    documents = db.query(models.Document).filter_by(corpus_id=corpus_id).all()
    return [
        DocumentOut(
            id=d.id,
            source_filename=d.source_filename,
            version=d.version,
            status="ready",
            chunk_count=len(d.chunks),
        )
        for d in documents
    ]


@router.delete("/{document_id}", status_code=204)
def delete_document(
    corpus_id: uuid.UUID, document_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    _require_corpus(db, corpus_id)
    removed = remove_document(db, corpus_id, document_id)
    if not removed:
        raise not_found("Document not found")
