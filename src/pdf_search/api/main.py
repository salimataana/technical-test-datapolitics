from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from pdf_search.ingestion.embedder import create_embeddings
from pdf_search.search.faiss_store import load_index, load_metadata, search_index


index = None
metadata = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global index, metadata

    index_path = Path("storage/index.faiss")
    metadata_path = Path("storage/metadata.json")

    if not index_path.exists():
        raise RuntimeError(
            f"Index FAISS introuvable : {index_path}. "
            "Lancez d'abord l'ingestion."
        )

    if not metadata_path.exists():
        raise RuntimeError(
            f"Métadonnées introuvables : {metadata_path}. "
            "Lancez d'abord l'ingestion."
        )

    index = load_index(index_path)
    metadata = load_metadata(metadata_path)

    yield


app = FastAPI(
    title="PDF Semantic Search API",
    lifespan=lifespan,
)


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


@app.post("/search")
def search(request: SearchRequest):
    if index is None or metadata is None:
        raise HTTPException(
            status_code=503,
            detail="L'index de recherche n'est pas disponible.",
        )

    query_embedding = create_embeddings([request.query])

    top_k = min(request.top_k, index.ntotal)

    scores, indices = search_index(
        index,
        query_embedding,
        top_k,
    )

    results = []

    for score, index_position in zip(scores, indices):
        if index_position == -1:
            continue

        result = metadata[index_position]

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

    return {"query": request.query, "results": results}