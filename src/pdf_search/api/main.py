from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from pdf_search.ingestion.embedder import create_embeddings
from pdf_search.search.faiss_store import load_index, load_metadata, search_index


app = FastAPI(title="PDF Semantic Search API")

index = load_index(Path("storage/index.faiss"))
metadata = load_metadata(Path("storage/metadata.json"))


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/search")
def search(request: SearchRequest):
    query_embedding = create_embeddings([request.query])

    scores, indices = search_index(
        index,
        query_embedding,
        request.top_k,
    )

    results = []

    for score, index_position in zip(scores, indices):
        result = metadata[index_position]

        results.append(
            {
                "document_name": result["document_name"],
                "page_number": result["page_number"],
                "chunk_index": result["chunk_index"],
                "score": float(score),
                "text": result["text"],
            }
        )

    return {"results": results}