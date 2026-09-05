# Technical Test - Datapolitics

[![CI](https://github.com/salimataana/technical-test-datapolitics/actions/workflows/ci.yml/badge.svg)](https://github.com/salimataana/technical-test-datapolitics/actions/workflows/ci.yml)

This project implements a local semantic search engine for French public PDF documents.

It provides:

- a PDF ingestion pipeline with native text extraction and French OCR;
- local multilingual embeddings and a FAISS vector index;
- a FastAPI endpoint for semantic search.

No paid external API is required.

## Quick start

### Requirements

- Python 3.12 or later;
- Docker, for the container workflow;
- uv 0.11.3, for dependency management;
- Tesseract OCR with the French language data.

On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra
```

Install uv and sync the locked dependencies:

```bash
python3 -m pip install --user "uv==0.11.3"
uv sync --locked --extra dev
```

### Build the search index

Place PDF files in `data/`, then run:

```bash
uv run --locked python -m pdf_search.ingestion.cli data
```

This creates:

```text
storage/index.faiss
storage/metadata.json
storage/manifest.json
```

The embedding model is downloaded from Hugging Face on its first use.

### Start the API

From the project root:

```bash
uv run --locked uvicorn pdf_search.api.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

Check its readiness:

```bash
curl http://127.0.0.1:8000/health
```

Search the indexed documents:

```bash
curl -X POST http://127.0.0.1:8000/search -H "Content-Type: application/json" -d '{"query":"Who signed the sponsorship agreement?","top_k":5}'
```

Swagger documentation is available at `http://127.0.0.1:8000/docs`.

## Docker execution

Build the image:

```bash
docker build -t pdf-search .
```

Run the complete Docker E2E test:

```bash
bash tests/e2e/docker_e2e.sh pdf-search
```

The image runs as a non-root `appuser`. The E2E test runs the complete flow in one container: it generates a deterministic PDF, builds the index and verifies `/health` and `/search`.

Run ingestion manually:

```bash
docker run --rm --user "$(id -u):$(id -g)" -v "$(pwd)/data:/app/data:ro" -v "$(pwd)/storage:/app/storage" pdf-search python -m pdf_search.ingestion.cli data --storage-dir /app/storage
```

Start the API with the generated artifacts:

```bash
docker run --rm --user "$(id -u):$(id -g)" -p 8000:8000 -v "$(pwd)/storage:/app/storage:ro" pdf-search
```

The storage volume persists the FAISS index, metadata and manifest. The model cache is not persisted by `docker run --rm` unless a cache volume is mounted.

## Tests and CI

Run the Python tests:

```bash
uv run --locked pytest -q
```

The tests cover extraction, OCR detection, chunking, embeddings, FAISS persistence, artifact validation, the ingestion pipeline, the search service and API validation.

The GitHub Actions workflow runs on pushes, pull requests and manual dispatch. It:

- installs Python 3.12 and French Tesseract data;
- installs dependencies from uv.lock;
- runs the Python test suite;
- builds the Docker image;
- runs the Docker E2E test.

## Rebuilding the index

The index is rebuilt from all top-level PDF files in the input folder:

```bash
uv run --locked python -m pdf_search.ingestion.cli data
```

Use another output directory when needed:

```bash
uv run --locked python -m pdf_search.ingestion.cli data --storage-dir /tmp/pdf-search-storage
```

Restart the API after rebuilding so it reloads the new index, metadata and manifest.

## Configuration

Shared runtime parameters are defined in `src/pdf_search/config.py`:

- `MODEL_NAME`: Hugging Face embedding model;
- `CHUNK_SIZE`: maximum number of characters per chunk;
- `CHUNK_OVERLAP`: number of overlapping characters between chunks;
- `EMBEDDING_BATCH_SIZE`: number of texts encoded at once;
- `OCR_LANGUAGE`, `OCR_MIN_TEXT_LENGTH` and `OCR_DPI`: OCR settings.

Rebuild the index after changing the model or chunking parameters.

## API reference

### `GET /health`

Returns:

```json
{
  "status": "ok",
  "indexed_vectors": 42
}
```

### `POST /search`

Request:

```json
{
  "query": "Who signed the sponsorship agreement?",
  "top_k": 5
}
```

Response:

```json
{
  "query": "Who signed the sponsorship agreement?",
  "results": [
    {
      "document_name": "document.pdf",
      "page_number": 5,
      "chunk_index": 0,
      "extraction_method": "text",
      "score": 0.43,
      "text": "..."
    }
  ]
}
```

`query` cannot be empty. `top_k` must be between 1 and 20 and is capped at the number of indexed vectors.

## Architecture

```text
PDF folder
    |
    v
Ingestion CLI
    |
    +-- IngestionPipeline
            |
            +-- PdfExtractor
            +-- TextChunker
            +-- EmbeddingModel
            +-- FaissVectorStore
                    |
                    +-- index.faiss
                    +-- metadata.json
                    +-- manifest.json

Search query
    |
    v
FastAPI
    |
    +-- SearchService
            |
            +-- EmbeddingModel
            +-- FaissVectorStore
            +-- JSON response
```

## Project structure

```text
.
├── data/                         # Input PDF documents
├── src/pdf_search/
│   ├── api/main.py               # FastAPI endpoints
│   ├── api/utils.py              # FastAPI lifecycle and service setup
│   ├── config.py                 # Shared application configuration
│   ├── ingestion/
│   │   ├── cli.py                # CLI entry point
│   │   ├── models.py             # PageContent and TextChunk
│   │   ├── extractor.py          # PdfExtractor
│   │   ├── chunker.py            # TextChunker
│   │   ├── embedder.py           # EmbeddingModel
│   │   └── pipeline.py           # IngestionPipeline
│   └── search/
│       ├── faiss_store.py        # FaissVectorStore and persistence
│       └── service.py             # SearchService
├── tests/
│   ├── e2e/                      # Docker E2E test and PDF fixture
│   └── test_*.py                 # Unit and integration tests
├── storage/                      # Generated search artifacts
├── .github/workflows/ci.yml      # GitHub Actions workflow
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

## Design

The code uses small classes with one responsibility:

- `PageContent` and `TextChunk`: immutable value objects;
- `PdfExtractor`: native text extraction and French OCR;
- `TextChunker`: overlapping character-based chunks;
- `EmbeddingModel`: lazy CPU model loading and vector generation;
- `FaissVectorStore`: FAISS persistence, manifest validation and search;
- `IngestionPipeline`: ingestion orchestration;
- `SearchService`: application-level search orchestration.

The components are composed through constructor injection. This keeps the CLI and API simple and allows tests to inject fake extractors, embedders and stores. The CLI and API use the classes directly without a compatibility wrapper layer.

## Technical behavior

### OCR

Native PDF text extraction is attempted first. If a page contains fewer than 20 extracted characters, it is rendered at 200 DPI and processed by Tesseract with `lang="fra"`.

Each chunk records whether it came from native text extraction or OCR. OCR can be inaccurate for tables, poor scans, unusual fonts and complex layouts.

### Embeddings and FAISS

The project uses `paraphrase-multilingual-MiniLM-L12-v2` on CPU. Embeddings are normalized, so the inner product used by `faiss.IndexFlatIP` is equivalent to cosine similarity.

`IndexFlatIP` performs an exact search and is appropriate for the small corpus in this exercise.

### Manifest and persistence

`manifest.json` records the format version, model name, vector counts, embedding dimension and SHA-256 checksums for the index and metadata.

Each artifact is written through a temporary sibling file and an atomic rename. The manifest is written last. At startup, the API validates the files, checksums, counts, dimensions, model name and metadata vector IDs. An inconsistent or corrupted store is rejected.

## Limitations and assumptions

- Search is semantic only and may rank similar text above exact names, dates, amounts or legal references.
- Character-based chunks can split words, sentences and paragraphs.
- OCR is not designed for handwritten content and may fail on complex layouts.
- The CLI processes only top-level PDF files with a `.pdf` extension, case-insensitive.
- The storage is local; there is no incremental indexing, database, authentication or access control.
- `IndexFlatIP` compares the query with every vector and is intended for a small corpus.
- The API uses local files and is configured for a single-process deployment.
- The model name, chunk size and OCR settings are configured in `src/pdf_search/config.py`.

## Production improvements

For a production system, I would consider:

- sentence- or paragraph-aware chunking;
- hybrid lexical and semantic search;
- a multilingual reranker;
- incremental indexing based on document hashes;
- versioned index releases and garbage collection;
- object storage and a metadata database;
- OCR preprocessing and quality scoring;
- structured logs, metrics and tracing;
- authentication and access control;
- an approximate FAISS index for larger corpora;
- asynchronous ingestion workers and a reverse proxy.
