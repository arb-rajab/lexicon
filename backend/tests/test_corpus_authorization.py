"""T-04 regression coverage (06-security-threat-model.md) — THE proof that
the multi-corpus API's cross-corpus IDOR gap is closed, not merely
documented as a requirement.

Before Session (T-04's own session), every {corpus_id}-scoped endpoint
(corpora.py, documents.py, query.py, query_logs.py) accepted any
syntactically valid UUID with no check that the caller had any relationship
to that corpus at all — despite 06-security-threat-model.md naming this
exact gap (T-04) as a required control and 02-requirements.md stating "no
multi-tenant... model in v1" for a product whose actual API is a full
multi-corpus surface (`POST/GET /api/v1/corpora` operate over an unscoped
collection of many corpora, not a single per-deployment one). This file
exercises that gap end-to-end through the real FastAPI app: two distinct
callers, one corpus each, and an assertion that neither can reach the
other's corpus through any scoped endpoint — upload, read, query, or audit-
log access.

ADR-0005 update: caller identity here now comes from a real, registered
account and a real verified bearer token (tests/support/auth.py), not a
caller-supplied X-User-Id header — this file proves T-04's ownership check
still holds against the real auth boundary, not that it merely holds
against whatever string a test hands it.
"""

import uuid

from fastapi.testclient import TestClient

from lexicon.main import app
from tests.support.auth import bearer_headers_for

client = TestClient(app)


def _create_corpus(headers: dict[str, str], name: str) -> str:
    resp = client.post("/api/v1/corpora", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return str(resp.json()["id"])


def test_owner_cannot_read_another_owners_corpus_detail(db) -> None:
    owner_a = bearer_headers_for(client, "user-a")
    owner_b = bearer_headers_for(client, "user-b")
    corpus_id = _create_corpus(owner_a, "a-only")

    own_resp = client.get(f"/api/v1/corpora/{corpus_id}", headers=owner_a)
    assert own_resp.status_code == 200

    other_resp = client.get(f"/api/v1/corpora/{corpus_id}", headers=owner_b)
    assert other_resp.status_code == 403
    assert other_resp.json()["error"]["code"] == "forbidden"


def test_list_corpora_is_scoped_per_caller(db) -> None:
    owner_a = bearer_headers_for(client, "user-a")
    owner_b = bearer_headers_for(client, "user-b")
    corpus_a = _create_corpus(owner_a, "a-listing")
    corpus_b = _create_corpus(owner_b, "b-listing")

    a_ids = {c["id"] for c in client.get("/api/v1/corpora", headers=owner_a).json()}
    b_ids = {c["id"] for c in client.get("/api/v1/corpora", headers=owner_b).json()}

    assert corpus_a in a_ids
    assert corpus_a not in b_ids
    assert corpus_b in b_ids
    assert corpus_b not in a_ids


def test_non_owner_cannot_upload_or_list_documents(db) -> None:
    owner_a = bearer_headers_for(client, "user-a")
    owner_b = bearer_headers_for(client, "user-b")
    corpus_id = _create_corpus(owner_a, "a-docs")

    upload_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/documents",
        files={"file": ("notes.md", b"# hi", "text/markdown")},
        headers=owner_b,
    )
    assert upload_resp.status_code == 403

    list_resp = client.get(f"/api/v1/corpora/{corpus_id}/documents", headers=owner_b)
    assert list_resp.status_code == 403

    delete_resp = client.delete(
        f"/api/v1/corpora/{corpus_id}/documents/{uuid.uuid4()}", headers=owner_b
    )
    assert delete_resp.status_code == 403


def test_non_owner_cannot_query_another_owners_corpus(db) -> None:
    owner_a = bearer_headers_for(client, "user-a")
    owner_b = bearer_headers_for(client, "user-b")
    corpus_id = _create_corpus(owner_a, "a-query")
    with_own_upload = client.post(
        f"/api/v1/corpora/{corpus_id}/documents",
        files={"file": ("notes.md", b"# Notes\n\nSome real content here.", "text/markdown")},
        headers=owner_a,
    )
    assert with_own_upload.status_code == 201

    query_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/query",
        json={"question": "What does this corpus say?"},
        headers=owner_b,
    )
    assert query_resp.status_code == 403
    assert query_resp.json()["error"]["code"] == "forbidden"


def test_non_owner_cannot_read_query_logs(db) -> None:
    owner_a = bearer_headers_for(client, "user-a")
    owner_b = bearer_headers_for(client, "user-b")
    corpus_id = _create_corpus(owner_a, "a-logs")

    list_resp = client.get(f"/api/v1/corpora/{corpus_id}/query-logs", headers=owner_b)
    assert list_resp.status_code == 403

    detail_resp = client.get(
        f"/api/v1/corpora/{corpus_id}/query-logs/{uuid.uuid4()}", headers=owner_b
    )
    assert detail_resp.status_code == 403


def test_corpus_scoped_endpoints_require_caller_identity(db) -> None:
    owner_a = bearer_headers_for(client, "user-a")
    corpus_id = _create_corpus(owner_a, "a-noauth")

    for method, path in (
        ("GET", f"/api/v1/corpora/{corpus_id}"),
        ("GET", f"/api/v1/corpora/{corpus_id}/documents"),
        ("GET", f"/api/v1/corpora/{corpus_id}/query-logs"),
    ):
        resp = client.request(method, path)
        assert resp.status_code == 401, f"{method} {path} should require a valid bearer token"
        assert resp.json()["error"]["code"] == "unauthenticated"

    query_resp = client.post(
        f"/api/v1/corpora/{corpus_id}/query", json={"question": "anything?"}
    )
    assert query_resp.status_code == 401


def test_forged_x_user_id_header_no_longer_grants_access(db) -> None:
    """ADR-0005's actual regression proof, at the ownership-boundary level:
    the pre-ADR-0005 vulnerability was that sending `X-User-Id: <victim>`
    made the caller BE that victim. Post-fix, that header is inert — a
    request that sends it (alongside no real credentials, or alongside a
    real token for a different, unrelated account) never gains the
    header's claimed identity's access.
    """
    owner_a = bearer_headers_for(client, "victim-user")
    corpus_id = _create_corpus(owner_a, "victim-corpus")

    # The exact pre-fix attack: no real credentials at all, just the header
    # an unauthenticated caller used to fully impersonate the victim.
    forged_only = client.get(
        f"/api/v1/corpora/{corpus_id}", headers={"X-User-Id": "victim-user"}
    )
    assert forged_only.status_code == 401
    assert forged_only.json()["error"]["code"] == "unauthenticated"

    # A real, valid token for a *different* account, with the header also
    # forged to claim the victim's identity — the header must still lose.
    attacker = bearer_headers_for(client, "attacker-user")
    attacker_with_forged_header = {**attacker, "X-User-Id": "victim-user"}
    still_forbidden = client.get(
        f"/api/v1/corpora/{corpus_id}", headers=attacker_with_forged_header
    )
    assert still_forbidden.status_code == 403
    assert still_forbidden.json()["error"]["code"] == "forbidden"
