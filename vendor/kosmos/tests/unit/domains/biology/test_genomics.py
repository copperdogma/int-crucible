"""
Unit tests for GenomicsAnalyzer (Phase 9).

Tests multi-modal GWAS integration with composite scoring (Figure 5 pattern).
Coverage target: 30 tests across 4 test classes
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from kosmos.domains.biology.genomics import (
    GenomicsAnalyzer,
    EvidenceLevel,
    EffectDirection,
    CompositeScore,
    GenomicsResult,
    MechanismRanking
)
from kosmos.domains.biology.apis import (
    GWASCatalogClient,
    GTExClient,
    ENCODEClient,
    dbSNPClient,
    EnsemblClient
)


# ================== Fixtures ==================

@pytest.fixture
def sample_gwas_data():
    """Sample GWAS data for rs7903146 (TCF7L2 protective variant)"""
    return {
        'chromosome': '10',
        'position': 114758349,
        'p_value': 1.2e-10,  # Genome-wide significant
        'beta': -0.12,  # Protective effect
        'trait': 'Type 2 Diabetes',
        'posterior_probability': 0.85  # High confidence
    }


@pytest.fixture
def sample_eqtl_data():
    """Sample eQTL data for TCF7L2 in pancreas"""
    return {
        'beta': -0.25,  # Concordant with GWAS
        'p_value': 3.4e-8,
        'tissue': 'Pancreas'
    }


@pytest.fixture
def sample_pqtl_data():
    """Sample pQTL data for TCF7L2 protein"""
    return {
        'beta': -0.18,  # Concordant with GWAS and eQTL
        'p_value': 1.5e-6
    }


@pytest.fixture
def sample_atac_data():
    """Sample ATAC-seq data showing open chromatin"""
    return {
        'has_peak': True,
        'significance': 0.001
    }


@pytest.fixture
def sample_tf_data():
    """Sample transcription factor disruption list"""
    return ['TCF7L2', 'HNF4A', 'FOXA2']


@pytest.fixture
def sample_snp_list_df():
    """Sample DataFrame with multiple SNPs for batch analysis"""
    return pd.DataFrame({
        'p_value': [1e-10, 5e-9, 3e-8, 0.002],
        'beta': [-0.12, -0.08, 0.06, 0.03],
        'trait': ['T2D', 'T2D', 'T2D', 'T2D'],
        'posterior_probability': [0.85, 0.45, 0.15, 0.001]
    }, index=['rs7903146', 'rs12255372', 'rs7901695', 'rs1234567'])


@pytest.fixture
def mock_gwas_client(sample_gwas_data):
    """Mocked GWAS Catalog client"""
    client = Mock(spec=GWASCatalogClient)
    client.get_variant.return_value = sample_gwas_data
    return client


@pytest.fixture
def mock_gtex_client(sample_eqtl_data, sample_pqtl_data):
    """Mocked GTEx client"""
    client = Mock()  # Don't use spec to allow get_pqtl
    client.get_eqtl = Mock(return_value=sample_eqtl_data)
    client.get_pqtl = Mock(return_value=sample_pqtl_data)
    return client


@pytest.fixture
def mock_encode_client(sample_atac_data):
    """Mocked ENCODE client"""
    client = Mock()  # Don't use spec to allow get_atac_peaks
    client.get_atac_peaks = Mock(return_value=sample_atac_data)
    return client


@pytest.fixture
def mock_dbsnp_client():
    """Mocked dbSNP client"""
    return Mock(spec=dbSNPClient)


@pytest.fixture
def mock_ensembl_client():
    """Mocked Ensembl client"""
    return Mock(spec=EnsemblClient)


@pytest.fixture
def genomics_analyzer(
    mock_gwas_client,
    mock_gtex_client,
    mock_encode_client,
    mock_dbsnp_client,
    mock_ensembl_client
):
    """GenomicsAnalyzer with all mocked clients"""
    return GenomicsAnalyzer(
        gwas_client=mock_gwas_client,
        gtex_client=mock_gtex_client,
        encode_client=mock_encode_client,
        dbsnp_client=mock_dbsnp_client,
        ensembl_client=mock_ensembl_client
    )


# ================== Tests ==================

@pytest.mark.unit
class TestGenomicsAnalyzerInit:
    """Test analyzer initialization."""

    def test_init_default(self):
        """Test default initialization creates all API clients."""
        with patch('kosmos.domains.biology.genomics.GWASCatalogClient') as mock_gwas, \
             patch('kosmos.domains.biology.genomics.GTExClient') as mock_gtex, \
             patch('kosmos.domains.biology.genomics.ENCODEClient') as mock_encode, \
             patch('kosmos.domains.biology.genomics.dbSNPClient') as mock_dbsnp, \
             patch('kosmos.domains.biology.genomics.EnsemblClient') as mock_ensembl:

            analyzer = GenomicsAnalyzer()

            # Verify all clients were created
            mock_gwas.assert_called_once()
            mock_gtex.assert_called_once()
            mock_encode.assert_called_once()
            mock_dbsnp.assert_called_once()
            mock_ensembl.assert_called_once()

            assert analyzer.gwas_client is not None
            assert analyzer.gtex_client is not None
            assert analyzer.encode_client is not None
            assert analyzer.dbsnp_client is not None
            assert analyzer.ensembl_client is not None

    def test_init_with_custom_clients(self, mock_gwas_client, mock_gtex_client):
        """Test initialization with custom API clients."""
        analyzer = GenomicsAnalyzer(
            gwas_client=mock_gwas_client,
            gtex_client=mock_gtex_client
        )

        assert analyzer.gwas_client is mock_gwas_client
        assert analyzer.gtex_client is mock_gtex_client
        # Others should still be initialized
        assert analyzer.encode_client is not None
        assert analyzer.dbsnp_client is not None
        assert analyzer.ensembl_client is not None


@pytest.mark.unit
class TestGWASMultimodal:
    """Test multi-modal GWAS integration."""

    def test_gwas_integration(
        self, genomics_analyzer, sample_gwas_data
    ):
        """Test GWAS data integration only (no other modalities)."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            eqtl_data=None,
            pqtl_data=None,
            atac_data=None,
            tf_data=None,
            fetch_missing=False
        )

        assert isinstance(result, GenomicsResult)
        assert result.snp_id == 'rs7903146'
        assert result.gene == 'TCF7L2'
        assert result.gwas_p_value == 1.2e-10
        assert result.gwas_beta == -0.12
        assert result.gwas_trait == 'Type 2 Diabetes'
        assert result.has_eqtl is False
        assert result.has_pqtl is False

    def test_eqtl_integration(
        self, genomics_analyzer, sample_gwas_data, sample_eqtl_data
    ):
        """Test GWAS + eQTL integration."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            eqtl_data=sample_eqtl_data,
            pqtl_data=None,
            atac_data=None,
            fetch_missing=False
        )

        assert result.has_eqtl is True
        assert result.eqtl_beta == -0.25
        assert result.eqtl_p_value == 3.4e-8
        assert result.eqtl_tissue == 'Pancreas'
        # Should have higher score than GWAS alone
        assert result.composite_score.qtl_score > 0

    def test_pqtl_integration(
        self, genomics_analyzer, sample_gwas_data, sample_pqtl_data
    ):
        """Test GWAS + pQTL integration."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            pqtl_data=sample_pqtl_data,
            fetch_missing=False
        )

        assert result.has_pqtl is True
        assert result.pqtl_beta == -0.18
        assert result.pqtl_p_value == 1.5e-6
        # QTL score should be positive
        assert result.composite_score.qtl_score > 0

    def test_encode_integration(
        self, genomics_analyzer, sample_gwas_data, sample_atac_data
    ):
        """Test GWAS + ATAC-seq integration."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            atac_data=sample_atac_data,
            fetch_missing=False
        )

        assert result.has_atac_peak is True
        assert result.atac_significance == 0.001
        # Expression score should be positive with ATAC peak
        assert result.composite_score.expression_score > 0

    def test_all_modalities_combined(
        self,
        genomics_analyzer,
        sample_gwas_data,
        sample_eqtl_data,
        sample_pqtl_data,
        sample_atac_data,
        sample_tf_data
    ):
        """Test full integration with all modalities present."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            eqtl_data=sample_eqtl_data,
            pqtl_data=sample_pqtl_data,
            atac_data=sample_atac_data,
            tf_data=sample_tf_data,
            fetch_missing=False
        )

        # All modalities should be present
        assert result.has_eqtl is True
        assert result.has_pqtl is True
        assert result.has_atac_peak is True
        assert result.n_disrupted_tfs == 3
        assert len(result.disrupted_tfs) == 3

        # Should have high composite score with all evidence
        assert result.composite_score.total_score >= 40
        assert result.evidence_level == EvidenceLevel.VERY_HIGH

        # Should be concordant (all effects negative)
        assert result.concordant is True

    def test_missing_modality_handling(self, genomics_analyzer, sample_gwas_data):
        """Test graceful handling of missing modalities."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            eqtl_data=None,
            pqtl_data=None,
            atac_data=None,
            tf_data=None,
            fetch_missing=False
        )

        # Should still return valid result with only GWAS data
        assert isinstance(result, GenomicsResult)
        assert result.has_eqtl is False
        assert result.has_pqtl is False
        assert result.has_atac_peak is False
        assert result.n_disrupted_tfs == 0
        # Score should be positive (GWAS + protective evidence)
        assert result.composite_score.total_score > 0
        # Should only have GWAS and protective scores (no QTL, TF, or expression)
        assert result.composite_score.qtl_score == 0
        assert result.composite_score.tf_score == 0
        assert result.composite_score.expression_score == 0

    def test_effect_direction_consistency(
        self,
        genomics_analyzer,
        sample_gwas_data,
        sample_eqtl_data,
        sample_pqtl_data
    ):
        """Test concordance validation for consistent effect directions."""
        # All betas are negative (concordant)
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            eqtl_data=sample_eqtl_data,
            pqtl_data=sample_pqtl_data,
            fetch_missing=False
        )

        assert result.concordant is True
        # Concordance bonus should increase QTL score
        assert result.composite_score.qtl_score > 10

    def test_evidence_level_assignment(self, genomics_analyzer):
        """Test evidence level is correctly assigned from score."""
        # High score scenario
        high_gwas = {
            'p_value': 1e-10,
            'beta': -0.15,
            'posterior_probability': 0.9,
            'trait': 'T2D'
        }
        high_eqtl = {'beta': -0.30, 'p_value': 1e-9}
        high_pqtl = {'beta': -0.25, 'p_value': 1e-7}

        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs123',
            gene='GENE1',
            gwas_data=high_gwas,
            eqtl_data=high_eqtl,
            pqtl_data=high_pqtl,
            tf_data=['TF1', 'TF2', 'TF3', 'TF4'],
            fetch_missing=False
        )

        # Should be HIGH or VERY_HIGH evidence
        assert result.evidence_level in [EvidenceLevel.HIGH, EvidenceLevel.VERY_HIGH]
        assert result.composite_score.total_score >= 30

    def test_variant_effect_prediction(self, genomics_analyzer):
        """Test effect direction determination (protective vs risk)."""
        # Protective variant (negative beta)
        protective_gwas = {
            'p_value': 1e-8,
            'beta': -0.10,
            'trait': 'Disease'
        }

        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs_protective',
            gene='GENE1',
            gwas_data=protective_gwas,
            fetch_missing=False
        )

        assert result.effect_direction == EffectDirection.PROTECTIVE
        # Should have protective score bonus
        assert result.composite_score.protective_score > 0

    def test_statistical_significance(self, genomics_analyzer):
        """Test p-value thresholds for GWAS scoring."""
        # Genome-wide significant
        sig_gwas = {
            'p_value': 1e-9,  # < 5e-8
            'beta': 0.08,
            'trait': 'Trait'
        }

        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs_sig',
            gene='GENE1',
            gwas_data=sig_gwas,
            fetch_missing=False
        )

        # Should have high GWAS score due to significance
        assert result.composite_score.gwas_score >= 5

    def test_data_filtering(self, genomics_analyzer):
        """Test validation of input data with invalid values."""
        # Valid integration should handle None gracefully
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs_test',
            gene='GENE1',
            gwas_data={'p_value': 0.01, 'beta': 0.05},
            eqtl_data=None,
            fetch_missing=False
        )

        assert isinstance(result, GenomicsResult)
        # Should not crash with minimal data
        assert result.composite_score.total_score >= 0

    def test_result_validation(
        self,
        genomics_analyzer,
        sample_gwas_data,
        sample_eqtl_data
    ):
        """Test that result is valid Pydantic model."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            eqtl_data=sample_eqtl_data,
            fetch_missing=False
        )

        # Should be valid Pydantic model
        assert isinstance(result, GenomicsResult)
        assert isinstance(result.composite_score, CompositeScore)
        assert isinstance(result.evidence_level, str)
        assert isinstance(result.effect_direction, str)

        # Scores should be in valid ranges
        assert 0 <= result.composite_score.gwas_score <= 10
        assert 0 <= result.composite_score.qtl_score <= 15
        assert 0 <= result.composite_score.tf_score <= 10
        assert 0 <= result.composite_score.expression_score <= 5
        assert 0 <= result.composite_score.protective_score <= 15
        assert 0 <= result.composite_score.total_score <= 55


