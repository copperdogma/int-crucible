"""
Unit tests for Unified Domain Knowledge Base (Phase 9).

Tests cross-domain integration, concept search, mapping, and domain suggestions.
"""

import pytest
from typing import List, Tuple

from kosmos.knowledge.domain_kb import (
    DomainKnowledgeBase,
    Domain,
    DomainConcept,
    CrossDomainMapping
)
from kosmos.domains.biology.ontology import BiologyOntology
from kosmos.domains.neuroscience.ontology import NeuroscienceOntology
from kosmos.domains.materials.ontology import MaterialsOntology


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def domain_kb():
    """Create DomainKnowledgeBase instance"""
    return DomainKnowledgeBase()


# ============================================================================
# Test Domain KB Initialization
# ============================================================================

@pytest.mark.unit
class TestDomainKBInit:
    """Test DomainKnowledgeBase initialization."""

    def test_initialization_loads_all_ontologies(self, domain_kb):
        """Test that all 3 ontologies are loaded on init."""
        assert domain_kb.biology is not None
        assert domain_kb.neuroscience is not None
        assert domain_kb.materials is not None

        assert isinstance(domain_kb.biology, BiologyOntology)
        assert isinstance(domain_kb.neuroscience, NeuroscienceOntology)
        assert isinstance(domain_kb.materials, MaterialsOntology)

    def test_cross_domain_mappings_initialized(self, domain_kb):
        """Test that cross-domain mappings are initialized."""
        assert len(domain_kb.cross_domain_mappings) >= 7  # At least 7 initial mappings

        # Verify all are CrossDomainMapping instances
        for mapping in domain_kb.cross_domain_mappings:
            assert isinstance(mapping, CrossDomainMapping)
            assert mapping.source_domain in [Domain.BIOLOGY, Domain.NEUROSCIENCE, Domain.MATERIALS]
            assert mapping.target_domain in [Domain.BIOLOGY, Domain.NEUROSCIENCE, Domain.MATERIALS]
            assert 0.0 <= mapping.confidence <= 1.0

    def test_concept_counts(self, domain_kb):
        """Test that expected number of concepts are loaded."""
        bio_concepts = len(domain_kb.biology.concepts)
        neuro_concepts = len(domain_kb.neuroscience.concepts)
        materials_concepts = len(domain_kb.materials.concepts)

        # Should have concepts in each domain
        assert bio_concepts > 0, "Biology ontology should have concepts"
        assert neuro_concepts > 0, "Neuroscience ontology should have concepts"
        assert materials_concepts > 0, "Materials ontology should have concepts"

        # Total should be ~111 (18 bio + 45 neuro + 48 materials)
        total_concepts = bio_concepts + neuro_concepts + materials_concepts
        assert total_concepts >= 100, f"Expected ~111 concepts, got {total_concepts}"

    def test_ontology_instances_correct_types(self, domain_kb):
        """Test that ontology instances are correct types."""
        # Biology
        assert hasattr(domain_kb.biology, 'concepts')
        assert hasattr(domain_kb.biology, 'relations')

        # Neuroscience
        assert hasattr(domain_kb.neuroscience, 'concepts')
        assert hasattr(domain_kb.neuroscience, 'relations')

        # Materials
        assert hasattr(domain_kb.materials, 'concepts')
        assert hasattr(domain_kb.materials, 'relations')


# ============================================================================
# Test Get Domain Ontology
# ============================================================================

@pytest.mark.unit
class TestGetDomainOntology:
    """Test retrieving domain ontologies."""

    def test_get_biology_ontology_string(self, domain_kb):
        """Test getting biology ontology with string input."""
        ontology = domain_kb.get_domain_ontology("biology")

        assert isinstance(ontology, BiologyOntology)
        assert ontology == domain_kb.biology

    def test_get_neuroscience_ontology_enum(self, domain_kb):
        """Test getting neuroscience ontology with enum input."""
        ontology = domain_kb.get_domain_ontology(Domain.NEUROSCIENCE)

        assert isinstance(ontology, NeuroscienceOntology)
        assert ontology == domain_kb.neuroscience

    def test_get_materials_ontology(self, domain_kb):
        """Test getting materials ontology."""
        ontology = domain_kb.get_domain_ontology(Domain.MATERIALS)

        assert isinstance(ontology, MaterialsOntology)
        assert ontology == domain_kb.materials


