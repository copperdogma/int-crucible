"""
Tests for kosmos.agents.literature_analyzer module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from kosmos.agents.literature_analyzer import LiteratureAnalyzerAgent, PaperAnalysis
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def literature_analyzer(mock_llm_client, mock_knowledge_graph, mock_vector_db):
    """Create LiteratureAnalyzerAgent with mocked dependencies."""
    with patch('kosmos.agents.literature_analyzer.get_client', return_value=mock_llm_client):
        with patch('kosmos.agents.literature_analyzer.get_knowledge_graph', return_value=mock_knowledge_graph):
            with patch('kosmos.agents.literature_analyzer.get_vector_db', return_value=mock_vector_db):
                agent = LiteratureAnalyzerAgent(config={"use_knowledge_graph": False})
                agent.llm_client = mock_llm_client
                agent.knowledge_graph = mock_knowledge_graph
                agent.vector_db = mock_vector_db
                return agent


@pytest.mark.unit
class TestLiteratureAnalyzerInit:
    """Test literature analyzer initialization."""

    def test_init_default(self, mock_llm_client):
        """Test default initialization."""
        with patch('kosmos.agents.literature_analyzer.get_client', return_value=mock_llm_client):
            agent = LiteratureAnalyzerAgent()
            assert agent.agent_type == "LiteratureAnalyzerAgent"

    def test_init_with_config(self, mock_llm_client):
        """Test initialization with custom config."""
        config = {"use_knowledge_graph": True, "use_semantic_similarity": True}
        with patch('kosmos.agents.literature_analyzer.get_client', return_value=mock_llm_client):
            agent = LiteratureAnalyzerAgent(config=config)
            assert agent.use_knowledge_graph is True
            assert agent.use_semantic_similarity is True


@pytest.mark.unit
class TestPaperSummarization:
    """Test paper summarization."""

    def test_summarize_paper(self, literature_analyzer, sample_paper_metadata):
        """Test summarizing a paper."""
        literature_analyzer.llm_client.generate_structured.return_value = {
            "executive_summary": "This paper proposes the Transformer.",
            "key_findings": ["Finding 1", "Finding 2"],
            "methodology": "Experiments on MT.",
            "significance": "State-of-the-art results.",
            "limitations": ["Computational cost"],
            "confidence_score": 0.9,
        }

        analysis = literature_analyzer.summarize_paper(sample_paper_metadata)

        assert isinstance(analysis, PaperAnalysis)
        assert analysis.executive_summary == "This paper proposes the Transformer."
        assert len(analysis.key_findings) == 2
        assert analysis.confidence_score == 0.9

    def test_summarize_paper_with_empty_abstract(self, literature_analyzer):
        """Test summarizing paper with no abstract."""
        paper = PaperMetadata(
            title="Test", authors=[], abstract="", year=2023, source="test"
        )

        literature_analyzer.llm_client.generate_structured.return_value = {
            "executive_summary": "Limited information.",
            "key_findings": [],
            "methodology": "Unknown",
            "significance": "Cannot assess",
            "limitations": [],
            "confidence_score": 0.3,
        }

        analysis = literature_analyzer.summarize_paper(paper)

        assert analysis.confidence_score < 0.5


@pytest.mark.unit
class TestCitationNetworkAnalysis:
    """Test citation network analysis."""

    def test_analyze_citation_network(self, literature_analyzer):
        """Test analyzing citation network."""
        literature_analyzer.knowledge_graph.get_citations.return_value = [
            {"paper_id": "cited1", "title": "Cited Paper 1"},
            {"paper_id": "cited2", "title": "Cited Paper 2"},
        ]
        literature_analyzer.knowledge_graph.get_citing_papers.return_value = [
            {"paper_id": "citing1", "title": "Citing Paper 1"},
        ]

        network_analysis = literature_analyzer.analyze_citation_network("paper_123", depth=1)

        assert "citation_count" in network_analysis
        assert "citing_count" in network_analysis
        assert network_analysis["citation_count"] == 2
        assert network_analysis["citing_count"] == 1

    def test_analyze_citation_network_with_build(self, literature_analyzer):
        """Test building citation network if missing."""
        literature_analyzer.knowledge_graph.get_citations.return_value = []

        network_analysis = literature_analyzer.analyze_citation_network(
            "paper_123", depth=1, build_if_missing=True
        )

        # Should attempt to build citation graph
        assert isinstance(network_analysis, dict)


@pytest.mark.unit
class TestSemanticSimilarity:
    """Test semantic similarity search."""

    def test_find_similar_papers(self, literature_analyzer, sample_paper_metadata):
        """Test finding semantically similar papers."""
        mock_similar = [
            (sample_paper_metadata, 0.95),
            (sample_paper_metadata, 0.88),
        ]

        with patch.object(literature_analyzer.semantic_search, 'find_similar_papers', return_value=mock_similar):
            similar = literature_analyzer.find_similar_papers(
                sample_paper_metadata, top_k=2
            )

            assert len(similar) == 2
            assert all(isinstance(item, tuple) for item in similar)
            assert all(0.0 <= score <= 1.0 for _, score in similar)


@pytest.mark.unit
class TestConceptExtraction:
    """Test concept extraction from papers."""

    def test_extract_concepts(self, literature_analyzer, sample_paper_metadata, mock_concept_extractor):
        """Test extracting concepts from a paper."""
        with patch('kosmos.agents.literature_analyzer.get_concept_extractor', return_value=mock_concept_extractor):
            literature_analyzer.concept_extractor = mock_concept_extractor

            result = literature_analyzer.extract_concepts(sample_paper_metadata)

            assert result is not None
            mock_concept_extractor.extract_from_paper.assert_called_once()


@pytest.mark.unit
class TestAgentLifecycle:
    """Test agent lifecycle methods."""

    def test_agent_start(self, literature_analyzer):
        """Test starting the agent."""
        literature_analyzer.start()

        assert literature_analyzer.status == "running"

    def test_agent_stop(self, literature_analyzer):
        """Test stopping the agent."""
        literature_analyzer.start()
        literature_analyzer.stop()

        assert literature_analyzer.status == "stopped"

    def test_agent_execute(self, literature_analyzer, sample_paper_metadata):
        """Test agent execute method with message."""
        message = {
            "action": "summarize",
            "paper": sample_paper_metadata,
        }

        literature_analyzer.llm_client.generate_structured.return_value = {
            "executive_summary": "Summary",
            "key_findings": [],
            "methodology": "Methods",
            "significance": "Important",
            "limitations": [],
            "confidence_score": 0.8,
        }

        response = literature_analyzer.execute(message)

        assert response is not None
        assert "result" in response


@pytest.mark.unit
class TestBatchAnalysis:
    """Test batch paper analysis."""

    def test_analyze_papers_batch(self, literature_analyzer, sample_papers_list):
        """Test analyzing multiple papers in batch."""
        literature_analyzer.llm_client.generate_structured.return_value = {
            "executive_summary": "Summary",
            "key_findings": ["Finding"],
            "methodology": "Methods",
            "significance": "Important",
            "limitations": [],
            "confidence_score": 0.8,
        }

        analyses = literature_analyzer.analyze_papers_batch(sample_papers_list[:3])

        assert len(analyses) == 3
        assert all(isinstance(a, PaperAnalysis) for a in analyses)


@pytest.mark.integration
@pytest.mark.requires_claude
class TestLiteratureAnalyzerIntegration:
    """Integration tests (requires Claude and services)."""

    def test_real_paper_summarization(self, sample_paper_metadata):
        """Test real paper summarization."""
        agent = LiteratureAnalyzerAgent(config={"use_knowledge_graph": False})

        agent.start()
        analysis = agent.summarize_paper(sample_paper_metadata)
        agent.stop()

        assert isinstance(analysis, PaperAnalysis)
        assert len(analysis.executive_summary) > 0
        assert len(analysis.key_findings) > 0