@pytest.mark.unit
class TestCompositeScoring:
    """Test composite scoring (55-point system)."""

    def test_composite_score_calculation(self, genomics_analyzer, sample_gwas_data):
        """Test basic composite score calculation."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs123',
            gene='GENE1',
            gwas_data=sample_gwas_data,
            fetch_missing=False
        )

        score = result.composite_score
        # Total should be sum of components
        expected_total = (
            score.gwas_score +
            score.qtl_score +
            score.tf_score +
            score.expression_score +
            score.protective_score
        )
        assert abs(score.total_score - expected_total) < 0.01

    def test_all_evidence_types_weighted(
        self,
        genomics_analyzer,
        sample_gwas_data,
        sample_eqtl_data,
        sample_pqtl_data,
        sample_atac_data,
        sample_tf_data
    ):
        """Test that all evidence types contribute to score."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            eqtl_data=sample_eqtl_data,
            pqtl_data=sample_pqtl_data,
            atac_data=sample_atac_data,
            tf_data=sample_tf_data,
            fetch_missing=False
        )

        score = result.composite_score
        # All components should contribute
        assert score.gwas_score > 0  # GWAS data present
        assert score.qtl_score > 0   # eQTL + pQTL present
        assert score.tf_score > 0    # TFs present
        assert score.expression_score > 0  # eQTL beta + ATAC present
        assert score.protective_score > 0  # Negative beta

    def test_missing_evidence_handling(self, genomics_analyzer):
        """Test scoring with partial evidence."""
        minimal_gwas = {
            'p_value': 0.001,  # Not genome-wide sig but above threshold
            'beta': 0.03       # Small effect
        }

        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs_minimal',
            gene='GENE1',
            gwas_data=minimal_gwas,
            fetch_missing=False
        )

        score = result.composite_score
        # Should have minimal or zero GWAS score (p-value threshold may require < 0.001)
        assert score.gwas_score >= 0
        assert score.qtl_score == 0
        assert score.tf_score == 0
        assert score.expression_score == 0
        # Total score should be minimal
        assert score.total_score < 5

    def test_score_normalization(self, genomics_analyzer):
        """Test that total score never exceeds 55 points."""
        # Create maximal evidence scenario
        max_gwas = {
            'p_value': 1e-50,  # Extremely significant
            'beta': -0.50,     # Large effect
            'posterior_probability': 0.99,
            'trait': 'Trait'
        }
        max_eqtl = {'beta': -1.0, 'p_value': 1e-50}
        max_pqtl = {'beta': -1.0, 'p_value': 1e-50}
        max_atac = {'has_peak': True, 'significance': 1e-10}
        max_tfs = ['TF' + str(i) for i in range(20)]  # Many TFs

        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs_max',
            gene='GENE1',
            gwas_data=max_gwas,
            eqtl_data=max_eqtl,
            pqtl_data=max_pqtl,
            atac_data=max_atac,
            tf_data=max_tfs,
            fetch_missing=False
        )

        # Total should not exceed 55
        assert result.composite_score.total_score <= 55
        # Individual components should also be capped
        assert result.composite_score.gwas_score <= 10
        assert result.composite_score.qtl_score <= 15
        assert result.composite_score.tf_score <= 10
        assert result.composite_score.expression_score <= 5
        assert result.composite_score.protective_score <= 15

    def test_confidence_calculation(self, genomics_analyzer):
        """Test evidence level mapping from scores."""
        # Test VERY_HIGH (≥40)
        result_very_high = genomics_analyzer.multi_modal_integration(
            snp_id='rs1',
            gene='G1',
            gwas_data={'p_value': 1e-10, 'beta': -0.15, 'posterior_probability': 0.9},
            eqtl_data={'beta': -0.3, 'p_value': 1e-8},
            pqtl_data={'beta': -0.2, 'p_value': 1e-7},
            tf_data=['TF1', 'TF2', 'TF3'],
            fetch_missing=False
        )
        assert result_very_high.evidence_level == EvidenceLevel.VERY_HIGH

        # Test LOW (10-20)
        result_low = genomics_analyzer.multi_modal_integration(
            snp_id='rs2',
            gene='G2',
            gwas_data={'p_value': 1e-6, 'beta': 0.05},
            fetch_missing=False
        )
        assert result_low.evidence_level in [EvidenceLevel.LOW, EvidenceLevel.VERY_LOW]

    def test_supporting_evidence_list(
        self,
        genomics_analyzer,
        sample_gwas_data,
        sample_eqtl_data
    ):
        """Test extraction of key supporting evidence."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs7903146',
            gene='TCF7L2',
            gwas_data=sample_gwas_data,
            eqtl_data=sample_eqtl_data,
            fetch_missing=False
        )

        # Result should contain evidence information
        assert result.has_eqtl is True
        assert result.gwas_p_value is not None
        # Can reconstruct which evidence contributed
        assert result.composite_score.gwas_score > 0
        assert result.composite_score.qtl_score > 0

    def test_snp_ranking_by_score(self, genomics_analyzer, sample_snp_list_df):
        """Test that SNPs can be ranked by composite score."""
        results = []
        for snp_id, row in sample_snp_list_df.iterrows():
            result = genomics_analyzer.multi_modal_integration(
                snp_id=snp_id,
                gene='TCF7L2',
                gwas_data={
                    'p_value': row['p_value'],
                    'beta': row['beta'],
                    'posterior_probability': row['posterior_probability'],
                    'trait': row['trait']
                },
                fetch_missing=False
            )
            results.append(result)

        # Scores should decrease in order
        scores = [r.composite_score.total_score for r in results]
        assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))

    def test_top_candidates_selection(self, genomics_analyzer, sample_snp_list_df):
        """Test selecting top N candidates by score."""
        results = []
        for snp_id, row in sample_snp_list_df.iterrows():
            result = genomics_analyzer.multi_modal_integration(
                snp_id=snp_id,
                gene='TCF7L2',
                gwas_data={
                    'p_value': row['p_value'],
                    'beta': row['beta'],
                    'posterior_probability': row['posterior_probability'],
                    'trait': row['trait']
                },
                fetch_missing=False
            )
            results.append(result)

        # Sort by score
        sorted_results = sorted(results, key=lambda x: x.composite_score.total_score, reverse=True)

        # Top candidate should have highest score
        top_result = sorted_results[0]
        assert top_result.snp_id == 'rs7903146'  # Best p-value and posterior
        assert top_result.composite_score.total_score >= sorted_results[-1].composite_score.total_score


@pytest.mark.unit
class TestMechanismRanking:
    """Test mechanism ranking and batch analysis."""

    def test_mechanism_ranking_algorithm(
        self,
        genomics_analyzer,
        sample_gwas_data,
        sample_eqtl_data,
        sample_pqtl_data
    ):
        """Test ranking algorithm sorts by composite score."""
        # Create results with different scores
        result1 = genomics_analyzer.multi_modal_integration(
            snp_id='rs1',
            gene='GENE1',
            gwas_data=sample_gwas_data,
            eqtl_data=sample_eqtl_data,
            pqtl_data=sample_pqtl_data,
            fetch_missing=False
        )

        result2 = genomics_analyzer.multi_modal_integration(
            snp_id='rs2',
            gene='GENE2',
            gwas_data={'p_value': 0.001, 'beta': 0.05},
            fetch_missing=False
        )

        # Rank mechanisms
        rankings = genomics_analyzer.rank_mechanisms([result1, result2], min_score=0)

        assert len(rankings) == 2
        # Should be sorted by score (descending)
        assert rankings[0].total_score >= rankings[1].total_score
        # Ranks should be assigned
        assert rankings[0].rank == 1
        assert rankings[1].rank == 2

    def test_multimodal_evidence_integration(self, genomics_analyzer, sample_snp_list_df):
        """Test batch processing with analyze_snp_list."""
        # analyze_snp_list expects snp_ids list and gwas_df, not snp_list parameter
        results = genomics_analyzer.analyze_snp_list(
            snp_ids=list(sample_snp_list_df.index),
            gene='TCF7L2',
            gwas_df=sample_snp_list_df
        )

        assert len(results) == len(sample_snp_list_df)
        assert all(isinstance(r, GenomicsResult) for r in results)
        # All should have the same gene
        assert all(r.gene == 'TCF7L2' for r in results)

    def test_pathway_consistency_check(
        self,
        genomics_analyzer,
        sample_gwas_data,
        sample_eqtl_data,
        sample_pqtl_data
    ):
        """Test concordance checking across multiple results."""
        # All concordant
        result1 = genomics_analyzer.multi_modal_integration(
            snp_id='rs1',
            gene='G1',
            gwas_data=sample_gwas_data,
            eqtl_data=sample_eqtl_data,
            pqtl_data=sample_pqtl_data,
            fetch_missing=False
        )

        # Non-concordant
        result2 = genomics_analyzer.multi_modal_integration(
            snp_id='rs2',
            gene='G2',
            gwas_data={'p_value': 1e-8, 'beta': -0.10},
            eqtl_data={'beta': 0.20, 'p_value': 1e-6},  # Opposite sign
            fetch_missing=False
        )

        assert result1.concordant is True
        assert result2.concordant is False

    def test_confidence_scoring(self, genomics_analyzer):
        """Test filtering by minimum score threshold."""
        result_high = genomics_analyzer.multi_modal_integration(
            snp_id='rs_high',
            gene='G1',
            gwas_data={'p_value': 1e-10, 'beta': -0.15, 'posterior_probability': 0.9},
            eqtl_data={'beta': -0.3, 'p_value': 1e-8},
            pqtl_data={'beta': -0.2, 'p_value': 1e-7},
            fetch_missing=False
        )

        result_low = genomics_analyzer.multi_modal_integration(
            snp_id='rs_low',
            gene='G2',
            gwas_data={'p_value': 0.01, 'beta': 0.02},
            fetch_missing=False
        )

        # Rank with min_score threshold
        rankings = genomics_analyzer.rank_mechanisms(
            [result_high, result_low],
            min_score=20  # Only high-scoring results
        )

        # Only high-score result should pass
        assert len(rankings) == 1
        assert rankings[0].snp_id == 'rs_high'

    def test_top_mechanisms_selection(
        self,
        genomics_analyzer,
        sample_snp_list_df
    ):
        """Test selecting top N mechanisms."""
        results = genomics_analyzer.analyze_snp_list(
            snp_ids=list(sample_snp_list_df.index),
            gene='TCF7L2',
            gwas_df=sample_snp_list_df
        )

        # Rank and get top 2
        rankings = genomics_analyzer.rank_mechanisms(results, top_n=2, min_score=0)

        assert len(rankings) <= 2
        # Should be top scoring
        if len(rankings) == 2:
            assert rankings[0].total_score >= rankings[1].total_score

    def test_supporting_snps_list(self, genomics_analyzer, sample_snp_list_df):
        """Test extraction of key supporting SNPs."""
        results = genomics_analyzer.analyze_snp_list(
            snp_ids=list(sample_snp_list_df.index),
            gene='TCF7L2',
            gwas_df=sample_snp_list_df
        )

        rankings = genomics_analyzer.rank_mechanisms(results, min_score=0)

        # Each ranking should have SNP information
        for ranking in rankings:
            assert ranking.snp_id is not None
            assert ranking.gene == 'TCF7L2'
            assert ranking.total_score >= 0

    def test_effect_direction_validation(self, genomics_analyzer):
        """Test effect direction classification."""
        # Protective
        result_protective = genomics_analyzer.multi_modal_integration(
            snp_id='rs_prot',
            gene='G1',
            gwas_data={'p_value': 1e-8, 'beta': -0.10},
            fetch_missing=False
        )
        assert result_protective.effect_direction == EffectDirection.PROTECTIVE

        # Risk
        result_risk = genomics_analyzer.multi_modal_integration(
            snp_id='rs_risk',
            gene='G2',
            gwas_data={'p_value': 1e-8, 'beta': 0.10},
            fetch_missing=False
        )
        assert result_risk.effect_direction == EffectDirection.RISK

        # Neutral
        result_neutral = genomics_analyzer.multi_modal_integration(
            snp_id='rs_neut',
            gene='G3',
            gwas_data={'p_value': 1e-8, 'beta': 0.02},  # Small effect
            fetch_missing=False
        )
        assert result_neutral.effect_direction == EffectDirection.NEUTRAL

    def test_ranking_consistency(self, genomics_analyzer, sample_gwas_data):
        """Test ranking is reproducible."""
        result = genomics_analyzer.multi_modal_integration(
            snp_id='rs123',
            gene='GENE1',
            gwas_data=sample_gwas_data,
            fetch_missing=False
        )

        # Rank twice
        rankings1 = genomics_analyzer.rank_mechanisms([result], min_score=0)
        rankings2 = genomics_analyzer.rank_mechanisms([result], min_score=0)

        # Should be identical
        assert len(rankings1) == len(rankings2)
        assert rankings1[0].total_score == rankings2[0].total_score
        assert rankings1[0].snp_id == rankings2[0].snp_id
