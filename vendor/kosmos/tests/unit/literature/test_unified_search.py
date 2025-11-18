"""
Tests for kosmos.literature.unified_search module.
"""

import pytest
from unittest.mock import Mock, patch

from kosmos.literature.unified_search import UnifiedLiteratureSearch
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def unified_search():
    """Create UnifiedLiteratureSearch instance."""
    return UnifiedLiteratureSearch()


@pytest.fixture
def sample_papers_from_sources(sample_papers_list):
    """Create papers from different sources."""
    papers = sample_papers_list[:4]
    papers[0].source = "arxiv"
    papers[1].source = "semantic_scholar"
    papers[2].source = "pubmed"
    papers[3].source = "arxiv"  # Duplicate
    papers[3].title = papers[0].title  # Same title as first
    return papers


@pytest.mark.unit
class TestUnifiedSearchInit:
    """Test unified search initialization."""

    def test_init_default(self):
        """Test default initialization."""
        search = UnifiedLiteratureSearch()
        assert search.arxiv_client is not None
        assert search.s2_client is not None
        assert search.pubmed_client is not None

    def test_init_with_custom_sources(self):
        """Test initialization with specific sources."""
        search = UnifiedLiteratureSearch(sources=["arxiv", "semantic_scholar"])
        assert "arxiv" in search.sources
        assert "semantic_scholar" in search.sources
        assert "pubmed" not in search.sources


@pytest.mark.unit
class TestUnifiedSearch:
    """Test unified search functionality."""

    @patch('kosmos.literature.arxiv_client.ArxivClient.search')
    @patch('kosmos.literature.semantic_scholar.SemanticScholarClient.search')
    @patch('kosmos.literature.pubmed_client.PubMedClient.search')
    def test_search_all_sources(
        self, mock_pubmed, mock_s2, mock_arxiv, unified_search, sample_papers_list
    ):
        """Test searching across all sources."""
        # Mock responses from each source
        mock_arxiv.return_value = [sample_papers_list[0]]
        mock_s2.return_value = [sample_papers_list[1]]
        mock_pubmed.return_value = [sample_papers_list[2]]

        papers = unified_search.search("machine learning", max_results=10)

        assert len(papers) == 3
        assert mock_arxiv.called
        assert mock_s2.called
        assert mock_pubmed.called

    @patch('kosmos.literature.arxiv_client.ArxivClient.search')
    @patch('kosmos.literature.semantic_scholar.SemanticScholarClient.search')
    def test_search_specific_sources(
        self, mock_s2, mock_arxiv, unified_search, sample_papers_list
    ):
        """Test searching specific sources only."""
        mock_arxiv.return_value = [sample_papers_list[0]]
        mock_s2.return_value = [sample_papers_list[1]]

        papers = unified_search.search(
            "test query", sources=["arxiv", "semantic_scholar"], max_results=10
        )

        assert len(papers) == 2
        assert mock_arxiv.called
        assert mock_s2.called

    @patch('kosmos.literature.arxiv_client.ArxivClient.search')
    @patch('kosmos.literature.semantic_scholar.SemanticScholarClient.search')
    @patch('kosmos.literature.pubmed_client.PubMedClient.search')
    def test_deduplication(self, mock_pubmed, mock_s2, mock_arxiv, unified_search):
        """Test that duplicate papers are removed."""
        # Create duplicate papers with same DOI
        paper1 = PaperMetadata(
            title="Same Paper",
            authors=["Author"],
            abstract="Abstract",
            year=2023,
            doi="10.1234/same",
            source="arxiv",
        )
        paper2 = PaperMetadata(
            title="Same Paper",
            authors=["Author"],
            abstract="Abstract",
            year=2023,
            doi="10.1234/same",
            source="semantic_scholar",
        )

        mock_arxiv.return_value = [paper1]
        mock_s2.return_value = [paper2]
        mock_pubmed.return_value = []

        papers = unified_search.search("test", max_results=10)

        # Should only return one paper after deduplication
        assert len(papers) == 1

    @patch('kosmos.literature.arxiv_client.ArxivClient.search')
    def test_search_with_errors(self, mock_arxiv, unified_search):
        """Test handling of search errors."""
        mock_arxiv.side_effect = Exception("API Error")

        # Should return empty list instead of raising
        papers = unified_search.search("test query", sources=["arxiv"])
        assert papers == []


@pytest.mark.unit
class TestUnifiedSearchParallel:
    """Test parallel search functionality."""

    @patch('kosmos.literature.arxiv_client.ArxivClient.search')
    @patch('kosmos.literature.semantic_scholar.SemanticScholarClient.search')
    def test_parallel_execution(self, mock_s2, mock_arxiv, unified_search, sample_papers_list):
        """Test that searches execute in parallel."""
        mock_arxiv.return_value = [sample_papers_list[0]]
        mock_s2.return_value = [sample_papers_list[1]]

        papers = unified_search.search("test query", max_results=10, parallel=True)

        assert len(papers) == 2
        # Both clients should be called
        assert mock_arxiv.called
        assert mock_s2.called


@pytest.mark.unit
class TestUnifiedSearchDeduplication:
    """Test deduplication strategies."""

    def test_deduplicate_by_doi(self, unified_search):
        """Test deduplication by DOI."""
        papers = [
            PaperMetadata(
                title="Paper 1", authors=[], abstract="", year=2023,
                doi="10.1234/test", source="arxiv"
            ),
            PaperMetadata(
                title="Paper 1 Duplicate", authors=[], abstract="", year=2023,
                doi="10.1234/test", source="semantic_scholar"
            ),
        ]

        deduplicated = unified_search._deduplicate_papers(papers)
        assert len(deduplicated) == 1

    def test_deduplicate_by_arxiv_id(self, unified_search):
        """Test deduplication by arXiv ID."""
        papers = [
            PaperMetadata(
                title="Paper 1", authors=[], abstract="", year=2023,
                arxiv_id="2301.00001", source="arxiv"
            ),
            PaperMetadata(
                title="Paper 1", authors=[], abstract="", year=2023,
                arxiv_id="2301.00001", source="semantic_scholar"
            ),
        ]

        deduplicated = unified_search._deduplicate_papers(papers)
        assert len(deduplicated) == 1

    def test_deduplicate_by_title_similarity(self, unified_search):
        """Test fuzzy title-based deduplication."""
        papers = [
            PaperMetadata(
                title="Attention Is All You Need", authors=[], abstract="", year=2017,
                source="arxiv"
            ),
            PaperMetadata(
                title="Attention is All You Need", authors=[], abstract="", year=2017,
                source="semantic_scholar"
            ),
        ]

        deduplicated = unified_search._deduplicate_papers(papers)
        # Should recognize these as duplicates despite minor differences
        assert len(deduplicated) == 1


@pytest.mark.integration
@pytest.mark.slow
class TestUnifiedSearchIntegration:
    """Integration tests."""

    def test_real_unified_search(self):
        """Test real unified search across sources."""
        search = UnifiedLiteratureSearch()
        papers = search.search("transformer neural network", max_results=5)

        assert len(papers) > 0
        assert all(isinstance(p, PaperMetadata) for p in papers)
        # Should have papers from multiple sources
        sources = set(p.source for p in papers)
        assert len(sources) > 1
