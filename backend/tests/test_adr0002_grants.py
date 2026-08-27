"""ADR-0002 grant-assertion test — the T-07 mitigation, tested against a
real database connection using the application's actual runtime role
(DATABASE_URL), not a config review. Mirrors privacy-forge's
PolicyDefinitionGrantTest pattern for the structurally equivalent threat
(12-session-handoff.md's Session 3 note).

Postgres checks table privileges before row-matching, so these UPDATE/
DELETE attempts raise `permission denied` even though no row actually
matches the WHERE clause — the grant itself is what's under test, not
whether particular data exists.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from lexicon.db.session import engine as app_role_engine

_AUDIT_TABLE_UPDATE_COLUMNS = {
    "query_log": "query_text",
    "retrieved_chunk": "fusion_rank",
    "citation_verdict": "entailed",
}


@pytest.mark.parametrize("table,column", _AUDIT_TABLE_UPDATE_COLUMNS.items())
def test_app_role_cannot_update_audit_tables(table: str, column: str) -> None:
    with app_role_engine.connect() as conn:
        with pytest.raises(ProgrammingError, match="permission denied"):
            conn.execute(
                text(f"UPDATE {table} SET {column} = {column} WHERE id = :id"),
                {"id": str(uuid.uuid4())},
            )
        conn.rollback()


@pytest.mark.parametrize("table", _AUDIT_TABLE_UPDATE_COLUMNS.keys())
def test_app_role_cannot_delete_from_audit_tables(table: str) -> None:
    with app_role_engine.connect() as conn:
        with pytest.raises(ProgrammingError, match="permission denied"):
            conn.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": str(uuid.uuid4())})
        conn.rollback()


@pytest.mark.parametrize("table", _AUDIT_TABLE_UPDATE_COLUMNS.keys())
def test_app_role_can_select_from_audit_tables(table: str) -> None:
    # Confirms the SELECT grant actually exists — without this, the
    # UPDATE/DELETE-denial tests above could pass vacuously for a role with
    # no grants on the table at all, rather than exactly the grant ADR-0002
    # specifies (SELECT, INSERT — not UPDATE, DELETE).
    with app_role_engine.connect() as conn:
        conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
