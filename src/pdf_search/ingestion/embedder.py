from sentence_transformers import SentenceTransformer


model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def create_embeddings(texts: list[str]):
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
    )
    return embeddings