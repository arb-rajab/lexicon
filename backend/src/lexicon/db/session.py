from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from lexicon.config import get_settings

settings = get_settings()

# Runtime engine — always the ADR-0002-restricted application role
# (INSERT/SELECT only on QUERY_LOG/RETRIEVED_CHUNK/CITATION_VERDICT).
# The API and pipeline code must only ever use this engine; migrations use
# the separate admin engine in alembic/env.py.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
