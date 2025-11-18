"""
Tests for kosmos.knowledge.graph module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from kosmos.knowledge.graph import KnowledgeGraph
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def knowledge_graph():
    """Create KnowledgeGraph instance with mocked Neo4j."""
    with patch('py2neo.Graph'):
        with patch('kosmos.knowledge.graph.KnowledgeGraph._ensure_container_running'):
            kg = KnowledgeGraph(auto_start_container=False, create_indexes=False)
            kg.graph = Mock()
            kg.node_matcher = Mock()
            kg.rel_matcher = Mock()
            return kg


@pytest.mark.unit
class TestKnowledgeGraphInit:
    """Test knowledge graph initialization."""

    @patch('py2neo.Graph')
    @patch('kosmos.knowledge.graph.KnowledgeGraph._ensure_container_running')
    def test_init_default(self, mock_container, mock_graph):
        """Test default initialization."""
        kg = KnowledgeGraph(auto_start_container=False, create_indexes=False)
        assert kg.uri == "bolt://localhost:7687"

    @patch('py2neo.Graph')
    @patch('kosmos.knowledge.graph.KnowledgeGraph._ensure_container_running')
    def test_init_custom_uri(self, mock_container, mock_graph):
        """Test initialization with custom URI."""
        kg = KnowledgeGraph(
            uri="bolt://custom:7687",
            auto_start_container=False,
            create_indexes=False,
        )
        assert kg.uri == "bolt://custom:7687"


@pytest.mark.unit
class TestKnowledgeGraphPapers:
    """Test paper operations."""

    def test_add_paper(self, knowledge_graph, sample_paper_metadata):
        """Test adding a paper to the graph."""
        knowledge_graph.node_matcher.match.return_value.first.return_value = None

        paper_id = knowledge_graph.add_paper(sample_paper_metadata)

        assert paper_id is not None
        knowledge_graph.graph.create.assert_called()

    def test_add_paper_duplicate(self, knowledge_graph, sample_paper_metadata):
        """Test adding duplicate paper returns existing ID."""
        existing_node = Mock()
        existing_node["paper_id"] = "existing_123"
        knowledge_graph.node_matcher.match.return_value.first.return_value = existing_node

        paper_id = knowledge_graph.add_paper(sample_paper_metadata)

        assert paper_id == "existing_123"
        # Should not create new node
        knowledge_graph.graph.create.assert_not_called()

    def test_get_paper(self, knowledge_graph):
        """Test getting a paper from graph."""
        mock_node = Mock()
        mock_node["title"] = "Test Paper"
        knowledge_graph.node_matcher.match.return_value.first.return_value = mock_node

        paper_data = knowledge_graph.get_paper("paper_123")

        assert paper_data is not None
        assert paper_data["title"] == "Test Paper"

    def test_get_paper_not_found(self, knowledge_graph):
        """Test getting non-existent paper."""
        knowledge_graph.node_matcher.match.return_value.first.return_value = None

        paper_data = knowledge_graph.get_paper("nonexistent")

        assert paper_data is None


@pytest.mark.unit
class TestKnowledgeGraphConcepts:
    """Test concept operations."""

    def test_add_concept(self, knowledge_graph):
        """Test adding a concept."""
        knowledge_graph.node_matcher.match.return_value.first.return_value = None

        concept_id = knowledge_graph.add_concept("Machine Learning", category="Method")

        assert concept_id is not None
        knowledge_graph.graph.create.assert_called()

    def test_add_concept_to_paper(self, knowledge_graph):
        """Test linking concept to paper."""
        paper_node = Mock()
        concept_node = Mock()
        knowledge_graph.node_matcher.match.return_value.first.side_effect = [
            paper_node,
            concept_node,
        ]

        knowledge_graph.add_concept_to_paper("paper_id", "concept_id", relevance=0.9)

        knowledge_graph.graph.create.assert_called()

    def test_get_concept_papers(self, knowledge_graph):
        """Test getting papers for a concept."""
        mock_result = [
            {"p.paper_id": "p1", "p.title": "Paper 1", "r.relevance": 0.9}
        ]
        knowledge_graph.graph.run.return_value.data.return_value = mock_result

        papers = knowledge_graph.get_concept_papers("Machine Learning")

        assert len(papers) == 1
        assert papers[0]["paper_id"] == "p1"


@pytest.mark.unit
class TestKnowledgeGraphCitations:
    """Test citation operations."""

    def test_add_citation(self, knowledge_graph):
        """Test adding a citation relationship."""
        citing_node = Mock()
        cited_node = Mock()
        knowledge_graph.node_matcher.match.return_value.first.side_effect = [
            citing_node,
            cited_node,
        ]

        knowledge_graph.add_citation("citing_id", "cited_id")

        knowledge_graph.graph.create.assert_called()

    def test_get_citations(self, knowledge_graph):
        """Test getting citations for a paper."""
        mock_result = [
            {"cited.paper_id": "c1", "cited.title": "Cited Paper 1"}
        ]
        knowledge_graph.graph.run.return_value.data.return_value = mock_result

        citations = knowledge_graph.get_citations("paper_123", depth=1)

        assert len(citations) == 1
        assert citations[0]["paper_id"] == "c1"

    def test_get_citing_papers(self, knowledge_graph):
        """Test getting papers that cite a given paper."""
        mock_result = [
            {"citing.paper_id": "c1", "citing.title": "Citing Paper 1"}
        ]
        knowledge_graph.graph.run.return_value.data.return_value = mock_result

        citing = knowledge_graph.get_citing_papers("paper_123")

        assert len(citing) == 1
        assert citing[0]["paper_id"] == "c1"


@pytest.mark.unit
class TestKnowledgeGraphAuthors:
    """Test author operations."""

    def test_add_author(self, knowledge_graph):
        """Test adding an author."""
        knowledge_graph.node_matcher.match.return_value.first.return_value = None

        author_id = knowledge_graph.add_author("John Doe")

        assert author_id is not None
        knowledge_graph.graph.create.assert_called()

    def test_link_author_to_paper(self, knowledge_graph):
        """Test linking author to paper."""
        paper_node = Mock()
        author_node = Mock()
        knowledge_graph.node_matcher.match.return_value.first.side_effect = [
            paper_node,
            author_node,
        ]

        knowledge_graph.link_author_to_paper("paper_id", "author_id")

        knowledge_graph.graph.create.assert_called()

    def test_get_author_papers(self, knowledge_graph):
        """Test getting papers by an author."""
        mock_result = [
            {"p.paper_id": "p1", "p.title": "Paper 1"}
        ]
        knowledge_graph.graph.run.return_value.data.return_value = mock_result

        papers = knowledge_graph.get_author_papers("John Doe")

        assert len(papers) == 1


@pytest.mark.unit
class TestKnowledgeGraphStats:
    """Test statistics and queries."""

    def test_get_stats(self, knowledge_graph):
        """Test getting graph statistics."""
        knowledge_graph.graph.run.return_value.data.return_value = [
            {"label": "Paper", "count": 100},
            {"label": "Concept", "count": 50},
        ]

        stats = knowledge_graph.get_stats()

        assert "total_papers" in stats
        assert "total_concepts" in stats

    def test_search_papers_by_title(self, knowledge_graph):
        """Test searching papers by title."""
        mock_result = [
            {"p.paper_id": "p1", "p.title": "Attention"}
        ]
        knowledge_graph.graph.run.return_value.data.return_value = mock_result

        papers = knowledge_graph.search_papers("attention")

        assert len(papers) == 1
        assert "Attention" in papers[0]["title"]


@pytest.mark.integration
@pytest.mark.requires_neo4j
class TestKnowledgeGraphIntegration:
    """Integration tests (requires Neo4j)."""

    def test_real_add_paper(self, sample_paper_metadata):
        """Test adding a real paper to Neo4j."""
        kg = KnowledgeGraph()

        paper_id = kg.add_paper(sample_paper_metadata)

        assert paper_id is not None

        # Retrieve it
        paper_data = kg.get_paper(paper_id)
        assert paper_data is not None
        assert paper_data["title"] == sample_paper_metadata.title

    def test_real_citation_network(self, sample_papers_list):
        """Test building a citation network."""
        kg = KnowledgeGraph()

        # Add papers
        paper_ids = [kg.add_paper(p) for p in sample_papers_list[:3]]

        # Add citation
        kg.add_citation(paper_ids[0], paper_ids[1])

        # Query citations
        citations = kg.get_citations(paper_ids[0])

        assert len(citations) > 0
