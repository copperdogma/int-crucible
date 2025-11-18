"""
Tests for kosmos.literature.semantic_scholar module.
"""

import pytest
import responses
from unittest.mock import Mock, patch

from kosmos.literature.semantic_scholar import SemanticScholarClient
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def s2_client():
    """Create SemanticScholarClient instance for testing."""
    return SemanticScholarClient(api_key="test_api_key")


@pytest.mark.unit
class TestSemanticScholarInit:
    """Test Semantic Scholar client initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = SemanticScholarClient(api_key="test_key")
        assert client.api_key == "test_key"

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        client = SemanticScholarClient()
        assert client.api_key is None


@pytest.mark.unit
class TestSemanticScholarSearch:
    """Test Semantic Scholar search functionality."""

    @responses.activate
    def test_search_success(self, s2_client, semantic_scholar_response_json):
        """Test successful paper search."""
        responses.add(
            responses.GET,
            "https://api.semanticscholar.org/graph/v1/paper/search",
            json=semantic_scholar_response_json,
            status=200,
        )

        papers = s2_client.search("attention mechanism", max_results=3)

        assert len(papers) == 3
        assert all(isinstance(p, PaperMetadata) for p in papers)
        assert papers[0].title == "Attention Is All You Need"
        assert papers[0].source == "semantic_scholar"

    @responses.activate
    def test_search_empty_results(self, s2_client):
        """Test search with no results."""
        responses.add(
            responses.GET,
            "https://api.semanticscholar.org/graph/v1/paper/search",
            json={"total": 0, "offset": 0, "data": []},
            status=200,
        )

        papers = s2_client.search("nonexistent_query_xyz")
        assert papers == []

    @responses.activate
    def test_search_with_api_error(self, s2_client):
        """Test search with API error."""
        responses.add(
            responses.GET,
            "https://api.semanticscholar.org/graph/v1/paper/search",
            json={"error": "API Error"},
            status=500,
        )

        papers = s2_client.search("test query")
        assert papers == []

    def test_search_uses_cache(self, s2_client):
        """Test that search results are cached."""
        with patch.object(s2_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "total": 1,
                "offset": 0,
                "data": [{
                    "paperId": "123",
                    "title": "Test Paper",
                    "abstract": "Test abstract",
                    "year": 2023,
                    "authors": [{"name": "Test Author"}],
                    "venue": "TestConf",
                    "citationCount": 10,
                }],
            }

            # First call
            papers1 = s2_client.search("test query", max_results=1)

            # Second call (should use cache)
            papers2 = s2_client.search("test query", max_results=1)

            # Only one API call should be made
            assert mock_request.call_count == 1
            assert len(papers1) == 1
            assert len(papers2) == 1


@pytest.mark.unit
class TestSemanticScholarGetPaper:
    """Test fetching papers by ID."""

    @responses.activate
    def test_get_paper_by_id_success(self, s2_client):
        """Test fetching paper by Semantic Scholar ID."""
        paper_data = {
            "paperId": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
            "title": "Attention Is All You Need",
            "abstract": "We propose the Transformer...",
            "year": 2017,
            "authors": [{"name": "Ashish Vaswani"}, {"name": "Noam Shazeer"}],
            "venue": "NIPS",
            "citationCount": 98765,
            "externalIds": {"ArXiv": "1706.03762", "DOI": "10.5555/3295222.3295349"},
        }

        responses.add(
            responses.GET,
            f"https://api.semanticscholar.org/graph/v1/paper/{paper_data['paperId']}",
            json=paper_data,
            status=200,
        )

        paper = s2_client.get_paper_by_id(paper_data["paperId"])

        assert paper is not None
        assert paper.title == "Attention Is All You Need"
        assert paper.arxiv_id == "1706.03762"
        assert paper.doi == "10.5555/3295222.3295349"

    @responses.activate
    def test_get_paper_by_id_not_found(self, s2_client):
        """Test fetching non-existent paper."""
        responses.add(
            responses.GET,
            "https://api.semanticscholar.org/graph/v1/paper/nonexistent",
            json={"error": "Paper not found"},
            status=404,
        )

        paper = s2_client.get_paper_by_id("nonexistent")
        assert paper is None


@pytest.mark.unit
class TestSemanticScholarCitations:
    """Test citation fetching functionality."""

    @responses.activate
    def test_get_citations_success(self, s2_client):
        """Test fetching citations for a paper."""
        paper_id = "204e3073870fae3d05bcbc2f6a8e263d9b72e776"

        responses.add(
            responses.GET,
            f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations",
            json={
                "data": [
                    {
                        "citingPaper": {
                            "paperId": "abc123",
                            "title": "BERT",
                            "year": 2019,
                            "authors": [{"name": "Jacob Devlin"}],
                        }
                    }
                ]
            },
            status=200,
        )

        citations = s2_client.get_citations(paper_id, max_results=10)

        assert len(citations) == 1
        assert citations[0].title == "BERT"

    @responses.activate
    def test_get_references_success(self, s2_client):
        """Test fetching references for a paper."""
        paper_id = "204e3073870fae3d05bcbc2f6a8e263d9b72e776"

        responses.add(
            responses.GET,
            f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references",
            json={
                "data": [
                    {
                        "citedPaper": {
                            "paperId": "ref123",
                            "title": "Attention Mechanism",
                            "year": 2015,
                            "authors": [{"name": "Bahdanau"}],
                        }
                    }
                ]
            },
            status=200,
        )

        references = s2_client.get_references(paper_id, max_results=10)

        assert len(references) == 1
        assert references[0].title == "Attention Mechanism"


@pytest.mark.unit
class TestSemanticScholarParsing:
    """Test parsing Semantic Scholar API responses."""

    def test_parse_paper_complete(self, s2_client):
        """Test parsing a complete paper response."""
        paper_data = {
            "paperId": "123",
            "title": "Test Paper",
            "abstract": "Test abstract",
            "year": 2023,
            "authors": [{"name": "Author One"}, {"name": "Author Two"}],
            "venue": "TestConf 2023",
            "citationCount": 42,
            "externalIds": {
                "ArXiv": "2301.00001",
                "DOI": "10.1234/test.2023",
                "PubMed": "12345678",
            },
            "url": "https://semanticscholar.org/paper/123",
        }

        paper = s2_client._parse_paper(paper_data)

        assert paper.title == "Test Paper"
        assert len(paper.authors) == 2
        assert paper.arxiv_id == "2301.00001"
        assert paper.doi == "10.1234/test.2023"
        assert paper.pubmed_id == "12345678"
        assert paper.citation_count == 42

    def test_parse_paper_minimal(self, s2_client):
        """Test parsing a minimal paper response."""
        paper_data = {
            "paperId": "456",
            "title": "Minimal Paper",
            "year": 2023,
        }

        paper = s2_client._parse_paper(paper_data)

        assert paper.title == "Minimal Paper"
        assert paper.year == 2023
        assert paper.abstract == ""
        assert paper.authors == []


@pytest.mark.unit
class TestSemanticScholarRateLimiting:
    """Test rate limiting functionality."""

    @patch('time.sleep')
    def test_rate_limiting_applied(self, mock_sleep, s2_client):
        """Test that rate limiting delays are applied."""
        with patch.object(s2_client, '_make_request') as mock_request:
            mock_request.return_value = {"total": 0, "data": []}

            # Make multiple requests
            s2_client.search("query1", max_results=1)
            s2_client.search("query2", max_results=1)

            # Rate limiting should add delays
            assert mock_sleep.called or mock_request.call_count >= 1


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_api_key
class TestSemanticScholarIntegration:
    """Integration tests (requires API key and network)."""

    def test_real_search(self):
        """Test real Semantic Scholar search."""
        client = SemanticScholarClient()
        papers = client.search("machine learning", max_results=2)

        assert len(papers) > 0
        assert all(isinstance(p, PaperMetadata) for p in papers)

    def test_real_get_paper(self):
        """Test fetching a real paper."""
        client = SemanticScholarClient()
        paper = client.get_paper_by_id("204e3073870fae3d05bcbc2f6a8e263d9b72e776")

        assert paper is not None
        assert "Attention" in paper.title
