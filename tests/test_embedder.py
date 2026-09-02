import numpy as np

from pdf_search.ingestion.embedder import create_embeddings


def test_embeddings_are_normalized():
    texts = [
        "La mairie organise une réunion.",
        "Le conseil municipal vote une délibération.",
    ]

    embeddings = create_embeddings(texts)

    norms = np.linalg.norm(embeddings, axis=1)

    assert embeddings.shape == (2, 384)
    assert np.allclose(norms, 1.0, atol=1e-5)