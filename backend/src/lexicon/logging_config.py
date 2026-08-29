"""Structured application logging (Session 7 — release readiness).

**Correcting an assumption this session started with:** this session's own
task framing described "structured logging" as "already partially present
given the audit-table work from Session 6." That is not accurate, and is
worth stating plainly rather than quietly building on top of a false
premise. `QUERY_LOG`/`RETRIEVED_CHUNK`/`CITATION_VERDICT`
(`db/models.py`, ADR-0002) are a permanent, tamper-evident **audit trail**
of pipeline decisions — what was asked, retrieved, generated, and
verified — written to Postgres, readable via `api/query_logs.py`, and
deliberately restricted from UPDATE/DELETE by the app's own DB role. They
are not operational log lines, were never emitted through Python's
`logging` module, and do not tell an operator anything about process
health, request latency, or errors. Before this session, `grep -r
"import logging" backend/src` matched nothing at all outside
`alembic/env.py`. This file is what actually adds structured **operational**
logging — a distinct, complementary concern to the audit trail, not a
continuation of it.

JSON-lines to stdout, one object per record — the shape a real deployment's
log collector (not built or run by this project, see
`docs/project-memory/08-deployment-and-operations.md`'s Observability
section for what that would take) would parse without a custom regex.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from lexicon.config import get_settings

_UVICORN_AND_GUNICORN_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "gunicorn.error",
    "gunicorn.access",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            payload.update(extra_fields)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Idempotent — safe to call from both `main.py` (import time, so it's
    active even under `pytest`'s TestClient) and gunicorn's own worker boot
    (each worker process re-imports `lexicon.main`, so this runs again per
    worker; re-running it just replaces the same handler, not a leak)."""
    settings = get_settings()
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # uvicorn/gunicorn's own loggers otherwise attach their own
    # non-JSON-formatted handlers — route their records through the same
    # root handler instead, so every line on stdout is consistently
    # JSON, not a mix of two formats.
    for name in _UVICORN_AND_GUNICORN_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
