from typing import Any

from pdf_search.ingestion.embedder import EmbeddingModel
from pdf_search.search.faiss_store import FaissVectorStore


class SearchService:
    """Application service for loading an index and searching its chunks."""

    def __init__(
        self,
        embedder: EmbeddingModel,
        vector_store: FaissVectorStore,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.index = None
        self.metadata: list[dict[str, Any]] | None = None
        self.manifest: dict[str, Any] | None = None

    def load(self) -> None:
        self.index, self.metadata, self.manifest = self.vector_store.load()
        self.embedder.load()

    @property
    def is_ready(self) -> bool:
        return self.index is not None and self.metadata is not None

    @property
    def indexed_vectors(self) -> int:
        if self.index is None:
            return 0
        return self.index.ntotal

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("The query cannot be empty")

        if not self.is_ready:
            raise RuntimeError("The search index is not available")

        if self.indexed_vectors == 0:
            raise RuntimeError("The search index is empty")

        query_embedding = self.embedder.encode([query])
        scores, indices = self.vector_store.search(
            self.index,
            query_embedding,
            min(top_k, self.indexed_vectors),
        )

        results = []
        for score, index_position in zip(scores, indices):
            if index_position < 0:
                continue

            result = self.metadata[index_position]
            results.append(
                {
                    "document_name": result["document_name"],
                    "page_number": result["page_number"],
                    "chunk_index": result["chunk_index"],
                    "extraction_method": result.get("extraction_method", "text"),
                    "score": float(score),
                    "text": result["text"],
                }
            )

        return results
