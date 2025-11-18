"""
Neuroscience Domain Ontology

Provides hierarchical knowledge about neuroscience concepts:
- Brain regions and structures
- Neuron types and cell classes
- Neurotransmitters and signaling molecules
- Neurodegenerative diseases
- Cellular and synaptic processes

Example usage:
    ontology = NeuroscienceOntology()

    # Get brain region hierarchy
    cortex = ontology.get_concept('cortex')
    subregions = ontology.get_child_concepts('cortex', BiologicalRelationType.PART_OF)

    # Get disease-associated genes
    ad_genes = ontology.get_disease_genes('alzheimers_disease')

    # Find neurotransmitter receptors
    dopamine_receptors = ontology.get_related_concepts('dopamine', BiologicalRelationType.INTERACTS_WITH)
"""

from typing import Dict, List, Optional, Set, Any
from enum import Enum
from pydantic import BaseModel, Field

# Import from biology ontology for shared types
from kosmos.domains.biology.ontology import (
    BiologicalRelationType,
    BiologicalConcept,
    BiologicalRelation
)


class NeuroscienceOntology:
    """
    Ontology for neuroscience domain knowledge.

    Provides hierarchical and relational knowledge about:
    - Brain anatomy (regions, structures)
    - Cell types (neurons, glia)
    - Neurotransmitter systems
    - Neurodegenerative diseases
    - Synaptic and cellular processes
    """

    def __init__(self):
        """Initialize neuroscience ontology with core knowledge"""
        self.concepts: Dict[str, BiologicalConcept] = {}
        self.relations: List[BiologicalRelation] = []

        # Initialize core ontology
        self._initialize_brain_regions()
        self._initialize_cell_types()
        self._initialize_neurotransmitters()
        self._initialize_diseases()
        self._initialize_processes()

    def _initialize_brain_regions(self) -> None:
        """Initialize brain region hierarchy"""
        # Top-level brain
        self.add_concept(BiologicalConcept(
            id="brain",
            name="Brain",
            type="anatomical_structure",
            description="Central nervous system organ",
            external_ids={"UBERON": "0000955"}
        ))

        # Major brain regions
        regions = [
            ("cortex", "Cerebral Cortex", "Outer layer of cerebrum", {"UBERON": "0000956"}),
            ("hippocampus", "Hippocampus", "Medial temporal lobe structure", {"UBERON": "0002421"}),
            ("amygdala", "Amygdala", "Almond-shaped structure in temporal lobe", {"UBERON": "0001876"}),
            ("basal_ganglia", "Basal Ganglia", "Subcortical nuclei", {"UBERON": "0010011"}),
            ("thalamus", "Thalamus", "Relay station for sensory information", {"UBERON": "0001897"}),
            ("cerebellum", "Cerebellum", "Motor control and coordination", {"UBERON": "0002037"}),
            ("brainstem", "Brainstem", "Connection between brain and spinal cord", {"UBERON": "0002298"}),
        ]

        for region_id, name, desc, ext_ids in regions:
            self.add_concept(BiologicalConcept(
                id=region_id,
                name=name,
                type="brain_region",
                description=desc,
                external_ids=ext_ids
            ))
            self.add_relation(region_id, "brain", BiologicalRelationType.PART_OF)

        # Cortical subregions
        cortical_regions = [
            ("prefrontal_cortex", "Prefrontal Cortex", "Executive function and decision-making"),
            ("motor_cortex", "Motor Cortex", "Voluntary movement control"),
            ("visual_cortex", "Visual Cortex", "Visual processing (V1)"),
            ("temporal_cortex", "Temporal Cortex", "Auditory processing and memory"),
            ("parietal_cortex", "Parietal Cortex", "Sensory integration"),
        ]

        for region_id, name, desc in cortical_regions:
            self.add_concept(BiologicalConcept(
                id=region_id,
                name=name,
                type="cortical_region",
                description=desc
            ))
            self.add_relation(region_id, "cortex", BiologicalRelationType.PART_OF)

    def _initialize_cell_types(self) -> None:
        """Initialize neuron and glial cell types"""
        # Top-level cell types
        self.add_concept(BiologicalConcept(
            id="neuron",
            name="Neuron",
            type="cell_type",
            description="Electrically excitable nerve cell"
        ))

        self.add_concept(BiologicalConcept(
            id="glia",
            name="Glial Cell",
            type="cell_type",
            description="Non-neuronal support cells"
        ))

        # Neuron types
        neuron_types = [
            ("pyramidal_neuron", "Pyramidal Neuron", "Excitatory principal neurons in cortex and hippocampus"),
            ("interneuron", "Interneuron", "Local inhibitory neurons"),
            ("motor_neuron", "Motor Neuron", "Controls muscle contraction"),
            ("dopaminergic_neuron", "Dopaminergic Neuron", "Produces dopamine"),
            ("gabaergic_neuron", "GABAergic Neuron", "Uses GABA as neurotransmitter"),
            ("glutamatergic_neuron", "Glutamatergic Neuron", "Uses glutamate as neurotransmitter"),
        ]

        for neuron_id, name, desc in neuron_types:
            self.add_concept(BiologicalConcept(
                id=neuron_id,
                name=name,
                type="neuron_subtype",
                description=desc
            ))
            self.add_relation(neuron_id, "neuron", BiologicalRelationType.IS_A)

        # Glial cell types
        glia_types = [
            ("astrocyte", "Astrocyte", "Star-shaped glial cells, support and regulation"),
            ("microglia", "Microglia", "Immune cells of the brain"),
            ("oligodendrocyte", "Oligodendrocyte", "Myelinating cells in CNS"),
        ]

        for glia_id, name, desc in glia_types:
            self.add_concept(BiologicalConcept(
                id=glia_id,
                name=name,
                type="glial_subtype",
                description=desc
            ))
            self.add_relation(glia_id, "glia", BiologicalRelationType.IS_A)

    def _initialize_neurotransmitters(self) -> None:
        """Initialize neurotransmitter systems"""
        neurotransmitters = [
            ("dopamine", "Dopamine", "Catecholamine neurotransmitter", {"CHEBI": "18243"}),
            ("serotonin", "Serotonin", "Monoamine neurotransmitter (5-HT)", {"CHEBI": "28790"}),
            ("glutamate", "Glutamate", "Primary excitatory neurotransmitter", {"CHEBI": "14321"}),
            ("gaba", "GABA", "Primary inhibitory neurotransmitter", {"CHEBI": "16865"}),
            ("acetylcholine", "Acetylcholine", "Cholinergic neurotransmitter", {"CHEBI": "15355"}),
            ("norepinephrine", "Norepinephrine", "Catecholamine neurotransmitter", {"CHEBI": "18357"}),
        ]

        for nt_id, name, desc, ext_ids in neurotransmitters:
            self.add_concept(BiologicalConcept(
                id=nt_id,
                name=name,
                type="neurotransmitter",
                description=desc,
                external_ids=ext_ids
            ))

        # Associate neurotransmitters with neuron types
        self.add_relation("dopaminergic_neuron", "dopamine", BiologicalRelationType.ENCODES)
        self.add_relation("gabaergic_neuron", "gaba", BiologicalRelationType.ENCODES)
        self.add_relation("glutamatergic_neuron", "glutamate", BiologicalRelationType.ENCODES)

    def _initialize_diseases(self) -> None:
        """Initialize neurodegenerative diseases"""
        diseases = [
            ("alzheimers_disease", "Alzheimer's Disease", "Neurodegenerative disease with memory loss and cognitive decline", {"DOID": "10652"}),
            ("parkinsons_disease", "Parkinson's Disease", "Movement disorder with dopaminergic neuron loss", {"DOID": "14330"}),
            ("huntingtons_disease", "Huntington's Disease", "Genetic disorder affecting motor control and cognition", {"DOID": "12858"}),
            ("als", "Amyotrophic Lateral Sclerosis", "Motor neuron disease (Lou Gehrig's disease)", {"DOID": "332"}),
            ("multiple_sclerosis", "Multiple Sclerosis", "Autoimmune demyelinating disease", {"DOID": "2377"}),
        ]

        for disease_id, name, desc, ext_ids in diseases:
            self.add_concept(BiologicalConcept(
                id=disease_id,
                name=name,
                type="disease",
                description=desc,
                external_ids=ext_ids
            ))

        # Disease-region associations
        self.add_relation("alzheimers_disease", "hippocampus", BiologicalRelationType.ASSOCIATED_WITH)
        self.add_relation("alzheimers_disease", "cortex", BiologicalRelationType.ASSOCIATED_WITH)
        self.add_relation("parkinsons_disease", "basal_ganglia", BiologicalRelationType.ASSOCIATED_WITH)

        # Disease-cell type associations
        self.add_relation("parkinsons_disease", "dopaminergic_neuron", BiologicalRelationType.ASSOCIATED_WITH)
        self.add_relation("als", "motor_neuron", BiologicalRelationType.ASSOCIATED_WITH)

        # Disease-neurotransmitter associations
        self.add_relation("parkinsons_disease", "dopamine", BiologicalRelationType.ASSOCIATED_WITH)
        self.add_relation("alzheimers_disease", "acetylcholine", BiologicalRelationType.ASSOCIATED_WITH)

        # Key genes associated with diseases
        ad_genes = [
            ("APP", "Amyloid Precursor Protein", "Key protein in amyloid plaques"),
            ("APOE", "Apolipoprotein E", "Major genetic risk factor for AD"),
            ("PSEN1", "Presenilin 1", "Early-onset AD gene"),
            ("MAPT", "Microtubule-Associated Protein Tau", "Tau protein, forms neurofibrillary tangles"),
        ]

        for gene_id, name, desc in ad_genes:
            self.add_concept(BiologicalConcept(
                id=gene_id,
                name=name,
                type="gene",
                description=desc,
                external_ids={"HGNC": gene_id}
            ))
            self.add_relation(gene_id, "alzheimers_disease", BiologicalRelationType.ASSOCIATED_WITH)

    def _initialize_processes(self) -> None:
        """Initialize cellular and synaptic processes"""
        processes = [
            ("synaptic_transmission", "Synaptic Transmission", "Communication between neurons at synapses", {"GO": "0007268"}),
            ("neuroplasticity", "Neuroplasticity", "Brain's ability to reorganize and form new connections", {"GO": "0031175"}),
            ("neurogenesis", "Neurogenesis", "Formation of new neurons", {"GO": "0022008"}),
            ("myelination", "Myelination", "Formation of myelin sheath around axons", {"GO": "0042552"}),
            ("neuroinflammation", "Neuroinflammation", "Inflammatory response in nervous system", {"GO": "0150076"}),
            ("apoptosis", "Neuronal Apoptosis", "Programmed cell death in neurons", {"GO": "0051402"}),
        ]

        for process_id, name, desc, ext_ids in processes:
            self.add_concept(BiologicalConcept(
                id=process_id,
                name=name,
                type="biological_process",
                description=desc,
                external_ids=ext_ids
            ))

        # Process associations
        self.add_relation("synaptic_transmission", "neuron", BiologicalRelationType.PART_OF)
        self.add_relation("myelination", "oligodendrocyte", BiologicalRelationType.PART_OF)
        self.add_relation("neuroinflammation", "microglia", BiologicalRelationType.ASSOCIATED_WITH)
        self.add_relation("neuroinflammation", "alzheimers_disease", BiologicalRelationType.ASSOCIATED_WITH)

    def add_concept(self, concept: BiologicalConcept) -> None:
        """Add a concept to the ontology"""
        self.concepts[concept.id] = concept

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: BiologicalRelationType,
        confidence: float = 1.0,
        evidence: Optional[List[str]] = None
    ) -> None:
        """Add a relationship between concepts"""
        relation = BiologicalRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            confidence=confidence,
            evidence=evidence or []
        )
        self.relations.append(relation)

    def get_concept(self, concept_id: str) -> Optional[BiologicalConcept]:
        """Get a concept by ID"""
        return self.concepts.get(concept_id)

    def find_concepts(
        self,
        name: str,
        concept_type: Optional[str] = None,
        fuzzy: bool = True
    ) -> List[BiologicalConcept]:
        """
        Find concepts by name.

        Args:
            name: Concept name or synonym
            concept_type: Filter by type (brain_region, neuron_subtype, etc.)
            fuzzy: Allow fuzzy matching

        Returns:
            List of matching concepts
        """
        name_lower = name.lower()
        matches = []

        for concept in self.concepts.values():
            # Type filter
            if concept_type and concept.type != concept_type:
                continue

            # Name matching
            if fuzzy:
                if (name_lower in concept.name.lower() or
                    any(name_lower in syn.lower() for syn in concept.synonyms)):
                    matches.append(concept)
            else:
                if (concept.name.lower() == name_lower or
                    name_lower in [syn.lower() for syn in concept.synonyms]):
                    matches.append(concept)

        return matches

    def get_parent_concepts(
        self,
        concept_id: str,
        relation_type: BiologicalRelationType = BiologicalRelationType.IS_A
    ) -> List[BiologicalConcept]:
        """Get parent concepts (via IS_A or PART_OF relations)"""
        parents = []

        for relation in self.relations:
            if (relation.source_id == concept_id and
                relation.relation_type == relation_type):
                parent = self.get_concept(relation.target_id)
                if parent:
                    parents.append(parent)

        return parents

    def get_child_concepts(
        self,
        concept_id: str,
        relation_type: BiologicalRelationType = BiologicalRelationType.IS_A
    ) -> List[BiologicalConcept]:
        """Get child concepts (via IS_A or PART_OF relations)"""
        children = []

        for relation in self.relations:
            if (relation.target_id == concept_id and
                relation.relation_type == relation_type):
                child = self.get_concept(relation.source_id)
                if child:
                    children.append(child)

        return children

    def get_related_concepts(
        self,
        concept_id: str,
        relation_type: Optional[BiologicalRelationType] = None,
        bidirectional: bool = True
    ) -> List[BiologicalConcept]:
        """
        Get all concepts related to given concept.

        Args:
            concept_id: Source concept ID
            relation_type: Filter by relation type (None = all types)
            bidirectional: Include both outgoing and incoming relations

        Returns:
            List of related concepts
        """
        related = []

        for relation in self.relations:
            if relation_type and relation.relation_type != relation_type:
                continue

            # Outgoing relations
            if relation.source_id == concept_id:
                target = self.get_concept(relation.target_id)
                if target:
                    related.append(target)

            # Incoming relations
            elif bidirectional and relation.target_id == concept_id:
                source = self.get_concept(relation.source_id)
                if source:
                    related.append(source)

        return related

    def get_brain_regions(self) -> List[BiologicalConcept]:
        """Get all brain regions"""
        return [c for c in self.concepts.values() if c.type in ["brain_region", "cortical_region"]]

    def get_neuron_types(self) -> List[BiologicalConcept]:
        """Get all neuron types"""
        return [c for c in self.concepts.values() if c.type in ["neuron_subtype", "cell_type"] and "neuron" in c.name.lower()]

    def get_diseases(self) -> List[BiologicalConcept]:
        """Get all neurodegenerative diseases"""
        return [c for c in self.concepts.values() if c.type == "disease"]

    def get_disease_genes(self, disease_id: str) -> List[BiologicalConcept]:
        """Get genes associated with a disease"""
        genes = []

        for relation in self.relations:
            if (relation.target_id == disease_id and
                relation.relation_type == BiologicalRelationType.ASSOCIATED_WITH):
                concept = self.get_concept(relation.source_id)
                if concept and concept.type == "gene":
                    genes.append(concept)

        return genes

    def get_disease_regions(self, disease_id: str) -> List[BiologicalConcept]:
        """Get brain regions affected by a disease"""
        regions = []

        for relation in self.relations:
            if (relation.source_id == disease_id and
                relation.relation_type == BiologicalRelationType.ASSOCIATED_WITH):
                concept = self.get_concept(relation.target_id)
                if concept and concept.type in ["brain_region", "cortical_region"]:
                    regions.append(concept)

        return regions

    def get_region_hierarchy(self, root_region_id: str) -> Dict[str, Any]:
        """
        Get hierarchical structure of brain regions.

        Args:
            root_region_id: Root region to start from (e.g., "brain", "cortex")

        Returns:
            Nested dictionary representing region hierarchy
        """
        root = self.get_concept(root_region_id)
        if not root:
            return {}

        def build_hierarchy(concept_id: str) -> Dict[str, Any]:
            concept = self.get_concept(concept_id)
            if not concept:
                return {}

            # Get children (subregions)
            children = self.get_child_concepts(
                concept_id,
                BiologicalRelationType.PART_OF
            )

            hierarchy = {
                'id': concept.id,
                'name': concept.name,
                'type': concept.type,
                'children': [build_hierarchy(child.id) for child in children]
            }

            return hierarchy

        return build_hierarchy(root_region_id)
