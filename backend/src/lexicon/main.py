import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from lexicon.api.corpora import router as corpora_router
from lexicon.api.deps import get_db
from lexicon.api.documents import router as documents_router
from lexicon.api.query import router as query_router
from lexicon.api.query_logs import router as query_logs_router
from lexicon.logging_config import configure_logging

# Runs at import time — active under `uvicorn`/gunicorn's real worker boot
# and under `pytest`'s `TestClient(app)` alike (see test_health.py), so
# there is exactly one place this is ever configured, not one per entry
# point.
configure_logging()
logger = logging.getLogger("lexicon.request")

app = FastAPI(title="lexicon", version="0.1.0")

app.include_router(corpora_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(query_logs_router)


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # Not correlated with QUERY_LOG's own primary key (db/models.py) — this
    # ID identifies one HTTP request/response cycle for operational log
    # correlation, independent of whether that request happens to write an
    # audit row at all (e.g. GET /health never does).
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["x-request-id"] = request_id
    logger.info(
        "request completed",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        },
    )
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # 05-api-contracts.md's Error model: {"error": {"code", "message", "field"}}
    # — not FastAPI's default {"detail": ...} shape. Route handlers raise
    # HTTPException(detail={"code", "message", "field"}); anything else
    # (e.g. a bare-string detail from a library-raised HTTPException) is
    # wrapped rather than assumed to already match the contract.
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        error = detail
    else:
        error = {"code": "http_error", "message": str(detail), "field": None}
    return JSONResponse(status_code=exc.status_code, content={"error": error})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc), "field": None}},
    )


@app.get("/health")
def health() -> dict[str, str]:
    # Liveness only — deliberately checks nothing beyond "the process is
    # up and can return a response." Existed since Session 4
    # (docker-compose.yml's `backend` healthcheck already targets this).
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> JSONResponse:
    # Readiness (Session 7) — distinct from /health above: this checks the
    # one real runtime dependency the app actually has (Postgres; see
    # db/session.py). REDIS_URL/MinIO are provisioned in the compose stack
    # (docker-compose.yml, docker-compose.prod.yml) for future use per
    # 03-architecture.md, but no application code path calls either today
    # (ingestion/service.py's own docstring already states the MinIO half
    # of this the same way) — a readiness check cannot honestly assert
    # dependencies the app doesn't actually have yet, so only Postgres is
    # checked here.
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error(
            "readiness check failed: database unreachable",
            extra={"extra_fields": {"error": str(exc)}},
        )
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(status_code=200, content={"status": "ready"})
