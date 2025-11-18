"""
Tests for kosmos.literature.arxiv_client module.
"""

import pytest
import responses
from unittest.mock import Mock, patch, MagicMock

from kosmos.literature.arxiv_client import ArxivClient
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def arxiv_client():
    """Create ArxivClient instance for testing."""
    return ArxivClient()


@pytest.mark.unit
class TestArxivClientInit:
    """Test ArxivClient initialization."""

    def test_init_default(self):
        """Test default initialization."""
        client = ArxivClient()
        assert client.max_results == 10
        assert client.sort_by == "relevance"
        assert client.sort_order == "descending"

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        client = ArxivClient(max_results=20, sort_by="lastUpdatedDate")
        assert client.max_results == 20
        assert client.sort_by == "lastUpdatedDate"


@pytest.mark.unit
class TestArxivSearch:
    """Test arXiv search functionality."""

    @patch('arxiv.Search')
    @patch('arxiv.Client')
    def test_search_success(self, mock_client_class, mock_search_class, arxiv_client):
        """Test successful paper search."""
        # Mock arxiv Result objects
        mock_result1 = Mock()
        mock_result1.get_short_id.return_value = "1706.03762"
        mock_result1.title = "Attention Is All You Need"
        mock_result1.authors = [Mock(name="Ashish Vaswani"), Mock(name="Noam Shazeer")]
        mock_result1.summary = "We propose the Transformer architecture..."
        mock_result1.published.year = 2017
        mock_result1.journal_ref = "NeurIPS 2017"
        mock_result1.doi = "10.5555/3295222.3295349"
        mock_result1.entry_id = "http://arxiv.org/abs/1706.03762v5"
        mock_result1.pdf_url = "http://arxiv.org/pdf/1706.03762v5"
        mock_result1.primary_category = "cs.CL"
        mock_result1.categories = ["cs.CL", "cs.LG"]

        # Mock client results method
        mock_client = Mock()
        mock_client.results.return_value = [mock_result1]
        mock_client_class.return_value = mock_client

        # Execute search
        papers = arxiv_client.search("attention mechanism", max_results=1)

        # Assertions
        assert len(papers) == 1
        assert isinstance(papers[0], PaperMetadata)
        assert papers[0].title == "Attention Is All You Need"
        assert papers[0].arxiv_id == "1706.03762"
        assert len(papers[0].authors) == 2
        assert papers[0].year == 2017
        assert papers[0].source == "arxiv"

    @patch('arxiv.Search')
    @patch('arxiv.Client')
    def test_search_empty_results(self, mock_client_class, mock_search_class, arxiv_client):
        """Test search with no results."""
        mock_client = Mock()
        mock_client.results.return_value = []
        mock_client_class.return_value = mock_client

        papers = arxiv_client.search("nonexistent_query_xyz123")
        assert papers == []

    @patch('arxiv.Search')
    @patch('arxiv.Client')
    def test_search_with_cache(self, mock_client_class, mock_search_class, arxiv_client):
        """Test that search uses caching."""
        mock_result = Mock()
        mock_result.get_short_id.return_value = "1706.03762"
        mock_result.title = "Test Paper"
        mock_result.authors = [Mock(name="Author One")]
        mock_result.summary = "Abstract"
        mock_result.published.year = 2023
        mock_result.journal_ref = None
        mock_result.doi = None
        mock_result.entry_id = "http://arxiv.org/abs/1706.03762"
        mock_result.pdf_url = "http://arxiv.org/pdf/1706.03762"
        mock_result.primary_category = "cs.AI"
        mock_result.categories = ["cs.AI"]

        mock_client = Mock()
        mock_client.results.return_value = [mock_result]
        mock_client_class.return_value = mock_client

        # First call - should hit API
        papers1 = arxiv_client.search("test query", max_results=1)
        assert len(papers1) == 1

        # Second call with same query - should use cache
        papers2 = arxiv_client.search("test query", max_results=1)
        assert len(papers2) == 1

        # Verify cache was used (client.results called only once)
        assert mock_client.results.call_count == 1

    @patch('arxiv.Client')
    def test_search_error_handling(self, mock_client_class, arxiv_client):
        """Test error handling during search."""
        mock_client = Mock()
        mock_client.results.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        papers = arxiv_client.search("test query")
        assert papers == []


