"""
Tests for statistical validation module.

Tests StatisticalValidator methods for hypothesis testing, effect sizes,
confidence intervals, and multiple testing correction.
"""

import pytest
import numpy as np
from scipy import stats as scipy_stats

from kosmos.execution.statistics import StatisticalValidator


class TestSignificanceTesting:
    """Test significance threshold and labeling."""

    def test_apply_significance_threshold_highly_significant(self):
        """Test p-value labeling for highly significant result."""
        result = StatisticalValidator.apply_significance_threshold(0.0001)

        assert result['p_value'] == 0.0001
        assert result['significant_0.05'] is True
        assert result['significant_0.01'] is True
        assert result['significant_0.001'] is True
        assert result['significance_label'] == '***'

    def test_apply_significance_threshold_very_significant(self):
        """Test p-value labeling for very significant result."""
        result = StatisticalValidator.apply_significance_threshold(0.005)

        assert result['significant_0.05'] is True
        assert result['significant_0.01'] is True
        assert result['significant_0.001'] is False
        assert result['significance_label'] == '**'

    def test_apply_significance_threshold_significant(self):
        """Test p-value labeling for significant result."""
        result = StatisticalValidator.apply_significance_threshold(0.03)

        assert result['significant_0.05'] is True
        assert result['significant_0.01'] is False
        assert result['significant_0.001'] is False
        assert result['significance_label'] == '*'

    def test_apply_significance_threshold_not_significant(self):
        """Test p-value labeling for non-significant result."""
        result = StatisticalValidator.apply_significance_threshold(0.15)

        assert result['significant_0.05'] is False
        assert result['significant_0.01'] is False
        assert result['significant_0.001'] is False
        assert result['significance_label'] == 'ns'


class TestEffectSizes:
    """Test effect size calculations."""

    def test_calculate_cohens_d_large_effect(self):
        """Test Cohen's d for large effect."""
        np.random.seed(42)
        group1 = np.random.normal(10, 2, 50)
        group2 = np.random.normal(15, 2, 50)  # Large difference

        d = StatisticalValidator.calculate_cohens_d(group1, group2)

        # Should be large negative (group1 < group2)
        assert d < -0.8  # Large effect

    def test_calculate_cohens_d_medium_effect(self):
        """Test Cohen's d for medium effect."""
        np.random.seed(42)
        group1 = np.random.normal(10, 2, 50)
        group2 = np.random.normal(11, 2, 50)  # Medium difference

        d = StatisticalValidator.calculate_cohens_d(group1, group2)

        # Should be medium negative
        assert -0.8 < d < -0.2

    def test_calculate_cohens_d_small_effect(self):
        """Test Cohen's d for small effect."""
        np.random.seed(42)
        group1 = np.random.normal(10, 2, 100)
        group2 = np.random.normal(10.4, 2, 100)  # Small difference

        d = StatisticalValidator.calculate_cohens_d(group1, group2)

        # Should be small
        assert abs(d) < 0.5

    def test_calculate_cohens_d_zero_variance(self):
        """Test Cohen's d with zero variance."""
        group1 = [5, 5, 5, 5]
        group2 = [5, 5, 5, 5]

        d = StatisticalValidator.calculate_cohens_d(group1, group2)

        assert d == 0.0

    def test_calculate_eta_squared(self):
        """Test eta-squared calculation."""
        np.random.seed(42)
        groups = [
            np.random.normal(10, 2, 30),
            np.random.normal(12, 2, 30),
            np.random.normal(14, 2, 30)
        ]

        eta_sq = StatisticalValidator.calculate_eta_squared(groups)

        # Should be medium to large (groups have different means)
        assert 0.1 < eta_sq < 0.9

    def test_calculate_eta_squared_no_effect(self):
        """Test eta-squared with no group differences."""
        np.random.seed(42)
        groups = [
            np.random.normal(10, 2, 30),
            np.random.normal(10, 2, 30),
            np.random.normal(10, 2, 30)
        ]

        eta_sq = StatisticalValidator.calculate_eta_squared(groups)

        # Should be very small
        assert eta_sq < 0.1

    def test_calculate_cramers_v(self):
        """Test Cramér's V calculation."""
        # 2x2 contingency table with association
        contingency = [
            [30, 10],
            [10, 50]
        ]

        v = StatisticalValidator.calculate_cramers_v(contingency)

        # Should indicate moderate to strong association
        assert 0.3 < v < 0.7

    def test_calculate_cramers_v_no_association(self):
        """Test Cramér's V with no association."""
        contingency = [
            [25, 25],
            [25, 25]
        ]

        v = StatisticalValidator.calculate_cramers_v(contingency)

        # Should be near zero
        assert v < 0.1

    def test_interpret_effect_size_cohens_d(self):
        """Test effect size interpretation for Cohen's d."""
        assert StatisticalValidator.interpret_effect_size(0.1, 'cohens_d') == 'negligible'
        assert StatisticalValidator.interpret_effect_size(0.3, 'cohens_d') == 'small'
        assert StatisticalValidator.interpret_effect_size(0.6, 'cohens_d') == 'medium'
        assert StatisticalValidator.interpret_effect_size(1.0, 'cohens_d') == 'large'

    def test_interpret_effect_size_eta_squared(self):
        """Test effect size interpretation for eta-squared."""
        assert StatisticalValidator.interpret_effect_size(0.005, 'eta_squared') == 'negligible'
        assert StatisticalValidator.interpret_effect_size(0.03, 'eta_squared') == 'small'
        assert StatisticalValidator.interpret_effect_size(0.10, 'eta_squared') == 'medium'
        assert StatisticalValidator.interpret_effect_size(0.20, 'eta_squared') == 'large'

    def test_interpret_effect_size_cramers_v(self):
        """Test effect size interpretation for Cramér's V."""
        assert StatisticalValidator.interpret_effect_size(0.05, 'cramers_v') == 'negligible'
        assert StatisticalValidator.interpret_effect_size(0.2, 'cramers_v') == 'small'
        assert StatisticalValidator.interpret_effect_size(0.4, 'cramers_v') == 'medium'
        assert StatisticalValidator.interpret_effect_size(0.6, 'cramers_v') == 'large'


