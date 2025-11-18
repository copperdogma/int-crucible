"""
Biology Domain Ontology

Provides hierarchical knowledge about biology concepts:
- Metabolic pathways and compounds
- Genes, proteins, and variants
- Biological processes and functions
- Disease associations

Example usage:
    ontology = BiologyOntology()

    # Get pathway hierarchy
    pathways = ontology.get_metabolic_pathways()

    # Get parent pathway
    parent = ontology.get_parent_pathway('purine_salvage')

    # Get all genes in a pathway
    genes = ontology.get_pathway_genes('glycolysis')

    # Find related concepts
    related = ontology.find_related_concepts('diabetes', relation_type='associated_gene')
"""

from typing import Dict, List, Optional, Set, Any
from enum import Enum
from pydantic import BaseModel, Field


class BiologicalRelationType(str, Enum):
    """Types of relationships between biological concepts"""
    IS_A = "is_a"  # Parent-child hierarchy
    PART_OF = "part_of"  # Component relationship
    REGULATES = "regulates"  # Regulatory relationship
    INTERACTS_WITH = "interacts_with"  # Physical interaction
    ASSOCIATED_WITH = "associated_with"  # Statistical/clinical association
    PRECURSOR_OF = "precursor_of"  # Metabolic transformation
    PRODUCT_OF = "product_of"  # Metabolic product
    ENCODES = "encodes"  # Gene-protein relationship
    EXPRESSED_IN = "expressed_in"  # Gene-tissue relationship


