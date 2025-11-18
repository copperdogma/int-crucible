"""
Metabolomics Group Comparison Template

Based on kosmos-figures Figure 2 pattern:
- Load metabolomics data (metabolites × samples)
- Log2 transformation
- Statistical comparison between groups (T-test/ANOVA)
- Pathway-level analysis (salvage vs synthesis)
- Volcano plot and heatmap visualization

Example usage:
    template = MetabolomicsComparisonTemplate()

    # Check if applicable
    if template.is_applicable(hypothesis):
        # Generate protocol
        protocol = template.generate_protocol(
            TemplateCustomizationParams(
                hypothesis=hypothesis,
                custom_variables={
                    'data_path': 'metabolomics_data.csv',
                    'group1_samples': ['Control_1', 'Control_2', ...],
                    'group2_samples': ['Treatment_1', 'Treatment_2', ...],
                    'metabolites_of_interest': ['Adenosine', 'AMP', ...]
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
    ControlGroup,
    ResourceRequirements,
    StatisticalTestSpec,
    ValidationCheck,
)
from kosmos.models.hypothesis import Hypothesis


class MetabolomicsComparisonTemplate(TemplateBase):
    """
    Template for metabolomics group comparison experiments.

    Implements the Figure 2 analysis pattern:
    1. Load metabolomics data
    2. Categorize metabolites by pathway
    3. Statistical comparison between groups
    4. Pathway-level pattern analysis
    5. Visualization (volcano plot, heatmap)
    """

    def __init__(self):
        super().__init__(
            name="metabolomics_comparison",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="biology",
            title="Metabolomics Group Comparison",
            description=(
                "Compare metabolite levels between two groups with "
                "pathway-level analysis. Based on nucleotide salvage "
                "pathway analysis pattern (Figure 2)."
            ),
            suitable_for=[
                "Metabolite level comparisons",
                "Pathway activation analysis",
                "Nucleotide metabolism studies",
                "Treatment effect on metabolomics"
            ],
            requirements=[
                "Metabolomics data (CSV format, metabolites × samples)",
                "Group assignments for samples",
                "At least 3 samples per group"
            ],
            complexity_score=0.6,
            rigor_score=0.8
        )

    def is_applicable(self, hypothesis: Hypothesis) -> bool:
        """
        Check if hypothesis is suitable for metabolomics comparison.

        Args:
            hypothesis: Hypothesis to check

        Returns:
            True if hypothesis involves metabolite comparison
        """
        statement_lower = hypothesis.statement.lower()

        # Check for metabolomics keywords
        metabolomics_keywords = [
            'metabolite', 'metabolomic', 'nucleotide',
            'purine', 'pyrimidine', 'salvage', 'synthesis',
            'pathway', 'compound', 'small molecule'
        ]

        # Check for comparison keywords
        comparison_keywords = [
            'compare', 'difference', 'between', 'versus', 'vs',
            'increase', 'decrease', 'change', 'affect', 'alter'
        ]

        has_metabolomics = any(kw in statement_lower for kw in metabolomics_keywords)
        has_comparison = any(kw in statement_lower for kw in comparison_keywords)

        return has_metabolomics and has_comparison

    def generate_protocol(
        self,
        params: TemplateCustomizationParams
    ) -> ExperimentProtocol:
        """
        Generate metabolomics comparison experiment protocol.

        Args:
            params: Customization parameters with hypothesis and variables

        Returns:
            Complete experiment protocol

        Raises:
            ValueError: If required variables are missing
        """
        hypothesis = params.hypothesis
        custom_vars = params.custom_variables or {}

        # Extract required parameters
        data_path = custom_vars.get('data_path', 'metabolomics_data.csv')
        group1_samples = custom_vars.get('group1_samples', [])
        group2_samples = custom_vars.get('group2_samples', [])
        metabolites = custom_vars.get('metabolites_of_interest', None)
        p_threshold = custom_vars.get('p_threshold', 0.05)
        log2_transform = custom_vars.get('log2_transform', True)

        # Validate
        if not group1_samples or not group2_samples:
            raise ValueError("Must specify group1_samples and group2_samples")

        # Define variables
        variables = [
            Variable(
                name="data_path",
                description="Path to metabolomics CSV file",
                value=data_path
            ),
            Variable(
                name="group1_samples",
                description="Sample names for group 1 (control)",
                value=group1_samples
            ),
            Variable(
                name="group2_samples",
                description="Sample names for group 2 (treatment)",
                value=group2_samples
            ),
            Variable(
                name="metabolites_of_interest",
                description="List of metabolites to analyze (None = all)",
                value=metabolites
            ),
            Variable(
                name="p_threshold",
                description="P-value threshold for significance",
                value=p_threshold
            ),
            Variable(
                name="log2_transform",
                description="Whether to apply log2 transformation",
                value=log2_transform
            ),
        ]

        # Define protocol steps
        steps = [
            ProtocolStep(
                name="load_data",
                description="Load metabolomics data from CSV",
                code_template=self._generate_load_data_code(),
                expected_duration_minutes=2,
                required_resources=ResourceRequirements(
                    cpu_cores=1,
                    memory_gb=2.0
                )
            ),
            ProtocolStep(
                name="analyze_comparison",
                description="Statistical comparison between groups using MetabolomicsAnalyzer",
                code_template=self._generate_analysis_code(
                    group1_samples, group2_samples,
                    metabolites, log2_transform, p_threshold
                ),
                expected_duration_minutes=5,
                required_resources=ResourceRequirements(
                    cpu_cores=2,
                    memory_gb=4.0
                )
            ),
            ProtocolStep(
                name="pathway_analysis",
                description="Analyze pathway-level patterns",
                code_template=self._generate_pathway_analysis_code(),
                expected_duration_minutes=3,
                required_resources=ResourceRequirements(
                    cpu_cores=1,
                    memory_gb=2.0
                )
            ),
            ProtocolStep(
                name="visualize_results",
                description="Create volcano plot and heatmap",
                code_template=self._generate_visualization_code(),
                expected_duration_minutes=5,
                required_resources=ResourceRequirements(
                    cpu_cores=1,
                    memory_gb=2.0
                )
            ),
        ]

        # Define statistical tests
        statistical_tests = [
            StatisticalTestSpec(
                test_name="Independent T-Test",
                test_type="parametric",
                description="Compare metabolite levels between groups",
                alpha=p_threshold,
                two_tailed=True
            )
        ]

        # Define validation checks
        validation_checks = [
            ValidationCheck(
                check_name="sample_size",
                description="Ensure at least 3 samples per group",
                validation_code=f"""
