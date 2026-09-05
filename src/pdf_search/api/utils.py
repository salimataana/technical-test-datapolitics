"""Application helpers for the FastAPI layer."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from pdf_search.config import MODEL_NAME
from pdf_search.ingestion.embedder import EmbeddingModel
from pdf_search.search.faiss_store import FaissVectorStore
from pdf_search.search.service import SearchService


def get_storage_dir() -> Path:
    return Path(os.getenv("PDF_SEARCH_STORAGE_DIR", "storage"))


def create_search_service(storage_dir: Path) -> SearchService:
    return SearchService(
        embedder=EmbeddingModel(model_name=MODEL_NAME),
        vector_store=FaissVectorStore(
            storage_dir=storage_dir,
            model_name=MODEL_NAME,
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.search_service = None
    service = create_search_service(get_storage_dir())

    try:
        service.load()
    except RuntimeError as error:
        raise RuntimeError(str(error)) from error

    app.state.search_service = service

    try:
        yield
    finally:
        app.state.search_service = None