@pytest.mark.unit
class TestArxivGetPaperById:
    """Test fetching papers by arXiv ID."""

    @patch('arxiv.Search')
    @patch('arxiv.Client')
    def test_get_paper_by_id_success(self, mock_client_class, mock_search_class, arxiv_client):
        """Test successfully fetching a paper by ID."""
        mock_result = Mock()
        mock_result.get_short_id.return_value = "1706.03762"
        mock_result.title = "Attention Is All You Need"
        mock_result.authors = [Mock(name="Ashish Vaswani")]
        mock_result.summary = "We propose the Transformer..."
        mock_result.published.year = 2017
        mock_result.journal_ref = "NeurIPS 2017"
        mock_result.doi = "10.5555/3295222.3295349"
        mock_result.entry_id = "http://arxiv.org/abs/1706.03762v5"
        mock_result.pdf_url = "http://arxiv.org/pdf/1706.03762v5"
        mock_result.primary_category = "cs.CL"
        mock_result.categories = ["cs.CL"]

        mock_client = Mock()
        mock_client.results.return_value = [mock_result]
        mock_client_class.return_value = mock_client

        paper = arxiv_client.get_paper_by_id("1706.03762")

        assert paper is not None
        assert paper.arxiv_id == "1706.03762"
        assert paper.title == "Attention Is All You Need"

    @patch('arxiv.Search')
    @patch('arxiv.Client')
    def test_get_paper_by_id_not_found(self, mock_client_class, mock_search_class, arxiv_client):
        """Test fetching a non-existent paper ID."""
        mock_client = Mock()
        mock_client.results.return_value = []
        mock_client_class.return_value = mock_client

        paper = arxiv_client.get_paper_by_id("9999.99999")
        assert paper is None


@pytest.mark.unit
class TestArxivParseResult:
    """Test parsing arXiv API results."""

    def test_parse_result_complete(self, arxiv_client):
        """Test parsing a complete arXiv result."""
        mock_result = Mock()
        mock_result.get_short_id.return_value = "1706.03762"
        mock_result.title = "Attention Is All You Need"
        mock_result.authors = [Mock(name="Ashish Vaswani"), Mock(name="Noam Shazeer")]
        mock_result.summary = "We propose the Transformer architecture..."
        mock_result.published.year = 2017
        mock_result.journal_ref = "NeurIPS 2017"
        mock_result.doi = "10.5555/3295222.3295349"
        mock_result.entry_id = "http://arxiv.org/abs/1706.03762v5"
        mock_result.pdf_url = "http://arxiv.org/pdf/1706.03762v5"
        mock_result.primary_category = "cs.CL"
        mock_result.categories = ["cs.CL", "cs.LG"]

        paper = arxiv_client._parse_result(mock_result)

        assert paper.title == "Attention Is All You Need"
        assert paper.arxiv_id == "1706.03762"
        assert len(paper.authors) == 2
        assert paper.authors[0] == "Ashish Vaswani"
        assert paper.year == 2017
        assert paper.venue == "NeurIPS 2017"
        assert paper.doi == "10.5555/3295222.3295349"
        assert paper.source == "arxiv"

    def test_parse_result_minimal(self, arxiv_client):
        """Test parsing a minimal arXiv result (only required fields)."""
        mock_result = Mock()
        mock_result.get_short_id.return_value = "2301.00000"
        mock_result.title = "Minimal Paper"
        mock_result.authors = [Mock(name="Anonymous")]
        mock_result.summary = "A minimal paper."
        mock_result.published.year = 2023
        mock_result.journal_ref = None
        mock_result.doi = None
        mock_result.entry_id = "http://arxiv.org/abs/2301.00000"
        mock_result.pdf_url = "http://arxiv.org/pdf/2301.00000"
        mock_result.primary_category = "cs.AI"
        mock_result.categories = ["cs.AI"]

        paper = arxiv_client._parse_result(mock_result)

        assert paper.title == "Minimal Paper"
        assert paper.arxiv_id == "2301.00000"
        assert paper.venue is None
        assert paper.doi is None
        assert paper.source == "arxiv"


