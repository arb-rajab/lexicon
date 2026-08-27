from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lexicon.api.corpora import router as corpora_router
from lexicon.api.documents import router as documents_router
from lexicon.api.query import router as query_router
from lexicon.api.query_logs import router as query_logs_router

app = FastAPI(title="lexicon", version="0.1.0")

app.include_router(corpora_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(query_logs_router)


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
    return {"status": "ok"}