class TestConfidenceIntervals:
    """Test confidence interval calculations."""

    def test_parametric_confidence_interval_95(self):
        """Test 95% parametric CI."""
        np.random.seed(42)
        data = np.random.normal(10, 2, 100)

        lower, upper = StatisticalValidator.parametric_confidence_interval(data, confidence=0.95)

        # Check CI contains true mean (10)
        assert lower < 10 < upper

        # Check CI width is reasonable
        assert upper - lower > 0
        assert upper - lower < 2  # Should be reasonably tight with n=100

    def test_parametric_confidence_interval_99(self):
        """Test 99% parametric CI."""
        np.random.seed(42)
        data = np.random.normal(10, 2, 100)

        lower_99, upper_99 = StatisticalValidator.parametric_confidence_interval(data, confidence=0.99)
        lower_95, upper_95 = StatisticalValidator.parametric_confidence_interval(data, confidence=0.95)

        # 99% CI should be wider than 95% CI
        assert (upper_99 - lower_99) > (upper_95 - lower_95)

    def test_bootstrap_confidence_interval_mean(self):
        """Test bootstrap CI for mean."""
        np.random.seed(42)
        data = np.random.normal(10, 2, 50)

        lower, upper = StatisticalValidator.bootstrap_confidence_interval(
            data, confidence=0.95, n_iterations=1000, statistic='mean'
        )

        # Check CI contains true mean
        assert lower < 10 < upper

        # Check types
        assert isinstance(lower, float)
        assert isinstance(upper, float)

    def test_bootstrap_confidence_interval_median(self):
        """Test bootstrap CI for median."""
        np.random.seed(42)
        data = np.random.exponential(scale=2, size=100)

        lower, upper = StatisticalValidator.bootstrap_confidence_interval(
            data, confidence=0.95, n_iterations=1000, statistic='median'
        )

        # Check CI is valid
        assert lower < upper

    def test_bootstrap_confidence_interval_std(self):
        """Test bootstrap CI for standard deviation."""
        np.random.seed(42)
        data = np.random.normal(10, 3, 100)

        lower, upper = StatisticalValidator.bootstrap_confidence_interval(
            data, confidence=0.95, n_iterations=1000, statistic='std'
        )

        # Check CI contains true std (3)
        assert lower < 3 < upper


