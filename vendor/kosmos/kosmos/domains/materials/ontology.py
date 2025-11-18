"""
Materials Science Domain Ontology

Provides hierarchical knowledge about materials science concepts:
- Crystal structures and symmetries
- Material properties (electrical, mechanical, optical, thermal)
- Elements and composition
- Processing methods and fabrication techniques
- Materials classes (ceramics, metals, polymers, semiconductors)

Example usage:
    ontology = MaterialsOntology()

    # Get crystal structures
    structures = ontology.get_crystal_structures()

    # Get material properties
    props = ontology.get_material_properties('electrical')

    # Find materials with specific property
    conductors = ontology.find_materials_by_property('electrical_conductivity', threshold='high')

    # Get processing methods
    methods = ontology.get_processing_methods()
"""

from typing import Dict, List, Optional, Set, Any
from enum import Enum
from pydantic import BaseModel, Field


class MaterialsRelationType(str, Enum):
    """Types of relationships between materials concepts"""
    IS_A = "is_a"  # Parent-child hierarchy
    PART_OF = "part_of"  # Component relationship
    HAS_STRUCTURE = "has_structure"  # Material-structure relationship
    HAS_PROPERTY = "has_property"  # Material-property relationship
    PROCESSED_BY = "processed_by"  # Material-processing relationship
    COMPOSED_OF = "composed_of"  # Composition relationship
    TRANSFORMS_TO = "transforms_to"  # Phase transformation
    DOPED_WITH = "doped_with"  # Doping relationship
    INTERACTS_WITH = "interacts_with"  # Material interaction


