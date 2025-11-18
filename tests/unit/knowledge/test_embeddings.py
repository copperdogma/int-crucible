"""
Tests for kosmos.knowledge.embeddings module.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from kosmos.knowledge.embeddings import EmbeddingGenerator
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def embedding_generator():
    """Create EmbeddingGenerator instance."""
    with patch('sentence_transformers.SentenceTransformer'):
        gen = EmbeddingGenerator(model_name="allenai/specter")
        return gen


@pytest.mark.unit
class TestEmbeddingGeneratorInit:
    """Test embedding generator initialization."""

    @patch('sentence_transformers.SentenceTransformer')
    def test_init_default(self, mock_st):
        """Test default initialization."""
        gen = EmbeddingGenerator()
        assert gen.model_name == "allenai/specter"
        mock_st.assert_called_once()

    @patch('sentence_transformers.SentenceTransformer')
    def test_init_custom_model(self, mock_st):
        """Test initialization with custom model."""
        gen = EmbeddingGenerator(model_name="custom-model")
        assert gen.model_name == "custom-model"


@pytest.mark.unit
class TestEmbeddingGeneration:
    """Test embedding generation."""

    def test_embed_text(self, embedding_generator):
        """Test embedding text."""
        with patch.object(embedding_generator.model, 'encode') as mock_encode:
            mock_encode.return_value = np.array([0.1, 0.2, 0.3])

            embedding = embedding_generator.embed_text("test text")

            assert isinstance(embedding, np.ndarray)
            assert len(embedding) == 3
            mock_encode.assert_called_once()

    def test_embed_paper(self, embedding_generator, sample_paper_metadata):
        """Test embedding a paper."""
        with patch.object(embedding_generator.model, 'encode') as mock_encode:
            mock_encode.return_value = np.array([0.1] * 768)

            embedding = embedding_generator.embed_paper(sample_paper_metadata)

            assert isinstance(embedding, np.ndarray)
            assert len(embedding) == 768
            # Should combine title and abstract
            mock_encode.assert_called_once()

    def test_embed_papers_batch(self, embedding_generator, sample_papers_list):
        """Test batch embedding of papers."""
        with patch.object(embedding_generator.model, 'encode') as mock_encode:
            mock_encode.return_value = np.array([[0.1] * 768] * len(sample_papers_list))

            embeddings = embedding_generator.embed_papers_batch(sample_papers_list)

            assert isinstance(embeddings, list)
            assert len(embeddings) == len(sample_papers_list)
            assert all(isinstance(e, np.ndarray) for e in embeddings)

    def test_embed_empty_text(self, embedding_generator):
        """Test embedding empty text."""
        with patch.object(embedding_generator.model, 'encode') as mock_encode:
            mock_encode.return_value = np.array([0.0] * 768)

            embedding = embedding_generator.embed_text("")

            assert isinstance(embedding, np.ndarray)


@pytest.mark.unit
class TestEmbeddingCaching:
    """Test embedding caching."""

    def test_cache_embedding(self, embedding_generator):
        """Test that embeddings are cached."""
        with patch.object(embedding_generator.model, 'encode') as mock_encode:
            mock_encode.return_value = np.array([0.1, 0.2, 0.3])

            # First call
            emb1 = embedding_generator.embed_text("same text")

            # Second call with same text
            emb2 = embedding_generator.embed_text("same text")

            # Should only encode once due to caching
            assert mock_encode.call_count == 1
            np.testing.assert_array_equal(emb1, emb2)

    def test_cache_different_texts(self, embedding_generator):
        """Test that different texts get different cache keys."""
        with patch.object(embedding_generator.model, 'encode') as mock_encode:
            mock_encode.return_value = np.array([0.1, 0.2, 0.3])

            embedding_generator.embed_text("text 1")
            embedding_generator.embed_text("text 2")

            # Should encode twice for different texts
            assert mock_encode.call_count == 2


@pytest.mark.unit
class TestEmbeddingSimilarity:
    """Test similarity calculations."""

    def test_cosine_similarity(self, embedding_generator):
        """Test cosine similarity calculation."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = embedding_generator.cosine_similarity(vec1, vec2)

        assert 0.99 <= similarity <= 1.01  # Should be 1.0 (identical)

    def test_cosine_similarity_orthogonal(self, embedding_generator):
        """Test cosine similarity for orthogonal vectors."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])

        similarity = embedding_generator.cosine_similarity(vec1, vec2)

        assert -0.01 <= similarity <= 0.01  # Should be 0.0 (orthogonal)

    def test_find_similar_papers(self, embedding_generator, sample_papers_list):
        """Test finding similar papers."""
        with patch.object(embedding_generator, 'embed_papers_batch') as mock_embed:
            # Create mock embeddings
            embeddings = [
                np.array([1.0, 0.0, 0.0]),
                np.array([0.9, 0.1, 0.0]),
                np.array([0.0, 1.0, 0.0]),
            ]
            mock_embed.return_value = embeddings

            query_embedding = np.array([1.0, 0.0, 0.0])
            similar = embedding_generator.find_similar(
                query_embedding, sample_papers_list[:3], top_k=2
            )

            assert len(similar) <= 2
            assert all(isinstance(item, tuple) for item in similar)


@pytest.mark.integration
@pytest.mark.slow
class TestEmbeddingGeneratorIntegration:
    """Integration tests (requires model download)."""

    def test_real_embedding_generation(self):
        """Test real embedding generation with SPECTER."""
        gen = EmbeddingGenerator()

        text = "Machine learning is a field of artificial intelligence."
        embedding = gen.embed_text(text)

        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == 768  # SPECTER embedding dimension

    def test_real_paper_embedding(self, sample_paper_metadata):
        """Test real paper embedding."""
        gen = EmbeddingGenerator()

        embedding = gen.embed_paper(sample_paper_metadata)

        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == 768