class TestMultipleTestingCorrection:
    """Test multiple testing correction methods."""

    def test_bonferroni_correction(self):
        """Test Bonferroni correction."""
        p_values = [0.001, 0.01, 0.03, 0.05, 0.10]

        result = StatisticalValidator.bonferroni_correction(p_values, alpha=0.05)

        # Check structure
        assert 'corrected_alpha' in result
        assert 'significant' in result
        assert result['n_tests'] == 5

        # Corrected alpha should be 0.05/5 = 0.01
        assert result['corrected_alpha'] == 0.01

        # Only first two should be significant
        assert result['significant'] == [True, True, False, False, False]
        assert result['n_significant'] == 2

    def test_benjamini_hochberg_fdr(self):
        """Test Benjamini-Hochberg FDR correction."""
        p_values = [0.001, 0.01, 0.02, 0.04, 0.08]

        result = StatisticalValidator.benjamini_hochberg_fdr(p_values, alpha=0.05)

        # Check structure
        assert 'significant' in result
        assert 'adjusted_p_values' in result
        assert result['n_tests'] == 5

        # FDR should be less conservative than Bonferroni
        assert result['n_significant'] > 0

        # Adjusted p-values should all be >= original
        for orig, adj in zip(p_values, result['adjusted_p_values']):
            assert adj >= orig

    def test_holm_bonferroni_correction(self):
        """Test Holm-Bonferroni correction."""
        p_values = [0.001, 0.005, 0.02, 0.05, 0.10]

        result = StatisticalValidator.holm_bonferroni_correction(p_values, alpha=0.05)

        # Check structure
        assert 'significant' in result
        assert result['n_tests'] == 5

        # Should be less conservative than Bonferroni but more than BH
        bonf_result = StatisticalValidator.bonferroni_correction(p_values, alpha=0.05)
        assert result['n_significant'] >= bonf_result['n_significant']

    def test_multiple_correction_comparison(self):
        """Compare different correction methods."""
        p_values = [0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.10]

        bonf = StatisticalValidator.bonferroni_correction(p_values)
        bh = StatisticalValidator.benjamini_hochberg_fdr(p_values)
        holm = StatisticalValidator.holm_bonferroni_correction(p_values)

        # BH (FDR) should generally be least conservative
        assert bh['n_significant'] >= holm['n_significant']
        assert holm['n_significant'] >= bonf['n_significant']


class TestHypothesisTests:
    """Test hypothesis testing methods."""

    def test_mann_whitney_u_test(self):
        """Test Mann-Whitney U test."""
        np.random.seed(42)
        group1 = np.random.normal(10, 2, 50)
        group2 = np.random.normal(12, 2, 50)

        result = StatisticalValidator.mann_whitney_u_test(group1, group2)

        # Check structure
        assert 'u_statistic' in result
        assert 'p_value' in result
        assert 'median1' in result
        assert 'median2' in result
        assert 'significance_label' in result

        # Groups have different medians, should be significant
        assert result['p_value'] < 0.05

    def test_mann_whitney_u_test_one_sided(self):
        """Test one-sided Mann-Whitney U test."""
        group1 = [1, 2, 3, 4, 5]
        group2 = [6, 7, 8, 9, 10]

        result = StatisticalValidator.mann_whitney_u_test(
            group1, group2, alternative='less'
        )

        # group1 < group2, should be highly significant
        assert result['p_value'] < 0.01

    def test_chi_square_test(self):
        """Test chi-square test of independence."""
        # Create contingency table with association
        contingency = [
            [40, 10],
            [10, 40]
        ]

        result = StatisticalValidator.chi_square_test(contingency)

        # Check structure
        assert 'chi2_statistic' in result
        assert 'p_value' in result
        assert 'degrees_of_freedom' in result
        assert 'expected_frequencies' in result
        assert 'cramers_v' in result

        # Should detect association
        assert result['p_value'] < 0.05
        assert result['cramers_v'] > 0.3

    def test_chi_square_test_no_association(self):
        """Test chi-square with no association."""
        contingency = [
            [25, 25],
            [25, 25]
        ]

        result = StatisticalValidator.chi_square_test(contingency)

        # Should not be significant
        assert result['p_value'] > 0.05
        assert result['cramers_v'] < 0.1


class TestStatisticalReports:
    """Test statistical report generation."""

    def test_generate_statistical_report_ttest(self):
        """Test report generation for t-test."""
        test_results = {
            't_statistic': 3.456,
            'p_value': 0.001,
            'significance_label': '***',
            'n_group1': 50,
            'n_group2': 50
        }

        report = StatisticalValidator.generate_statistical_report(
            test_type='t-test',
            test_results=test_results,
            effect_size=0.65,
            confidence_interval=(0.5, 1.2)
        )

        # Check report contains key information
        assert 'T-TEST' in report
        assert 't-statistic: 3.456' in report
        assert 'p-value: 0.001' in report
        assert 'HIGHLY SIGNIFICANT' in report
        assert 'Effect size: 0.65' in report
        assert 'Confidence interval' in report

    def test_generate_statistical_report_anova(self):
        """Test report generation for ANOVA."""
        test_results = {
            'f_statistic': 8.234,
            'p_value': 0.0003,
            'significance_label': '***',
            'n_groups': 3
        }

        report = StatisticalValidator.generate_statistical_report(
            test_type='anova',
            test_results=test_results,
            effect_size=0.12
        )

        # Check report contains ANOVA info
        assert 'ANOVA' in report
        assert 'F-statistic: 8.234' in report
        assert 'Number of groups: 3' in report

    def test_generate_statistical_report_chi_square(self):
        """Test report generation for chi-square."""
        test_results = {
            'chi2_statistic': 15.67,
            'p_value': 0.0001,
            'significance_label': '***'
        }

        report = StatisticalValidator.generate_statistical_report(
            test_type='chi-square',
            test_results=test_results
        )

        # Check report contains chi-square info
        assert 'CHI-SQUARE' in report
        assert 'χ² statistic: 15.67' in report