assert len({group1_samples}) >= 3, "Group 1 must have at least 3 samples"
assert len({group2_samples}) >= 3, "Group 2 must have at least 3 samples"
"""
            ),
            ValidationCheck(
                check_name="data_quality",
                description="Check for excessive missing values",
                validation_code="""
missing_rate = data_df.isnull().sum().sum() / (data_df.shape[0] * data_df.shape[1])
assert missing_rate < 0.3, f"Too many missing values: {missing_rate:.1%}"
"""
            ),
        ]

        # Create protocol
        protocol = ExperimentProtocol(
            title=f"Metabolomics Comparison: {hypothesis.statement[:50]}...",
            description=f"Compare metabolite levels to test: {hypothesis.statement}",
            hypothesis_id=str(hypothesis.id) if hasattr(hypothesis, 'id') else None,
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="biology",
            variables=variables,
            steps=steps,
            control_groups=[
                ControlGroup(
                    name="Control",
                    description="Group 1 (baseline)",
                    sample_ids=group1_samples
                )
            ],
            statistical_tests=statistical_tests,
            validation_checks=validation_checks,
            required_resources=ResourceRequirements(
                cpu_cores=2,
                memory_gb=4.0,
                storage_gb=1.0,
                estimated_duration_minutes=15
            )
        )

        return protocol

    def _generate_load_data_code(self) -> str:
        """Generate code for loading metabolomics data"""
        return """
import pandas as pd
import numpy as np

# Load metabolomics data
data_df = pd.read_csv(data_path, index_col=0)

# Display data shape
print(f"Loaded data: {data_df.shape[0]} metabolites × {data_df.shape[1]} samples")
print(f"Sample names: {list(data_df.columns)}")
"""

    def _generate_analysis_code(
        self,
        group1_samples: List[str],
        group2_samples: List[str],
        metabolites: Optional[List[str]],
        log2_transform: bool,
        p_threshold: float
    ) -> str:
        """Generate code for statistical analysis"""
        return f"""
from kosmos.domains.biology.metabolomics import MetabolomicsAnalyzer

# Initialize analyzer
analyzer = MetabolomicsAnalyzer()

# Perform group comparison
results = analyzer.analyze_group_comparison(
    data_df=data_df,
    group1_samples={group1_samples},
    group2_samples={group2_samples},
    metabolites={metabolites},
    log2_transform={log2_transform},
    p_threshold={p_threshold},
    use_kegg=False  # Disable KEGG queries for speed
)

