#!/bin/sh
# Production entrypoint (Session 7). Mirrors ../Dockerfile's dev CMD
# (`alembic upgrade head && uvicorn lexicon.main:app`) for the migration
# step — same DATABASE_ADMIN_URL-as-migration-role / DATABASE_URL-as-
# runtime-role split (ADR-0002) — and replaces bare uvicorn with gunicorn
# managing multiple uvicorn worker processes for the serve step.
#
# WEB_CONCURRENCY (default 4) is a config placeholder, not a load-tested
# number — no capacity/load data exists for this project (see
# docs/project-memory/08-deployment-and-operations.md's Capacity and cost
# notes), same honesty standard as config.py's `max_question_length`.
#
# gunicorn's own --access-logfile is deliberately not set: per-request
# access logging is already produced, in structured JSON, by
# lexicon.main's `log_requests` middleware (logging_config.py). Enabling
# gunicorn's separate access log too would duplicate every request as a
# second, differently-formatted line. --error-logfile - is kept, since
# that carries worker boot/crash/reload events the app-level middleware
# never sees.
set -eu

alembic upgrade head

exec gunicorn lexicon.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${WEB_CONCURRENCY:-4}" \
    --bind 0.0.0.0:8000 \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --graceful-timeout 30 \
    --error-logfile - \
    --log-level "${LOG_LEVEL:-info}"
