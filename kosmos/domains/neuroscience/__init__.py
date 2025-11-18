"""Neuroscience domain module - connectomics, neurodegeneration, and brain network analysis"""

from kosmos.domains.neuroscience.apis import (
    FlyWireClient,
    AllenBrainClient,
    MICrONSClient,
    GEOClient,
    AMPADClient,
    OpenConnectomeClient,
    WormBaseClient,
    NeuronData,
    GeneExpressionData,
    ConnectomeDataset,
    DifferentialExpressionResult as APIDifferentialExpressionResult,
)

from kosmos.domains.neuroscience.connectomics import (
    ConnectomicsAnalyzer,
    ConnectomicsResult,
    ScalingRelationship,
    PowerLawFit,
    CrossSpeciesComparison,
)

from kosmos.domains.neuroscience.neurodegeneration import (
    NeurodegenerationAnalyzer,
    NeurodegenerationResult,
    DifferentialExpressionResult,
    PathwayEnrichmentResult,
    CrossSpeciesValidation,
    TemporalStage,
)

from kosmos.domains.neuroscience.ontology import (
    NeuroscienceOntology,
)

__all__ = [
    # API Clients
    'FlyWireClient',
    'AllenBrainClient',
    'MICrONSClient',
    'GEOClient',
    'AMPADClient',
    'OpenConnectomeClient',
    'WormBaseClient',

    # API Data Models
    'NeuronData',
    'GeneExpressionData',
    'ConnectomeDataset',
    'APIDifferentialExpressionResult',

    # Connectomics
    'ConnectomicsAnalyzer',
    'ConnectomicsResult',
    'ScalingRelationship',
    'PowerLawFit',
    'CrossSpeciesComparison',

    # Neurodegeneration
    'NeurodegenerationAnalyzer',
    'NeurodegenerationResult',
    'DifferentialExpressionResult',
    'PathwayEnrichmentResult',
    'CrossSpeciesValidation',
    'TemporalStage',

    # Ontology
    'NeuroscienceOntology',
]
