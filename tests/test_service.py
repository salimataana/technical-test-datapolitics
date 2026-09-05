import numpy as np
import pytest

from pdf_search.search.faiss_store import create_index
from pdf_search.search.service import SearchService


class FakeEmbedder:
    def encode(self, texts):
        assert texts == ["conseil municipal"]
        return np.array([[1.0, 0.0]], dtype="float32")


class FakeVectorStore:
    def __init__(self):
        self.index = create_index(
            np.array(
                [
                    [1.0, 0.0],
                    [0.0, 1.0],
                ],
                dtype="float32",
            )
        )
        self.metadata = [
            {
                "vector_id": 0,
                "document_name": "test.pdf",
                "page_number": 1,
                "chunk_index": 0,
                "extraction_method": "text",
                "text": "Le conseil municipal se réunit.",
            },
            {
                "vector_id": 1,
                "document_name": "other.pdf",
                "page_number": 2,
                "chunk_index": 0,
                "extraction_method": "ocr",
                "text": "Un autre document.",
            },
        ]

    def load(self):
        return self.index, self.metadata, {"format_version": 1}

    def search(self, index, query_embedding, top_k):
        scores, indices = index.search(query_embedding, top_k)
        return scores[0], indices[0]


def test_search_service_loads_and_searches():
    service = SearchService(FakeEmbedder(), FakeVectorStore())

    service.load()
    results = service.search("conseil municipal", top_k=1)

    assert service.is_ready
    assert service.indexed_vectors == 2
    assert results[0]["document_name"] == "test.pdf"
    assert results[0]["page_number"] == 1
    assert results[0]["score"] == 1.0


def test_search_service_rejects_blank_query():
    service = SearchService(FakeEmbedder(), FakeVectorStore())

    with pytest.raises(ValueError, match="empty"):
        service.search("   ")
