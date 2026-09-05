"""Application configuration shared by the ingestion and API layers."""

from pathlib import Path

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
EMBEDDING_BATCH_SIZE = 32
OCR_LANGUAGE = "fra"
OCR_MIN_TEXT_LENGTH = 20
OCR_DPI = 200
DEFAULT_STORAGE_DIR = Path("storage")