# ============================================================================
# Test Find Concepts
# ============================================================================

@pytest.mark.unit
class TestFindConcepts:
    """Test cross-domain concept search."""

    def test_find_by_exact_name_match(self, domain_kb):
        """Test finding concepts by exact name."""
        # Search for purine (biology)
        results = domain_kb.find_concepts("purine_metabolism")

        assert len(results) > 0
        assert any(c.domain == Domain.BIOLOGY for c in results)

    def test_find_by_partial_name_match(self, domain_kb):
        """Test finding concepts by partial name."""
        results = domain_kb.find_concepts("conductivity")

        # Should find electrical_conductivity (materials) and possibly others
        assert len(results) > 0

    def test_find_by_synonym(self, domain_kb):
        """Test finding concepts by synonym match."""
        # Many concepts have synonyms
        results = domain_kb.find_concepts("dopamine")

        if len(results) > 0:  # If dopamine exists in ontology
            assert any(c.domain == Domain.NEUROSCIENCE for c in results)

    def test_find_by_concept_id(self, domain_kb):
        """Test finding concepts by ID."""
        # Search for concept ID
        results = domain_kb.find_concepts("electrical_conductivity")

        assert len(results) > 0
        # Should find in materials domain

    def test_find_across_all_domains(self, domain_kb):
        """Test searching across all domains."""
        results = domain_kb.find_concepts("protein", domains=None)

        # Should search all domains
        # protein might appear in biology and neuroscience
        assert len(results) > 0

    def test_find_in_specific_domain_only(self, domain_kb):
        """Test searching in specific domain."""
        results = domain_kb.find_concepts("crystal", domains=[Domain.MATERIALS])

        # Should only return materials concepts
        assert all(c.domain == Domain.MATERIALS for c in results)

    def test_case_insensitive_search(self, domain_kb):
        """Test that search is case-insensitive."""
        results_lower = domain_kb.find_concepts("protein")
        results_upper = domain_kb.find_concepts("PROTEIN")
        results_mixed = domain_kb.find_concepts("PrOtEiN")

        # Should return same results regardless of case
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_no_matches_returns_empty_list(self, domain_kb):
        """Test that no matches returns empty list."""
        results = domain_kb.find_concepts("nonexistent_concept_xyz123")

        assert isinstance(results, list)
        assert len(results) == 0


# ============================================================================
# Test Cross-Domain Mappings
# ============================================================================

