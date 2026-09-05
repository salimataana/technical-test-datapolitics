#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE="${1:-pdf-search:ci}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(mktemp -d)"
DATA_DIR="${WORK_DIR}/data"
STORAGE_DIR="${WORK_DIR}/storage"
CONTAINER_NAME="pdf-search-e2e-${RANDOM}-$$"
CONTAINER_USER="$(id -u):$(id -g)"
PORT="${PDF_SEARCH_E2E_PORT:-18000}"
HEALTH_FILE="${WORK_DIR}/health.json"
RESPONSE_FILE="${WORK_DIR}/response.json"

cleanup() {
    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    rm -rf "${WORK_DIR}"
}
trap cleanup EXIT

mkdir -p "${DATA_DIR}" "${STORAGE_DIR}"

echo "Starting Docker end-to-end test"
docker run --detach \
    --user "${CONTAINER_USER}" \
    --name "${CONTAINER_NAME}" \
    --env HF_HOME=/tmp/huggingface \
    --publish "127.0.0.1:${PORT}:8000" \
    --volume "${DATA_DIR}:/app/data" \
    --volume "${STORAGE_DIR}:/app/storage" \
    --volume "${SCRIPT_DIR}/create_e2e_pdf.py:/tmp/create_e2e_pdf.py:ro" \
    "${IMAGE}" \
    sh -c '
        python /tmp/create_e2e_pdf.py /app/data/e2e.pdf &&
        python -m pdf_search.ingestion.cli /app/data --storage-dir /app/storage &&
        exec uvicorn pdf_search.api.main:app --host 0.0.0.0 --port 8000
    ' >/dev/null

echo "Waiting for API"
if ! curl --fail --silent \
    --retry 30 \
    --retry-delay 2 \
    --retry-all-errors \
    --retry-connrefused \
    "http://127.0.0.1:${PORT}/health" >"${HEALTH_FILE}"; then
    echo "API did not become ready" >&2
    docker logs "${CONTAINER_NAME}" >&2
    exit 1
fi

curl --fail --silent --show-error \
    --request POST "http://127.0.0.1:${PORT}/search" \
    --header "Content-Type: application/json" \
    --data '{"query":"Docker semantic search test","top_k":1}' \
    >"${RESPONSE_FILE}"

python3 - "${HEALTH_FILE}" "${RESPONSE_FILE}" <<'PY'
import json
import sys
from pathlib import Path

health = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
response = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert health["status"] == "ok"
assert health["indexed_vectors"] >= 1

assert response["query"] == "Docker semantic search test"
assert len(response["results"]) == 1
result = response["results"][0]
assert result["document_name"] == "e2e.pdf"
assert result["page_number"] == 1
assert result["extraction_method"] == "text"
assert result["text"]
PY

echo "Docker end-to-end test passed"
