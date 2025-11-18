"""
Tests for kosmos.literature.pubmed_client module.
"""

import pytest
import responses
from unittest.mock import Mock, patch
from Bio import Entrez

from kosmos.literature.pubmed_client import PubMedClient
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def pubmed_client():
    """Create PubMedClient instance for testing."""
    return PubMedClient(email="test@example.com")


@pytest.mark.unit
class TestPubMedInit:
    """Test PubMed client initialization."""

    def test_init_with_email(self):
        """Test initialization with email."""
        client = PubMedClient(email="test@example.com")
        assert client.email == "test@example.com"
        assert Entrez.email == "test@example.com"

    def test_init_sets_tool_name(self):
        """Test that tool name is set."""
        client = PubMedClient(email="test@example.com")
        assert Entrez.tool == "Kosmos"


@pytest.mark.unit
class TestPubMedSearch:
    """Test PubMed search functionality."""

    @patch('Bio.Entrez.esearch')
    @patch('Bio.Entrez.efetch')
    def test_search_success(self, mock_efetch, mock_esearch, pubmed_client, pubmed_response_xml):
        """Test successful PubMed search."""
        # Mock esearch response
        mock_esearch.return_value.__enter__.return_value.read.return_value = {
            "IdList": ["23287718", "28753425"],
            "Count": "2",
        }

        # Mock efetch response
        mock_efetch.return_value.__enter__.return_value.read.return_value = pubmed_response_xml

        papers = pubmed_client.search("CRISPR", max_results=2)

        assert len(papers) <= 2
        assert all(isinstance(p, PaperMetadata) for p in papers)

    @patch('Bio.Entrez.esearch')
    def test_search_empty_results(self, mock_esearch, pubmed_client):
        """Test search with no results."""
        mock_esearch.return_value.__enter__.return_value.read.return_value = {
            "IdList": [],
            "Count": "0",
        }

        papers = pubmed_client.search("nonexistent_query_xyz")
        assert papers == []

    @patch('Bio.Entrez.esearch')
    def test_search_with_error(self, mock_esearch, pubmed_client):
        """Test search error handling."""
        mock_esearch.side_effect = Exception("API Error")

        papers = pubmed_client.search("test query")
        assert papers == []


@pytest.mark.unit
class TestPubMedGetPaper:
    """Test fetching papers by PubMed ID."""

    @patch('Bio.Entrez.efetch')
    def test_get_paper_by_id_success(self, mock_efetch, pubmed_client):
        """Test fetching paper by PubMed ID."""
        mock_xml = """<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>23287718</PMID>
                    <Article>
                        <ArticleTitle>CRISPR Test</ArticleTitle>
                        <Abstract><AbstractText>Test abstract</AbstractText></Abstract>
                        <AuthorList>
                            <Author><LastName>Test</LastName><ForeName>Author</ForeName></Author>
                        </AuthorList>
                    </Article>
                </MedlineCitation>
                <PubmedData>
                    <ArticleIdList>
                        <ArticleId IdType="doi">10.1234/test</ArticleId>
                    </ArticleIdList>
                </PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>"""

        mock_efetch.return_value.__enter__.return_value.read.return_value = mock_xml

        paper = pubmed_client.get_paper_by_id("23287718")

        assert paper is not None
        assert paper.pubmed_id == "23287718"

    @patch('Bio.Entrez.efetch')
    def test_get_paper_by_id_not_found(self, mock_efetch, pubmed_client):
        """Test fetching non-existent paper."""
        mock_efetch.side_effect = Exception("Not found")

        paper = pubmed_client.get_paper_by_id("99999999")
        assert paper is None


@pytest.mark.unit
class TestPubMedRateLimiting:
    """Test rate limiting."""

    @patch('time.sleep')
    @patch('Bio.Entrez.esearch')
    def test_rate_limiting_delay(self, mock_esearch, mock_sleep, pubmed_client):
        """Test that rate limiting adds delays."""
        mock_esearch.return_value.__enter__.return_value.read.return_value = {
            "IdList": [],
            "Count": "0",
        }

        # Make multiple requests
        pubmed_client.search("query1", max_results=1)
        pubmed_client.search("query2", max_results=1)

        # Should add delays between requests
        assert mock_sleep.called


@pytest.mark.integration
@pytest.mark.slow
class TestPubMedIntegration:
    """Integration tests (requires network)."""

    def test_real_search(self):
        """Test real PubMed search."""
        client = PubMedClient(email="test@example.com")
        papers = client.search("diabetes", max_results=2)

        assert len(papers) > 0
        assert all(isinstance(p, PaperMetadata) for p in papers)
        assert all(p.pubmed_id is not None for p in papers)
