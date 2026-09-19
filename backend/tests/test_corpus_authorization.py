"""T-04 regression coverage (06-security-threat-model.md) — THE proof that
the multi-corpus API's cross-corpus IDOR gap is closed, not merely
documented as a requirement.

Before this session, every {corpus_id}-scoped endpoint (corpora.py,
documents.py, query.py, query_logs.py) accepted any syntactically valid
UUID with no check that the caller had any relationship to that corpus at
all — despite 06-security-threat-model.md naming this exact gap (T-04) as
a required control and 02-requirements.md stating "no multi-tenant... model
in v1" for a product whose actual API is a full multi-corpus surface
(`POST/GET /api/v1/corpora` operate over an unscoped collection of many
corpora, not a single per-deployment one). This file exercises that gap
end-to-end through the real FastAPI app: two distinct callers, one
corpus each, and an assertion that neither can reach the other's corpus
through any scoped endpoint — upload, read, query, or audit-log access.
"""

import uuid

from fastapi.testclient import TestClient

from lexicon.main import app

client = TestClient(app)

OWNER_A = {"X-User-Id": "user-a"}
OWNER_B = {"X-User-Id": "user-b"}


def _create_corpus(headers: dict[str, str], name: str) -> str:
    resp = client.post("/api/v1/corpora", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return str(resp.json()["id"])


def test_owner_cannot_read_another_owners_corpus_detail(db) -> None:
    corpus_id = _create_corpus(OWNER_A, "a-only")

    own_resp = client.get(f"/api/v1/corpora/{corpus_id}", headers=OWNER_A)
    assert own_resp.status_code == 200

    other_resp = client.get(f"/api/v1/corpora/{corpus_id}", headers=OWNER_B)
    assert other_resp.status_code == 403
    assert other_resp.json()["error"]["code"] == "forbidden"


def test_list_corpora_is_scoped_per_caller(db) -> None:
    corpus_a = _create_corpus(OWNER_A, "a-listing")
    corpus_b = _create_corpus(OWNER_B, "b-listing")

    a_ids = {c["id"] for c in client.get("/api/v1/corpora", headers=OWNER_A).json()}
    b_ids = {c["id"] for c in client.get("/api/v1/corpora", headers=OWNER_B).json()}

    assert corpus_a in a_ids
    assert corpus_a not in b_ids
    assert corpus_b in b_ids
    assert corpus_b not in a_ids


def test_non_owner_cannot_upload_or_list_documents(db) -> None:
    corpus_id = _create_corpus(OWNER_A, "a-docs")

    upload_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/documents",
        files={"file": ("notes.md", b"# hi", "text/markdown")},
        headers=OWNER_B,
    )
    assert upload_resp.status_code == 403

    list_resp = client.get(f"/api/v1/corpora/{corpus_id}/documents", headers=OWNER_B)
    assert list_resp.status_code == 403

    delete_resp = client.delete(
        f"/api/v1/corpora/{corpus_id}/documents/{uuid.uuid4()}", headers=OWNER_B
    )
    assert delete_resp.status_code == 403


def test_non_owner_cannot_query_another_owners_corpus(db) -> None:
    corpus_id = _create_corpus(OWNER_A, "a-query")
    with_own_upload = client.post(
        f"/api/v1/corpora/{corpus_id}/documents",
        files={"file": ("notes.md", b"# Notes\n\nSome real content here.", "text/markdown")},
        headers=OWNER_A,
    )
    assert with_own_upload.status_code == 201

    query_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/query",
        json={"question": "What does this corpus say?"},
        headers=OWNER_B,
    )
    assert query_resp.status_code == 403
    assert query_resp.json()["error"]["code"] == "forbidden"


def test_non_owner_cannot_read_query_logs(db) -> None:
    corpus_id = _create_corpus(OWNER_A, "a-logs")

    list_resp = client.get(f"/api/v1/corpora/{corpus_id}/query-logs", headers=OWNER_B)
    assert list_resp.status_code == 403

    detail_resp = client.get(
        f"/api/v1/corpora/{corpus_id}/query-logs/{uuid.uuid4()}", headers=OWNER_B
    )
    assert detail_resp.status_code == 403


def test_corpus_scoped_endpoints_require_caller_identity(db) -> None:
    corpus_id = _create_corpus(OWNER_A, "a-noauth")

    for method, path in (
        ("GET", f"/api/v1/corpora/{corpus_id}"),
        ("GET", f"/api/v1/corpora/{corpus_id}/documents"),
        ("GET", f"/api/v1/corpora/{corpus_id}/query-logs"),
    ):
        resp = client.request(method, path)
        assert resp.status_code == 401, f"{method} {path} should require X-User-Id"
        assert resp.json()["error"]["code"] == "unauthenticated"

    query_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/query", json={"question": "anything?"}
    )
    assert query_resp.status_code == 401
