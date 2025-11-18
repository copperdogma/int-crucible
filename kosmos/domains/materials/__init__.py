"""Materials Science domain module - materials optimization and parameter analysis"""

from kosmos.domains.materials.apis import (
    MaterialsProjectClient,
    NOMADClient,
    AflowClient,
    CitrinationClient,
    PerovskiteDBClient,
    MaterialProperties,
    NomadEntry,
    AflowMaterial,
    CitrinationData,
    PerovskiteExperiment,
)

from kosmos.domains.materials.optimization import (
    MaterialsOptimizer,
    CorrelationResult,
    SHAPResult,
    OptimizationResult,
    DOEResult,
)

from kosmos.domains.materials.ontology import (
    MaterialsOntology,
    MaterialsConcept,
    MaterialsRelation,
    MaterialsRelationType,
)

__all__ = [
    # API Clients
    'MaterialsProjectClient',
    'NOMADClient',
    'AflowClient',
    'CitrinationClient',
    'PerovskiteDBClient',

    # API Data Models
    'MaterialProperties',
    'NomadEntry',
    'AflowMaterial',
    'CitrinationData',
    'PerovskiteExperiment',

    # Optimization
    'MaterialsOptimizer',
    'CorrelationResult',
    'SHAPResult',
    'OptimizationResult',
    'DOEResult',

    # Ontology
    'MaterialsOntology',
    'MaterialsConcept',
    'MaterialsRelation',
    'MaterialsRelationType',
]
