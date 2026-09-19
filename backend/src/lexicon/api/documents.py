import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from lexicon.api.auth import CallerContext, get_caller
from lexicon.api.deps import get_db
from lexicon.api.errors import not_found
from lexicon.api.ownership import require_owned_corpus
from lexicon.api.schemas import DocumentDetailOut, DocumentOut, DocumentUploadOut
from lexicon.config import get_settings
from lexicon.db import models
from lexicon.ingestion.service import UnsupportedDocumentType, ingest_document, remove_document

router = APIRouter(prefix="/api/v1/corpora/{corpus_id}/documents", tags=["documents"])

_UPLOAD_READ_CHUNK_SIZE = 1024 * 1024  # 1 MiB


async def _read_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """T-06 cost/resource-abuse control (06-security-threat-model.md):
    05-api-contracts.md has always documented a `413` "exceeds the
    configured size limit" response, but nothing enforced it until now —
    `await file.read()` pulled the entire body into memory unconditionally.
    Reads in bounded chunks and aborts as soon as the running total crosses
    the limit, rather than trusting the client-supplied `Content-Length`
    header (which a caller can simply omit or lie about) and rather than
    buffering an oversized body fully before rejecting it.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_UPLOAD_READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail={
                    "code": "file_too_large",
                    "message": f"Uploaded file exceeds the {max_bytes}-byte limit",
                    "field": "file",
                },
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("", status_code=201, response_model=DocumentUploadOut)
async def upload_document(
    corpus_id: uuid.UUID,
    file: UploadFile,
    db: Session = Depends(get_db),
    caller: CallerContext = Depends(get_caller),
) -> DocumentUploadOut:
    require_owned_corpus(db, corpus_id, caller)
    settings = get_settings()
    raw_bytes = await _read_bounded(file, settings.max_upload_size_bytes)
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
    corpus_id: uuid.UUID,
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    caller: CallerContext = Depends(get_caller),
) -> DocumentDetailOut:
    require_owned_corpus(db, corpus_id, caller)
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
def list_documents(
    corpus_id: uuid.UUID,
    db: Session = Depends(get_db),
    caller: CallerContext = Depends(get_caller),
) -> list[DocumentOut]:
    require_owned_corpus(db, corpus_id, caller)
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
    corpus_id: uuid.UUID,
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    caller: CallerContext = Depends(get_caller),
) -> None:
    require_owned_corpus(db, corpus_id, caller)
    removed = remove_document(db, corpus_id, document_id)
    if not removed:
        raise not_found("Document not found")
