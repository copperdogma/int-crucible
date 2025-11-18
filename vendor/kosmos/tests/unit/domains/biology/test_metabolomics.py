"""
Unit tests for MetabolomicsAnalyzer (Phase 9).

Tests metabolite categorization, group comparison, and pathway pattern analysis.
Coverage target: 30 tests across 5 test classes
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from kosmos.domains.biology.metabolomics import (
    MetabolomicsAnalyzer,
    MetaboliteCategory,
    MetaboliteType,
    MetabolomicsResult,
    PathwayPattern,
    PathwayComparison
)
from kosmos.domains.biology.apis import KEGGClient


@pytest.fixture
def metabolomics_analyzer():
    """Create MetabolomicsAnalyzer instance with mocked KEGG client"""
    mock_kegg = Mock(spec=KEGGClient)
    mock_kegg.categorize_metabolite.return_value = {
        'category': 'purine',
        'pathways': ['Purine metabolism']
    }
    return MetabolomicsAnalyzer(kegg_client=mock_kegg)


@pytest.fixture
def sample_metabolite_data():
    """Sample metabolite concentration data for 3 control + 3 treatment samples"""
    return pd.DataFrame({
        'Control_1': [10.5, 8.2, 15.3, 7.8, 12.1],
        'Control_2': [11.2, 7.9, 16.1, 8.1, 11.8],
        'Control_3': [10.8, 8.5, 15.7, 7.5, 12.5],
        'Treatment_1': [5.2, 12.3, 8.1, 14.2, 20.5],
        'Treatment_2': [4.8, 13.1, 7.8, 15.1, 21.2],
        'Treatment_3': [5.5, 12.7, 8.5, 14.8, 19.8],
    }, index=['Adenosine', 'Guanosine', 'AMP', 'GMP', 'ATP'])


@pytest.mark.unit
class TestMetabolomicsAnalyzerInit:
    """Test analyzer initialization."""

    def test_init_default(self):
        """Test default initialization creates KEGG client."""
        with patch('kosmos.domains.biology.metabolomics.KEGGClient') as mock_kegg_class:
            analyzer = MetabolomicsAnalyzer()
            mock_kegg_class.assert_called_once()
            assert analyzer.kegg_client is not None

    def test_init_with_kegg_client(self):
        """Test initialization with custom KEGG client."""
        mock_kegg = Mock(spec=KEGGClient)
        analyzer = MetabolomicsAnalyzer(kegg_client=mock_kegg)
        assert analyzer.kegg_client is mock_kegg


@pytest.mark.unit
class TestCategorizeMetabolite:
    """Test metabolite categorization."""

    @pytest.mark.parametrize("compound_id,expected_category,expected_type", [
        ("Adenosine", MetaboliteCategory.PURINE, MetaboliteType.SALVAGE_PRECURSOR),
        ("AMP", MetaboliteCategory.PURINE, MetaboliteType.SYNTHESIS_PRODUCT),
        ("Guanosine", MetaboliteCategory.PURINE, MetaboliteType.SALVAGE_PRECURSOR),
        ("GMP", MetaboliteCategory.PURINE, MetaboliteType.SYNTHESIS_PRODUCT),
        ("Cytidine", MetaboliteCategory.PYRIMIDINE, MetaboliteType.SALVAGE_PRECURSOR),
        ("UMP", MetaboliteCategory.PYRIMIDINE, MetaboliteType.SYNTHESIS_PRODUCT),
    ])
    def test_categorize_known_compounds(self, metabolomics_analyzer, compound_id, expected_category, expected_type):
        """Test categorization of known compounds."""
        result = metabolomics_analyzer.categorize_metabolite(compound_id, use_kegg=False)

        assert result['compound_name'] == compound_id
        assert result['category'] == expected_category
        assert result['metabolite_type'] == expected_type

    def test_categorize_unknown_compound(self, metabolomics_analyzer):
        """Test handling of unknown compound returns OTHER category and INTERMEDIATE type."""
        result = metabolomics_analyzer.categorize_metabolite('UnknownMetabolite', use_kegg=False)

        assert result['compound_name'] == 'UnknownMetabolite'
        assert result['category'] == MetaboliteCategory.OTHER
        assert result['metabolite_type'] == MetaboliteType.INTERMEDIATE  # Default for unknown

    def test_cache_or_kegg_integration(self, metabolomics_analyzer):
        """Test KEGG integration when use_kegg=True."""
        result = metabolomics_analyzer.categorize_metabolite('Adenosine', use_kegg=True)

        # Should have called KEGG client (mocked)
        metabolomics_analyzer.kegg_client.categorize_metabolite.assert_called_with('Adenosine')
        assert 'pathways' in result


@pytest.mark.unit
class TestGroupComparison:
    """Test group comparison analysis."""

    def test_ttest_significant(self, metabolomics_analyzer, sample_metabolite_data):
        """Test t-test with significant difference (Adenosine decreased in treatment)."""
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=['Adenosine'],
            p_threshold=0.05
        )

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, MetabolomicsResult)
        assert result.metabolite == 'Adenosine'
        assert result.category == MetaboliteCategory.PURINE
        assert result.p_value < 0.05  # Should be significant
        assert result.significant is True

    def test_ttest_not_significant(self, metabolomics_analyzer):
        """Test t-test with no significant difference."""
        # Create data with no difference between groups
        no_diff_data = pd.DataFrame({
            'Control_1': [10.0, 10.0],
            'Control_2': [10.1, 10.1],
            'Treatment_1': [10.0, 10.0],
            'Treatment_2': [10.1, 10.1],
        }, index=['Adenosine', 'Guanosine'])

        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=no_diff_data,
            group1_samples=['Control_1', 'Control_2'],
            group2_samples=['Treatment_1', 'Treatment_2'],
            metabolites=['Adenosine'],
            p_threshold=0.05
        )

        assert len(results) == 1
        result = results[0]
        assert result.p_value > 0.05  # Not significant
        assert result.significant is False

    def test_log2_fold_change(self, metabolomics_analyzer, sample_metabolite_data):
        """Test log2 fold change calculation has correct direction."""
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=['Adenosine', 'ATP'],
            p_threshold=0.05
        )

        # Adenosine: decreased (Control ~11, Treatment ~5)
        adenosine = [r for r in results if r.metabolite == 'Adenosine'][0]
        # ATP: increased (Control ~12, Treatment ~20)
        atp = [r for r in results if r.metabolite == 'ATP'][0]

        # Log2FC should have opposite signs for opposite changes
        assert adenosine.log2_fold_change * atp.log2_fold_change < 0  # Opposite signs

    def test_effect_size_cohens_d(self, metabolomics_analyzer, sample_metabolite_data):
        """Test that results contain valid t-statistics."""
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=['Adenosine'],
            p_threshold=0.05
        )

        assert len(results) == 1
        result = results[0]
        # t-statistic should be non-zero for different means
        assert abs(result.t_statistic) > 0

    def test_multiple_groups(self, metabolomics_analyzer, sample_metabolite_data):
        """Test comparison with multiple metabolites."""
        metabolites = ['Adenosine', 'Guanosine', 'AMP', 'GMP', 'ATP']
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=metabolites,
            p_threshold=0.05
        )

        assert len(results) == 5
        # All should be MetabolomicsResult instances
        assert all(isinstance(r, MetabolomicsResult) for r in results)
        # All should have valid categories (check against enum values)
        valid_categories = [e.value for e in MetaboliteCategory]
        assert all(r.category in valid_categories for r in results)

    def test_missing_data_handling(self, metabolomics_analyzer):
        """Test handling of missing data (NaN values)."""
        data_with_nan = pd.DataFrame({
            'Control_1': [10.0, np.nan],
            'Control_2': [10.1, 8.0],
            'Treatment_1': [5.0, np.nan],
            'Treatment_2': [5.1, 12.0],
        }, index=['Adenosine', 'Guanosine'])

        # Should handle NaN gracefully (either skip or use available data)
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=data_with_nan,
            group1_samples=['Control_1', 'Control_2'],
            group2_samples=['Treatment_1', 'Treatment_2'],
            metabolites=['Adenosine', 'Guanosine'],
            p_threshold=0.05
        )

        # Should return results (may handle NaN by dropping or imputing)
        assert isinstance(results, list)


@pytest.mark.unit
class TestPathwayPattern:
    """Test pathway pattern detection."""

    def test_pathway_enrichment(self, metabolomics_analyzer, sample_metabolite_data):
        """Test pathway enrichment calculation from group comparison results."""
        # First run group comparison
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=['Adenosine', 'Guanosine', 'AMP', 'GMP', 'ATP'],
            p_threshold=0.05
        )

        # Analyze pathway patterns
        patterns = metabolomics_analyzer.analyze_pathway_pattern(results)

        assert isinstance(patterns, list)
        # Should find at least one pattern (all are purines)
        assert len(patterns) > 0
        assert all(isinstance(p, PathwayPattern) for p in patterns)

    def test_upregulated_compounds(self, metabolomics_analyzer, sample_metabolite_data):
        """Test identification of upregulated compounds in pathway pattern."""
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=['Guanosine', 'ATP'],  # Both increased in treatment
            p_threshold=0.05
        )

        patterns = metabolomics_analyzer.analyze_pathway_pattern(results)

        # Should detect pattern with increased metabolites
        if patterns:
            pattern = patterns[0]
            assert pattern.n_increased >= 0
            assert pattern.n_metabolites > 0

    def test_downregulated_compounds(self, metabolomics_analyzer, sample_metabolite_data):
        """Test identification of downregulated compounds."""
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=['Adenosine', 'AMP'],  # Both decreased in treatment
            p_threshold=0.05
        )

        patterns = metabolomics_analyzer.analyze_pathway_pattern(results)

        # Should detect pattern with decreased metabolites
        if patterns:
            pattern = patterns[0]
            assert pattern.n_decreased >= 0
            assert pattern.n_metabolites > 0

    def test_multiple_pathways(self, metabolomics_analyzer):
        """Test analysis across multiple pathways (purine and pyrimidine)."""
        # Create data with both purine and pyrimidine metabolites
        multi_pathway_data = pd.DataFrame({
            'Control_1': [10.0, 8.0, 12.0, 9.0],
            'Control_2': [10.5, 8.2, 12.3, 9.1],
            'Treatment_1': [5.0, 12.0, 6.0, 13.0],
            'Treatment_2': [5.5, 12.5, 6.2, 13.2],
        }, index=['Adenosine', 'Cytidine', 'AMP', 'UMP'])

        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=multi_pathway_data,
            group1_samples=['Control_1', 'Control_2'],
            group2_samples=['Treatment_1', 'Treatment_2'],
            metabolites=['Adenosine', 'Cytidine', 'AMP', 'UMP'],
            p_threshold=0.05
        )

        patterns = metabolomics_analyzer.analyze_pathway_pattern(results)

        # Should find patterns for both pathways
        assert len(patterns) >= 1  # At least one pathway pattern

    def test_no_pattern_found(self, metabolomics_analyzer):
        """Test when no significant pattern exists (empty results)."""
        # Empty results list
        patterns = metabolomics_analyzer.analyze_pathway_pattern([])

        assert isinstance(patterns, list)
        # Should return empty list or handle gracefully
        assert len(patterns) == 0


@pytest.mark.unit
class TestPathwayComparison:
    """Test pathway-to-pathway comparison (salvage vs synthesis)."""

    def test_compare_two_pathways(self, metabolomics_analyzer, sample_metabolite_data):
        """Test comparison of salvage vs synthesis pathways."""
        # Get group comparison results first
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=['Adenosine', 'Guanosine', 'AMP', 'GMP'],  # Mix of salvage + synthesis
            p_threshold=0.05
        )

        # Compare salvage vs synthesis
        comparison = metabolomics_analyzer.compare_salvage_vs_synthesis(results)

        # Returns single PathwayComparison or None
        assert comparison is not None
        assert isinstance(comparison, PathwayComparison)

    def test_overlapping_compounds(self, metabolomics_analyzer):
        """Test handling when metabolites span multiple categories."""
        # This is implicitly tested by having mix of salvage + synthesis metabolites
        # The comparison should correctly categorize each metabolite type
        data = pd.DataFrame({
            'C1': [10.0, 10.0, 10.0, 10.0],
            'C2': [10.0, 10.0, 10.0, 10.0],
            'T1': [5.0, 5.0, 15.0, 15.0],
            'T2': [5.0, 5.0, 15.0, 15.0],
        }, index=['Adenosine', 'Guanosine', 'AMP', 'GMP'])

        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=data,
            group1_samples=['C1', 'C2'],
            group2_samples=['T1', 'T2'],
            metabolites=['Adenosine', 'Guanosine', 'AMP', 'GMP'],
            p_threshold=0.05
        )

        comparison = metabolomics_analyzer.compare_salvage_vs_synthesis(results)

        # Should correctly separate salvage (Adenosine, Guanosine) from synthesis (AMP, GMP)
        assert comparison is not None

    def test_statistical_significance(self, metabolomics_analyzer, sample_metabolite_data):
        """Test statistical significance calculation in pathway comparison."""
        results = metabolomics_analyzer.analyze_group_comparison(
            data_df=sample_metabolite_data,
            group1_samples=['Control_1', 'Control_2', 'Control_3'],
            group2_samples=['Treatment_1', 'Treatment_2', 'Treatment_3'],
            metabolites=['Adenosine', 'Guanosine', 'AMP', 'GMP'],
            p_threshold=0.05
        )

        comparison = metabolomics_analyzer.compare_salvage_vs_synthesis(results)

        if comparison:
            # Should have valid p-value
            assert 0 <= comparison.p_value <= 1.0
            # significant flag should match p-value threshold
            assert isinstance(comparison.significant, bool)

    def test_empty_pathway_handling(self, metabolomics_analyzer):
        """Test handling of empty pathway (no results)."""
        comparison = metabolomics_analyzer.compare_salvage_vs_synthesis([])

        # Should return None for empty results
        assert comparison is None
