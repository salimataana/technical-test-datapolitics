import json

import numpy as np
import pytest

from pdf_search.search.faiss_store import (
    FaissVectorStore,
    create_index,
    load_index,
    load_manifest,
    load_metadata,
    save_search_artifacts,
    search_index,
    validate_artifacts,
)


def _metadata(count):
    return [
        {
            "vector_id": vector_id,
            "document_name": "test.pdf",
            "page_number": 1,
            "chunk_index": vector_id,
            "extraction_method": "text",
            "text": f"Chunk {vector_id}",
        }
        for vector_id in range(count)
    ]


def test_create_index_and_search():
    embeddings = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.9, 0.1, 0.0],
        ],
        dtype="float32",
    )

    index = create_index(embeddings)

    assert index.ntotal == 3

    query = np.array(
        [[1.0, 0.0, 0.0]],
        dtype="float32",
    )

    scores, indices = search_index(
        index,
        query,
        top_k=2,
    )

    assert len(scores) == 2
    assert len(indices) == 2
    assert indices[0] == 0
    assert np.isclose(scores[0], 1.0)


def test_save_and_validate_search_artifacts(tmp_path):
    embeddings = np.array([[1.0, 0.0, 0.0]], dtype="float32")
    index = create_index(embeddings)
    metadata = _metadata(1)

    manifest = save_search_artifacts(
        index,
        metadata,
        tmp_path,
        model_name="test-model",
    )

    index_path = tmp_path / "index.faiss"
    metadata_path = tmp_path / "metadata.json"
    manifest_path = tmp_path / "manifest.json"

    assert manifest_path.exists()
    assert manifest["vector_count"] == 1
    assert manifest["metadata_count"] == 1

    loaded_index = load_index(index_path)
    loaded_metadata = load_metadata(metadata_path)
    loaded_manifest = load_manifest(manifest_path)

    validate_artifacts(
        loaded_index,
        loaded_metadata,
        loaded_manifest,
        index_path,
        metadata_path,
        expected_model_name="test-model",
    )


def test_validation_rejects_modified_metadata(tmp_path):
    index = create_index(np.array([[1.0, 0.0]], dtype="float32"))
    save_search_artifacts(index, _metadata(1), tmp_path, model_name="test-model")

    metadata_path = tmp_path / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata[0]["text"] = "tampered"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="checksum"):
        validate_artifacts(
            load_index(tmp_path / "index.faiss"),
            load_metadata(metadata_path),
            load_manifest(tmp_path / "manifest.json"),
            tmp_path / "index.faiss",
            metadata_path,
            expected_model_name="test-model",
        )


def test_create_index_rejects_empty_embeddings():
    with pytest.raises(ValueError, match="At least one embedding"):
        create_index(np.empty((0, 3), dtype="float32"))


def test_save_rejects_mismatched_metadata(tmp_path):
    index = create_index(np.array([[1.0, 0.0]], dtype="float32"))

    with pytest.raises(ValueError, match="number of FAISS vectors"):
        save_search_artifacts(index, [], tmp_path, model_name="test-model")


def test_vector_store_saves_and_loads(tmp_path):
    index = create_index(np.array([[1.0, 0.0]], dtype="float32"))
    metadata = _metadata(1)
    store = FaissVectorStore(tmp_path, "test-model")

    store.save(index, metadata)
    loaded_index, loaded_metadata, manifest = store.load()

    assert loaded_index.ntotal == 1
    assert loaded_metadata == metadata
    assert manifest["model_name"] == "test-model"
