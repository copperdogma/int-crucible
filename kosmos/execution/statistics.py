"""
Statistical validation and hypothesis testing.

This module provides comprehensive statistical testing, effect size calculation,
confidence intervals, and multiple testing correction.

Based on kosmos-figures patterns and standard statistical practices.
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


class StatisticalValidator:
    """
    Statistical validation methods from kosmos-figures.

    Provides:
    - Hypothesis testing (t-test, ANOVA, chi-square, Mann-Whitney)
    - P-value calculation and interpretation
    - Confidence intervals (parametric and bootstrap)
    - Effect size calculation
    - Multiple testing correction
    - Statistical report generation
    """

    @staticmethod
    def apply_significance_threshold(p_value: float) -> Dict[str, Any]:
        """
        Standard significance thresholding from kosmos-figures.

        Args:
            p_value: P-value to threshold

        Returns:
            Dictionary with:
                - p_value: Original p-value
                - significant_0.05: Boolean, p < 0.05
                - significant_0.01: Boolean, p < 0.01
                - significant_0.001: Boolean, p < 0.001
                - significance_label: '***', '**', '*', or 'ns'
        """
        return {
            'p_value': float(p_value),
            'significant_0.05': bool(p_value < 0.05),
            'significant_0.01': bool(p_value < 0.01),
            'significant_0.001': bool(p_value < 0.001),
            'significance_label': (
                '***' if p_value < 0.001 else
                '**' if p_value < 0.01 else
                '*' if p_value < 0.05 else
                'ns'
            )
        }

    @staticmethod
    def calculate_cohens_d(
        group1: Union[np.ndarray, List[float]],
        group2: Union[np.ndarray, List[float]]
    ) -> float:
        """
        Calculate Cohen's d effect size for two groups.

        Args:
            group1: First group data
            group2: Second group data

        Returns:
            Cohen's d effect size

        Interpretation:
            - Small: d = 0.2
            - Medium: d = 0.5
            - Large: d = 0.8
        """
        group1 = np.array(group1)
        group2 = np.array(group2)

        mean_diff = np.mean(group1) - np.mean(group2)

        # Pooled standard deviation
        n1, n2 = len(group1), len(group2)
        var1 = np.var(group1, ddof=1)
        var2 = np.var(group2, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        return mean_diff / pooled_std

    @staticmethod
    def calculate_eta_squared(
        groups: List[Union[np.ndarray, List[float]]]
    ) -> float:
        """
        Calculate eta-squared (η²) effect size for ANOVA.

        Args:
            groups: List of group data arrays

        Returns:
            Eta-squared effect size

        Interpretation:
            - Small: η² = 0.01
            - Medium: η² = 0.06
            - Large: η² = 0.14
        """
        groups = [np.array(g) for g in groups]

        # Grand mean
        all_data = np.concatenate(groups)
        grand_mean = np.mean(all_data)

        # Sum of squares between groups
        ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)

        # Total sum of squares
        ss_total = np.sum((all_data - grand_mean) ** 2)

        if ss_total == 0:
            return 0.0

        return ss_between / ss_total

    @staticmethod
    def calculate_cramers_v(
        contingency_table: Union[np.ndarray, List[List[int]]]
    ) -> float:
        """
        Calculate Cramér's V effect size for chi-square test.

        Args:
            contingency_table: 2D contingency table

        Returns:
            Cramér's V effect size

        Interpretation (for df=1):
            - Small: V = 0.1
            - Medium: V = 0.3
            - Large: V = 0.5
        """
        contingency_table = np.array(contingency_table)

        # Chi-square statistic
        chi2 = stats.chi2_contingency(contingency_table)[0]

        # Total sample size
        n = np.sum(contingency_table)

        # Min dimension
        k = min(contingency_table.shape) - 1

        if n == 0 or k == 0:
            return 0.0

        return np.sqrt(chi2 / (n * k))

    @staticmethod
    def interpret_effect_size(
        effect_size: float,
        measure: str
    ) -> str:
        """
        Interpret effect size magnitude.

        Args:
            effect_size: Effect size value
            measure: Type of measure ('cohens_d', 'eta_squared', 'cramers_v')

        Returns:
            Interpretation string ('small', 'medium', 'large', 'negligible')
        """
        effect_size = abs(effect_size)

        if measure == 'cohens_d':
            if effect_size < 0.2:
                return 'negligible'
            elif effect_size < 0.5:
                return 'small'
            elif effect_size < 0.8:
                return 'medium'
            else:
                return 'large'

        elif measure == 'eta_squared':
            if effect_size < 0.01:
                return 'negligible'
            elif effect_size < 0.06:
                return 'small'
            elif effect_size < 0.14:
                return 'medium'
            else:
                return 'large'

        elif measure == 'cramers_v':
            if effect_size < 0.1:
                return 'negligible'
            elif effect_size < 0.3:
                return 'small'
            elif effect_size < 0.5:
                return 'medium'
            else:
                return 'large'

        else:
            return 'unknown'

    @staticmethod
    def parametric_confidence_interval(
        data: Union[np.ndarray, List[float]],
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate parametric confidence interval for mean.

        Args:
            data: Sample data
            confidence: Confidence level (default 0.95 for 95% CI)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        data = np.array(data)
        n = len(data)
        mean = np.mean(data)
        se = stats.sem(data)

        # t-distribution critical value
        alpha = 1 - confidence
        t_crit = stats.t.ppf(1 - alpha/2, df=n-1)

        margin_of_error = t_crit * se

        return (mean - margin_of_error, mean + margin_of_error)

    @staticmethod
    def bootstrap_confidence_interval(
        data: Union[np.ndarray, List[float]],
        confidence: float = 0.95,
        n_iterations: int = 10000,
        statistic: str = 'mean'
    ) -> Tuple[float, float]:
        """
        Calculate bootstrap confidence interval.

        Args:
            data: Sample data
            confidence: Confidence level (default 0.95)
            n_iterations: Number of bootstrap samples
            statistic: Statistic to compute ('mean', 'median', 'std')

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        data = np.array(data)
        n = len(data)

        # Statistic function
        if statistic == 'mean':
            stat_func = np.mean
        elif statistic == 'median':
            stat_func = np.median
        elif statistic == 'std':
            stat_func = np.std
        else:
            raise ValueError(f"Unknown statistic '{statistic}'. Use 'mean', 'median', or 'std'")

        # Bootstrap sampling
        np.random.seed(42)
        bootstrap_stats = []
        for _ in range(n_iterations):
            sample = np.random.choice(data, size=n, replace=True)
            bootstrap_stats.append(stat_func(sample))

        # Percentile method
        alpha = 1 - confidence
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        lower_bound = np.percentile(bootstrap_stats, lower_percentile)
        upper_bound = np.percentile(bootstrap_stats, upper_percentile)

        return (float(lower_bound), float(upper_bound))

    @staticmethod
    def bonferroni_correction(
        p_values: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Apply Bonferroni correction for multiple comparisons.

        Args:
            p_values: List of p-values to correct
            alpha: Family-wise error rate (default 0.05)

        Returns:
            Dictionary with:
                - corrected_alpha: Adjusted significance threshold
                - significant: List of booleans indicating significance
                - n_tests: Number of tests
                - n_significant: Number of significant tests after correction
        """
        n_tests = len(p_values)
        corrected_alpha = alpha / n_tests

        significant = [p < corrected_alpha for p in p_values]

        return {
            'corrected_alpha': corrected_alpha,
            'significant': significant,
            'n_tests': n_tests,
            'n_significant': sum(significant),
            'method': 'bonferroni'
        }

    @staticmethod
    def benjamini_hochberg_fdr(
        p_values: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Apply Benjamini-Hochberg FDR correction.

        Args:
            p_values: List of p-values to correct
            alpha: False discovery rate (default 0.05)

        Returns:
            Dictionary with:
                - significant: List of booleans indicating significance
                - adjusted_p_values: FDR-adjusted p-values
                - n_tests: Number of tests
                - n_significant: Number of significant tests after correction
        """
        n_tests = len(p_values)

        # Sort p-values with original indices
        sorted_indices = np.argsort(p_values)
        sorted_p_values = np.array(p_values)[sorted_indices]

        # BH procedure
        significant = np.zeros(n_tests, dtype=bool)
        for i in range(n_tests - 1, -1, -1):
            critical_value = (i + 1) / n_tests * alpha
            if sorted_p_values[i] <= critical_value:
                significant[sorted_indices[:(i+1)]] = True
                break

        # Adjusted p-values
        adjusted_p_values = np.zeros(n_tests)
        for i in range(n_tests):
            adjusted_p_values[sorted_indices[i]] = min(
                sorted_p_values[i] * n_tests / (i + 1),
                1.0
            )

        return {
            'significant': significant.tolist(),
            'adjusted_p_values': adjusted_p_values.tolist(),
            'n_tests': n_tests,
            'n_significant': int(np.sum(significant)),
            'method': 'benjamini_hochberg'
        }

    @staticmethod
    def holm_bonferroni_correction(
        p_values: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Apply Holm-Bonferroni step-down correction.

        Args:
            p_values: List of p-values to correct
            alpha: Family-wise error rate (default 0.05)

        Returns:
            Dictionary with:
                - significant: List of booleans indicating significance
                - n_tests: Number of tests
                - n_significant: Number of significant tests after correction
        """
        n_tests = len(p_values)

        # Sort p-values with original indices
        sorted_indices = np.argsort(p_values)
        sorted_p_values = np.array(p_values)[sorted_indices]

        # Holm-Bonferroni procedure
        significant = np.zeros(n_tests, dtype=bool)
        for i in range(n_tests):
            critical_value = alpha / (n_tests - i)
            if sorted_p_values[i] <= critical_value:
                significant[sorted_indices[i]] = True
            else:
                # Stop at first non-significant test
                break

        return {
            'significant': significant.tolist(),
            'n_tests': n_tests,
            'n_significant': int(np.sum(significant)),
            'method': 'holm_bonferroni'
        }

    @staticmethod
    def mann_whitney_u_test(
        group1: Union[np.ndarray, List[float]],
        group2: Union[np.ndarray, List[float]],
        alternative: str = 'two-sided'
    ) -> Dict[str, Any]:
        """
        Perform Mann-Whitney U test (non-parametric alternative to t-test).

        Args:
            group1: First group data
            group2: Second group data
            alternative: 'two-sided', 'less', or 'greater'

        Returns:
            Dictionary with:
                - u_statistic: Mann-Whitney U statistic
                - p_value: P-value
                - significant_0.05: Boolean
                - significance_label: '***', '**', '*', or 'ns'
                - median1: Median of group1
                - median2: Median of group2
        """
        group1 = np.array(group1)
        group2 = np.array(group2)

        u_stat, p_value = stats.mannwhitneyu(
            group1, group2,
            alternative=alternative
        )

        sig_result = StatisticalValidator.apply_significance_threshold(p_value)

        return {
            'u_statistic': float(u_stat),
            'p_value': float(p_value),
            **sig_result,
            'median1': float(np.median(group1)),
            'median2': float(np.median(group2)),
            'n_group1': len(group1),
            'n_group2': len(group2)
        }

    @staticmethod
    def chi_square_test(
        contingency_table: Union[np.ndarray, List[List[int]]]
    ) -> Dict[str, Any]:
        """
        Perform chi-square test of independence.

        Args:
            contingency_table: 2D contingency table

        Returns:
            Dictionary with:
                - chi2_statistic: Chi-square statistic
                - p_value: P-value
                - degrees_of_freedom: Degrees of freedom
                - expected_frequencies: Expected frequencies under null
                - cramers_v: Effect size
                - significant_0.05: Boolean
                - significance_label: '***', '**', '*', or 'ns'
        """
        contingency_table = np.array(contingency_table)

        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

        cramers_v = StatisticalValidator.calculate_cramers_v(contingency_table)
        sig_result = StatisticalValidator.apply_significance_threshold(p_value)

        return {
            'chi2_statistic': float(chi2),
            'p_value': float(p_value),
            'degrees_of_freedom': int(dof),
            'expected_frequencies': expected.tolist(),
            'cramers_v': float(cramers_v),
            **sig_result
        }

    @staticmethod
    def generate_statistical_report(
        test_type: str,
        test_results: Dict[str, Any],
        effect_size: Optional[float] = None,
        confidence_interval: Optional[Tuple[float, float]] = None
    ) -> str:
        """
        Generate comprehensive statistical report.

        Args:
            test_type: Type of test ('t-test', 'anova', 'chi-square', 'mann-whitney')
            test_results: Results dictionary from statistical test
            effect_size: Optional effect size value
            confidence_interval: Optional (lower, upper) confidence interval

        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append(f"STATISTICAL TEST REPORT: {test_type.upper()}")
        report_lines.append("=" * 60)
        report_lines.append("")

        # Test results
        if 't_statistic' in test_results:
            report_lines.append(f"t-statistic: {test_results['t_statistic']:.4f}")
        if 'f_statistic' in test_results:
            report_lines.append(f"F-statistic: {test_results['f_statistic']:.4f}")
        if 'u_statistic' in test_results:
            report_lines.append(f"U-statistic: {test_results['u_statistic']:.4f}")
        if 'chi2_statistic' in test_results:
            report_lines.append(f"χ² statistic: {test_results['chi2_statistic']:.4f}")

        # P-value
        p_value = test_results.get('p_value', 0)
        report_lines.append(f"p-value: {p_value:.6f}")

        # Significance
        sig_label = test_results.get('significance_label', 'ns')
        if sig_label == '***':
            sig_text = "HIGHLY SIGNIFICANT (p < 0.001)"
        elif sig_label == '**':
            sig_text = "VERY SIGNIFICANT (p < 0.01)"
        elif sig_label == '*':
            sig_text = "SIGNIFICANT (p < 0.05)"
        else:
            sig_text = "NOT SIGNIFICANT (p ≥ 0.05)"

        report_lines.append(f"Significance: {sig_text} {sig_label}")
        report_lines.append("")

        # Effect size
        if effect_size is not None:
            report_lines.append(f"Effect size: {effect_size:.4f}")

            # Determine measure type
            if 'cohens_d' in str(test_type).lower():
                interpretation = StatisticalValidator.interpret_effect_size(effect_size, 'cohens_d')
            elif 'anova' in str(test_type).lower():
                interpretation = StatisticalValidator.interpret_effect_size(effect_size, 'eta_squared')
            elif 'chi' in str(test_type).lower():
                interpretation = StatisticalValidator.interpret_effect_size(effect_size, 'cramers_v')
            else:
                interpretation = 'unknown'

            report_lines.append(f"Effect magnitude: {interpretation.upper()}")
            report_lines.append("")

        # Confidence interval
        if confidence_interval is not None:
            lower, upper = confidence_interval
            report_lines.append(f"Confidence interval: [{lower:.4f}, {upper:.4f}]")
            report_lines.append("")

        # Sample sizes
        if 'n_group1' in test_results and 'n_group2' in test_results:
            report_lines.append(f"Sample size (group 1): {test_results['n_group1']}")
            report_lines.append(f"Sample size (group 2): {test_results['n_group2']}")

        if 'n_groups' in test_results:
            report_lines.append(f"Number of groups: {test_results['n_groups']}")

        report_lines.append("")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    @staticmethod
    def check_assumptions(
        data: Union[np.ndarray, List[float]],
        test_type: str = 't-test'
    ) -> Dict[str, Any]:
        """
        Check statistical test assumptions.

        Args:
            data: Sample data
            test_type: Type of test ('t-test', 'anova')

        Returns:
            Dictionary with:
                - normality_test: Shapiro-Wilk test results
                - normality_assumption_met: Boolean
                - warnings: List of assumption violations
        """
        data = np.array(data)
        warnings_list = []

        # Normality test (Shapiro-Wilk)
        if len(data) >= 3:
            shapiro_stat, shapiro_p = stats.shapiro(data)
            normality_met = shapiro_p > 0.05
        else:
            shapiro_stat, shapiro_p = None, None
            normality_met = None
            warnings_list.append("Sample size too small for normality test")

        if normality_met is False:
            warnings_list.append(
                f"Normality assumption violated (Shapiro-Wilk p={shapiro_p:.4f}). "
                "Consider non-parametric alternative."
            )

        # Sample size check
        if test_type in ['t-test', 'anova']:
            if len(data) < 30:
                warnings_list.append(
                    f"Small sample size (n={len(data)}). "
                    "Results may not be reliable. Consider n ≥ 30."
                )

        return {
            'normality_test': {
                'statistic': float(shapiro_stat) if shapiro_stat is not None else None,
                'p_value': float(shapiro_p) if shapiro_p is not None else None
            },
            'normality_assumption_met': normality_met,
            'warnings': warnings_list,
            'sample_size': len(data)
        }
