from sentence_transformers import SentenceTransformer


MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model = None


def _get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, device="cpu")

    return _model


def create_embeddings(texts: list[str]):
    if not texts:
        raise ValueError("At least one text is required to create embeddings")

    embeddings = _get_model().encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
    )
    return embeddings.astype("float32", copy=False)
