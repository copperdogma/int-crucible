"""
Unit tests for MaterialsOntology (Phase 9).

Tests materials science ontology:
- Crystal structures (FCC, BCC, HCP, perovskite, diamond, wurtzite)
- Material properties (electrical, mechanical, optical, thermal, magnetic)
- Materials classes (metals, ceramics, semiconductors, polymers, composites)
- Processing methods (CVD, annealing, doping, sintering)

Coverage target: 25 tests across 5 test classes
"""

import pytest
from kosmos.domains.materials.ontology import (
    MaterialsOntology,
    MaterialsConcept,
    MaterialsRelation,
    MaterialsRelationType
)


@pytest.fixture
def materials_ontology():
    """Fixture providing a MaterialsOntology instance"""
    return MaterialsOntology()


@pytest.mark.unit
class TestMaterialsOntologyInit:
    """Test MaterialsOntology initialization"""

    def test_initialization_creates_concepts(self, materials_ontology):
        """Test that initialization creates all core concepts"""
        assert len(materials_ontology.concepts) > 40
        assert "crystal_structure" in materials_ontology.concepts
        assert "fcc" in materials_ontology.concepts
        assert "silicon" in materials_ontology.concepts

    def test_concept_count_validation(self, materials_ontology):
        """Test expected number of concepts in each category"""
        # Crystal structures
        crystal_structures = [c for c in materials_ontology.concepts.values()
                             if c.type == "crystal_structure"]
        assert len(crystal_structures) >= 7  # FCC, BCC, HCP, perovskite, diamond, wurtzite, simple_cubic

        # Material properties
        properties = [c for c in materials_ontology.concepts.values()
                     if c.type == "property"]
        assert len(properties) >= 14  # Electrical(4) + Mechanical(4) + Optical(3) + Thermal(3)

        # Processing methods
        processing = [c for c in materials_ontology.concepts.values()
                     if c.type == "processing_method"]
        assert len(processing) >= 8  # annealing, doping, CVD, PVD, sintering, sputtering, MBE, sol-gel

    def test_relations_created(self, materials_ontology):
        """Test that relationships are properly established"""
        assert len(materials_ontology.relations) >= 29
        # Check some specific relations exist
        relation_types = [r.relation_type for r in materials_ontology.relations]
        assert MaterialsRelationType.IS_A in relation_types
        assert MaterialsRelationType.PART_OF in relation_types

    def test_hierarchical_structure(self, materials_ontology):
        """Test hierarchical parent-child relationships"""
        # FCC should be child of crystal_structure
        fcc_relations = [r for r in materials_ontology.relations
                        if r.source_id == "fcc" and r.relation_type == MaterialsRelationType.IS_A]
        assert len(fcc_relations) > 0
        assert fcc_relations[0].target_id == "crystal_structure"


@pytest.mark.unit
class TestCrystalStructures:
    """Test crystal structure concepts"""

    def test_structure_types_fcc_bcc_hcp(self, materials_ontology):
        """Test cubic and hexagonal structure types"""
        # FCC
        fcc = materials_ontology.concepts["fcc"]
        assert fcc.name == "Face-Centered Cubic"
        assert fcc.type == "crystal_structure"

        # BCC
        bcc = materials_ontology.concepts["bcc"]
        assert bcc.name == "Body-Centered Cubic"
        assert bcc.type == "crystal_structure"

        # HCP
        hcp = materials_ontology.concepts["hcp"]
        assert hcp.name == "Hexagonal Close-Packed"
        assert hcp.type == "crystal_structure"

    def test_perovskite_structure(self, materials_ontology):
        """Test perovskite structure"""
        perovskite = materials_ontology.concepts["perovskite"]
        assert perovskite.name == "Perovskite Structure"
        assert perovskite.type == "crystal_structure"
        assert "ABX3" in perovskite.synonyms

    def test_lattice_parameters(self, materials_ontology):
        """Test structure descriptions contain lattice info"""
        fcc = materials_ontology.concepts["fcc"]
        assert "CN=12" in fcc.description  # Coordination number

        bcc = materials_ontology.concepts["bcc"]
        assert "CN=8" in bcc.description

    def test_structure_hierarchy(self, materials_ontology):
        """Test all structures are children of crystal_structure"""
        structure_ids = ["fcc", "bcc", "hcp", "perovskite", "diamond", "wurtzite"]

        for struct_id in structure_ids:
            # Find IS_A relation to crystal_structure
            relations = [r for r in materials_ontology.relations
                        if r.source_id == struct_id and r.relation_type == MaterialsRelationType.IS_A]
            assert len(relations) > 0
            assert any(r.target_id == "crystal_structure" for r in relations)

    def test_symmetry_groups(self, materials_ontology):
        """Test crystal structures have proper classification"""
        # Cubic structures
        cubic_structs = ["fcc", "bcc", "simple_cubic"]
        for struct_id in cubic_structs:
            assert struct_id in materials_ontology.concepts
            concept = materials_ontology.concepts[struct_id]
            assert "cubic" in concept.name.lower() or "Cubic" in concept.name

    def test_structure_relations(self, materials_ontology):
        """Test materials have structure relationships"""
        # Silicon should have diamond structure
        silicon_relations = [r for r in materials_ontology.relations
                            if r.source_id == "silicon" and
                            r.relation_type == MaterialsRelationType.HAS_STRUCTURE]
        assert len(silicon_relations) > 0
        assert silicon_relations[0].target_id == "diamond"


