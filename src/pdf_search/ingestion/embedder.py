from sentence_transformers import SentenceTransformer

from pdf_search.config import EMBEDDING_BATCH_SIZE, MODEL_NAME


class EmbeddingModel:
    """Lazy CPU-backed wrapper around Sentence-Transformers."""

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        batch_size: int = EMBEDDING_BATCH_SIZE,
        device: str = "cpu",
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self._model = None

    def _get_model(self):
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )
        return self._model

    def encode(self, texts: list[str]):
        if not texts:
            raise ValueError("At least one text is required to create embeddings")

        embeddings = self._get_model().encode(
            texts,
            normalize_embeddings=True,
            batch_size=self.batch_size,
        )
        return embeddings.astype("float32", copy=False)