class TestAssumptionChecking:
    """Test statistical assumption checking."""

    def test_check_assumptions_normal_data(self):
        """Test assumption checking with normal data."""
        np.random.seed(42)
        data = np.random.normal(10, 2, 100)

        result = StatisticalValidator.check_assumptions(data, test_type='t-test')

        # Check structure
        assert 'normality_test' in result
        assert 'normality_assumption_met' in result
        assert 'warnings' in result
        assert 'sample_size' in result

        # Normal data should pass normality test
        assert result['normality_assumption_met'] is True
        assert result['sample_size'] == 100

    def test_check_assumptions_non_normal_data(self):
        """Test assumption checking with non-normal data."""
        np.random.seed(42)
        data = np.random.exponential(scale=2, size=100)

        result = StatisticalValidator.check_assumptions(data, test_type='t-test')

        # Exponential data should fail normality test
        assert result['normality_assumption_met'] is False
        assert len(result['warnings']) > 0
        assert any('Normality' in w for w in result['warnings'])

    def test_check_assumptions_small_sample(self):
        """Test assumption checking with small sample."""
        data = [1, 2, 3, 4, 5]

        result = StatisticalValidator.check_assumptions(data, test_type='t-test')

        # Should warn about small sample size
        assert any('small sample size' in w.lower() for w in result['warnings'])

    def test_check_assumptions_very_small_sample(self):
        """Test assumption checking with very small sample."""
        data = [1, 2]

        result = StatisticalValidator.check_assumptions(data)

        # Should indicate sample too small for normality test
        assert result['normality_assumption_met'] is None
        assert any('too small' in w.lower() for w in result['warnings'])


class TestStatisticalValidatorIntegration:
    """Integration tests for complete statistical workflows."""

    def test_complete_ttest_workflow(self):
        """Test complete t-test analysis workflow."""
        np.random.seed(42)
        group1 = np.random.normal(100, 15, 60)
        group2 = np.random.normal(110, 15, 60)

        # Check assumptions
        assumptions = StatisticalValidator.check_assumptions(
            np.concatenate([group1, group2])
        )

        # Calculate effect size
        cohens_d = StatisticalValidator.calculate_cohens_d(group1, group2)

        # Get confidence interval for difference
        diff = group1 - group2[:len(group1)]
        ci = StatisticalValidator.parametric_confidence_interval(diff)

        # Perform t-test (using scipy for full test)
        t_stat, p_value = scipy_stats.ttest_ind(group1, group2)
        test_results = {
            't_statistic': t_stat,
            'p_value': p_value,
            **StatisticalValidator.apply_significance_threshold(p_value),
            'n_group1': len(group1),
            'n_group2': len(group2)
        }

        # Generate report
        report = StatisticalValidator.generate_statistical_report(
            test_type='t-test',
            test_results=test_results,
            effect_size=cohens_d,
            confidence_interval=ci
        )

        # Verify workflow
        assert assumptions['normality_assumption_met'] is True
        assert abs(cohens_d) > 0.4  # Medium to large effect
        assert test_results['p_value'] < 0.05
        assert 'SIGNIFICANT' in report

    def test_complete_multiple_comparison_workflow(self):
        """Test workflow with multiple comparisons and correction."""
        np.random.seed(42)

        # Generate 10 comparisons, 3 with real effects
        p_values = []
        for i in range(10):
            if i < 3:
                # Real effect
                group1 = np.random.normal(10, 2, 30)
                group2 = np.random.normal(12, 2, 30)
            else:
                # No effect
                group1 = np.random.normal(10, 2, 30)
                group2 = np.random.normal(10, 2, 30)

            _, p = scipy_stats.ttest_ind(group1, group2)
            p_values.append(p)

        # Apply corrections
        bonf = StatisticalValidator.bonferroni_correction(p_values, alpha=0.05)
        bh = StatisticalValidator.benjamini_hochberg_fdr(p_values, alpha=0.05)

        # BH should detect more true positives
        assert bh['n_significant'] >= bonf['n_significant']

        # At least some should be significant (the 3 with real effects)
        assert bh['n_significant'] > 0
