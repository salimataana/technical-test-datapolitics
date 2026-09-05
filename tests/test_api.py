import pytest
from fastapi.testclient import TestClient

import pdf_search.api.main as api_main
import pdf_search.api.utils as api_utils

client = TestClient(api_main.app)


class FakeSearchService:
    def __init__(self):
        self.is_ready = True
        self.indexed_vectors = 2

    def load(self):
        pass

    def search(self, query, top_k):
        return [
            {
                "document_name": "test.pdf",
                "page_number": 1,
                "chunk_index": 0,
                "extraction_method": "text",
                "score": 1.0,
                "text": "Le conseil municipal se réunit.",
            }
        ]


def test_search_rejects_invalid_top_k():
    response = client.post(
        "/search",
        json={
            "query": "test",
            "top_k": 0,
        },
    )

    assert response.status_code == 422


def test_search_rejects_top_k_above_limit():
    response = client.post(
        "/search",
        json={
            "query": "test",
            "top_k": 21,
        },
    )

    assert response.status_code == 422


def test_search_rejects_blank_query():
    response = client.post(
        "/search",
        json={
            "query": "   ",
            "top_k": 1,
        },
    )

    assert response.status_code == 422


def test_search_returns_matching_result(monkeypatch):
    fake_service = FakeSearchService()
    monkeypatch.setattr(
        api_utils,
        "create_search_service",
        lambda storage_dir: fake_service,
    )

    with TestClient(api_main.app) as test_client:
        health_response = test_client.get("/health")
        response = test_client.post(
            "/search",
            json={"query": "conseil municipal", "top_k": 1},
        )

    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "ok",
        "indexed_vectors": 2,
    }
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "conseil municipal"
    assert payload["results"] == [
        {
            "document_name": "test.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "extraction_method": "text",
            "score": 1.0,
            "text": "Le conseil municipal se réunit.",
        }
    ]


def test_startup_rejects_invalid_artifacts(monkeypatch):
    class BrokenSearchService:
        def load(self):
            raise RuntimeError("Search artifacts are invalid: checksum mismatch")

    monkeypatch.setattr(
        api_utils,
        "create_search_service",
        lambda storage_dir: BrokenSearchService(),
    )

    with pytest.raises(RuntimeError, match="Search artifacts are invalid"):
        with TestClient(api_main.app):
            pass
