"""
Neuroscience Domain - Connectomics Analysis

Analyzes neural network connectivity and scaling laws across species:
- Power law scaling relationships
- Cross-species comparisons
- Network topology analysis

Based on kosmos-figures Figure 4 pattern.

Example usage:
    # Analyze connectome scaling
    analyzer = ConnectomicsAnalyzer()

    # Single species analysis
    results = analyzer.analyze_scaling_laws(connectome_df)
    print(f"Length-Synapses exponent: {results.length_synapses.exponent:.3f}")

    # Cross-species comparison
    datasets = {
        'Celegans': celegans_df,
        'FlyWire': flywire_df,
        'H01': human_df
    }
    comparison = analyzer.cross_species_comparison(datasets)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, linregress
from pydantic import BaseModel, Field


# Data models for analysis results

@dataclass
class PowerLawFit:
    """Power law relationship: y = coefficient * x^exponent"""
    exponent: float  # b in y = a * x^b
    coefficient: float  # a in y = a * x^b
    r_squared: float  # Goodness of fit
    equation: str  # Human-readable equation


@dataclass
class ScalingRelationship:
    """Scaling relationship between two connectome properties"""
    x_variable: str  # e.g., "Length"
    y_variable: str  # e.g., "Synapses"
    spearman_rho: float  # Spearman correlation coefficient
    p_value: float  # Statistical significance
    power_law: PowerLawFit  # Power law fit parameters
    n_neurons: int  # Sample size

    @property
    def is_significant(self) -> bool:
        """Check if correlation is statistically significant (p < 0.05)"""
        return self.p_value < 0.05

    @property
    def correlation_strength(self) -> str:
        """Interpret correlation strength"""
        rho_abs = abs(self.spearman_rho)
        if rho_abs >= 0.8:
            return "very strong"
        elif rho_abs >= 0.6:
            return "strong"
        elif rho_abs >= 0.4:
            return "moderate"
        elif rho_abs >= 0.2:
            return "weak"
        else:
            return "very weak"


@dataclass
class ConnectomicsResult:
    """Complete connectomics analysis results for a single species"""
    species_name: str
    n_neurons: int
    n_synapses: Optional[int] = None

    # Scaling relationships
    length_synapses: Optional[ScalingRelationship] = None
    synapses_degree: Optional[ScalingRelationship] = None
    length_degree: Optional[ScalingRelationship] = None

    # Raw data statistics
    mean_length: Optional[float] = None
    mean_synapses: Optional[float] = None
    mean_degree: Optional[float] = None

    # Metadata
    dataset_source: Optional[str] = None
    analysis_notes: List[str] = field(default_factory=list)

    def get_scaling_summary(self) -> Dict[str, Any]:
        """Get summary of all scaling relationships"""
        summary = {
            'species': self.species_name,
            'n_neurons': self.n_neurons,
            'scaling_relationships': {}
        }

        for relationship in [self.length_synapses, self.synapses_degree, self.length_degree]:
            if relationship:
                key = f"{relationship.x_variable}_vs_{relationship.y_variable}"
                summary['scaling_relationships'][key] = {
                    'exponent': relationship.power_law.exponent,
                    'r_squared': relationship.power_law.r_squared,
                    'spearman_rho': relationship.spearman_rho,
                    'p_value': relationship.p_value,
                    'significant': relationship.is_significant,
                    'strength': relationship.correlation_strength
                }

        return summary


@dataclass
class CrossSpeciesComparison:
    """Comparison of scaling relationships across multiple species"""
    species_results: Dict[str, ConnectomicsResult]

    # Cross-species statistics
    mean_length_synapses_exponent: Optional[float] = None
    std_length_synapses_exponent: Optional[float] = None
    mean_synapses_degree_exponent: Optional[float] = None
    std_synapses_degree_exponent: Optional[float] = None

    # Universality assessment
    is_universal_scaling: bool = False
    universality_notes: List[str] = field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame for easy viewing"""
        rows = []

        for species_name, result in self.species_results.items():
            row = {
                'species': species_name,
                'n_neurons': result.n_neurons
            }

            # Add scaling relationships
            if result.length_synapses:
                row['length_synapses_exponent'] = result.length_synapses.power_law.exponent
                row['length_synapses_rho'] = result.length_synapses.spearman_rho
                row['length_synapses_p'] = result.length_synapses.p_value
                row['length_synapses_r2'] = result.length_synapses.power_law.r_squared

            if result.synapses_degree:
                row['synapses_degree_exponent'] = result.synapses_degree.power_law.exponent
                row['synapses_degree_rho'] = result.synapses_degree.spearman_rho
                row['synapses_degree_p'] = result.synapses_degree.p_value
                row['synapses_degree_r2'] = result.synapses_degree.power_law.r_squared

            rows.append(row)

        return pd.DataFrame(rows)


# Analyzer class