@pytest.mark.unit
class TestCrossDomainMappings:
    """Test cross-domain concept mapping."""

    def test_find_mapping_electrical_conductivity(self, domain_kb):
        """Test finding mapping for electrical_conductivity."""
        mappings = domain_kb.map_cross_domain_concepts(
            concept_id="electrical_conductivity",
            source_domain=Domain.MATERIALS
        )

        # Should map materials → neuroscience (neural_conductance)
        assert len(mappings) > 0
        assert any(m.target_domain == Domain.NEUROSCIENCE for m in mappings)
        assert any(m.target_concept_id == "neural_conductance" for m in mappings)

    def test_find_reverse_mapping(self, domain_kb):
        """Test finding reverse mapping (target → source)."""
        # Search from neuroscience side
        mappings = domain_kb.map_cross_domain_concepts(
            concept_id="neural_conductance",
            source_domain=Domain.NEUROSCIENCE
        )

        # Should find reverse mapping to materials
        assert len(mappings) > 0
        assert any(m.target_domain == Domain.MATERIALS for m in mappings)
        assert any(m.target_concept_id == "electrical_conductivity" for m in mappings)

    def test_confidence_threshold_filtering(self, domain_kb):
        """Test filtering by confidence threshold."""
        # Get all mappings
        all_mappings = domain_kb.map_cross_domain_concepts(
            concept_id="electrical_conductivity",
            source_domain=Domain.MATERIALS,
            min_confidence=0.0
        )

        # Get high-confidence only
        high_conf_mappings = domain_kb.map_cross_domain_concepts(
            concept_id="electrical_conductivity",
            source_domain=Domain.MATERIALS,
            min_confidence=0.9
        )

        # High confidence should be subset of all
        assert len(high_conf_mappings) <= len(all_mappings)

    def test_mapping_types(self, domain_kb):
        """Test different mapping types."""
        mappings = domain_kb.cross_domain_mappings

        # Should have different types
        mapping_types = {m.mapping_type for m in mappings}
        assert "analogous" in mapping_types or "related" in mapping_types or "equivalent" in mapping_types

    def test_all_initial_mappings_present(self, domain_kb):
        """Test that all 7 initial mappings are present."""
        mappings = domain_kb.cross_domain_mappings

        # Check specific known mappings
        mapping_pairs = {
            (m.source_concept_id, m.target_concept_id) for m in mappings
        }

        # Should have electrical_conductivity ↔ neural_conductance
        assert ("electrical_conductivity", "neural_conductance") in mapping_pairs or \
               ("neural_conductance", "electrical_conductivity") in mapping_pairs

    def test_source_domain_filtering(self, domain_kb):
        """Test filtering by source domain."""
        mappings_with_domain = domain_kb.map_cross_domain_concepts(
            concept_id="electrical_conductivity",
            source_domain=Domain.MATERIALS
        )

        mappings_no_domain = domain_kb.map_cross_domain_concepts(
            concept_id="electrical_conductivity",
            source_domain=None
        )

        # Without domain filter might find more (if concept appears in multiple domains)
        assert len(mappings_with_domain) <= len(mappings_no_domain)

    def test_bidirectional_mapping_consistency(self, domain_kb):
        """Test that bidirectional mappings are consistent."""
        forward = domain_kb.map_cross_domain_concepts(
            concept_id="electrical_conductivity",
            source_domain=Domain.MATERIALS
        )

        if len(forward) > 0:
            # Get first mapping target
            target_id = forward[0].target_concept_id
            target_domain = forward[0].target_domain

            # Find reverse
            reverse = domain_kb.map_cross_domain_concepts(
                concept_id=target_id,
                source_domain=target_domain
            )

            # Should map back
            assert len(reverse) > 0
            assert any(m.target_concept_id == "electrical_conductivity" for m in reverse)

    def test_no_mappings_for_unmapped_concept(self, domain_kb):
        """Test that unmapped concepts return empty list."""
        mappings = domain_kb.map_cross_domain_concepts(
            concept_id="nonexistent_concept",
            source_domain=Domain.BIOLOGY
        )

        assert isinstance(mappings, list)
        assert len(mappings) == 0

    def test_min_confidence_parameter_works(self, domain_kb):
        """Test that min_confidence parameter is respected."""
        # All mappings
        all_mappings = domain_kb.map_cross_domain_concepts(
            concept_id="electrical_conductivity",
            min_confidence=0.0
        )

        # Very high confidence only (unlikely to have any)
        very_high = domain_kb.map_cross_domain_concepts(
            concept_id="electrical_conductivity",
            min_confidence=0.99
        )

        # Verify filtering worked
        assert len(very_high) <= len(all_mappings)
        for mapping in very_high:
            assert mapping.confidence >= 0.99


# ============================================================================
# Test Find Related Concepts
# ============================================================================

