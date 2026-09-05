from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pdf_search.config import DEFAULT_STORAGE_DIR, MODEL_NAME
from pdf_search.ingestion.chunker import TextChunker
from pdf_search.ingestion.embedder import EmbeddingModel
from pdf_search.ingestion.extractor import PdfExtractor
from pdf_search.ingestion.models import TextChunk
from pdf_search.search.faiss_store import FaissVectorStore, create_index


@dataclass(frozen=True, slots=True)
class IngestionStats:
    """Summary of the documents, pages, chunks and vectors created."""

    document_count: int
    total_pages: int
    total_chunks: int
    ocr_pages: int
    vector_count: int
    manifest: dict[str, Any]


class IngestionPipeline:
    """Coordinate PDF extraction, chunking, embeddings and persistence."""

    def __init__(
        self,
        extractor: PdfExtractor | None = None,
        chunker: TextChunker | None = None,
        embedder: EmbeddingModel | None = None,
        vector_store: FaissVectorStore | None = None,
    ) -> None:
        self.extractor = extractor or PdfExtractor()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or EmbeddingModel()
        self.vector_store = vector_store or FaissVectorStore(
            storage_dir=DEFAULT_STORAGE_DIR,
            model_name=MODEL_NAME,
        )

    def run(self, input_folder: Path) -> IngestionStats:
        input_folder = Path(input_folder)

        if not input_folder.exists():
            raise ValueError(f"Input folder does not exist: {input_folder}")

        if not input_folder.is_dir():
            raise ValueError(f"Input path is not a directory: {input_folder}")

        pdf_files = sorted(
            path
            for path in input_folder.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        )

        if not pdf_files:
            raise ValueError(f"No PDF files found in: {input_folder}")

        all_chunks: list[TextChunk] = []
        total_pages = 0
        ocr_pages = 0

        for pdf_file in pdf_files:
            pages = self.extractor.extract(pdf_file)
            total_pages += len(pages)
            ocr_pages += sum(page.extraction_method == "ocr" for page in pages)

            for page in pages:
                all_chunks.extend(self.chunker.split(page))

        if not all_chunks:
            raise ValueError(
                "No searchable text was extracted from the PDF files; "
                "index creation stopped"
            )

        embeddings = self.embedder.encode([chunk.text for chunk in all_chunks])
        index = create_index(embeddings)

        metadata = []
        for vector_id, chunk in enumerate(all_chunks):
            record = chunk.to_dict()
            record["vector_id"] = vector_id
            metadata.append(record)

        manifest = self.vector_store.save(index, metadata)

        return IngestionStats(
            document_count=len(pdf_files),
            total_pages=total_pages,
            total_chunks=len(all_chunks),
            ocr_pages=ocr_pages,
            vector_count=index.ntotal,
            manifest=manifest,
        )
