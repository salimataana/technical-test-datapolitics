import numpy as np
from fastapi.testclient import TestClient

import pdf_search.api.main as api_main
from pdf_search.search.faiss_store import create_index


client = TestClient(api_main.app)


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


def test_search_returns_matching_result(monkeypatch, tmp_path):
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    (storage_dir / "index.faiss").touch()
    (storage_dir / "metadata.json").touch()

    fake_index = create_index(
        np.array(
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ],
            dtype="float32",
        )
    )
    fake_metadata = [
        {
            "document_name": "test.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "extraction_method": "text",
            "text": "Le conseil municipal se réunit.",
        },
        {
            "document_name": "other.pdf",
            "page_number": 2,
            "chunk_index": 0,
            "extraction_method": "ocr",
            "text": "Un autre document.",
        },
    ]

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(api_main, "load_index", lambda path: fake_index)
    monkeypatch.setattr(api_main, "load_metadata", lambda path: fake_metadata)
    monkeypatch.setattr(
        api_main,
        "create_embeddings",
        lambda texts: np.array([[1.0, 0.0]], dtype="float32"),
    )

    with TestClient(api_main.app) as test_client:
        response = test_client.post(
            "/search",
            json={"query": "conseil municipal", "top_k": 1},
        )

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
