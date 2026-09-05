import numpy as np

from pdf_search.ingestion.models import PageContent, TextChunk
from pdf_search.ingestion.pipeline import IngestionPipeline


class FakeExtractor:
    def extract(self, pdf_path):
        return [
            PageContent(
                document_name=pdf_path.name,
                page_number=1,
                text="Le conseil municipal se réunit.",
                extraction_method="text",
            )
        ]


class FakeChunker:
    def split(self, page):
        return [
            TextChunk(
                document_name=page.document_name,
                page_number=page.page_number,
                chunk_index=0,
                extraction_method=page.extraction_method,
                text=page.text,
            )
        ]


class FakeEmbedder:
    def encode(self, texts):
        assert texts == ["Le conseil municipal se réunit."]
        return np.array([[1.0, 0.0]], dtype="float32")


class FakeVectorStore:
    def __init__(self):
        self.saved_index = None
        self.saved_metadata = None

    def save(self, index, metadata):
        self.saved_index = index
        self.saved_metadata = metadata
        return {"format_version": 1}


def test_pipeline_composes_injected_components(tmp_path):
    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"not parsed by fake extractor")
    vector_store = FakeVectorStore()

    pipeline = IngestionPipeline(
        extractor=FakeExtractor(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        vector_store=vector_store,
    )

    stats = pipeline.run(tmp_path)

    assert stats.document_count == 1
    assert stats.total_pages == 1
    assert stats.total_chunks == 1
    assert stats.vector_count == 1
    assert vector_store.saved_index.ntotal == 1
    assert vector_store.saved_metadata[0]["vector_id"] == 0


def test_pipeline_rejects_folder_without_pdfs(tmp_path):
    pipeline = IngestionPipeline(
        extractor=FakeExtractor(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        vector_store=FakeVectorStore(),
    )

    try:
        pipeline.run(tmp_path)
    except ValueError as error:
        assert "No PDF files found" in str(error)
    else:
        raise AssertionError("Expected a ValueError")
