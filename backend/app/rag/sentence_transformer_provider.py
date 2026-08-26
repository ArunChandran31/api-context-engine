from typing import Any

from app.rag.embeddings import EmbeddingProvider


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding provider backed by Sentence Transformers.

    The underlying model is loaded lazily on first use so importing the
    application does not immediately initialize the ML model.
    """

    DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_DIMENSION = 384

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        if not model_name.strip():
            raise ValueError("Model name cannot be empty.")

        self.model_name = model_name
        self._model: Any | None = None

    @property
    def dimension(self) -> int:
        if self._model is None:
            return self.DEFAULT_DIMENSION

        dimension = self._model.get_sentence_embedding_dimension()

        if dimension is None:
            raise RuntimeError("Unable to determine sentence embedding dimension.")

        return int(dimension)

    def warm_up(self) -> None:
        """
        Load the Sentence Transformer model into memory.

        This is intended to be called during application startup so
        the first embedding request does not pay the model-loading cost.
        """
        self._get_model()

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Text cannot be empty.")

        model = self._get_model()

        embedding = model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise ValueError("Texts cannot contain empty values.")

        model = self._get_model()

        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    def _get_model(self) -> Any:
        if self._model is None:
            self._model = self._load_model()

        return self._model

    def _load_model(self) -> Any:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self.model_name)
