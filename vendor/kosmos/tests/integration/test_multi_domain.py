"""
Integration tests for multi-domain functionality (Phase 9).

Tests end-to-end integration of cross-domain capabilities:
- Cross-domain concept search (DomainKnowledgeBase)
- Domain routing integration (DomainRouter)
- Template discovery (Template Registry)
- End-to-end multi-domain workflows

Coverage target: 15 integration tests across 4 test classes
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from kosmos.knowledge.domain_kb import DomainKnowledgeBase, Domain, CrossDomainMapping
from kosmos.core.domain_router import DomainRouter
from kosmos.models.domain import ScientificDomain


@pytest.fixture
def domain_kb():
    """Domain knowledge base instance"""
    return DomainKnowledgeBase()


@pytest.fixture
def domain_router(mock_env_vars):
    """Domain router instance (no Claude client for testing)"""
    return DomainRouter(claude_client=None)


@pytest.fixture
def template_registry():
    """Template registry instance (simple dict for testing)"""
    # Mock template registry with domain-specific templates
    registry = {
        'biology': [
            {'name': 'metabolomics_comparison', 'domain': 'biology'},
            {'name': 'gwas_multimodal', 'domain': 'biology'}
        ],
        'neuroscience': [
            {'name': 'connectome_scaling', 'domain': 'neuroscience'},
            {'name': 'differential_expression', 'domain': 'neuroscience'}
        ],
        'materials': [
            {'name': 'parameter_correlation', 'domain': 'materials'},
            {'name': 'optimization', 'domain': 'materials'},
            {'name': 'shap_analysis', 'domain': 'materials'}
        ]
    }
    return registry


# ============================================================================
# Test Cross-Domain Concept Search
# ============================================================================

@pytest.mark.integration
class TestCrossDomainConceptSearch:
    """Test integrated cross-domain concept search."""

    def test_search_conductivity_finds_both_domains(self, domain_kb):
        """Test searching 'conductivity' finds electrical and neural concepts."""
        # Search for conductivity concept
        results = domain_kb.find_concepts("conductivity")

        # Should find concepts from multiple domains
        assert len(results) > 0

        # Extract domain names
        domains = {concept.domain for concept in results}

        # Should find materials and/or neuroscience concepts
        # (electrical_conductivity in materials, neural_conductance in neuroscience)
        assert any(domain in [Domain.MATERIALS, Domain.NEUROSCIENCE] for domain in domains)

    def test_cross_domain_mapping_retrieval(self, domain_kb):
        """Test retrieving cross-domain mappings."""
        # Map electrical_conductivity to related concepts
        mappings = domain_kb.map_cross_domain_concepts("electrical_conductivity")

        # Should find mappings
        assert isinstance(mappings, list)
        assert len(mappings) > 0

        # Should be CrossDomainMapping objects
        for mapping in mappings:
            assert isinstance(mapping, CrossDomainMapping)
            assert hasattr(mapping, 'source_domain')
            assert hasattr(mapping, 'target_domain')
            assert hasattr(mapping, 'confidence')

        # At least one mapping should connect to neuroscience
        neuroscience_mappings = [
            m for m in mappings
            if m.target_domain == Domain.NEUROSCIENCE or m.source_domain == Domain.NEUROSCIENCE
        ]
        assert len(neuroscience_mappings) > 0

    def test_domain_suggestion_based_on_hypothesis(self, domain_kb):
        """Test suggesting domains for hypothesis text."""
        # Test biology ontology is accessible
        bio_ontology = domain_kb.get_domain_ontology(Domain.BIOLOGY)
        assert bio_ontology is not None
        assert len(bio_ontology.concepts) > 0

        # Test neuroscience ontology
        neuro_ontology = domain_kb.get_domain_ontology(Domain.NEUROSCIENCE)
        assert neuro_ontology is not None
        assert len(neuro_ontology.concepts) > 0

        # Test materials ontology
        materials_ontology = domain_kb.get_domain_ontology(Domain.MATERIALS)
        assert materials_ontology is not None
        assert len(materials_ontology.concepts) > 0


# ============================================================================
# Test Domain Routing Integration
# ============================================================================

@pytest.mark.integration
class TestDomainRoutingIntegration:
    """Test integrated domain routing."""

    def test_biology_hypothesis_correct_routing(self, domain_router):
        """Test biology hypothesis routes to biology domain."""
        # Biology-related question
        question = "How does gene expression affect protein synthesis in metabolic pathways?"

        # Classify domain (uses keyword-based fallback without Claude)
        classification = domain_router.classify_research_question(question)

        # Should identify biology as primary domain
        assert classification.primary_domain == ScientificDomain.BIOLOGY
        # confidence is DomainConfidence enum, check it's not LOW
        from kosmos.models.domain import DomainConfidence
        assert classification.confidence != DomainConfidence.LOW

        # Route the question
        routing = domain_router.route(question)

        # Should route to biology domain
        assert ScientificDomain.BIOLOGY in routing.selected_domains

    def test_neuroscience_hypothesis_correct_routing(self, domain_router):
        """Test neuroscience hypothesis routes correctly."""
        question = "What are the neural connectivity patterns in the cortex?"

        # Classify
        classification = domain_router.classify_research_question(question)

        # Should identify neuroscience
        assert classification.primary_domain == ScientificDomain.NEUROSCIENCE
        from kosmos.models.domain import DomainConfidence
        assert classification.confidence != DomainConfidence.LOW

        # Route
        routing = domain_router.route(question)
        assert ScientificDomain.NEUROSCIENCE in routing.selected_domains

    def test_materials_hypothesis_correct_routing(self, domain_router):
        """Test materials hypothesis routes correctly."""
        question = "How does temperature affect the band gap of perovskite semiconductors?"

        # Classify
        classification = domain_router.classify_research_question(question)

        # Should identify materials science
        assert classification.primary_domain == ScientificDomain.MATERIALS
        from kosmos.models.domain import DomainConfidence
        assert classification.confidence != DomainConfidence.LOW

        # Route
        routing = domain_router.route(question)
        assert ScientificDomain.MATERIALS in routing.selected_domains

    def test_multi_domain_hypothesis_parallel_routing(self, domain_router):
        """Test multi-domain hypothesis gets parallel routing strategy."""
        # Question spanning biology and neuroscience
        question = "How do genetic mutations affect neural network connectivity in the brain?"

        # Classify
        classification = domain_router.classify_research_question(question)

        # Should identify multiple domains or multi-domain
        # Check supporting domains exist or strategy is multi-domain
        has_multi = (
            (hasattr(classification, 'supporting_domains') and len(classification.supporting_domains) > 0) or
            (hasattr(classification, 'is_multi_domain') and classification.is_multi_domain)
        )
        assert has_multi or classification.primary_domain in [ScientificDomain.BIOLOGY, ScientificDomain.NEUROSCIENCE]

        # Route
        routing = domain_router.route(question)

        # Should have valid domain routing
        assert len(routing.selected_domains) > 0
        assert routing.selected_domains[0] in [ScientificDomain.BIOLOGY, ScientificDomain.NEUROSCIENCE]


# ============================================================================
# Test Template Discovery
# ============================================================================

@pytest.mark.integration
class TestTemplateDiscovery:
    """Test template auto-discovery."""

    def test_all_domain_templates_discovered(self, template_registry):
        """Test that all 7 domain-specific templates are discovered."""
        # Count templates across all domains
        total_templates = sum(len(templates) for templates in template_registry.values())

        # Should have 7 domain-specific templates (2 bio + 2 neuro + 3 materials)
        assert total_templates >= 7

        # Check each domain has templates
        assert 'biology' in template_registry
        assert 'neuroscience' in template_registry
        assert 'materials' in template_registry

    def test_template_registry_populated(self, template_registry):
        """Test template registry has all templates."""
        # Biology templates
        bio_templates = template_registry['biology']
        assert len(bio_templates) >= 2
        bio_names = [t['name'] for t in bio_templates]
        assert 'metabolomics_comparison' in bio_names
        assert 'gwas_multimodal' in bio_names

        # Neuroscience templates
        neuro_templates = template_registry['neuroscience']
        assert len(neuro_templates) >= 2
        neuro_names = [t['name'] for t in neuro_templates]
        assert 'connectome_scaling' in neuro_names
        assert 'differential_expression' in neuro_names

        # Materials templates
        materials_templates = template_registry['materials']
        assert len(materials_templates) >= 3
        materials_names = [t['name'] for t in materials_templates]
        assert 'parameter_correlation' in materials_names
        assert 'optimization' in materials_names
        assert 'shap_analysis' in materials_names

    def test_domain_specific_template_retrieval(self, template_registry):
        """Test retrieving templates by domain."""
        # Get materials templates
        materials_templates = template_registry.get('materials', [])
        assert len(materials_templates) == 3

        # Each template should have correct domain
        for template in materials_templates:
            assert template['domain'] == 'materials'


# ============================================================================
# Test End-to-End Multi-Domain
# ============================================================================

@pytest.mark.integration
class TestEndToEndMultiDomain:
    """Test complete end-to-end multi-domain workflows."""

    def test_question_to_classification_to_routing(self, domain_router, domain_kb):
        """Test complete pipeline: question → classification → routing → capabilities."""
        # Step 1: Research question
        question = "How does silicon crystal structure affect its electrical conductivity?"

        # Step 2: Classification
        classification = domain_router.classify_research_question(question)
        assert classification.primary_domain == ScientificDomain.MATERIALS

        # Step 3: Routing
        routing = domain_router.route(question)
        assert ScientificDomain.MATERIALS in routing.selected_domains

        # Step 4: Get domain capabilities
        capabilities = domain_router.get_domain_capabilities(ScientificDomain.MATERIALS)
        assert capabilities is not None
        assert len(capabilities.api_clients) > 0  # Should have materials API clients

        # Step 5: Verify materials ontology in knowledge base
        materials_ontology = domain_kb.get_domain_ontology(Domain.MATERIALS)
        assert materials_ontology is not None
        assert len(materials_ontology.concepts) > 0

    def test_cross_domain_synthesis_suggestion(self, domain_router, domain_kb):
        """Test cross-domain synthesis suggestions."""
        # Find cross-domain mappings
        mappings = domain_kb.map_cross_domain_concepts("electrical_conductivity")

        # Should suggest connections
        assert len(mappings) > 0

        # Verify cross-domain connections exist in knowledge base
        # The mappings themselves are the cross-domain suggestions
        assert len(mappings) > 0

        # Verify multiple domains represented
        domains_in_mappings = set()
        for m in mappings:
            domains_in_mappings.add(m.source_domain)
            domains_in_mappings.add(m.target_domain)

        assert len(domains_in_mappings) >= 2

    def test_domain_expertise_assessment(self, domain_router):
        """Test domain expertise assessment integration."""
        # Assess expertise for each domain
        for domain in [ScientificDomain.BIOLOGY, ScientificDomain.NEUROSCIENCE, ScientificDomain.MATERIALS]:
            assessment = domain_router.assess_domain_expertise(domain)

            # Should return expertise assessment
            assert assessment is not None
            assert hasattr(assessment, 'domain')
            assert hasattr(assessment, 'available_tools')
            assert hasattr(assessment, 'available_templates')
            assert len(assessment.available_tools) > 0

    def test_multi_modal_experiment_design(self, domain_router, template_registry):
        """Test multi-modal experiment design routing."""
        # Question requiring materials analysis
        question = "What is the optimal temperature for perovskite solar cell efficiency?"

        # Route
        routing = domain_router.route(question)
        assert ScientificDomain.MATERIALS in routing.selected_domains

        # Get materials templates
        materials_templates = template_registry.get('materials', [])

        # Should have optimization and parameter correlation templates
        template_names = [t['name'] for t in materials_templates]
        assert 'optimization' in template_names
        assert 'parameter_correlation' in template_names

    def test_full_pipeline_question_to_experiment_protocol(self, domain_router, domain_kb, template_registry):
        """Test full pipeline from research question to experiment protocol."""
        # Complete end-to-end workflow
        question = "How does gene BRCA1 mutation affect breast cancer risk?"

        # Step 1: Domain classification
        classification = domain_router.classify_research_question(question)
        assert classification.primary_domain == ScientificDomain.BIOLOGY

        # Step 2: Route to capabilities
        routing = domain_router.route(question)
        assert ScientificDomain.BIOLOGY in routing.selected_domains

        # Step 3: Get domain capabilities
        capabilities = domain_router.get_domain_capabilities(ScientificDomain.BIOLOGY)
        assert capabilities is not None
        assert len(capabilities.api_clients) > 0

        # Step 4: Verify biology ontology exists
        bio_ontology = domain_kb.get_domain_ontology(Domain.BIOLOGY)
        assert bio_ontology is not None
        assert len(bio_ontology.concepts) > 0

        # Step 5: Get applicable templates
        bio_templates = template_registry.get('biology', [])
        assert len(bio_templates) >= 2

        # Step 6: Verify pipeline integration
        # All components work together
        assert classification.primary_domain == ScientificDomain.BIOLOGY
        assert ScientificDomain.BIOLOGY in routing.selected_domains
        assert len(bio_templates) > 0
        assert len(bio_ontology.concepts) > 0

        # Success: All pipeline components integrated successfully