@pytest.mark.unit
class TestMaterialProperties:
    """Test material properties"""

    def test_electrical_properties(self, materials_ontology):
        """Test electrical property concepts"""
        electrical_props = materials_ontology.get_material_properties("electrical")

        assert len(electrical_props) >= 4
        prop_ids = [p.id for p in electrical_props]

        # Expected electrical properties
        assert "band_gap" in prop_ids
        assert "electrical_conductivity" in prop_ids
        assert "carrier_mobility" in prop_ids
        assert "dielectric_constant" in prop_ids

    def test_mechanical_properties(self, materials_ontology):
        """Test mechanical property concepts"""
        mechanical_props = materials_ontology.get_material_properties("mechanical")

        assert len(mechanical_props) >= 4
        prop_ids = [p.id for p in mechanical_props]

        assert "youngs_modulus" in prop_ids
        assert "hardness" in prop_ids
        assert "fracture_toughness" in prop_ids
        assert "tensile_strength" in prop_ids

    def test_thermal_properties(self, materials_ontology):
        """Test thermal property concepts"""
        thermal_props = materials_ontology.get_material_properties("thermal")

        assert len(thermal_props) >= 3
        prop_ids = [p.id for p in thermal_props]

        assert "thermal_conductivity" in prop_ids
        assert "melting_point" in prop_ids
        assert "thermal_expansion" in prop_ids

    def test_optical_properties(self, materials_ontology):
        """Test optical property concepts"""
        optical_props = materials_ontology.get_material_properties("optical")

        assert len(optical_props) >= 3
        prop_ids = [p.id for p in optical_props]

        assert "refractive_index" in prop_ids
        assert "absorption_coefficient" in prop_ids
        assert "transmittance" in prop_ids

    def test_property_relationships(self, materials_ontology):
        """Test properties are linked to categories"""
        # Band gap should be PART_OF electrical_properties
        band_gap_relations = [r for r in materials_ontology.relations
                             if r.source_id == "band_gap" and
                             r.relation_type == MaterialsRelationType.PART_OF]
        assert len(band_gap_relations) > 0
        assert band_gap_relations[0].target_id == "electrical_properties"

        # Young's modulus should be PART_OF mechanical_properties
        youngs_relations = [r for r in materials_ontology.relations
                           if r.source_id == "youngs_modulus" and
                           r.relation_type == MaterialsRelationType.PART_OF]
        assert len(youngs_relations) > 0
        assert youngs_relations[0].target_id == "mechanical_properties"

    def test_property_units(self, materials_ontology):
        """Test properties have unit information in descriptions"""
        # Band gap - eV
        band_gap = materials_ontology.concepts["band_gap"]
        assert "eV" in band_gap.description

        # Thermal conductivity - W/m·K
        thermal_cond = materials_ontology.concepts["thermal_conductivity"]
        assert "W/m" in thermal_cond.description

        # Young's modulus - GPa
        youngs = materials_ontology.concepts["youngs_modulus"]
        assert "GPa" in youngs.description


