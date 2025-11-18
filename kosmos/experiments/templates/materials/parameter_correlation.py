"""
Parameter-Performance Correlation Template

Based on kosmos-figures Figure 3 pattern (Perovskite Solar Cell Optimization):
- Load experimental data (parameters × experiments)
- Correlation analysis (Pearson + linear regression)
- Significance testing with p-value thresholds
- Visualization (scatter plot with regression line)

Example usage:
    template = ParameterCorrelationTemplate()

    # Check if applicable
    if template.is_applicable(hypothesis):
        # Generate protocol
        protocol = template.generate_protocol(
            TemplateCustomizationParams(
                hypothesis=hypothesis,
                custom_variables={
                    'data_path': 'Summary table analysis.xlsx',
                    'parameter': 'Spin coater: Solvent Partial Pressure [ppm]',
                    'metric': 'Short circuit current density, Jsc [mA/cm2]'
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


class ParameterCorrelationTemplate(TemplateBase):
    """
    Template for parameter-performance correlation analysis.

    Implements the Figure 3 analysis pattern:
    1. Load experimental data
    2. Clean data (remove NaN, outliers)
    3. Correlation analysis (Pearson + linear regression)
    4. Significance testing
    5. Visualization with regression line
    """

    def __init__(self):
        super().__init__(
            name="parameter_correlation",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="materials",
            title="Parameter-Performance Correlation Analysis",
            description=(
                "Analyze correlation between experimental parameters "
                "and performance metrics using Pearson correlation and "
                "linear regression. Based on perovskite solar cell "
                "optimization pattern (Figure 3)."
            ),
            suitable_for=[
                "Materials optimization studies",
                "Parameter correlation analysis",
                "Solar cell efficiency optimization",
                "Process parameter effects"
            ],
            requirements=[
                "Experimental data (CSV/Excel format)",
                "At least 20 data points for reliable statistics",
                "Numerical parameter and metric columns"
            ],
            complexity_score=0.5,
            rigor_score=0.8
        )

    def is_applicable(self, hypothesis: Hypothesis) -> bool:
        """
        Check if hypothesis is suitable for parameter correlation analysis.

        Args:
            hypothesis: Hypothesis to check

        Returns:
            True if hypothesis involves parameter-performance relationships
        """
        statement_lower = hypothesis.statement.lower()

        # Check for materials/optimization keywords
        materials_keywords = [
            'material', 'perovskite', 'solar cell', 'efficiency',
            'optimization', 'parameter', 'fabrication', 'synthesis',
            'process', 'property', 'performance'
        ]

        # Check for correlation/relationship keywords
        correlation_keywords = [
            'correlate', 'correlation', 'relationship', 'affect',
            'influence', 'depend', 'impact', 'effect', 'association',
            'increase', 'decrease', 'improve', 'reduce'
        ]

        has_materials = any(kw in statement_lower for kw in materials_keywords)
        has_correlation = any(kw in statement_lower for kw in correlation_keywords)

        return has_materials and has_correlation

    def generate_protocol(
        self,
        params: TemplateCustomizationParams
    ) -> ExperimentProtocol:
        """
        Generate experiment protocol for parameter correlation analysis.

        Args:
            params: Customization parameters

        Returns:
            ExperimentProtocol with analysis steps
        """
        # Extract custom variables
        data_path = params.custom_variables.get('data_path', 'data.xlsx')
        parameter = params.custom_variables.get('parameter', 'Parameter')
        metric = params.custom_variables.get('metric', 'Performance')
        sheet_name = params.custom_variables.get('sheet_name', None)
        min_samples = params.custom_variables.get('min_samples', 20)

        # Define protocol steps
        steps = [
            ProtocolStep(
                name="load_data",
                description="Load experimental data from file",
                code_template=self._generate_load_data_code(data_path, sheet_name),
                expected_output="DataFrame with experimental data",
                validation=["Check column names", "Verify data types"]
            ),
            ProtocolStep(
                name="correlation_analysis",
                description="Analyze correlation between parameter and metric",
                code_template=self._generate_correlation_code(parameter, metric, min_samples),
                expected_output="CorrelationResult with r, p-value, R², regression equation",
                validation=["Check significance level", "Verify sample size"]
            ),
            ProtocolStep(
                name="visualize_results",
                description="Create scatter plot with regression line",
                code_template=self._generate_visualization_code(parameter, metric),
                expected_output="Matplotlib figure with scatter plot and regression line",
                validation=["Plot saved to file", "Axes labeled correctly"]
            ),
            ProtocolStep(
                name="summary_report",
                description="Generate analysis summary",
                code_template=self._generate_summary_code(),
                expected_output="Text summary of correlation analysis",
                validation=["All metrics reported", "Interpretation included"]
            )
        ]

        # Define variables
        variables = [
            Variable(
                name="parameter",
                description=f"Independent variable: {parameter}",
                type="numerical",
                values=None
            ),
            Variable(
                name="metric",
                description=f"Dependent variable: {metric}",
                type="numerical",
                values=None
            )
        ]

        # Statistical tests
        statistical_tests = [
            StatisticalTestSpec(
                test_type="pearson_correlation",
                significance_threshold=0.05,
                correction_method=None
            )
        ]

        # Resource requirements
        resources = ResourceRequirements(
            compute_hours=0.1,
            memory_gb=2.0,
            storage_gb=0.1,
            special_equipment=[]
        )

        # Validation checks
        validation_checks = [
            ValidationCheck(
                check_type="sample_size",
                threshold=min_samples,
                description=f"At least {min_samples} samples required"
            ),
            ValidationCheck(
                check_type="data_quality",
                threshold=0.8,
                description="At least 80% valid (non-NaN) data points"
            )
        ]

        # Create protocol
        protocol = ExperimentProtocol(
            title=f"Correlation: {parameter} vs {metric}",
            domain="materials",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            hypothesis_id=params.hypothesis.id if params.hypothesis else None,
            steps=steps,
            variables=variables,
            statistical_tests=statistical_tests,
            resource_requirements=resources,
            validation_checks=validation_checks,
            estimated_duration_hours=0.5,
            safety_considerations=["None - data analysis only"],
            ethical_considerations=["Ensure data provenance is documented"],
            reproducibility_notes=[
                "Use provided data file",
                "Random seed not applicable (deterministic analysis)"
            ]
        )

        return protocol

    def _generate_load_data_code(
        self,
        data_path: str,
        sheet_name: Optional[str] = None
    ) -> str:
        """Generate code for loading experimental data."""
        sheet_param = f", sheet_name='{sheet_name}'" if sheet_name else ""

        return f'''
import pandas as pd
import numpy as np

# Load experimental data
print(f"Loading data from: {data_path}")

# Determine file type and load
if '{data_path}'.endswith('.csv'):
    df = pd.read_csv('{data_path}')
elif '{data_path}'.endswith(('.xlsx', '.xls')):
    df = pd.read_excel('{data_path}'{sheet_param})
else:
    raise ValueError("Unsupported file format. Use CSV or Excel.")

print(f"Loaded {{len(df)}} experiments")
print(f"Columns: {{df.columns.tolist()}}")
print(f"\\nFirst few rows:")
print(df.head())
'''

    def _generate_correlation_code(
        self,
        parameter: str,
        metric: str,
        min_samples: int
    ) -> str:
        """Generate code for correlation analysis."""
        return f'''
from kosmos.domains.materials.optimization import MaterialsOptimizer

# Initialize analyzer
analyzer = MaterialsOptimizer()

# Perform correlation analysis
print("\\nPerforming correlation analysis...")
result = analyzer.correlation_analysis(
    data=df,
    parameter='{parameter}',
    metric='{metric}',
    min_samples={min_samples}
)

# Display results
print("\\n" + "="*60)
print("CORRELATION ANALYSIS RESULTS")
print("="*60)
print(f"Parameter: {{result.parameter}}")
print(f"Metric: {{result.metric}}")
print(f"Sample size: {{result.n_samples}}")
print(f"\\nCorrelation (r): {{result.correlation:.4f}}")
print(f"P-value: {{result.p_value:.4e}}")
print(f"Significance: {{result.significance}}")
print(f"\\nR-squared: {{result.r_squared:.4f}}")
print(f"Regression equation: {{result.equation}}")
print(f"Slope: {{result.slope:.4f}}")
print(f"Intercept: {{result.intercept:.4f}}")
print(f"Standard error: {{result.std_err:.4f}}")
print("="*60)

# Interpretation
if result.significance == "***":
    print("\\nInterpretation: HIGHLY SIGNIFICANT correlation (p < 0.001)")
elif result.significance == "**":
    print("\\nInterpretation: SIGNIFICANT correlation (p < 0.01)")
elif result.significance == "*":
    print("\\nInterpretation: MARGINALLY SIGNIFICANT correlation (p < 0.05)")
else:
    print("\\nInterpretation: NO SIGNIFICANT correlation (p >= 0.05)")

if result.correlation > 0:
    print(f"Direction: POSITIVE - {{result.metric}} increases with {{result.parameter}}")
else:
    print(f"Direction: NEGATIVE - {{result.metric}} decreases with {{result.parameter}}")
'''

    def _generate_visualization_code(
        self,
        parameter: str,
        metric: str
    ) -> str:
        """Generate code for visualization."""
        return f'''
import matplotlib.pyplot as plt
import numpy as np

# Create figure (Figure 3 style)
fig, ax = plt.subplots(figsize=(8, 6))

# Get clean data
df_plot = result.clean_data

# Scatter plot
ax.scatter(
    df_plot['{parameter}'],
    df_plot['{metric}'],
    alpha=0.6,
    color='#abd9e9',
    s=80,
    edgecolors='black',
    linewidth=0.5,
    label='Experimental data'
)

# Regression line
x_range = np.linspace(
    df_plot['{parameter}'].min(),
    df_plot['{parameter}'].max(),
    100
)
y_pred = result.slope * x_range + result.intercept

ax.plot(
    x_range,
    y_pred,
    color='#d7191c',
    linewidth=2.5,
    label=f'Linear fit (R² = {{result.r_squared:.3f}})'
)

# Formatting (Figure 3 style: clean, no grid)
ax.set_xlabel('{parameter}', fontsize=12, fontweight='bold')
ax.set_ylabel('{metric}', fontsize=12, fontweight='bold')
ax.set_title(
    f'Correlation: r = {{result.correlation:.3f}}, p = {{result.p_value:.2e}} {{result.significance}}',
    fontsize=13,
    fontweight='bold'
)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Legend
ax.legend(loc='best', frameon=False)

# Tight layout
plt.tight_layout()

# Save figure
output_file = 'correlation_plot.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\\nFigure saved: {{output_file}}")

plt.show()
'''

    def _generate_summary_code(self) -> str:
        """Generate code for summary report."""
        return '''
# Generate summary report
print("\\n" + "="*60)
print("SUMMARY")
print("="*60)

summary = f"""
Analysis Type: Parameter-Performance Correlation
Statistical Method: Pearson correlation + Linear regression

Key Findings:
- Correlation coefficient: {result.correlation:.4f}
- Statistical significance: {result.significance} (p = {result.p_value:.4e})
- Variance explained: {result.r_squared*100:.2f}%
- Linear relationship: {result.equation}

Sample Information:
- Total experiments analyzed: {result.n_samples}
- Parameter: {result.parameter}
- Performance metric: {result.metric}

Interpretation:
The analysis {'shows' if result.significance != 'ns' else 'does not show'} a statistically significant
{'positive' if result.correlation > 0 else 'negative'} correlation between {result.parameter}
and {result.metric}.

{'This suggests that ' + result.parameter + ' is a significant factor affecting ' + result.metric + '.'
 if result.significance != 'ns' else
 'No significant relationship detected. Consider other parameters or non-linear effects.'}
"""

print(summary)
print("="*60)

# Save summary to file
with open('correlation_summary.txt', 'w') as f:
    f.write(summary)

print("\\nSummary saved: correlation_summary.txt")
'''
