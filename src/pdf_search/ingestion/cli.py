import argparse
from pathlib import Path

from pdf_search.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DEFAULT_STORAGE_DIR,
    MODEL_NAME,
)
from pdf_search.ingestion.chunker import TextChunker
from pdf_search.ingestion.embedder import EmbeddingModel
from pdf_search.ingestion.extractor import PdfExtractor
from pdf_search.ingestion.pipeline import IngestionPipeline
from pdf_search.search.faiss_store import FaissVectorStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a semantic search index from PDF files"
    )
    parser.add_argument(
        "input_folder",
        type=Path,
        help="Folder containing PDF files",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default=DEFAULT_STORAGE_DIR,
        help="Output folder for the index and metadata (default: storage)",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    print("Dossier reçu :", args.input_folder)

    pipeline = IngestionPipeline(
        extractor=PdfExtractor(),
        chunker=TextChunker(
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP,
        ),
        embedder=EmbeddingModel(model_name=MODEL_NAME),
        vector_store=FaissVectorStore(
            storage_dir=args.storage_dir,
            model_name=MODEL_NAME,
        ),
    )

    try:
        stats = pipeline.run(args.input_folder)
    except ValueError as error:
        parser.error(str(error))

    print("Nombre de PDF trouvés :", stats.document_count)
    print("Metadata sauvegardées :", args.storage_dir / "metadata.json")
    print("Index FAISS sauvegardé :", args.storage_dir / "index.faiss")
    print("Manifest sauvegardé :", args.storage_dir / "manifest.json")
    print("Version du manifest :", stats.manifest["format_version"])
    print("Nombre de vecteurs dans FAISS :", stats.vector_count)
    print("Nombre total de chunks :", stats.total_chunks)
    print("Nombre total de pages :", stats.total_pages)
    print("Nombre de pages avec OCR :", stats.ocr_pages)


if __name__ == "__main__":
    main()