class ConnectomicsAnalyzer:
    """
    Analyzer for connectomics data and scaling laws.

    Implements the Figure 4 analysis pattern from kosmos-figures:
    - Power law scaling relationships
    - Spearman correlation (non-parametric)
    - Log-log linear regression
    - Cross-species comparison

    Example:
        analyzer = ConnectomicsAnalyzer()

        # Load connectome data with columns: Length, Synapses, Degree
        df = pd.read_csv('connectome_data.csv')

        # Analyze scaling laws
        results = analyzer.analyze_scaling_laws(
            connectome_data=df,
            species_name='Celegans'
        )

        # Print results
        print(f"Length-Synapses scaling: {results.length_synapses.power_law.equation}")
        print(f"Correlation: rho={results.length_synapses.spearman_rho:.3f}, "
              f"p={results.length_synapses.p_value:.2e}")
    """

    def __init__(self):
        """Initialize ConnectomicsAnalyzer"""
        pass

    def analyze_scaling_laws(
        self,
        connectome_data: pd.DataFrame,
        species_name: str = "Unknown",
        dataset_source: Optional[str] = None,
        properties: Optional[List[str]] = None
    ) -> ConnectomicsResult:
        """
        Analyze power law scaling relationships in a connectome dataset.

        Implements the Figure 4 pattern:
        1. Clean data (remove NaN, non-positive values)
        2. Calculate Spearman correlation (non-parametric, robust)
        3. Log-log linear regression to extract power law exponents
        4. Return results with scaling relationships

        Args:
            connectome_data: DataFrame with neuron properties
            species_name: Species identifier
            dataset_source: Data source (e.g., "FlyWire", "MICrONS")
            properties: Properties to analyze (default: ['Length', 'Synapses', 'Degree'])

        Returns:
            ConnectomicsResult with all scaling relationships

        Raises:
            ValueError: If required columns are missing
        """
        # Default properties
        if properties is None:
            properties = ['Length', 'Synapses', 'Degree']

        # Validate data
        missing_cols = [col for col in properties if col not in connectome_data.columns]
        if missing_cols:
            raise ValueError(
                f"Missing required columns: {missing_cols}. "
                f"Available columns: {list(connectome_data.columns)}"
            )

        # Step 1: Clean data
        df_clean = self._clean_connectome_data(connectome_data, properties)

        if len(df_clean) == 0:
            raise ValueError(
                f"No valid data after cleaning. Original size: {len(connectome_data)}, "
                "all rows had NaN or non-positive values."
            )

        # Calculate basic statistics
        mean_stats = {
            'mean_length': df_clean['Length'].mean() if 'Length' in properties else None,
            'mean_synapses': df_clean['Synapses'].mean() if 'Synapses' in properties else None,
            'mean_degree': df_clean['Degree'].mean() if 'Degree' in properties else None,
        }

        # Total synapses
        n_synapses = int(df_clean['Synapses'].sum()) if 'Synapses' in properties else None

        # Step 2-3: Analyze property pairs
        property_pairs = [
            ('Length', 'Synapses'),
            ('Synapses', 'Degree'),
            ('Length', 'Degree')
        ]

        scaling_relationships = {}

        for x_var, y_var in property_pairs:
            if x_var in properties and y_var in properties:
                relationship = self._analyze_property_pair(
                    df_clean, x_var, y_var
                )
                scaling_relationships[f"{x_var}_{y_var}"] = relationship

        # Create result
        result = ConnectomicsResult(
            species_name=species_name,
            n_neurons=len(df_clean),
            n_synapses=n_synapses,
            length_synapses=scaling_relationships.get('Length_Synapses'),
            synapses_degree=scaling_relationships.get('Synapses_Degree'),
            length_degree=scaling_relationships.get('Length_Degree'),
            dataset_source=dataset_source,
            **mean_stats
        )

        # Add analysis notes
        result.analysis_notes.append(
            f"Cleaned data: {len(connectome_data)} → {len(df_clean)} neurons "
            f"({len(df_clean)/len(connectome_data)*100:.1f}% retained)"
        )

        return result

    def _clean_connectome_data(
        self,
        data: pd.DataFrame,
        properties: List[str]
    ) -> pd.DataFrame:
        """
        Clean connectome data for scaling analysis.

        Steps:
        1. Select only required properties
        2. Remove rows with NaN values
        3. Remove rows with non-positive values (required for log-log analysis)

        Args:
            data: Raw connectome DataFrame
            properties: Properties to keep

        Returns:
            Cleaned DataFrame
        """
        # Select properties
        df = data[properties].copy()

        # Remove NaN
        df = df.dropna()

        # Remove non-positive values (can't take log of zero or negative)
        df = df[(df > 0).all(axis=1)]

        return df

    def _analyze_property_pair(
        self,
        data: pd.DataFrame,
        x_variable: str,
        y_variable: str
    ) -> ScalingRelationship:
        """
        Analyze scaling relationship between two properties.

        Steps:
        1. Calculate Spearman correlation (non-parametric, robust to outliers)
        2. Log-log linear regression to extract power law parameters
        3. Package results into ScalingRelationship

        Power law model: y = coefficient * x^exponent
        Log transform: log(y) = log(coefficient) + exponent * log(x)
        Linear fit on log-log scale gives exponent as slope

        Args:
            data: Cleaned connectome data
            x_variable: Independent variable name
            y_variable: Dependent variable name

        Returns:
            ScalingRelationship with correlation and power law fit
        """
        x = data[x_variable].values
        y = data[y_variable].values

        # Step 1: Spearman correlation
        rho, p_value = spearmanr(x, y)

        # Step 2: Log-log linear regression
        log_x = np.log10(x)
        log_y = np.log10(y)

        # Linear fit: log(y) = intercept + slope * log(x)
        slope, intercept, r_value, _, _ = linregress(log_x, log_y)

        # Convert to power law: y = coefficient * x^exponent
        exponent = slope
        coefficient = 10**intercept
        r_squared = r_value**2

        # Create power law fit
        power_law = PowerLawFit(
            exponent=exponent,
            coefficient=coefficient,
            r_squared=r_squared,
            equation=f"{y_variable} = {coefficient:.3f} * {x_variable}^{exponent:.3f}"
        )

        # Create scaling relationship
        relationship = ScalingRelationship(
            x_variable=x_variable,
            y_variable=y_variable,
            spearman_rho=rho,
            p_value=p_value,
            power_law=power_law,
            n_neurons=len(data)
        )

        return relationship

    def cross_species_comparison(
        self,
        datasets: Dict[str, pd.DataFrame],
        properties: Optional[List[str]] = None
    ) -> CrossSpeciesComparison:
        """
        Compare scaling relationships across multiple species.

        Analyzes whether scaling laws are universal across species.

        Args:
            datasets: Dict mapping species names to connectome DataFrames
            properties: Properties to analyze (default: ['Length', 'Synapses', 'Degree'])

        Returns:
            CrossSpeciesComparison with results for all species

        Example:
            datasets = {
                'Celegans': celegans_df,
                'FlyWire': flywire_df,
                'H01': human_h01_df,
                'Mouse': mouse_df
            }
            comparison = analyzer.cross_species_comparison(datasets)

            # Get summary DataFrame
            df = comparison.to_dataframe()
            print(df[['species', 'n_neurons', 'length_synapses_exponent']])
        """
        # Analyze each species
        species_results = {}

        for species_name, connectome_df in datasets.items():
            try:
                result = self.analyze_scaling_laws(
                    connectome_data=connectome_df,
                    species_name=species_name,
                    properties=properties
                )
                species_results[species_name] = result
            except Exception as e:
                # Log error but continue with other species
                print(f"Warning: Failed to analyze {species_name}: {e}")
                continue

        if not species_results:
            raise ValueError("No species could be successfully analyzed")

        # Calculate cross-species statistics
        length_synapses_exponents = []
        synapses_degree_exponents = []

        for result in species_results.values():
            if result.length_synapses:
                length_synapses_exponents.append(result.length_synapses.power_law.exponent)
            if result.synapses_degree:
                synapses_degree_exponents.append(result.synapses_degree.power_law.exponent)

        # Mean and std of exponents
        mean_ls_exp = np.mean(length_synapses_exponents) if length_synapses_exponents else None
        std_ls_exp = np.std(length_synapses_exponents) if length_synapses_exponents else None
        mean_sd_exp = np.mean(synapses_degree_exponents) if synapses_degree_exponents else None
        std_sd_exp = np.std(synapses_degree_exponents) if synapses_degree_exponents else None

        # Assess universality (low coefficient of variation suggests universal scaling)
        is_universal = False
        universality_notes = []

        if mean_ls_exp and std_ls_exp:
            cv_ls = std_ls_exp / abs(mean_ls_exp)  # Coefficient of variation
            if cv_ls < 0.2:  # Less than 20% variation
                is_universal = True
                universality_notes.append(
                    f"Length-Synapses scaling shows universal pattern: "
                    f"exponent = {mean_ls_exp:.3f} ± {std_ls_exp:.3f} "
                    f"(CV = {cv_ls:.1%})"
                )
            else:
                universality_notes.append(
                    f"Length-Synapses scaling varies across species: "
                    f"exponent = {mean_ls_exp:.3f} ± {std_ls_exp:.3f} "
                    f"(CV = {cv_ls:.1%})"
                )

        # Create comparison result
        comparison = CrossSpeciesComparison(
            species_results=species_results,
            mean_length_synapses_exponent=mean_ls_exp,
            std_length_synapses_exponent=std_ls_exp,
            mean_synapses_degree_exponent=mean_sd_exp,
            std_synapses_degree_exponent=std_sd_exp,
            is_universal_scaling=is_universal,
            universality_notes=universality_notes
        )

        return comparison
