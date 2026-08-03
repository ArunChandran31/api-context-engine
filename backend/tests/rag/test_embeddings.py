import pytest

from app.rag.embeddings import EmbeddingProvider


class FakeEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic embedding provider used only for unit tests.
    """

    @property
    def dimension(self) -> int:
        return 3

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Text cannot be empty.")

        length = float(len(text))

        return [
            length,
            length / 2,
            length / 4,
        ]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def test_embedding_provider_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        EmbeddingProvider()


def test_fake_embedding_provider_dimension() -> None:
    provider = FakeEmbeddingProvider()

    assert provider.dimension == 3


def test_fake_embedding_provider_embeds_text() -> None:
    provider = FakeEmbeddingProvider()

    embedding = provider.embed("hello")

    assert embedding == [
        5.0,
        2.5,
        1.25,
    ]


def test_fake_embedding_provider_embeds_batch() -> None:
    provider = FakeEmbeddingProvider()

    embeddings = provider.embed_batch(
        [
            "hello",
            "api",
        ]
    )

    assert embeddings == [
        [5.0, 2.5, 1.25],
        [3.0, 1.5, 0.75],
    ]


def test_fake_embedding_provider_rejects_empty_text() -> None:
    provider = FakeEmbeddingProvider()

    with pytest.raises(
        ValueError,
        match="Text cannot be empty",
    ):
        provider.embed("")
