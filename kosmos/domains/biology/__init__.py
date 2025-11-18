"""Biology domain module - metabolomics, genomics, and multi-modal integration"""

from kosmos.domains.biology.apis import (
    KEGGClient,
    GWASCatalogClient,
    GTExClient,
    ENCODEClient,
    dbSNPClient,
    EnsemblClient,
    HMDBClient,
    MetaboLightsClient,
    UniProtClient,
    PDBClient,
)

from kosmos.domains.biology.metabolomics import (
    MetabolomicsAnalyzer,
    MetabolomicsResult,
    PathwayPattern,
    PathwayComparison,
    MetaboliteCategory,
    MetaboliteType,
)

from kosmos.domains.biology.genomics import (
    GenomicsAnalyzer,
    GenomicsResult,
    CompositeScore,
    MechanismRanking,
    EvidenceLevel,
    EffectDirection,
)

from kosmos.domains.biology.ontology import (
    BiologyOntology,
    BiologicalConcept,
    BiologicalRelation,
    BiologicalRelationType,
)

__all__ = [
    # API Clients
    'KEGGClient',
    'GWASCatalogClient',
    'GTExClient',
    'ENCODEClient',
    'dbSNPClient',
    'EnsemblClient',
    'HMDBClient',
    'MetaboLightsClient',
    'UniProtClient',
    'PDBClient',

    # Metabolomics
    'MetabolomicsAnalyzer',
    'MetabolomicsResult',
    'PathwayPattern',
    'PathwayComparison',
    'MetaboliteCategory',
    'MetaboliteType',

    # Genomics
    'GenomicsAnalyzer',
    'GenomicsResult',
    'CompositeScore',
    'MechanismRanking',
    'EvidenceLevel',
    'EffectDirection',

    # Ontology
    'BiologyOntology',
    'BiologicalConcept',
    'BiologicalRelation',
    'BiologicalRelationType',
]
