"""T-06 regression coverage (06-security-threat-model.md) — the real
`413` enforcement api/documents.py now has. 05-api-contracts.md has
documented this response since Session 2, but nothing in the code path
actually produced it before this session: `upload_document` called
`await file.read()` unconditionally, buffering an unbounded body into
memory regardless of size.
"""

from fastapi.testclient import TestClient

from lexicon.config import Settings
from lexicon.main import app
from tests.support.auth import bearer_headers_for

client = TestClient(app)


def _create_corpus(name: str) -> tuple[str, dict[str, str]]:
    headers = bearer_headers_for(client, "upload-limit-user")
    resp = client.post("/api/v1/corpora", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return str(resp.json()["id"]), headers


def test_oversized_upload_returns_413(db, monkeypatch) -> None:
    corpus_id, AUTH_HEADERS = _create_corpus("upload-size-test")
    test_settings = Settings(max_upload_size_bytes=100)
    monkeypatch.setattr("lexicon.api.documents.get_settings", lambda: test_settings)

    oversized_content = b"# Heading\n\n" + (b"x" * 1000)
    resp = client.post(
        f"/api/v1/corpora/{corpus_id}/documents",
        files={"file": ("too-big.md", oversized_content, "text/markdown")},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "file_too_large"


def test_upload_within_limit_still_succeeds(db, monkeypatch) -> None:
    corpus_id, AUTH_HEADERS = _create_corpus("upload-size-ok-test")
    test_settings = Settings(max_upload_size_bytes=100)
    monkeypatch.setattr("lexicon.api.documents.get_settings", lambda: test_settings)

    small_content = b"# Heading\n\nShort body."
    resp = client.post(
        f"/api/v1/corpora/{corpus_id}/documents",
        files={"file": ("small.md", small_content, "text/markdown")},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
