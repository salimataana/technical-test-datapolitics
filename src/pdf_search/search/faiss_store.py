from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

import faiss

MANIFEST_FILENAME = "manifest.json"
MANIFEST_VERSION = 1


def _atomic_write(path: Path, writer: Callable[[Path], None]) -> None:
    """Write one file through a temporary sibling and an atomic rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)

    try:
        writer(temporary_path)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def create_index(embeddings):
    if getattr(embeddings, "ndim", None) != 2:
        raise ValueError("Embeddings must be a two-dimensional array")

    if embeddings.shape[0] == 0:
        raise ValueError("At least one embedding is required to create an index")

    if embeddings.shape[1] == 0:
        raise ValueError("Embeddings must have at least one dimension")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


def save_index(index, output_path):
    _atomic_write(
        Path(output_path),
        lambda temporary_path: faiss.write_index(index, str(temporary_path)),
    )


def load_index(input_path):
    return faiss.read_index(str(input_path))


def save_metadata(metadata, output_path):
    _atomic_write(
        Path(output_path),
        lambda temporary_path: _write_json(temporary_path, metadata),
    )


def load_metadata(input_path):
    with open(input_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_search_artifacts(
    index, metadata, output_dir, model_name: str
) -> dict[str, Any]:
    """Save index, metadata and a consistency manifest.

    Each file is written atomically. The manifest is written last and contains
    hashes and counts that allow readers to reject a partially updated store.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if index.ntotal != len(metadata):
        raise ValueError(
            "The number of FAISS vectors must match the number of metadata records"
        )

    index_path = output_dir / "index.faiss"
    metadata_path = output_dir / "metadata.json"
    manifest_path = output_dir / MANIFEST_FILENAME

    save_index(index, index_path)
    save_metadata(metadata, metadata_path)

    manifest = {
        "format_version": MANIFEST_VERSION,
        "index_file": index_path.name,
        "metadata_file": metadata_path.name,
        "vector_count": index.ntotal,
        "metadata_count": len(metadata),
        "embedding_dimension": index.d,
        "model_name": model_name,
        "index_sha256": _sha256(index_path),
        "metadata_sha256": _sha256(metadata_path),
    }
    _atomic_write(
        manifest_path,
        lambda temporary_path: _write_json(temporary_path, manifest),
    )

    return manifest


def load_manifest(input_path):
    with open(input_path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_artifacts(
    index,
    metadata,
    manifest,
    index_path,
    metadata_path,
    expected_model_name: str | None = None,
) -> None:
    """Validate that FAISS, metadata and manifest describe the same snapshot."""
    if not isinstance(manifest, dict):
        raise ValueError("The manifest must contain a JSON object")

    required_fields = {
        "format_version",
        "index_file",
        "metadata_file",
        "vector_count",
        "metadata_count",
        "embedding_dimension",
        "model_name",
        "index_sha256",
        "metadata_sha256",
    }
    missing_fields = required_fields - manifest.keys()
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Manifest fields missing: {missing}")

    if manifest["format_version"] != MANIFEST_VERSION:
        raise ValueError("Unsupported manifest version")

    if manifest["index_file"] != Path(index_path).name:
        raise ValueError("Manifest does not reference the loaded FAISS index")

    if manifest["metadata_file"] != Path(metadata_path).name:
        raise ValueError("Manifest does not reference the loaded metadata")

    if (
        expected_model_name is not None
        and manifest["model_name"] != expected_model_name
    ):
        raise ValueError(
            "The indexed model does not match the model configured by the API"
        )

    if index.ntotal != manifest["vector_count"]:
        raise ValueError("FAISS vector count does not match the manifest")

    if not isinstance(metadata, list):
        raise ValueError("Metadata must contain a JSON list")

    if len(metadata) != manifest["metadata_count"]:
        raise ValueError("Metadata count does not match the manifest")

    if index.d != manifest["embedding_dimension"]:
        raise ValueError("FAISS dimension does not match the manifest")

    if _sha256(index_path) != manifest["index_sha256"]:
        raise ValueError("FAISS index checksum does not match the manifest")

    if _sha256(metadata_path) != manifest["metadata_sha256"]:
        raise ValueError("Metadata checksum does not match the manifest")

    for vector_id, record in enumerate(metadata):
        if not isinstance(record, dict):
            raise ValueError("Each metadata record must be a JSON object")

        if record.get("vector_id") != vector_id:
            raise ValueError("Metadata vector IDs must be contiguous and ordered")


class FaissVectorStore:
    """Repository for FAISS, metadata and manifest persistence."""

    def __init__(
        self,
        storage_dir: Path,
        model_name: str,
    ) -> None:
        self.storage_dir = Path(storage_dir)
        self.model_name = model_name

    @property
    def index_path(self) -> Path:
        return self.storage_dir / "index.faiss"

    @property
    def metadata_path(self) -> Path:
        return self.storage_dir / "metadata.json"

    @property
    def manifest_path(self) -> Path:
        return self.storage_dir / MANIFEST_FILENAME

    def save(self, index, metadata) -> dict[str, Any]:
        return save_search_artifacts(
            index,
            metadata,
            self.storage_dir,
            model_name=self.model_name,
        )

    def load(self):
        missing_files = [
            path
            for path in (
                self.index_path,
                self.metadata_path,
                self.manifest_path,
            )
            if not path.exists()
        ]
        if missing_files:
            missing = ", ".join(str(path) for path in missing_files)
            raise RuntimeError(
                f"Search artifacts are missing: {missing}. Run ingestion first."
            )

        try:
            index = load_index(self.index_path)
            metadata = load_metadata(self.metadata_path)
            manifest = load_manifest(self.manifest_path)
            validate_artifacts(
                index,
                metadata,
                manifest,
                self.index_path,
                self.metadata_path,
                expected_model_name=self.model_name,
            )
        except Exception as error:
            raise RuntimeError(
                f"Search artifacts are invalid: {error}. Rebuild the index."
            ) from error

        return index, metadata, manifest

    def search(self, index, query_embedding, top_k: int = 5):
        return search_index(index, query_embedding, top_k)


def search_index(index, query_embedding, top_k=5):
    scores, indices = index.search(query_embedding, top_k)
    return scores[0], indices[0]