@pytest.mark.unit
class TestArxivFiltering:
    """Test filtering and sorting functionality."""

    @patch('arxiv.Search')
    @patch('arxiv.Client')
    def test_search_with_sort_by_date(self, mock_client_class, mock_search_class):
        """Test search with sorting by date."""
        client = ArxivClient(sort_by="submittedDate", sort_order="descending")

        mock_result = Mock()
        mock_result.get_short_id.return_value = "2023.00001"
        mock_result.title = "Recent Paper"
        mock_result.authors = [Mock(name="Author")]
        mock_result.summary = "Recent work"
        mock_result.published.year = 2023
        mock_result.journal_ref = None
        mock_result.doi = None
        mock_result.entry_id = "http://arxiv.org/abs/2023.00001"
        mock_result.pdf_url = "http://arxiv.org/pdf/2023.00001"
        mock_result.primary_category = "cs.AI"
        mock_result.categories = ["cs.AI"]

        mock_client = Mock()
        mock_client.results.return_value = [mock_result]
        mock_client_class.return_value = mock_client

        papers = client.search("recent papers", max_results=1)
        assert len(papers) == 1

    @patch('arxiv.Search')
    @patch('arxiv.Client')
    def test_search_with_max_results(self, mock_client_class, mock_search_class, arxiv_client):
        """Test that max_results parameter is respected."""
        # Create 5 mock results
        mock_results = []
        for i in range(5):
            mock_result = Mock()
            mock_result.get_short_id.return_value = f"2023.0000{i}"
            mock_result.title = f"Paper {i}"
            mock_result.authors = [Mock(name=f"Author {i}")]
            mock_result.summary = f"Abstract {i}"
            mock_result.published.year = 2023
            mock_result.journal_ref = None
            mock_result.doi = None
            mock_result.entry_id = f"http://arxiv.org/abs/2023.0000{i}"
            mock_result.pdf_url = f"http://arxiv.org/pdf/2023.0000{i}"
            mock_result.primary_category = "cs.AI"
            mock_result.categories = ["cs.AI"]
            mock_results.append(mock_result)

        mock_client = Mock()
        mock_client.results.return_value = mock_results[:3]  # Only return 3
        mock_client_class.return_value = mock_client

        papers = arxiv_client.search("test query", max_results=3)
        assert len(papers) == 3


@pytest.mark.unit
class TestArxivCaching:
    """Test caching behavior."""

    def test_cache_key_generation(self, arxiv_client):
        """Test that cache keys are generated correctly."""
        key1 = arxiv_client._get_cache_key("machine learning", 10)
        key2 = arxiv_client._get_cache_key("machine learning", 10)
        key3 = arxiv_client._get_cache_key("deep learning", 10)

        assert key1 == key2  # Same query, same key
        assert key1 != key3  # Different query, different key

    @patch('arxiv.Search')
    @patch('arxiv.Client')
    def test_cache_hit_reduces_api_calls(self, mock_client_class, mock_search_class, arxiv_client):
        """Test that cache hits reduce API calls."""
        mock_result = Mock()
        mock_result.get_short_id.return_value = "2023.00001"
        mock_result.title = "Test Paper"
        mock_result.authors = [Mock(name="Test Author")]
        mock_result.summary = "Test abstract"
        mock_result.published.year = 2023
        mock_result.journal_ref = None
        mock_result.doi = None
        mock_result.entry_id = "http://arxiv.org/abs/2023.00001"
        mock_result.pdf_url = "http://arxiv.org/pdf/2023.00001"
        mock_result.primary_category = "cs.AI"
        mock_result.categories = ["cs.AI"]

        mock_client = Mock()
        mock_client.results.return_value = [mock_result]
        mock_client_class.return_value = mock_client

        # First call
        papers1 = arxiv_client.search("cache test", max_results=1)

        # Second call (should use cache)
        papers2 = arxiv_client.search("cache test", max_results=1)

        # Verify only one API call was made
        assert mock_client.results.call_count == 1
        assert len(papers1) == 1
        assert len(papers2) == 1


@pytest.mark.integration
@pytest.mark.slow
class TestArxivClientIntegration:
    """Integration tests for ArxivClient (requires network)."""

    def test_real_arxiv_search(self):
        """Test real arXiv API search (requires network)."""
        client = ArxivClient()
        papers = client.search("transformer neural network", max_results=2)

        assert len(papers) > 0
        assert all(isinstance(p, PaperMetadata) for p in papers)
        assert all(p.arxiv_id is not None for p in papers)

    def test_real_get_paper_by_id(self):
        """Test fetching a real paper by ID."""
        client = ArxivClient()
        paper = client.get_paper_by_id("1706.03762")  # "Attention Is All You Need"

        assert paper is not None
        assert paper.arxiv_id == "1706.03762"
        assert "Attention" in paper.title
        assert paper.year == 2017
