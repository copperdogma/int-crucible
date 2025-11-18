"""
Tests for kosmos.knowledge.concept_extractor module.
"""

import pytest
from unittest.mock import Mock, patch

from kosmos.knowledge.concept_extractor import ConceptExtractor, ExtractedConcept, ExtractedMethod
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def concept_extractor(mock_llm_client):
    """Create ConceptExtractor with mocked LLM."""
    with patch('kosmos.knowledge.concept_extractor.get_client', return_value=mock_llm_client):
        extractor = ConceptExtractor()
        extractor.llm_client = mock_llm_client
        return extractor


@pytest.mark.unit
class TestConceptExtractorInit:
    """Test concept extractor initialization."""

    def test_init_default(self, mock_llm_client):
        """Test default initialization."""
        with patch('kosmos.knowledge.concept_extractor.get_client', return_value=mock_llm_client):
            extractor = ConceptExtractor()
            assert extractor.model == "claude-sonnet-4-5"

    def test_init_custom_model(self, mock_llm_client):
        """Test initialization with custom model."""
        with patch('kosmos.knowledge.concept_extractor.get_client', return_value=mock_llm_client):
            extractor = ConceptExtractor(model="claude-opus-4")
            assert extractor.model == "claude-opus-4"


@pytest.mark.unit
class TestConceptExtraction:
    """Test concept extraction."""

    def test_extract_from_paper(self, concept_extractor, sample_paper_metadata):
        """Test extracting concepts from a paper."""
        # Mock Claude response
        concept_extractor.llm_client.generate_structured.return_value = {
            "concepts": [
                {"name": "Transformer", "category": "Architecture", "relevance": 0.95},
                {"name": "Attention Mechanism", "category": "Method", "relevance": 0.90},
            ],
            "methods": [
                {"name": "Self-Attention", "category": "Technique", "relevance": 0.88},
            ],
            "relationships": [],
        }

        result = concept_extractor.extract_from_paper(sample_paper_metadata)

        assert len(result.concepts) == 2
        assert len(result.methods) == 1
        assert result.concepts[0].name == "Transformer"
        assert result.methods[0].name == "Self-Attention"

    def test_extract_with_relationships(self, concept_extractor, sample_paper_metadata):
        """Test extracting concepts with relationships."""
        concept_extractor.llm_client.generate_structured.return_value = {
            "concepts": [
                {"name": "Neural Network", "category": "Concept", "relevance": 0.85},
                {"name": "Deep Learning", "category": "Field", "relevance": 0.90},
            ],
            "methods": [],
            "relationships": [
                {
                    "source": "Neural Network",
                    "target": "Deep Learning",
                    "relationship_type": "PART_OF",
                    "confidence": 0.8,
                }
            ],
        }

        result = concept_extractor.extract_from_paper(
            sample_paper_metadata, include_relationships=True
        )

        assert len(result.relationships) == 1
        assert result.relationships[0].source == "Neural Network"
        assert result.relationships[0].target == "Deep Learning"

    def test_extract_with_limits(self, concept_extractor, sample_paper_metadata):
        """Test extraction with max limits."""
        # Return more concepts than limit
        concept_extractor.llm_client.generate_structured.return_value = {
            "concepts": [
                {"name": f"Concept {i}", "category": "Test", "relevance": 0.5}
                for i in range(20)
            ],
            "methods": [
                {"name": f"Method {i}", "category": "Test", "relevance": 0.5}
                for i in range(10)
            ],
            "relationships": [],
        }

        result = concept_extractor.extract_from_paper(
            sample_paper_metadata, max_concepts=5, max_methods=3
        )

        # Should respect limits
        assert len(result.concepts) <= 5
        assert len(result.methods) <= 3


@pytest.mark.unit
class TestConceptCaching:
    """Test concept extraction caching."""

    def test_cache_extractions(self, concept_extractor, sample_paper_metadata):
        """Test that extractions are cached."""
        concept_extractor.llm_client.generate_structured.return_value = {
            "concepts": [{"name": "Test", "category": "Test", "relevance": 0.5}],
            "methods": [],
            "relationships": [],
        }

        # First extraction
        result1 = concept_extractor.extract_from_paper(sample_paper_metadata)

        # Second extraction (should use cache)
        result2 = concept_extractor.extract_from_paper(sample_paper_metadata)

        # Should only call Claude once
        assert concept_extractor.llm_client.generate_structured.call_count == 1
        assert result1.concepts[0].name == result2.concepts[0].name


@pytest.mark.unit
class TestPromptBuilding:
    """Test prompt construction."""

    def test_build_prompt_complete_paper(self, concept_extractor, sample_paper_metadata):
        """Test building prompt for paper with all fields."""
        prompt = concept_extractor._build_concept_extraction_prompt(
            sample_paper_metadata, max_concepts=10, max_methods=5
        )

        assert isinstance(prompt, str)
        assert sample_paper_metadata.title in prompt
        assert sample_paper_metadata.abstract in prompt
        assert "10" in prompt  # max_concepts
        assert "5" in prompt  # max_methods

    def test_build_prompt_minimal_paper(self, concept_extractor):
        """Test building prompt for paper with minimal fields."""
        paper = PaperMetadata(
            title="Minimal", authors=[], abstract="", year=2023, source="test"
        )

        prompt = concept_extractor._build_concept_extraction_prompt(paper)

        assert isinstance(prompt, str)
        assert "Minimal" in prompt


@pytest.mark.unit
class TestConceptFiltering:
    """Test concept filtering and validation."""

    def test_filter_low_relevance(self, concept_extractor, sample_paper_metadata):
        """Test filtering concepts with low relevance."""
        concept_extractor.llm_client.generate_structured.return_value = {
            "concepts": [
                {"name": "High Relevance", "category": "Test", "relevance": 0.9},
                {"name": "Low Relevance", "category": "Test", "relevance": 0.3},
            ],
            "methods": [],
            "relationships": [],
        }

        result = concept_extractor.extract_from_paper(
            sample_paper_metadata, min_relevance=0.5
        )

        # Should only include high relevance concept
        assert len(result.concepts) == 1
        assert result.concepts[0].name == "High Relevance"


@pytest.mark.integration
@pytest.mark.requires_claude
class TestConceptExtractorIntegration:
    """Integration tests (requires Claude API)."""

    def test_real_concept_extraction(self, sample_paper_metadata):
        """Test real concept extraction using Claude."""
        extractor = ConceptExtractor()

        result = extractor.extract_from_paper(sample_paper_metadata, max_concepts=5)

        assert len(result.concepts) > 0
        assert all(isinstance(c, ExtractedConcept) for c in result.concepts)
        assert all(0.0 <= c.relevance <= 1.0 for c in result.concepts)