# Convert to DataFrame for easy viewing
results_df = pd.DataFrame([r.dict() for r in results])

# Sort by p-value
results_df = results_df.sort_values('p_value')

# Display summary
n_significant = results_df['significant'].sum()
print(f"\\nAnalyzed {{len(results)}} metabolites")
print(f"Significant changes: {{n_significant}} ({{n_significant/len(results)*100:.1f}}%)")
print(f"\\nTop 10 most significant metabolites:")
print(results_df[['metabolite', 'log2_fold_change', 'p_value', 'category']].head(10))
"""

    def _generate_pathway_analysis_code(self) -> str:
        """Generate code for pathway analysis"""
        return """
from kosmos.domains.biology.metabolomics import MetaboliteCategory

# Analyze pathway patterns
patterns = analyzer.analyze_pathway_pattern(results)

print("\\nPathway-level patterns:")
for pattern in patterns:
    print(f"  {{pattern.pathway_category}} {{pattern.metabolite_type}}: "
          f"{{pattern.n_metabolites}} metabolites, "
          f"mean FC={{pattern.mean_log2_fc:.2f}}, "
          f"{{pattern.n_significant}} significant")

# Compare salvage vs synthesis for purines
purine_comparison = analyzer.compare_salvage_vs_synthesis(
    results,
    category=MetaboliteCategory.PURINE
)

if purine_comparison:
    print(f"\\nPurine salvage vs synthesis:")
    print(f"  Salvage mean FC: {{purine_comparison.salvage_mean_fc:.2f}}")
    print(f"  Synthesis mean FC: {{purine_comparison.synthesis_mean_fc:.2f}}")
    print(f"  Pattern: {{purine_comparison.pattern}}")
    print(f"  P-value: {{purine_comparison.p_value:.4f}}")

# Repeat for pyrimidines
pyrimidine_comparison = analyzer.compare_salvage_vs_synthesis(
    results,
    category=MetaboliteCategory.PYRIMIDINE
)

if pyrimidine_comparison:
    print(f"\\nPyrimidine salvage vs synthesis:")
    print(f"  Salvage mean FC: {{pyrimidine_comparison.salvage_mean_fc:.2f}}")
    print(f"  Synthesis mean FC: {{pyrimidine_comparison.synthesis_mean_fc:.2f}}")
    print(f"  Pattern: {{pyrimidine_comparison.pattern}}")
"""

    def _generate_visualization_code(self) -> str:
        """Generate code for visualizations"""
        return """
import matplotlib.pyplot as plt
import seaborn as sns

# Create figure with subplots
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 1. Volcano plot
ax1 = axes[0]
ax1.scatter(
    results_df['log2_fold_change'],
    -np.log10(results_df['p_value']),
    c=results_df['significant'].map({{True: 'red', False: 'gray'}}),
    alpha=0.6
)
ax1.axhline(y=-np.log10(p_threshold), color='black', linestyle='--', alpha=0.5)
ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)
ax1.set_xlabel('Log2 Fold Change')
ax1.set_ylabel('-Log10 P-value')
ax1.set_title('Volcano Plot: Metabolite Changes')

# Add labels for top metabolites
top_metabolites = results_df.nsmallest(5, 'p_value')
for _, row in top_metabolites.iterrows():
    ax1.annotate(
        row['metabolite'],
        xy=(row['log2_fold_change'], -np.log10(row['p_value'])),
        xytext=(5, 5),
        textcoords='offset points',
        fontsize=8
    )

# 2. Heatmap of significant metabolites
ax2 = axes[1]
significant_metabolites = results_df[results_df['significant']]['metabolite'].tolist()

if significant_metabolites:
    # Get data for significant metabolites
    sig_data = data_df.loc[significant_metabolites, group1_samples + group2_samples]

    # Log2 transform if needed
    if log2_transform:
        sig_data_plot = np.log2(sig_data + 1)
    else:
        sig_data_plot = sig_data

    # Create heatmap
    sns.heatmap(
        sig_data_plot,
        cmap='RdBu_r',
        center=0,
        cbar_kws={{'label': 'Log2 Intensity'}},
        ax=ax2
    )
    ax2.set_title(f'Significant Metabolites (n={{len(significant_metabolites)}})')
    ax2.set_xlabel('Samples')
    ax2.set_ylabel('Metabolites')

plt.tight_layout()
plt.savefig('metabolomics_results.png', dpi=300, bbox_inches='tight')
print("\\nSaved visualization to metabolomics_results.png")
"""
