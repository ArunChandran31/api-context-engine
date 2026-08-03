from unittest.mock import MagicMock

import numpy as np
import pytest

from app.rag.sentence_transformer_provider import (
    SentenceTransformerEmbeddingProvider,
)


def create_mock_model() -> MagicMock:
    model = MagicMock()

    model.get_sentence_embedding_dimension.return_value = 384

    return model


def test_provider_uses_default_model() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    assert provider.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert provider.dimension == 384


def test_provider_rejects_empty_model_name() -> None:
    with pytest.raises(
        ValueError,
        match="Model name cannot be empty",
    ):
        SentenceTransformerEmbeddingProvider(model_name="")


def test_provider_loads_model_lazily() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    mock_model = create_mock_model()

    provider._load_model = MagicMock(return_value=mock_model)

    assert provider._model is None

    provider._get_model()

    assert provider._model is mock_model
    provider._load_model.assert_called_once()


def test_provider_reuses_loaded_model() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    mock_model = create_mock_model()

    provider._load_model = MagicMock(return_value=mock_model)

    provider._get_model()
    provider._get_model()

    provider._load_model.assert_called_once()


def test_provider_embeds_single_text() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    mock_model = create_mock_model()

    mock_model.encode.return_value = np.array(
        [0.1, 0.2, 0.3],
        dtype=float,
    )

    provider._model = mock_model

    embedding = provider.embed("Create a user")

    assert embedding == pytest.approx([0.1, 0.2, 0.3])

    mock_model.encode.assert_called_once_with(
        "Create a user",
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def test_provider_embeds_batch() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    mock_model = create_mock_model()

    mock_model.encode.return_value = np.array(
        [
            [0.1, 0.2],
            [0.3, 0.4],
        ],
        dtype=float,
    )

    provider._model = mock_model

    embeddings = provider.embed_batch(
        [
            "Create user",
            "Delete user",
        ]
    )

    assert embeddings == [
        pytest.approx([0.1, 0.2]),
        pytest.approx([0.3, 0.4]),
    ]


def test_provider_rejects_empty_text() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    with pytest.raises(
        ValueError,
        match="Text cannot be empty",
    ):
        provider.embed("")


def test_provider_returns_empty_batch() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    assert provider.embed_batch([]) == []


def test_provider_rejects_empty_text_in_batch() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    with pytest.raises(
        ValueError,
        match="Texts cannot contain empty values",
    ):
        provider.embed_batch(
            [
                "Create user",
                "",
            ]
        )
