"""
Connectome Scaling Analysis Template

Based on kosmos-figures Figure 4 pattern:
- Load connectome data (neurons with Length, Synapses, Degree)
- Power law scaling analysis
- Spearman correlation (non-parametric)
- Log-log linear regression
- Cross-species comparison
- Visualization (log-log scatter plots)

Example usage:
    template = ConnectomeScalingTemplate()

    # Check if applicable
    if template.is_applicable(hypothesis):
        # Generate protocol
        protocol = template.generate_protocol(
            TemplateCustomizationParams(
                hypothesis=hypothesis,
                custom_variables={
                    'connectome_data_path': 'flywire_connectome.csv',
                    'species_name': 'Drosophila',
                    'properties': ['Length', 'Synapses', 'Degree']
                }
            )
        )
"""

from typing import List, Dict, Any, Optional
from kosmos.experiments.templates.base import (
    TemplateBase,
    TemplateCustomizationParams
)
from kosmos.models.experiment import (
    ExperimentProtocol,
    ExperimentType,
    ProtocolStep,
    Variable,
    ResourceRequirements,
    StatisticalTestSpec,
    ValidationCheck,
)
from kosmos.models.hypothesis import Hypothesis


class ConnectomeScalingTemplate(TemplateBase):
    """
    Template for connectome scaling law analysis.

    Implements the Figure 4 analysis pattern:
    1. Load connectome data
    2. Clean data (remove NaN, non-positive values)
    3. Spearman correlation analysis
    4. Log-log linear regression for power law extraction
    5. Cross-species comparison (if multiple datasets)
    6. Visualization
    """

    def __init__(self):
        super().__init__(
            name="connectome_scaling",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="neuroscience",
            title="Connectome Power Law Scaling Analysis",
            description=(
                "Analyze power law scaling relationships in neural networks. "
                "Tests for universal scaling patterns across species connectomes. "
                "Based on Figure 4 pattern."
            ),
            suitable_for=[
                "Connectome scaling law analysis",
                "Neural network topology studies",
                "Cross-species comparisons",
                "Power law relationship testing"
            ],
            requirements=[
                "Connectome data (neurons × properties: Length, Synapses, Degree)",
                "At least 50+ neurons for reliable power law fitting",
                "Data in CSV format with neuron-level measurements"
            ],
            complexity_score=0.7,
            rigor_score=0.9
        )

    def is_applicable(self, hypothesis: Hypothesis) -> bool:
        """
        Check if hypothesis is suitable for connectome scaling analysis.

        Args:
            hypothesis: Hypothesis to check

        Returns:
            True if hypothesis involves connectome scaling or power laws
        """
        statement_lower = hypothesis.statement.lower()

        # Check for connectome keywords
        connectome_keywords = [
            'connectome', 'neural network', 'neuron', 'synapse',
            'connectivity', 'brain network', 'neuronal'
        ]

        # Check for scaling keywords
        scaling_keywords = [
            'scale', 'scaling', 'power law', 'log-log',
            'relationship', 'correlation', 'universal'
        ]

        has_connectome = any(kw in statement_lower for kw in connectome_keywords)
        has_scaling = any(kw in statement_lower for kw in scaling_keywords)

        return has_connectome and has_scaling

    def generate_protocol(self, params: TemplateCustomizationParams) -> ExperimentProtocol:
        """
        Generate connectome scaling analysis protocol.

        Args:
            params: Customization parameters

        Returns:
            Complete experiment protocol

        Required custom_variables:
            - connectome_data_path: Path to connectome data CSV
            - species_name: Species identifier
            - properties: List of properties to analyze (default: ['Length', 'Synapses', 'Degree'])

        Optional custom_variables:
            - additional_datasets: Dict of {species_name: data_path} for cross-species comparison
            - min_neurons: Minimum number of neurons required (default: 50)
        """
        # Extract parameters
        data_path = params.custom_variables.get('connectome_data_path', 'connectome_data.csv')
        species_name = params.custom_variables.get('species_name', 'Unknown')
        properties = params.custom_variables.get('properties', ['Length', 'Synapses', 'Degree'])
        additional_datasets = params.custom_variables.get('additional_datasets', {})
        min_neurons = params.custom_variables.get('min_neurons', 50)

        # Create protocol steps
        steps = [
            ProtocolStep(
                name="load_data",
                description="Load connectome data from CSV",
                code_template=self._generate_load_data_code(data_path, species_name),
                expected_output="Pandas DataFrame with neuron properties",
                validation=["Data has required columns: " + ", ".join(properties)]
            ),
            ProtocolStep(
                name="analyze_scaling",
                description="Analyze power law scaling relationships",
                code_template=self._generate_scaling_analysis_code(
                    species_name, properties, min_neurons
                ),
                expected_output="ConnectomicsResult with scaling relationships",
                validation=[
                    f"At least {min_neurons} neurons after cleaning",
                    "All correlations have p-values",
                    "Power law exponents are finite"
                ]
            ),
            ProtocolStep(
                name="visualize_results",
                description="Create log-log scatter plots",
                code_template=self._generate_visualization_code(properties),
                expected_output="Matplotlib figures showing power law relationships",
                validation=["Plots created successfully"]
            )
        ]

        # Add cross-species comparison if additional datasets provided
        if additional_datasets:
            steps.append(
                ProtocolStep(
                    name="cross_species_comparison",
                    description="Compare scaling relationships across species",
                    code_template=self._generate_cross_species_code(
                        data_path, species_name, additional_datasets, properties
                    ),
                    expected_output="CrossSpeciesComparison with summary DataFrame",
                    validation=[
                        "All species analyzed successfully",
                        "Universality assessment completed"
                    ]
                )
            )

        # Variables
        variables = [
            Variable(
                name="species_name",
                type="string",
                value=species_name,
                description="Species being analyzed"
            ),
            Variable(
                name="properties",
                type="list",
                value=str(properties),
                description="Neuron properties to analyze"
            ),
            Variable(
                name="min_neurons",
                type="integer",
                value=str(min_neurons),
                description="Minimum number of neurons required"
            )
        ]

        # Statistical tests
        statistical_tests = [
            StatisticalTestSpec(
                test_type="spearman_correlation",
                parameters={
                    "alternative": "two-sided",
                    "significance_level": 0.05
                },
                description="Non-parametric correlation between neuron properties"
            ),
            StatisticalTestSpec(
                test_type="linear_regression",
                parameters={
                    "transform": "log-log",
                    "robust": True
                },
                description="Power law exponent extraction via log-log regression"
            )
        ]

        # Validation checks
        validation_checks = [
            ValidationCheck(
                check_type="data_quality",
                parameters={
                    "min_sample_size": min_neurons,
                    "allow_missing": False,
                    "positive_values_only": True
                },
                description="Ensure sufficient high-quality data"
            ),
            ValidationCheck(
                check_type="statistical_significance",
                parameters={"p_threshold": 0.05},
                description="Check correlation significance"
            ),
            ValidationCheck(
                check_type="goodness_of_fit",
                parameters={"min_r_squared": 0.5},
                description="Ensure power law fits are reasonable"
            )
        ]

        # Resource requirements
        resources = ResourceRequirements(
            estimated_runtime_seconds=60,
            memory_mb=512,
            cpu_cores=1,
            requires_gpu=False
        )

        # Create protocol
        protocol = ExperimentProtocol(
            title=f"Connectome Scaling Analysis: {species_name}",
            hypothesis_id=params.hypothesis.id if params.hypothesis else "unknown",
            experiment_type=self.experiment_type,
            domain=self.domain,
            steps=steps,
            variables=variables,
            statistical_tests=statistical_tests,
            validation_checks=validation_checks,
            resource_requirements=resources,
            expected_duration_hours=0.1,
            reproducibility_notes=[
                "Analysis is deterministic (no random components)",
                "Power law fitting uses standard scipy.stats.linregress",
                "Results depend on data cleaning thresholds"
            ]
        )

        return protocol

    def _generate_load_data_code(self, data_path: str, species_name: str) -> str:
        """Generate code to load connectome data"""
        return f'''
import pandas as pd
import numpy as np
from kosmos.domains.neuroscience.connectomics import ConnectomicsAnalyzer

# Load connectome data
connectome_df = pd.read_csv('{data_path}')

print(f"Loaded {{len(connectome_df)}} neurons from {{'{data_path}'}}")
print(f"Columns: {{list(connectome_df.columns)}}")
print(f"\\nFirst few rows:")
print(connectome_df.head())

# Basic statistics
print(f"\\nBasic statistics:")
print(connectome_df.describe())
'''

    def _generate_scaling_analysis_code(
        self,
        species_name: str,
        properties: List[str],
        min_neurons: int
    ) -> str:
        """Generate code for scaling analysis"""
        return f'''
from kosmos.domains.neuroscience.connectomics import ConnectomicsAnalyzer

# Initialize analyzer
analyzer = ConnectomicsAnalyzer()

# Analyze scaling laws
results = analyzer.analyze_scaling_laws(
    connectome_data=connectome_df,
    species_name='{species_name}',
    properties={properties}
)

# Display results
print(f"\\n=== Connectome Scaling Analysis: {species_name} ===")
print(f"Neurons analyzed: {{results.n_neurons}}")

if results.n_neurons < {min_neurons}:
    raise ValueError(f"Insufficient neurons: {{results.n_neurons}} < {min_neurons}")

# Length-Synapses scaling
if results.length_synapses:
    ls = results.length_synapses
    print(f"\\nLength-Synapses Relationship:")
    print(f"  Spearman rho: {{ls.spearman_rho:.4f}} (p={{ls.p_value:.2e}})")
    print(f"  Power law: {{ls.power_law.equation}}")
    print(f"  R-squared: {{ls.power_law.r_squared:.4f}}")
    print(f"  Correlation: {{ls.correlation_strength}}")

# Synapses-Degree scaling
if results.synapses_degree:
    sd = results.synapses_degree
    print(f"\\nSynapses-Degree Relationship:")
    print(f"  Spearman rho: {{sd.spearman_rho:.4f}} (p={{sd.p_value:.2e}})")
    print(f"  Power law: {{sd.power_law.equation}}")
    print(f"  R-squared: {{sd.power_law.r_squared:.4f}}")

# Length-Degree scaling
if results.length_degree:
    ld = results.length_degree
    print(f"\\nLength-Degree Relationship:")
    print(f"  Spearman rho: {{ld.spearman_rho:.4f}} (p={{ld.p_value:.2e}})")
    print(f"  Power law: {{ld.power_law.equation}}")
    print(f"  R-squared: {{ld.power_law.r_squared:.4f}}")

# Analysis notes
print(f"\\nAnalysis Notes:")
for note in results.analysis_notes:
    print(f"  - {{note}}")

scaling_results = results
'''

    def _generate_visualization_code(self, properties: List[str]) -> str:
        """Generate code for log-log visualization"""
        return f'''
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 14

# Create figure
n_plots = 0
relationships = []

if 'Length' in {properties} and 'Synapses' in {properties}:
    relationships.append(('Length', 'Synapses', scaling_results.length_synapses))
    n_plots += 1

if 'Synapses' in {properties} and 'Degree' in {properties}:
    relationships.append(('Synapses', 'Degree', scaling_results.synapses_degree))
    n_plots += 1

if 'Length' in {properties} and 'Degree' in {properties}:
    relationships.append(('Length', 'Degree', scaling_results.length_degree))
    n_plots += 1

if n_plots > 0:
    fig, axes = plt.subplots(1, n_plots, figsize=(6*n_plots, 5))
    if n_plots == 1:
        axes = [axes]

    for idx, (x_var, y_var, relationship) in enumerate(relationships):
        ax = axes[idx]

        # Get data
        x_data = connectome_df[x_var].dropna()
        y_data = connectome_df[y_var].dropna()

        # Remove non-positive values
        valid_idx = (x_data > 0) & (y_data > 0)
        x_clean = x_data[valid_idx]
        y_clean = y_data[valid_idx]

        # Log-log scatter plot
        ax.scatter(x_clean, y_clean, alpha=0.5, s=20)
        ax.set_xscale('log')
        ax.set_yscale('log')

        # Add power law fit line if available
        if relationship:
            x_fit = np.logspace(np.log10(x_clean.min()), np.log10(x_clean.max()), 100)
            y_fit = relationship.power_law.coefficient * x_fit**relationship.power_law.exponent
            ax.plot(x_fit, y_fit, 'r-', linewidth=2,
                   label=f'Power law (exp={{relationship.power_law.exponent:.2f}})')
            ax.legend()

        ax.set_xlabel(f'{{x_var}} (log scale)', fontsize=16)
        ax.set_ylabel(f'{{y_var}} (log scale)', fontsize=16)
        ax.set_title(f'{{x_var}} vs {{y_var}}', fontsize=18)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('connectome_scaling_plots.png', dpi=300, bbox_inches='tight')
    print(f"\\nSaved visualization: connectome_scaling_plots.png")
    plt.show()
else:
    print("No relationships to plot")
'''

    def _generate_cross_species_code(
        self,
        primary_data_path: str,
        primary_species: str,
        additional_datasets: Dict[str, str],
        properties: List[str]
    ) -> str:
        """Generate code for cross-species comparison"""
        datasets_dict = {primary_species: primary_data_path}
        datasets_dict.update(additional_datasets)

        return f'''
from kosmos.domains.neuroscience.connectomics import ConnectomicsAnalyzer
import pandas as pd

# Load all species datasets
datasets = {{}}
species_info = {datasets_dict}

for species_name, data_path in species_info.items():
    try:
        df = pd.read_csv(data_path)
        datasets[species_name] = df
        print(f"Loaded {{species_name}}: {{len(df)}} neurons")
    except Exception as e:
        print(f"Warning: Could not load {{species_name}}: {{e}}")

# Cross-species comparison
analyzer = ConnectomicsAnalyzer()
comparison = analyzer.cross_species_comparison(
    datasets=datasets,
    properties={properties}
)

# Display results
print(f"\\n=== Cross-Species Comparison ===")
print(f"Species analyzed: {{len(comparison.species_results)}}")

# Summary DataFrame
summary_df = comparison.to_dataframe()
print(f"\\nSummary:")
print(summary_df.to_string())

# Universality assessment
if comparison.is_universal_scaling:
    print(f"\\n✓ UNIVERSAL SCALING DETECTED")
else:
    print(f"\\n✗ No universal scaling pattern")

print(f"\\nUniversality Notes:")
for note in comparison.universality_notes:
    print(f"  - {{note}}")

if comparison.mean_length_synapses_exponent:
    print(f"\\nLength-Synapses Exponent:")
    print(f"  Mean: {{comparison.mean_length_synapses_exponent:.3f}}")
    print(f"  Std:  {{comparison.std_length_synapses_exponent:.3f}}")
    print(f"  CV:   {{comparison.std_length_synapses_exponent/comparison.mean_length_synapses_exponent:.1%}}")

cross_species_results = comparison
'''
