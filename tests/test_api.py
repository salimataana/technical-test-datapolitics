from fastapi.testclient import TestClient

from pdf_search.api.main import app


client = TestClient(app)


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