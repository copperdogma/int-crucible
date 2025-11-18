"""
Tests for kosmos.knowledge.vector_db module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from kosmos.knowledge.vector_db import VectorDatabase
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def vector_db():
    """Create VectorDatabase instance with mocked ChromaDB."""
    with patch('chromadb.Client'):
        db = VectorDatabase(persist_directory=":memory:")
        db.collection = Mock()
        return db


@pytest.mark.unit
class TestVectorDatabaseInit:
    """Test vector database initialization."""

    @patch('chromadb.Client')
    def test_init_default(self, mock_client):
        """Test default initialization."""
        db = VectorDatabase()
        assert db.collection_name == "papers"

    @patch('chromadb.Client')
    def test_init_custom_collection(self, mock_client):
        """Test initialization with custom collection name."""
        db = VectorDatabase(collection_name="custom_papers")
        assert db.collection_name == "custom_papers"


@pytest.mark.unit
class TestVectorDatabaseAdd:
    """Test adding papers to vector database."""

    def test_add_paper(self, vector_db, sample_paper_metadata):
        """Test adding a single paper."""
        with patch.object(vector_db, 'embedding_generator') as mock_emb:
            mock_emb.embed_paper.return_value = np.array([0.1] * 768)

            vector_db.add_paper(sample_paper_metadata)

            vector_db.collection.add.assert_called_once()

    def test_add_papers_batch(self, vector_db, sample_papers_list):
        """Test adding multiple papers in batch."""
        with patch.object(vector_db, 'embedding_generator') as mock_emb:
            mock_emb.embed_papers_batch.return_value = [
                np.array([0.1] * 768) for _ in sample_papers_list
            ]

            vector_db.add_papers(sample_papers_list)

            vector_db.collection.add.assert_called()

    def test_add_paper_with_empty_abstract(self, vector_db):
        """Test adding paper with no abstract."""
        paper = PaperMetadata(
            title="Test", authors=[], abstract="", year=2023, source="test"
        )

        with patch.object(vector_db, 'embedding_generator') as mock_emb:
            mock_emb.embed_paper.return_value = np.array([0.1] * 768)

            vector_db.add_paper(paper)

            mock_emb.embed_paper.assert_called_once_with(paper)


@pytest.mark.unit
class TestVectorDatabaseSearch:
    """Test searching in vector database."""

    def test_search_by_text(self, vector_db):
        """Test searching by text query."""
        mock_results = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.2]],
            "metadatas": [[
                {"title": "Paper 1", "paper_id": "id1"},
                {"title": "Paper 2", "paper_id": "id2"},
            ]],
        }
        vector_db.collection.query.return_value = mock_results

        with patch.object(vector_db, 'embedding_generator') as mock_emb:
            mock_emb.embed_text.return_value = np.array([0.1] * 768)

            results = vector_db.search("test query", top_k=2)

            assert len(results) == 2
            vector_db.collection.query.assert_called_once()

    def test_search_by_paper(self, vector_db, sample_paper_metadata):
        """Test searching by paper (find similar)."""
        mock_results = {
            "ids": [["id1"]],
            "distances": [[0.1]],
            "metadatas": [[{"title": "Similar Paper", "paper_id": "id1"}]],
        }
        vector_db.collection.query.return_value = mock_results

        with patch.object(vector_db, 'embedding_generator') as mock_emb:
            mock_emb.embed_paper.return_value = np.array([0.1] * 768)

            results = vector_db.search_by_paper(sample_paper_metadata, top_k=5)

            assert len(results) <= 5
            vector_db.collection.query.assert_called_once()

    def test_search_empty_results(self, vector_db):
        """Test search with no results."""
        vector_db.collection.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
        }

        with patch.object(vector_db, 'embedding_generator') as mock_emb:
            mock_emb.embed_text.return_value = np.array([0.1] * 768)

            results = vector_db.search("nonexistent query")

            assert results == []


@pytest.mark.unit
class TestVectorDatabaseCRUD:
    """Test CRUD operations."""

    def test_get_paper(self, vector_db):
        """Test getting a specific paper."""
        vector_db.collection.get.return_value = {
            "ids": ["paper_123"],
            "metadatas": [{"title": "Test Paper", "paper_id": "paper_123"}],
        }

        paper_data = vector_db.get_paper("paper_123")

        assert paper_data is not None
        assert paper_data["paper_id"] == "paper_123"

    def test_delete_paper(self, vector_db):
        """Test deleting a paper."""
        vector_db.delete_paper("paper_123")

        vector_db.collection.delete.assert_called_once_with(ids=["paper_123"])

    def test_get_paper_count(self, vector_db):
        """Test getting total paper count."""
        vector_db.collection.count.return_value = 42

        count = vector_db.get_paper_count()

        assert count == 42


@pytest.mark.unit
class TestVectorDatabaseSimilarity:
    """Test similarity calculations."""

    def test_convert_distance_to_similarity(self, vector_db):
        """Test converting distance to similarity score."""
        # ChromaDB uses L2 distance, lower is more similar
        distance = 0.1
        similarity = vector_db._distance_to_similarity(distance)

        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.5  # Small distance = high similarity

    def test_filter_by_similarity_threshold(self, vector_db):
        """Test filtering results by similarity threshold."""
        mock_results = {
            "ids": [["id1", "id2", "id3"]],
            "distances": [[0.1, 0.5, 0.9]],  # Different distances
            "metadatas": [[
                {"paper_id": "id1"},
                {"paper_id": "id2"},
                {"paper_id": "id3"},
            ]],
        }
        vector_db.collection.query.return_value = mock_results

        with patch.object(vector_db, 'embedding_generator') as mock_emb:
            mock_emb.embed_text.return_value = np.array([0.1] * 768)

            results = vector_db.search("test", top_k=10, min_similarity=0.7)

            # Only high similarity results should be returned
            assert len(results) < 3


@pytest.mark.integration
@pytest.mark.requires_chromadb
class TestVectorDatabaseIntegration:
    """Integration tests (requires ChromaDB)."""

    def test_real_add_and_search(self, sample_papers_list):
        """Test real add and search operations."""
        db = VectorDatabase(persist_directory=":memory:")

        # Add papers
        db.add_papers(sample_papers_list[:3])

        # Search
        results = db.search("transformer attention", top_k=2)

        assert len(results) > 0

    def test_real_similarity_search(self, sample_paper_metadata):
        """Test real similarity search."""
        db = VectorDatabase(persist_directory=":memory:")

        db.add_paper(sample_paper_metadata)

        # Search for similar papers
        results = db.search_by_paper(sample_paper_metadata, top_k=1)

        assert len(results) > 0
