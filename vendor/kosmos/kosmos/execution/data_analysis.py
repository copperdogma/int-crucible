"""
Data analysis pipeline implementing proven patterns from kosmos-figures.

This module provides the DataAnalyzer class with statistical analysis methods
extracted directly from kosmos-figures repository analysis scripts.

References:
- Figure 2 (hypothermia_nucleotide_salvage): T-test comparison pattern
- Figure 3 (perovskite_solar_cell): Correlation analysis pattern
- Figure 4 (neural_network): Log-log scaling analysis pattern
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
from pathlib import Path
import warnings

# Suppress scientific computation warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """
    Reusable analysis methods extracted from kosmos-figures.

    Implements proven statistical patterns:
    - T-test comparison (group mean differences)
    - Correlation analysis (Pearson and Spearman)
    - Linear regression with significance testing
    - Log-log scaling analysis for power laws
    """

    def __init__(self):
        """Initialize DataAnalyzer."""
        self.results_cache = {}

    @staticmethod
    def ttest_comparison(
        data: pd.DataFrame,
        group_col: str,
        measure_col: str,
        groups: Tuple[str, str],
        log_transform: bool = False
    ) -> Dict[str, Any]:
        """
        Perform t-test comparison between two groups.

        Pattern from: Figure_2_hypothermia_nucleotide_salvage

        Args:
            data: DataFrame with group assignments and measurements
            group_col: Column name containing group labels
            measure_col: Column name containing measurements to compare
            groups: Tuple of (group1_label, group2_label) to compare
            log_transform: If True, apply log2 transformation before comparison

        Returns:
            Dictionary with:
                - t_statistic: T-test statistic
                - p_value: P-value for the test
                - group1_mean: Mean of group 1
                - group2_mean: Mean of group 2
                - group1_std: Standard deviation of group 1
                - group2_std: Standard deviation of group 2
                - mean_difference: group1_mean - group2_mean
                - log2_fold_change: log2(group1_mean / group2_mean)
                - significant_0.05: Boolean, p < 0.05
                - significant_0.01: Boolean, p < 0.01
                - significant_0.001: Boolean, p < 0.001
                - significance_label: '***', '**', '*', or 'ns'
                - n_group1: Sample size group 1
                - n_group2: Sample size group 2

        Example:
            >>> df = pd.DataFrame({
            ...     'treatment': ['control']*30 + ['experimental']*30,
            ...     'score': np.concatenate([np.random.normal(10, 2, 30),
            ...                              np.random.normal(12, 2, 30)])
            ... })
            >>> result = DataAnalyzer.ttest_comparison(
            ...     df, 'treatment', 'score', ('experimental', 'control')
            ... )
            >>> print(f"P-value: {result['p_value']:.4f}")
        """
        # Extract group data
        group1_data = data[data[group_col] == groups[0]][measure_col].dropna()
        group2_data = data[data[group_col] == groups[1]][measure_col].dropna()

        # Validate data
        if len(group1_data) == 0 or len(group2_data) == 0:
            raise ValueError(f"One or both groups have no data. "
                           f"Group '{groups[0]}': {len(group1_data)} samples, "
                           f"Group '{groups[1]}': {len(group2_data)} samples")

        # Log transformation if requested (kosmos-figures Figure 2 pattern)
        if log_transform:
            # Add 1 to avoid log(0)
            group1_data = np.log2(group1_data + 1)
            group2_data = np.log2(group2_data + 1)

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(group1_data, group2_data)

        # Calculate statistics
        group1_mean = np.mean(group1_data)
        group2_mean = np.mean(group2_data)
        mean_diff = group1_mean - group2_mean

        # Log2 fold change (handle division by zero)
        if group2_mean != 0:
            log2_fc = np.log2(group1_mean / group2_mean) if group1_mean > 0 and group2_mean > 0 else np.nan
        else:
            log2_fc = np.nan

        # Significance thresholds (kosmos-figures standard)
        sig_0_05 = p_value < 0.05
        sig_0_01 = p_value < 0.01
        sig_0_001 = p_value < 0.001

        # Significance label
        if sig_0_001:
            sig_label = "***"
        elif sig_0_01:
            sig_label = "**"
        elif sig_0_05:
            sig_label = "*"
        else:
            sig_label = "ns"

        return {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'group1_mean': float(group1_mean),
            'group2_mean': float(group2_mean),
            'group1_std': float(np.std(group1_data, ddof=1)),
            'group2_std': float(np.std(group2_data, ddof=1)),
            'mean_difference': float(mean_diff),
            'log2_fold_change': float(log2_fc) if not np.isnan(log2_fc) else None,
            'significant_0.05': bool(sig_0_05),
            'significant_0.01': bool(sig_0_01),
            'significant_0.001': bool(sig_0_001),
            'significance_label': sig_label,
            'n_group1': int(len(group1_data)),
            'n_group2': int(len(group2_data))
        }

    @staticmethod
    def correlation_analysis(
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        method: str = 'pearson'
    ) -> Dict[str, Any]:
        """
        Perform correlation analysis with linear regression.

        Pattern from: Figure_3_perovskite_solar_cell

        Args:
            data: DataFrame with variables to correlate
            x_col: Column name for x variable
            y_col: Column name for y variable
            method: 'pearson' or 'spearman' correlation

        Returns:
            Dictionary with:
                - correlation: Correlation coefficient
                - p_value: P-value for correlation test
                - r_squared: Coefficient of determination (R²)
                - slope: Linear regression slope
                - intercept: Linear regression intercept
                - std_err: Standard error of the regression
                - significance: '***', '**', '*', or 'ns'
                - n_samples: Number of samples used
                - equation: Regression equation string

        Example:
            >>> df = pd.DataFrame({
            ...     'x': np.random.randn(100),
            ...     'y': np.random.randn(100)
            ... })
            >>> result = DataAnalyzer.correlation_analysis(df, 'x', 'y')
            >>> print(f"r = {result['correlation']:.3f}, p = {result['p_value']:.4f}")
        """
        # Remove missing values (kosmos-figures pattern)
        df_clean = data[[x_col, y_col]].dropna()

        if len(df_clean) < 3:
            raise ValueError(f"Insufficient data after removing NaN values. "
                           f"Need at least 3 samples, got {len(df_clean)}")

        x = df_clean[x_col].values
        y = df_clean[y_col].values

        # Correlation
        if method == 'pearson':
            corr, p_val = stats.pearsonr(x, y)
        elif method == 'spearman':
            corr, p_val = stats.spearmanr(x, y)
        else:
            raise ValueError(f"Unknown method '{method}'. Use 'pearson' or 'spearman'")

        # Linear regression (always use for equation regardless of correlation method)
        slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)

        # Significance label (kosmos-figures pattern)
        if p_val < 0.001:
            significance = "***"
        elif p_val < 0.01:
            significance = "**"
        elif p_val < 0.05:
            significance = "*"
        else:
            significance = "ns"

        # Regression equation
        sign = "+" if intercept >= 0 else ""
        equation = f"y = {slope:.4f}x {sign}{intercept:.4f}"

        return {
            'correlation': float(corr),
            'p_value': float(p_val),
            'r_squared': float(r_value ** 2),
            'slope': float(slope),
            'intercept': float(intercept),
            'std_err': float(std_err),
            'significance': significance,
            'n_samples': int(len(x)),
            'equation': equation,
            'method': method
        }

    @staticmethod
    def log_log_scaling_analysis(
        data: pd.DataFrame,
        x_col: str,
        y_col: str
    ) -> Dict[str, Any]:
        """
        Analyze scaling relationships on log-log scale.

        Pattern from: Figure_4_neural_network (connectomics scaling laws)

        Fits a power law: y = a * x^b

        Args:
            data: DataFrame with variables to analyze
            x_col: Column name for x variable
            y_col: Column name for y variable

        Returns:
            Dictionary with:
                - spearman_rho: Spearman correlation coefficient
                - p_value: P-value for Spearman correlation
                - power_law_exponent: Exponent b in y = a * x^b
                - power_law_coefficient: Coefficient a in y = a * x^b
                - r_squared: R² of log-log linear fit
                - equation: Power law equation string
                - n_samples: Number of samples used
                - log_log_slope: Slope of log-log regression
                - log_log_intercept: Intercept of log-log regression

        Example:
            >>> df = pd.DataFrame({
            ...     'length': np.random.uniform(1, 100, 100),
            ...     'synapses': np.random.uniform(1, 100, 100)
            ... })
            >>> result = DataAnalyzer.log_log_scaling_analysis(df, 'length', 'synapses')
            >>> print(result['equation'])
        """
        # Clean data - remove NaN and non-positive values (kosmos-figures pattern)
        df_clean = data[[x_col, y_col]].dropna()
        df_clean = df_clean[(df_clean[x_col] > 0) & (df_clean[y_col] > 0)]

        if len(df_clean) < 3:
            raise ValueError(f"Insufficient positive data for log-log analysis. "
                           f"Need at least 3 positive samples, got {len(df_clean)}")

        x = df_clean[x_col].values
        y = df_clean[y_col].values

        # Log-transform
        log_x = np.log10(x)
        log_y = np.log10(y)

        # Spearman correlation (non-parametric, kosmos-figures standard)
        rho, p_value = stats.spearmanr(x, y)

        # Linear fit on log-log scale: log(y) = log(a) + b*log(x)
        # This gives power law: y = a * x^b
        slope, intercept, r_value, p_value_reg, std_err = stats.linregress(log_x, log_y)

        # Convert back to power law parameters
        # log(y) = log(a) + b*log(x)  =>  y = 10^intercept * x^slope
        a = 10 ** intercept  # power_law_coefficient
        b = slope  # power_law_exponent

        # Power law equation
        equation = f"y = {a:.3f} * x^{b:.3f}"

        return {
            'spearman_rho': float(rho),
            'p_value': float(p_value),
            'power_law_exponent': float(b),
            'power_law_coefficient': float(a),
            'r_squared': float(r_value ** 2),
            'equation': equation,
            'n_samples': int(len(x)),
            'log_log_slope': float(slope),
            'log_log_intercept': float(intercept)
        }

    @staticmethod
    def anova_comparison(
        data: pd.DataFrame,
        group_col: str,
        measure_col: str,
        groups: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform one-way ANOVA for multiple group comparison.

        Args:
            data: DataFrame with group assignments and measurements
            group_col: Column name containing group labels
            measure_col: Column name containing measurements to compare
            groups: Optional list of specific groups to compare (default: all unique groups)

        Returns:
            Dictionary with:
                - f_statistic: F-statistic
                - p_value: P-value for ANOVA
                - group_means: Dict of {group: mean} for each group
                - group_stds: Dict of {group: std} for each group
                - group_sizes: Dict of {group: n} for each group
                - significant_0.05: Boolean, p < 0.05
                - eta_squared: Effect size (η²)
                - between_group_variance: Variance between groups
                - within_group_variance: Variance within groups
        """
        # Filter groups if specified
        if groups is not None:
            data = data[data[group_col].isin(groups)]

        # Get unique groups
        unique_groups = data[group_col].unique()

        if len(unique_groups) < 2:
            raise ValueError(f"Need at least 2 groups for ANOVA, got {len(unique_groups)}")

        # Prepare data for each group
        group_data = [data[data[group_col] == g][measure_col].dropna() for g in unique_groups]

        # Validate all groups have data
        for i, gd in enumerate(group_data):
            if len(gd) == 0:
                raise ValueError(f"Group '{unique_groups[i]}' has no data")

        # Perform one-way ANOVA
        f_stat, p_value = stats.f_oneway(*group_data)

        # Calculate group statistics
        group_means = {str(g): float(np.mean(gd)) for g, gd in zip(unique_groups, group_data)}
        group_stds = {str(g): float(np.std(gd, ddof=1)) for g, gd in zip(unique_groups, group_data)}
        group_sizes = {str(g): int(len(gd)) for g, gd in zip(unique_groups, group_data)}

        # Calculate effect size (eta-squared)
        grand_mean = np.mean(np.concatenate(group_data))
        ss_between = sum(len(gd) * (np.mean(gd) - grand_mean) ** 2 for gd in group_data)
        ss_total = sum((x - grand_mean) ** 2 for gd in group_data for x in gd)
        eta_squared = ss_between / ss_total if ss_total > 0 else 0

        # Variance components
        between_var = np.var([np.mean(gd) for gd in group_data], ddof=1)
        within_var = np.mean([np.var(gd, ddof=1) for gd in group_data])

        return {
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            'group_means': group_means,
            'group_stds': group_stds,
            'group_sizes': group_sizes,
            'significant_0.05': bool(p_value < 0.05),
            'significant_0.01': bool(p_value < 0.01),
            'eta_squared': float(eta_squared),
            'between_group_variance': float(between_var),
            'within_group_variance': float(within_var),
            'n_groups': int(len(unique_groups))
        }


