import numpy as np

from pdf_search.ingestion.embedder import EmbeddingModel


def test_embeddings_are_normalized():
    texts = [
        "La mairie organise une réunion.",
        "Le conseil municipal vote une délibération.",
    ]

    embeddings = EmbeddingModel().encode(texts)

    norms = np.linalg.norm(embeddings, axis=1)

    assert embeddings.shape == (2, 384)
    assert np.allclose(norms, 1.0, atol=1e-5)
