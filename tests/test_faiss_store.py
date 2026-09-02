import numpy as np

from pdf_search.search.faiss_store import create_index, search_index


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

    # Le premier résultat doit être le vecteur [1, 0, 0]
    assert indices[0] == 0

    # Son produit scalaire avec la question vaut 1
    assert np.isclose(scores[0], 1.0)