class DataLoader:
    """
    Utility class for loading data from various formats.

    Supports CSV, Excel, JSON with automatic type detection and validation.
    """

    @staticmethod
    def load_csv(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        Load CSV file with pandas.

        Args:
            file_path: Path to CSV file
            **kwargs: Additional arguments to pass to pd.read_csv()

        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Loading CSV from {file_path}")
        df = pd.read_csv(file_path, **kwargs)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df

    @staticmethod
    def load_excel(file_path: Union[str, Path], sheet_name: Union[str, int] = 0, **kwargs) -> pd.DataFrame:
        """
        Load Excel file with pandas.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name or index to load
            **kwargs: Additional arguments to pass to pd.read_excel()

        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Loading Excel from {file_path}, sheet: {sheet_name}")
        df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df

    @staticmethod
    def load_json(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        Load JSON file with pandas.

        Args:
            file_path: Path to JSON file
            **kwargs: Additional arguments to pass to pd.read_json()

        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Loading JSON from {file_path}")
        df = pd.read_json(file_path, **kwargs)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df

    @staticmethod
    def load_data(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        Auto-detect file type and load data.

        Args:
            file_path: Path to data file
            **kwargs: Additional arguments to pass to loader

        Returns:
            DataFrame with loaded data

        Raises:
            ValueError: If file type is not supported
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == '.csv':
            return DataLoader.load_csv(file_path, **kwargs)
        elif suffix in ['.xlsx', '.xls']:
            return DataLoader.load_excel(file_path, **kwargs)
        elif suffix == '.json':
            return DataLoader.load_json(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file type: {suffix}. "
                           f"Supported: .csv, .xlsx, .xls, .json")


class DataCleaner:
    """
    Utility class for data cleaning and preprocessing.

    Implements common data cleaning patterns from kosmos-figures.
    """

    @staticmethod
    def remove_missing(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove rows with missing values.

        Args:
            df: DataFrame to clean
            subset: Optional list of columns to check for NaN (default: all columns)

        Returns:
            DataFrame with missing values removed
        """
        initial_rows = len(df)
        df_clean = df.dropna(subset=subset)
        removed = initial_rows - len(df_clean)

        if removed > 0:
            logger.info(f"Removed {removed} rows with missing values ({removed/initial_rows*100:.1f}%)")

        return df_clean

    @staticmethod
    def filter_positive(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Filter to keep only rows where specified columns have positive values.

        Pattern from: Figure_4_neural_network (log-log analysis requires positive values)

        Args:
            df: DataFrame to filter
            columns: Columns that must be positive

        Returns:
            DataFrame with only positive values in specified columns
        """
        initial_rows = len(df)

        for col in columns:
            df = df[df[col] > 0]

        removed = initial_rows - len(df)
        if removed > 0:
            logger.info(f"Removed {removed} rows with non-positive values in {columns} "
                       f"({removed/initial_rows*100:.1f}%)")

        return df

    @staticmethod
    def remove_outliers(
        df: pd.DataFrame,
        column: str,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """
        Remove outliers using IQR or Z-score method.

        Args:
            df: DataFrame to clean
            column: Column to check for outliers
            method: 'iqr' (interquartile range) or 'zscore'
            threshold: IQR multiplier (default 1.5) or Z-score threshold (default 1.5)

        Returns:
            DataFrame with outliers removed
        """
        initial_rows = len(df)

        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df_clean = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(df[column]))
            df_clean = df[z_scores < threshold]

        else:
            raise ValueError(f"Unknown method '{method}'. Use 'iqr' or 'zscore'")

        removed = initial_rows - len(df_clean)
        if removed > 0:
            logger.info(f"Removed {removed} outliers from '{column}' using {method} "
                       f"({removed/initial_rows*100:.1f}%)")

        return df_clean

    @staticmethod
    def normalize(df: pd.DataFrame, columns: List[str], method: str = 'zscore') -> pd.DataFrame:
        """
        Normalize specified columns.

        Args:
            df: DataFrame to normalize
            columns: Columns to normalize
            method: 'zscore' (standardize) or 'minmax' (scale to 0-1)

        Returns:
            DataFrame with normalized columns
        """
        df_normalized = df.copy()

        for col in columns:
            if method == 'zscore':
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    df_normalized[col] = (df[col] - mean) / std
                else:
                    logger.warning(f"Column '{col}' has zero variance, skipping normalization")

            elif method == 'minmax':
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val > min_val:
                    df_normalized[col] = (df[col] - min_val) / (max_val - min_val)
                else:
                    logger.warning(f"Column '{col}' has constant value, skipping normalization")

            else:
                raise ValueError(f"Unknown method '{method}'. Use 'zscore' or 'minmax'")

        return df_normalized