class MaterialsConcept(BaseModel):
    """A concept in the materials science ontology"""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Human-readable name")
    type: str = Field(..., description="Concept type (structure, property, material, etc.)")
    description: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    external_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="External database IDs (Materials Project, AFLOW, etc.)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MaterialsRelation(BaseModel):
    """A relationship between two materials concepts"""
    source_id: str
    target_id: str
    relation_type: MaterialsRelationType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class MaterialsOntology:
    """
    Ontology for materials science domain knowledge.

    Provides hierarchical and relational knowledge about:
    - Crystal structures (FCC, BCC, HCP, perovskite, etc.)
    - Material properties (conductivity, bandgap, hardness, etc.)
    - Elements and compositions
    - Processing methods (annealing, doping, CVD, etc.)
    - Materials classes (metals, ceramics, semiconductors, etc.)
    """

    def __init__(self):
        """Initialize materials ontology with core knowledge"""
        self.concepts: Dict[str, MaterialsConcept] = {}
        self.relations: List[MaterialsRelation] = []

        # Initialize core ontology
        self._initialize_crystal_structures()
        self._initialize_material_properties()
        self._initialize_materials_classes()
        self._initialize_processing_methods()
        self._initialize_common_materials()

    def add_concept(self, concept: MaterialsConcept) -> None:
        """Add a concept to the ontology"""
        self.concepts[concept.id] = concept

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: MaterialsRelationType,
        confidence: float = 1.0,
        evidence: Optional[List[str]] = None
    ) -> None:
        """Add a relationship between concepts"""
        self.relations.append(MaterialsRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            confidence=confidence,
            evidence=evidence or []
        ))

    def _initialize_crystal_structures(self) -> None:
        """Initialize crystal structure hierarchy"""
        # Top-level crystal systems
        self.add_concept(MaterialsConcept(
            id="crystal_structure",
            name="Crystal Structure",
            type="structure_category",
            description="Periodic arrangement of atoms in crystalline materials"
        ))

        # Cubic structures
        structures = [
            ("fcc", "Face-Centered Cubic", "Close-packed cubic structure, CN=12"),
            ("bcc", "Body-Centered Cubic", "Cubic structure with center atom, CN=8"),
            ("simple_cubic", "Simple Cubic", "Basic cubic structure, CN=6"),
        ]

        for struct_id, name, desc in structures:
            self.add_concept(MaterialsConcept(
                id=struct_id,
                name=name,
                type="crystal_structure",
                description=desc
            ))
            self.add_relation(struct_id, "crystal_structure", MaterialsRelationType.IS_A)

        # Hexagonal structures
        self.add_concept(MaterialsConcept(
            id="hcp",
            name="Hexagonal Close-Packed",
            type="crystal_structure",
            description="Close-packed hexagonal structure, CN=12"
        ))
        self.add_relation("hcp", "crystal_structure", MaterialsRelationType.IS_A)

        # Complex structures
        self.add_concept(MaterialsConcept(
            id="perovskite",
            name="Perovskite Structure",
            type="crystal_structure",
            description="ABX3 structure, important for solar cells and catalysts",
            synonyms=["ABX3"]
        ))
        self.add_relation("perovskite", "crystal_structure", MaterialsRelationType.IS_A)

        # Diamond structure
        self.add_concept(MaterialsConcept(
            id="diamond",
            name="Diamond Structure",
            type="crystal_structure",
            description="Cubic structure with tetrahedral coordination, CN=4",
            synonyms=["diamond_cubic"]
        ))
        self.add_relation("diamond", "crystal_structure", MaterialsRelationType.IS_A)

        # Wurtzite
        self.add_concept(MaterialsConcept(
            id="wurtzite",
            name="Wurtzite Structure",
            type="crystal_structure",
            description="Hexagonal structure common in semiconductors"
        ))
        self.add_relation("wurtzite", "crystal_structure", MaterialsRelationType.IS_A)

    def _initialize_material_properties(self) -> None:
        """Initialize material properties hierarchy"""
        # Top-level properties
        property_categories = [
            ("electrical", "Electrical Properties", "Electronic transport and conductivity"),
            ("mechanical", "Mechanical Properties", "Strength, hardness, elasticity"),
            ("optical", "Optical Properties", "Light absorption, transmission, reflection"),
            ("thermal", "Thermal Properties", "Heat capacity, conductivity, expansion"),
            ("magnetic", "Magnetic Properties", "Magnetization and magnetic ordering"),
        ]

        for prop_id, name, desc in property_categories:
            self.add_concept(MaterialsConcept(
                id=f"{prop_id}_properties",
                name=name,
                type="property_category",
                description=desc
            ))

        # Electrical properties
        electrical_props = [
            ("band_gap", "Band Gap", "Energy gap between valence and conduction bands (eV)"),
            ("electrical_conductivity", "Electrical Conductivity", "Ability to conduct electricity (S/m)"),
            ("carrier_mobility", "Carrier Mobility", "Electron/hole mobility (cm²/Vs)"),
            ("dielectric_constant", "Dielectric Constant", "Relative permittivity"),
        ]

        for prop_id, name, desc in electrical_props:
            self.add_concept(MaterialsConcept(
                id=prop_id,
                name=name,
                type="property",
                description=desc
            ))
            self.add_relation(prop_id, "electrical_properties", MaterialsRelationType.PART_OF)

        # Mechanical properties
        mechanical_props = [
            ("youngs_modulus", "Young's Modulus", "Elastic modulus (GPa)"),
            ("hardness", "Hardness", "Resistance to deformation"),
            ("fracture_toughness", "Fracture Toughness", "Resistance to crack propagation"),
            ("tensile_strength", "Tensile Strength", "Maximum stress before failure (MPa)"),
        ]

        for prop_id, name, desc in mechanical_props:
            self.add_concept(MaterialsConcept(
                id=prop_id,
                name=name,
                type="property",
                description=desc
            ))
            self.add_relation(prop_id, "mechanical_properties", MaterialsRelationType.PART_OF)

        # Optical properties
        optical_props = [
            ("refractive_index", "Refractive Index", "Light bending in material"),
            ("absorption_coefficient", "Absorption Coefficient", "Light absorption rate"),
            ("transmittance", "Transmittance", "Fraction of light transmitted"),
        ]

        for prop_id, name, desc in optical_props:
            self.add_concept(MaterialsConcept(
                id=prop_id,
                name=name,
                type="property",
                description=desc
            ))
            self.add_relation(prop_id, "optical_properties", MaterialsRelationType.PART_OF)

        # Thermal properties
        thermal_props = [
            ("thermal_conductivity", "Thermal Conductivity", "Heat conduction (W/m·K)"),
            ("melting_point", "Melting Point", "Solid-liquid phase transition temperature (K)"),
            ("thermal_expansion", "Thermal Expansion Coefficient", "Size change with temperature (K⁻¹)"),
        ]

        for prop_id, name, desc in thermal_props:
            self.add_concept(MaterialsConcept(
                id=prop_id,
                name=name,
                type="property",
                description=desc
            ))
            self.add_relation(prop_id, "thermal_properties", MaterialsRelationType.PART_OF)

    def _initialize_materials_classes(self) -> None:
        """Initialize materials classification hierarchy"""
        # Top-level materials classes
        materials_classes = [
            ("metal", "Metals", "Metallic elements and alloys"),
            ("ceramic", "Ceramics", "Inorganic non-metallic materials"),
            ("polymer", "Polymers", "Organic macromolecules"),
            ("semiconductor", "Semiconductors", "Materials with intermediate conductivity"),
            ("composite", "Composites", "Multi-component materials"),
        ]

        for class_id, name, desc in materials_classes:
            self.add_concept(MaterialsConcept(
                id=class_id,
                name=name,
                type="material_class",
                description=desc
            ))

        # Semiconductor subclasses
        semiconductor_types = [
            ("elemental_semiconductor", "Elemental Semiconductors", "Si, Ge, etc."),
            ("compound_semiconductor", "Compound Semiconductors", "GaAs, InP, GaN, etc."),
            ("organic_semiconductor", "Organic Semiconductors", "Conductive polymers and molecules"),
        ]

        for semi_id, name, desc in semiconductor_types:
            self.add_concept(MaterialsConcept(
                id=semi_id,
                name=name,
                type="material_subclass",
                description=desc
            ))
            self.add_relation(semi_id, "semiconductor", MaterialsRelationType.IS_A)

    def _initialize_processing_methods(self) -> None:
        """Initialize materials processing methods"""
        # Processing methods
        processing_methods = [
            ("annealing", "Annealing", "Heat treatment to reduce defects and stress"),
            ("doping", "Doping", "Intentional introduction of impurities"),
            ("cvd", "Chemical Vapor Deposition", "Thin film deposition from gas phase"),
            ("pvd", "Physical Vapor Deposition", "Thin film deposition by physical means"),
            ("sintering", "Sintering", "Densification by heating below melting point"),
            ("sputtering", "Sputtering", "Physical vapor deposition by ion bombardment"),
            ("mbe", "Molecular Beam Epitaxy", "Atomic-layer precision crystal growth"),
            ("sol_gel", "Sol-Gel Processing", "Wet chemistry synthesis route"),
        ]

        for proc_id, name, desc in processing_methods:
            self.add_concept(MaterialsConcept(
                id=proc_id,
                name=name,
                type="processing_method",
                description=desc
            ))

    def _initialize_common_materials(self) -> None:
        """Initialize common materials with their properties"""
        # Silicon
        self.add_concept(MaterialsConcept(
            id="silicon",
            name="Silicon",
            type="material",
            description="Elemental semiconductor, basis of electronics industry",
            synonyms=["Si"],
            external_ids={"Materials_Project": "mp-149"}
        ))
        self.add_relation("silicon", "elemental_semiconductor", MaterialsRelationType.IS_A)
        self.add_relation("silicon", "diamond", MaterialsRelationType.HAS_STRUCTURE)

        # Gallium Arsenide
        self.add_concept(MaterialsConcept(
            id="gaas",
            name="Gallium Arsenide",
            type="material",
            description="III-V compound semiconductor for optoelectronics",
            synonyms=["GaAs"],
            external_ids={"Materials_Project": "mp-2534"}
        ))
        self.add_relation("gaas", "compound_semiconductor", MaterialsRelationType.IS_A)

        # Perovskite solar cell materials
        self.add_concept(MaterialsConcept(
            id="mapi",
            name="Methylammonium Lead Iodide",
            type="material",
            description="Hybrid perovskite for solar cells",
            synonyms=["MAPbI3", "CH3NH3PbI3"],
            metadata={"applications": ["solar_cells", "LEDs"]}
        ))
        self.add_relation("mapi", "perovskite", MaterialsRelationType.HAS_STRUCTURE)

        # Titanium Dioxide
        self.add_concept(MaterialsConcept(
            id="tio2",
            name="Titanium Dioxide",
            type="material",
            description="Oxide semiconductor, photocatalyst",
            synonyms=["TiO2", "titania"],
            external_ids={"Materials_Project": "mp-2657"}
        ))
        self.add_concept(MaterialsConcept(
            id="steel",
            name="Steel",
            type="material",
            description="Iron-carbon alloy",
            synonyms=["Fe-C alloy"]
        ))
        self.add_relation("steel", "metal", MaterialsRelationType.IS_A)

    # Query methods

    def get_crystal_structures(self) -> List[MaterialsConcept]:
        """Get all crystal structures"""
        return [
            concept for concept in self.concepts.values()
            if concept.type == "crystal_structure"
        ]

    def get_material_properties(self, category: Optional[str] = None) -> List[MaterialsConcept]:
        """
        Get material properties, optionally filtered by category.

        Args:
            category: Property category ("electrical", "mechanical", "optical", "thermal", "magnetic")

        Returns:
            List of property concepts
        """
        if category:
            # Get properties in specific category
            category_id = f"{category}_properties"
            property_ids = set()

            for relation in self.relations:
                if (relation.target_id == category_id and
                    relation.relation_type == MaterialsRelationType.PART_OF):
                    property_ids.add(relation.source_id)

            return [self.concepts[pid] for pid in property_ids if pid in self.concepts]
        else:
            # Get all properties
            return [
                concept for concept in self.concepts.values()
                if concept.type == "property"
            ]

    def get_processing_methods(self) -> List[MaterialsConcept]:
        """Get all processing methods"""
        return [
            concept for concept in self.concepts.values()
            if concept.type == "processing_method"
        ]

    def get_materials_by_class(self, material_class: str) -> List[MaterialsConcept]:
        """Get materials belonging to a specific class"""
        # Find materials that are instances of the class
        material_ids = set()

        for relation in self.relations:
            if (relation.target_id == material_class and
                relation.relation_type == MaterialsRelationType.IS_A and
                relation.source_id in self.concepts and
                self.concepts[relation.source_id].type == "material"):
                material_ids.add(relation.source_id)

        return [self.concepts[mid] for mid in material_ids]

    def find_concept(self, query: str) -> Optional[MaterialsConcept]:
        """Find a concept by ID or name (case-insensitive)"""
        query_lower = query.lower()

        # Try exact ID match first
        if query in self.concepts:
            return self.concepts[query]

        # Try name and synonym matching
        for concept in self.concepts.values():
            if (concept.name.lower() == query_lower or
                query_lower in [s.lower() for s in concept.synonyms]):
                return concept

        return None

    def get_related_concepts(
        self,
        concept_id: str,
        relation_type: Optional[MaterialsRelationType] = None
    ) -> List[MaterialsConcept]:
        """Get concepts related to a given concept"""
        related_ids = set()

        for relation in self.relations:
            if relation.source_id == concept_id:
                if relation_type is None or relation.relation_type == relation_type:
                    related_ids.add(relation.target_id)
            elif relation.target_id == concept_id:
                if relation_type is None or relation.relation_type == relation_type:
                    related_ids.add(relation.source_id)

        return [self.concepts[rid] for rid in related_ids if rid in self.concepts]