class BiologicalConcept(BaseModel):
    """A concept in the biology ontology"""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Human-readable name")
    type: str = Field(..., description="Concept type (pathway, gene, metabolite, etc.)")
    description: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    external_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="External database IDs (KEGG, GO, UniProt, etc.)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BiologicalRelation(BaseModel):
    """A relationship between two biological concepts"""
    source_id: str
    target_id: str
    relation_type: BiologicalRelationType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class BiologyOntology:
    """
    Ontology for biology domain knowledge.

    Provides hierarchical and relational knowledge about:
    - Metabolic pathways (purine/pyrimidine metabolism, glycolysis, etc.)
    - Genes and proteins
    - Genetic variants
    - Diseases and phenotypes
    """

    def __init__(self):
        """Initialize biology ontology with core knowledge"""
        self.concepts: Dict[str, BiologicalConcept] = {}
        self.relations: List[BiologicalRelation] = []

        # Initialize core ontology
        self._initialize_metabolic_pathways()
        self._initialize_genetic_concepts()
        self._initialize_disease_concepts()

    def _initialize_metabolic_pathways(self) -> None:
        """Initialize metabolic pathway ontology"""
        # Top-level pathways
        self.add_concept(BiologicalConcept(
            id="nucleotide_metabolism",
            name="Nucleotide Metabolism",
            type="pathway",
            description="Biosynthesis and degradation of nucleotides",
            external_ids={"KEGG": "map00230"}
        ))

        # Purine metabolism
        self.add_concept(BiologicalConcept(
            id="purine_metabolism",
            name="Purine Metabolism",
            type="pathway",
            description="Synthesis and degradation of purine nucleotides",
            external_ids={"KEGG": "map00230", "GO": "GO:0006163"}
        ))
        self.add_relation("purine_metabolism", "nucleotide_metabolism", BiologicalRelationType.IS_A)

        self.add_concept(BiologicalConcept(
            id="purine_salvage",
            name="Purine Salvage Pathway",
            type="pathway",
            description="Recycling of purine bases from degradation",
            synonyms=["salvage pathway"]
        ))
        self.add_relation("purine_salvage", "purine_metabolism", BiologicalRelationType.PART_OF)

        self.add_concept(BiologicalConcept(
            id="purine_de_novo_synthesis",
            name="Purine De Novo Synthesis",
            type="pathway",
            description="Synthesis of purines from simple precursors",
            synonyms=["de novo purine biosynthesis"]
        ))
        self.add_relation("purine_de_novo_synthesis", "purine_metabolism", BiologicalRelationType.PART_OF)

        # Pyrimidine metabolism
        self.add_concept(BiologicalConcept(
            id="pyrimidine_metabolism",
            name="Pyrimidine Metabolism",
            type="pathway",
            description="Synthesis and degradation of pyrimidine nucleotides",
            external_ids={"KEGG": "map00240", "GO": "GO:0006220"}
        ))
        self.add_relation("pyrimidine_metabolism", "nucleotide_metabolism", BiologicalRelationType.IS_A)

        self.add_concept(BiologicalConcept(
            id="pyrimidine_salvage",
            name="Pyrimidine Salvage Pathway",
            type="pathway",
            description="Recycling of pyrimidine bases from degradation"
        ))
        self.add_relation("pyrimidine_salvage", "pyrimidine_metabolism", BiologicalRelationType.PART_OF)

        self.add_concept(BiologicalConcept(
            id="pyrimidine_de_novo_synthesis",
            name="Pyrimidine De Novo Synthesis",
            type="pathway",
            description="Synthesis of pyrimidines from simple precursors",
            synonyms=["de novo pyrimidine biosynthesis"]
        ))
        self.add_relation("pyrimidine_de_novo_synthesis", "pyrimidine_metabolism", BiologicalRelationType.PART_OF)

        # Key metabolites
        metabolites = [
            ("adenosine", "Adenosine", "metabolite", "Purine nucleoside", ["purine_salvage"]),
            ("amp", "Adenosine Monophosphate", "metabolite", "Purine nucleotide", ["purine_de_novo_synthesis"]),
            ("guanosine", "Guanosine", "metabolite", "Purine nucleoside", ["purine_salvage"]),
            ("gmp", "Guanosine Monophosphate", "metabolite", "Purine nucleotide", ["purine_de_novo_synthesis"]),
            ("cytidine", "Cytidine", "metabolite", "Pyrimidine nucleoside", ["pyrimidine_salvage"]),
            ("cmp", "Cytidine Monophosphate", "metabolite", "Pyrimidine nucleotide", ["pyrimidine_de_novo_synthesis"]),
        ]

        for met_id, name, mtype, desc, pathways in metabolites:
            self.add_concept(BiologicalConcept(
                id=met_id,
                name=name,
                type=mtype,
                description=desc
            ))
            for pathway_id in pathways:
                self.add_relation(met_id, pathway_id, BiologicalRelationType.PART_OF)

    def _initialize_genetic_concepts(self) -> None:
        """Initialize gene and variant ontology"""
        # Example genes from kosmos-figures
        genes = [
            ("TCF7L2", "Transcription Factor 7 Like 2", "Type 2 diabetes susceptibility gene"),
            ("SSR1", "Signal Sequence Receptor Subunit 1", "Type 2 diabetes protective gene"),
            ("SOD2", "Superoxide Dismutase 2", "Antioxidant enzyme, mitochondrial"),
        ]

        for gene_id, name, desc in genes:
            self.add_concept(BiologicalConcept(
                id=gene_id,
                name=name,
                type="gene",
                description=desc,
                external_ids={"HGNC": gene_id}
            ))

    def _initialize_disease_concepts(self) -> None:
        """Initialize disease ontology"""
        diseases = [
            ("type_2_diabetes", "Type 2 Diabetes Mellitus", "Metabolic disorder characterized by insulin resistance"),
            ("cardiovascular_disease", "Cardiovascular Disease", "Diseases affecting the heart and blood vessels"),
        ]

        for disease_id, name, desc in diseases:
            self.add_concept(BiologicalConcept(
                id=disease_id,
                name=name,
                type="disease",
                description=desc
            ))

        # Add gene-disease associations
        self.add_relation("TCF7L2", "type_2_diabetes", BiologicalRelationType.ASSOCIATED_WITH)
        self.add_relation("SSR1", "type_2_diabetes", BiologicalRelationType.ASSOCIATED_WITH)
        self.add_relation("SOD2", "cardiovascular_disease", BiologicalRelationType.ASSOCIATED_WITH)

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
            concept_type: Filter by type (pathway, gene, metabolite, etc.)
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
                # Fuzzy match: substring in name or synonyms
                if (name_lower in concept.name.lower() or
                    any(name_lower in syn.lower() for syn in concept.synonyms)):
                    matches.append(concept)
            else:
                # Exact match
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

            # Incoming relations (if bidirectional)
            elif bidirectional and relation.target_id == concept_id:
                source = self.get_concept(relation.source_id)
                if source:
                    related.append(source)

        return related

    def get_pathway_hierarchy(self, root_pathway_id: str) -> Dict[str, Any]:
        """
        Get hierarchical structure of a pathway and its sub-pathways.

        Args:
            root_pathway_id: Root pathway to start from

        Returns:
            Nested dictionary representing pathway hierarchy
        """
        root = self.get_concept(root_pathway_id)
        if not root:
            return {}

        def build_hierarchy(concept_id: str) -> Dict[str, Any]:
            concept = self.get_concept(concept_id)
            if not concept:
                return {}

            # Get children
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

        return build_hierarchy(root_pathway_id)

    def get_metabolic_pathways(self) -> List[BiologicalConcept]:
        """Get all metabolic pathways"""
        return [c for c in self.concepts.values() if c.type == "pathway"]

    def get_pathway_genes(self, pathway_id: str) -> List[BiologicalConcept]:
        """Get all genes associated with a pathway"""
        genes = []

        for relation in self.relations:
            if relation.target_id == pathway_id:
                concept = self.get_concept(relation.source_id)
                if concept and concept.type == "gene":
                    genes.append(concept)

        return genes

    def get_pathway_metabolites(self, pathway_id: str) -> List[BiologicalConcept]:
        """Get all metabolites in a pathway"""
        metabolites = []

        for relation in self.relations:
            if (relation.target_id == pathway_id and
                relation.relation_type == BiologicalRelationType.PART_OF):
                concept = self.get_concept(relation.source_id)
                if concept and concept.type == "metabolite":
                    metabolites.append(concept)

        return metabolites

    def get_gene_diseases(self, gene_id: str) -> List[BiologicalConcept]:
        """Get all diseases associated with a gene"""
        diseases = []

        for relation in self.relations:
            if (relation.source_id == gene_id and
                relation.relation_type == BiologicalRelationType.ASSOCIATED_WITH):
                concept = self.get_concept(relation.target_id)
                if concept and concept.type == "disease":
                    diseases.append(concept)

        return diseases