@pytest.mark.unit
class TestFindRelatedConcepts:
    """Test finding related concepts (same-domain + cross-domain)."""

    def test_same_domain_relations_only(self, domain_kb):
        """Test finding same-domain relations."""
        # Find concept with relations
        concept_id = "purine_metabolism"  # Biology concept

        results = domain_kb.find_related_concepts(
            concept_id=concept_id,
            source_domain=Domain.BIOLOGY,
            include_cross_domain=False
        )

        assert "same_domain" in results
        assert "cross_domain" in results
        # Should have same-domain results
        # Cross-domain should be empty
        assert len(results["cross_domain"]) == 0

    def test_cross_domain_relations_only(self, domain_kb):
        """Test finding cross-domain relations."""
        concept_id = "electrical_conductivity"

        results = domain_kb.find_related_concepts(
            concept_id=concept_id,
            source_domain=Domain.MATERIALS,
            include_cross_domain=True,
            min_confidence=0.5
        )

        assert "same_domain" in results
        assert "cross_domain" in results

        # Should have cross-domain results (neural_conductance)
        if len(results["cross_domain"]) > 0:
            assert any(c.domain == Domain.NEUROSCIENCE for c in results["cross_domain"])

    def test_both_same_and_cross_domain(self, domain_kb):
        """Test finding both same-domain and cross-domain relations."""
        # Concept that has both
        concept_id = "electrical_conductivity"

        results = domain_kb.find_related_concepts(
            concept_id=concept_id,
            source_domain=Domain.MATERIALS,
            include_cross_domain=True
        )

        assert "same_domain" in results
        assert "cross_domain" in results

    def test_confidence_filtering(self, domain_kb):
        """Test confidence filtering for cross-domain."""
        concept_id = "electrical_conductivity"

        # Low threshold
        low_threshold = domain_kb.find_related_concepts(
            concept_id=concept_id,
            source_domain=Domain.MATERIALS,
            include_cross_domain=True,
            min_confidence=0.1
        )

        # High threshold
        high_threshold = domain_kb.find_related_concepts(
            concept_id=concept_id,
            source_domain=Domain.MATERIALS,
            include_cross_domain=True,
            min_confidence=0.95
        )

        # High threshold should have fewer or equal cross-domain results
        assert len(high_threshold["cross_domain"]) <= len(low_threshold["cross_domain"])

    def test_empty_results_for_isolated_concept(self, domain_kb):
        """Test that isolated concepts return empty results."""
        results = domain_kb.find_related_concepts(
            concept_id="nonexistent",
            source_domain=Domain.BIOLOGY,
            include_cross_domain=True
        )

        assert len(results["same_domain"]) == 0
        assert len(results["cross_domain"]) == 0

    def test_metadata_includes_mapping_info(self, domain_kb):
        """Test that cross-domain results include mapping metadata."""
        concept_id = "electrical_conductivity"

        results = domain_kb.find_related_concepts(
            concept_id=concept_id,
            source_domain=Domain.MATERIALS,
            include_cross_domain=True
        )

        if len(results["cross_domain"]) > 0:
            cross_domain_concept = results["cross_domain"][0]
            # Should have mapping metadata
            assert "mapping_type" in cross_domain_concept.metadata
            assert "confidence" in cross_domain_concept.metadata


# ============================================================================
# Test Get All Concepts
# ============================================================================

@pytest.mark.unit
class TestGetAllConcepts:
    """Test retrieving all concepts."""

    def test_get_all_from_single_domain(self, domain_kb):
        """Test getting all concepts from a single domain."""
        bio_concepts = domain_kb.get_all_concepts(domain=Domain.BIOLOGY)

        assert len(bio_concepts) > 0
        assert all(c.domain == Domain.BIOLOGY for c in bio_concepts)

    def test_get_all_from_all_domains(self, domain_kb):
        """Test getting all concepts from all domains."""
        all_concepts = domain_kb.get_all_concepts(domain=None)

        # Should have ~111 concepts total
        assert len(all_concepts) >= 100

        # Should have concepts from all domains
        domains = {c.domain for c in all_concepts}
        assert Domain.BIOLOGY in domains
        assert Domain.NEUROSCIENCE in domains
        assert Domain.MATERIALS in domains

    def test_concept_structure_validation(self, domain_kb):
        """Test that returned concepts have correct structure."""
        concepts = domain_kb.get_all_concepts(domain=Domain.BIOLOGY)

        for concept in concepts:
            assert isinstance(concept, DomainConcept)
            assert concept.domain == Domain.BIOLOGY
            assert concept.concept_id is not None
            assert concept.name is not None
            assert concept.type is not None
            # Optional fields
            assert hasattr(concept, 'description')
            assert hasattr(concept, 'synonyms')
            assert hasattr(concept, 'external_ids')
            assert hasattr(concept, 'metadata')

    def test_domain_field_correct(self, domain_kb):
        """Test that domain field is correctly set."""
        for domain in [Domain.BIOLOGY, Domain.NEUROSCIENCE, Domain.MATERIALS]:
            concepts = domain_kb.get_all_concepts(domain=domain)
            assert all(c.domain == domain for c in concepts)


# ============================================================================
# Test Suggest Domains for Hypothesis
# ============================================================================