@pytest.mark.unit
class TestMaterialsClasses:
    """Test materials classification"""

    def test_metals_classification(self, materials_ontology):
        """Test metals classification"""
        assert "metal" in materials_ontology.concepts
        metal = materials_ontology.concepts["metal"]
        assert metal.type == "material_class"
        assert metal.name == "Metals"

        # Steel should be classified as metal
        steel_materials = materials_ontology.get_materials_by_class("metal")
        steel_ids = [m.id for m in steel_materials]
        assert "steel" in steel_ids

    def test_ceramics_classification(self, materials_ontology):
        """Test ceramics classification"""
        assert "ceramic" in materials_ontology.concepts
        ceramic = materials_ontology.concepts["ceramic"]
        assert ceramic.type == "material_class"
        assert ceramic.name == "Ceramics"

    def test_semiconductors_classification(self, materials_ontology):
        """Test semiconductor classification and subclasses"""
        assert "semiconductor" in materials_ontology.concepts
        semiconductor = materials_ontology.concepts["semiconductor"]
        assert semiconductor.type == "material_class"

        # Check semiconductor subclasses exist
        assert "elemental_semiconductor" in materials_ontology.concepts
        assert "compound_semiconductor" in materials_ontology.concepts
        assert "organic_semiconductor" in materials_ontology.concepts

        # Subclasses should be IS_A semiconductor
        elemental_relations = [r for r in materials_ontology.relations
                              if r.source_id == "elemental_semiconductor" and
                              r.relation_type == MaterialsRelationType.IS_A]
        assert len(elemental_relations) > 0
        assert elemental_relations[0].target_id == "semiconductor"

    def test_polymers_classification(self, materials_ontology):
        """Test polymers classification"""
        assert "polymer" in materials_ontology.concepts
        polymer = materials_ontology.concepts["polymer"]
        assert polymer.type == "material_class"
        assert "macro" in polymer.description.lower()

    def test_material_hierarchy(self, materials_ontology):
        """Test material instance hierarchy"""
        # Silicon is elemental semiconductor
        silicon_materials = materials_ontology.get_materials_by_class("elemental_semiconductor")
        silicon_ids = [m.id for m in silicon_materials]
        assert "silicon" in silicon_ids

        # GaAs is compound semiconductor
        compound_materials = materials_ontology.get_materials_by_class("compound_semiconductor")
        compound_ids = [m.id for m in compound_materials]
        assert "gaas" in compound_ids


@pytest.mark.unit
class TestProcessingMethods:
    """Test materials processing methods"""

    def test_cvd_processing(self, materials_ontology):
        """Test CVD and PVD processing methods"""
        cvd = materials_ontology.concepts["cvd"]
        assert cvd.name == "Chemical Vapor Deposition"
        assert cvd.type == "processing_method"

        pvd = materials_ontology.concepts["pvd"]
        assert pvd.name == "Physical Vapor Deposition"
        assert pvd.type == "processing_method"

    def test_annealing_processes(self, materials_ontology):
        """Test thermal processing methods"""
        annealing = materials_ontology.concepts["annealing"]
        assert annealing.name == "Annealing"
        assert annealing.type == "processing_method"
        assert "heat" in annealing.description.lower()

        sintering = materials_ontology.concepts["sintering"]
        assert sintering.name == "Sintering"
        assert "heating" in sintering.description.lower() or "densif" in sintering.description.lower()

    def test_doping_methods(self, materials_ontology):
        """Test doping and modification methods"""
        doping = materials_ontology.concepts["doping"]
        assert doping.name == "Doping"
        assert doping.type == "processing_method"
        assert "impurities" in doping.description.lower()

    def test_process_property_relations(self, materials_ontology):
        """Test all processing methods are accessible"""
        all_processing = materials_ontology.get_processing_methods()

        assert len(all_processing) >= 8
        method_names = [p.name for p in all_processing]

        # Check expected methods
        expected_methods = ["Annealing", "Doping", "Chemical Vapor Deposition",
                          "Physical Vapor Deposition", "Sintering", "Sputtering",
                          "Molecular Beam Epitaxy", "Sol-Gel Processing"]

        for expected in expected_methods:
            assert expected in method_names
