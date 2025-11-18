"""
Unified Domain Knowledge Base

Integrates knowledge from Biology, Neuroscience, and Materials Science ontologies
into a single queryable system with cross-domain concept mapping.

Example usage:
    kb = DomainKnowledgeBase()

    # Query concepts across all domains
    results = kb.find_concepts("conductivity")  # Finds both electrical and neural conductivity

    # Cross-domain mapping
    mappings = kb.map_cross_domain_concepts("electrical_conductivity")
    # Returns: [("materials", "electrical_conductivity"), ("neuroscience", "synaptic_conductance")]

    # Get domain-specific ontology
    bio_ontology = kb.get_domain_ontology("biology")
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
from pydantic import BaseModel, Field

from kosmos.domains.biology.ontology import (
    BiologyOntology,
    BiologicalConcept,
    BiologicalRelation,
    BiologicalRelationType
)
from kosmos.domains.neuroscience.ontology import (
    NeuroscienceOntology
)
from kosmos.domains.materials.ontology import (
    MaterialsOntology,
    MaterialsConcept,
    MaterialsRelation,
    MaterialsRelationType
)


class Domain(str, Enum):
    """Scientific domains"""
    BIOLOGY = "biology"
    NEUROSCIENCE = "neuroscience"
    MATERIALS = "materials"


class CrossDomainMapping(BaseModel):
    """Mapping between concepts across different domains"""
    source_domain: Domain
    source_concept_id: str
    target_domain: Domain
    target_concept_id: str
    mapping_type: str  # "equivalent", "related", "analogous"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    rationale: Optional[str] = None


class DomainConcept(BaseModel):
    """Unified concept representation across domains"""
    domain: Domain
    concept_id: str
    name: str
    type: str
    description: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    external_ids: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DomainKnowledgeBase:
    """
    Unified knowledge base integrating Biology, Neuroscience, and Materials ontologies.

    Provides:
    - Cross-domain concept search
    - Cross-domain concept mapping
    - Domain-specific ontology access
    - Knowledge graph queries across domains
    """

    def __init__(self):
        """Initialize unified knowledge base with all domain ontologies"""
        # Load domain ontologies
        self.biology = BiologyOntology()
        self.neuroscience = NeuroscienceOntology()
        self.materials = MaterialsOntology()

        # Cross-domain mappings
        self.cross_domain_mappings: List[CrossDomainMapping] = []

        # Initialize cross-domain mappings
        self._initialize_cross_domain_mappings()

    def _initialize_cross_domain_mappings(self) -> None:
        """Initialize cross-domain concept mappings"""

        # Electrical concepts: Materials ↔ Neuroscience
        self._add_mapping(
            source_domain=Domain.MATERIALS,
            source_concept_id="electrical_conductivity",
            target_domain=Domain.NEUROSCIENCE,
            target_concept_id="neural_conductance",
            mapping_type="analogous",
            confidence=0.8,
            rationale="Both involve electrical signal propagation"
        )

        self._add_mapping(
            source_domain=Domain.MATERIALS,
            source_concept_id="band_gap",
            target_domain=Domain.NEUROSCIENCE,
            target_concept_id="action_potential_threshold",
            mapping_type="analogous",
            confidence=0.7,
            rationale="Energy barriers for activation/conduction"
        )

        # Structural concepts: Materials ↔ Biology
        self._add_mapping(
            source_domain=Domain.MATERIALS,
            source_concept_id="crystal_structure",
            target_domain=Domain.BIOLOGY,
            target_concept_id="protein_structure",
            mapping_type="analogous",
            confidence=0.6,
            rationale="Ordered structural organization at different scales"
        )

        # Network concepts: Neuroscience ↔ Biology
        self._add_mapping(
            source_domain=Domain.NEUROSCIENCE,
            source_concept_id="neural_network",
            target_domain=Domain.BIOLOGY,
            target_concept_id="metabolic_pathway",
            mapping_type="analogous",
            confidence=0.7,
            rationale="Network structures with interconnected nodes"
        )

        # Optimization concepts: All domains
        self._add_mapping(
            source_domain=Domain.MATERIALS,
            source_concept_id="optimization",
            target_domain=Domain.BIOLOGY,
            target_concept_id="metabolic_optimization",
            mapping_type="related",
            confidence=0.85,
            rationale="Parameter optimization methodologies"
        )

        # Degenerative processes: Neuroscience ↔ Materials
        self._add_mapping(
            source_domain=Domain.NEUROSCIENCE,
            source_concept_id="neurodegeneration",
            target_domain=Domain.MATERIALS,
            target_concept_id="material_degradation",
            mapping_type="analogous",
            confidence=0.6,
            rationale="Progressive structural deterioration over time"
        )

        # Signal transmission: Neuroscience ↔ Materials
        self._add_mapping(
            source_domain=Domain.NEUROSCIENCE,
            source_concept_id="synaptic_transmission",
            target_domain=Domain.MATERIALS,
            target_concept_id="carrier_transport",
            mapping_type="analogous",
            confidence=0.75,
            rationale="Information/charge carrier transmission mechanisms"
        )

    def _add_mapping(
        self,
        source_domain: Domain,
        source_concept_id: str,
        target_domain: Domain,
        target_concept_id: str,
        mapping_type: str,
        confidence: float,
        rationale: Optional[str] = None
    ) -> None:
        """Add a cross-domain mapping"""
        self.cross_domain_mappings.append(CrossDomainMapping(
            source_domain=source_domain,
            source_concept_id=source_concept_id,
            target_domain=target_domain,
            target_concept_id=target_concept_id,
            mapping_type=mapping_type,
            confidence=confidence,
            rationale=rationale
        ))

    def get_domain_ontology(self, domain: Union[str, Domain]) -> Union[BiologyOntology, NeuroscienceOntology, MaterialsOntology]:
        """Get ontology for a specific domain"""
        if isinstance(domain, str):
            domain = Domain(domain)

        ontology_map = {
            Domain.BIOLOGY: self.biology,
            Domain.NEUROSCIENCE: self.neuroscience,
            Domain.MATERIALS: self.materials
        }

        return ontology_map[domain]

    def find_concepts(self, query: str, domains: Optional[List[Domain]] = None) -> List[DomainConcept]:
        """
        Search for concepts across domains by name, ID, or synonym.

        Args:
            query: Search query (case-insensitive)
            domains: List of domains to search (default: all)

        Returns:
            List of matching concepts from all specified domains
        """
        if domains is None:
            domains = [Domain.BIOLOGY, Domain.NEUROSCIENCE, Domain.MATERIALS]

        results = []
        query_lower = query.lower()

        for domain in domains:
            ontology = self.get_domain_ontology(domain)

            # Search in domain-specific ontology
            for concept_id, concept in ontology.concepts.items():
                # Check name, ID, and synonyms
                if (query_lower in concept.name.lower() or
                    query_lower in concept_id.lower() or
                    any(query_lower in syn.lower() for syn in concept.synonyms)):

                    results.append(DomainConcept(
                        domain=domain,
                        concept_id=concept_id,
                        name=concept.name,
                        type=concept.type,
                        description=concept.description,
                        synonyms=concept.synonyms,
                        external_ids=concept.external_ids,
                        metadata=concept.metadata
                    ))

        return results

    def map_cross_domain_concepts(
        self,
        concept_id: str,
        source_domain: Optional[Domain] = None,
        min_confidence: float = 0.5
    ) -> List[CrossDomainMapping]:
        """
        Find cross-domain mappings for a concept.

        Args:
            concept_id: Concept ID to map
            source_domain: Source domain (if known)
            min_confidence: Minimum confidence threshold

        Returns:
            List of cross-domain mappings
        """
        results = []

        for mapping in self.cross_domain_mappings:
            if mapping.confidence < min_confidence:
                continue

            # Check if concept matches source
            if mapping.source_concept_id == concept_id:
                if source_domain is None or mapping.source_domain == source_domain:
                    results.append(mapping)

            # Check if concept matches target
            if mapping.target_concept_id == concept_id:
                if source_domain is None or mapping.target_domain == source_domain:
                    # Reverse the mapping
                    results.append(CrossDomainMapping(
                        source_domain=mapping.target_domain,
                        source_concept_id=mapping.target_concept_id,
                        target_domain=mapping.source_domain,
                        target_concept_id=mapping.source_concept_id,
                        mapping_type=mapping.mapping_type,
                        confidence=mapping.confidence,
                        rationale=mapping.rationale
                    ))

        return results

    def find_related_concepts(
        self,
        concept_id: str,
        source_domain: Domain,
        include_cross_domain: bool = True,
        min_confidence: float = 0.5
    ) -> Dict[str, List[DomainConcept]]:
        """
        Find all related concepts (within domain and cross-domain).

        Args:
            concept_id: Concept ID
            source_domain: Source domain
            include_cross_domain: Include cross-domain mappings
            min_confidence: Minimum confidence for cross-domain mappings

        Returns:
            Dict with keys "same_domain" and "cross_domain" containing lists of related concepts
        """
        results = {
            "same_domain": [],
            "cross_domain": []
        }

        # Same-domain relations
        ontology = self.get_domain_ontology(source_domain)

        # Get related concept IDs from ontology
        related_ids = set()
        for relation in ontology.relations:
            if relation.source_id == concept_id:
                related_ids.add(relation.target_id)
            elif relation.target_id == concept_id:
                related_ids.add(relation.source_id)

        # Convert IDs to DomainConcepts
        for related_id in related_ids:
            if related_id in ontology.concepts:
                concept = ontology.concepts[related_id]
                results["same_domain"].append(DomainConcept(
                    domain=source_domain,
                    concept_id=related_id,
                    name=concept.name,
                    type=concept.type,
                    description=concept.description,
                    synonyms=concept.synonyms,
                    external_ids=concept.external_ids,
                    metadata=concept.metadata
                ))

        # Cross-domain mappings
        if include_cross_domain:
            mappings = self.map_cross_domain_concepts(
                concept_id=concept_id,
                source_domain=source_domain,
                min_confidence=min_confidence
            )

            for mapping in mappings:
                target_ontology = self.get_domain_ontology(mapping.target_domain)
                if mapping.target_concept_id in target_ontology.concepts:
                    concept = target_ontology.concepts[mapping.target_concept_id]
                    results["cross_domain"].append(DomainConcept(
                        domain=mapping.target_domain,
                        concept_id=mapping.target_concept_id,
                        name=concept.name,
                        type=concept.type,
                        description=concept.description,
                        synonyms=concept.synonyms,
                        external_ids=concept.external_ids,
                        metadata={**concept.metadata, "mapping_type": mapping.mapping_type, "confidence": mapping.confidence}
                    ))

        return results

    def get_all_concepts(self, domain: Optional[Domain] = None) -> List[DomainConcept]:
        """
        Get all concepts from specified domain(s).

        Args:
            domain: Specific domain (default: all domains)

        Returns:
            List of all concepts
        """
        if domain is not None:
            domains = [domain]
        else:
            domains = [Domain.BIOLOGY, Domain.NEUROSCIENCE, Domain.MATERIALS]

        results = []
        for dom in domains:
            ontology = self.get_domain_ontology(dom)
            for concept_id, concept in ontology.concepts.items():
                results.append(DomainConcept(
                    domain=dom,
                    concept_id=concept_id,
                    name=concept.name,
                    type=concept.type,
                    description=concept.description,
                    synonyms=concept.synonyms,
                    external_ids=concept.external_ids,
                    metadata=concept.metadata
                ))

        return results

    def get_concept_by_id(self, concept_id: str, domain: Domain) -> Optional[DomainConcept]:
        """Get a specific concept by ID and domain"""
        ontology = self.get_domain_ontology(domain)

        if concept_id in ontology.concepts:
            concept = ontology.concepts[concept_id]
            return DomainConcept(
                domain=domain,
                concept_id=concept_id,
                name=concept.name,
                type=concept.type,
                description=concept.description,
                synonyms=concept.synonyms,
                external_ids=concept.external_ids,
                metadata=concept.metadata
            )

        return None

    def suggest_domains_for_hypothesis(self, hypothesis_text: str) -> List[Tuple[Domain, float]]:
        """
        Suggest relevant domains for a hypothesis based on concept matching.

        Args:
            hypothesis_text: Hypothesis statement

        Returns:
            List of (domain, relevance_score) tuples, sorted by relevance
        """
        hypothesis_lower = hypothesis_text.lower()
        domain_scores = {
            Domain.BIOLOGY: 0.0,
            Domain.NEUROSCIENCE: 0.0,
            Domain.MATERIALS: 0.0
        }

        # Score based on concept matches
        for domain in [Domain.BIOLOGY, Domain.NEUROSCIENCE, Domain.MATERIALS]:
            ontology = self.get_domain_ontology(domain)

            for concept_id, concept in ontology.concepts.items():
                # Check if concept name or synonyms appear in hypothesis
                if concept.name.lower() in hypothesis_lower:
                    domain_scores[domain] += 1.0

                for synonym in concept.synonyms:
                    if synonym.lower() in hypothesis_lower:
                        domain_scores[domain] += 0.8

        # Normalize scores
        max_score = max(domain_scores.values()) if max(domain_scores.values()) > 0 else 1.0
        domain_scores = {k: v / max_score for k, v in domain_scores.items()}

        # Sort by score
        results = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)

        return results