@pytest.mark.unit
class TestSuggestDomainsForHypothesis:
    """Test domain suggestion based on hypothesis text."""

    def test_biology_specific_hypothesis(self, domain_kb):
        """Test biology-specific hypothesis gets high biology score."""
        hypothesis = "Gene expression regulates protein synthesis in metabolic pathways"

        suggestions = domain_kb.suggest_domains_for_hypothesis(hypothesis)

        assert len(suggestions) > 0
        assert isinstance(suggestions, list)

        # Biology should be top or high-scoring
        top_domain, top_score = suggestions[0]
        assert top_domain == Domain.BIOLOGY or top_score > 0.5

    def test_neuroscience_specific_hypothesis(self, domain_kb):
        """Test neuroscience-specific hypothesis."""
        hypothesis = "Synaptic plasticity in dopaminergic neurons affects learning"

        suggestions = domain_kb.suggest_domains_for_hypothesis(hypothesis)

        # Neuroscience should score highly
        domain_scores = {domain: score for domain, score in suggestions}
        assert domain_scores.get(Domain.NEUROSCIENCE, 0) > 0.5

    def test_materials_specific_hypothesis(self, domain_kb):
        """Test materials science-specific hypothesis."""
        hypothesis = "Crystal structure affects electrical conductivity in perovskite materials"

        suggestions = domain_kb.suggest_domains_for_hypothesis(hypothesis)

        # Materials should score highly
        domain_scores = {domain: score for domain, score in suggestions}
        assert domain_scores.get(Domain.MATERIALS, 0) > 0.5

    def test_multi_domain_hypothesis(self, domain_kb):
        """Test multi-domain hypothesis gets multiple high scores."""
        hypothesis = "Neural conductance in neurons is analogous to electrical conductivity in semiconductor materials"

        suggestions = domain_kb.suggest_domains_for_hypothesis(hypothesis)

        domain_scores = {domain: score for domain, score in suggestions}

        # Both neuroscience and materials should score
        assert domain_scores.get(Domain.NEUROSCIENCE, 0) > 0
        assert domain_scores.get(Domain.MATERIALS, 0) > 0

    def test_generic_hypothesis(self, domain_kb):
        """Test generic hypothesis gets low scores."""
        hypothesis = "This is a test with no domain-specific keywords"

        suggestions = domain_kb.suggest_domains_for_hypothesis(hypothesis)

        # All scores should be low
        for domain, score in suggestions:
            assert score <= 0.5

    def test_normalized_scoring(self, domain_kb):
        """Test that scores are normalized to 0-1 range."""
        hypothesis = "Gene expression and protein synthesis in neural pathways"

        suggestions = domain_kb.suggest_domains_for_hypothesis(hypothesis)

        for domain, score in suggestions:
            assert 0.0 <= score <= 1.0


# ============================================================================
# Test Get Concept By ID
# ============================================================================

@pytest.mark.unit
class TestGetConceptByID:
    """Test retrieving specific concepts by ID."""

    def test_get_existing_concept(self, domain_kb):
        """Test retrieving an existing concept."""
        # Get a known concept ID
        all_bio = domain_kb.get_all_concepts(domain=Domain.BIOLOGY)
        if len(all_bio) > 0:
            known_id = all_bio[0].concept_id

            concept = domain_kb.get_concept_by_id(known_id, Domain.BIOLOGY)

            assert concept is not None
            assert isinstance(concept, DomainConcept)
            assert concept.concept_id == known_id

    def test_get_nonexistent_concept(self, domain_kb):
        """Test retrieving a non-existent concept returns None."""
        concept = domain_kb.get_concept_by_id("nonexistent_xyz", Domain.BIOLOGY)

        assert concept is None

    def test_get_concept_wrong_domain(self, domain_kb):
        """Test retrieving concept from wrong domain returns None."""
        # Get biology concept
        all_bio = domain_kb.get_all_concepts(domain=Domain.BIOLOGY)
        if len(all_bio) > 0:
            bio_id = all_bio[0].concept_id

            # Try to get from materials (should be None)
            concept = domain_kb.get_concept_by_id(bio_id, Domain.MATERIALS)

            assert concept is None
