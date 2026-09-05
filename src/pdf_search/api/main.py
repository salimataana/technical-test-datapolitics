from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from pdf_search.api.utils import lifespan

app = FastAPI(
    title="PDF Semantic Search API",
    lifespan=lifespan,
)

app.state.search_service = None


class SearchRequest(BaseModel):
    """Request body accepted by the semantic search endpoint."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


@app.post("/search")
def search(request: Request, search_request: SearchRequest):
    if not search_request.query.strip():
        raise HTTPException(
            status_code=422,
            detail="La requête ne peut pas être vide.",
        )

    service = request.app.state.search_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="L'index de recherche n'est pas disponible.",
        )

    try:
        results = service.search(
            query=search_request.query,
            top_k=search_request.top_k,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return {"query": search_request.query, "results": results}


@app.get("/health")
def health(request: Request):
    service = request.app.state.search_service
    if service is None or not service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="L'index de recherche n'est pas disponible.",
        )

    return {
        "status": "ok",
        "indexed_vectors": service.indexed_vectors,
    }
