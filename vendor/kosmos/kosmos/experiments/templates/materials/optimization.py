"""
Multi-Parameter Optimization Template

Based on surrogate modeling + global optimization pattern:
- Load experimental data
- Train surrogate model (RandomForest or XGBoost)
- Global optimization using differential evolution
- Recommend optimal parameter settings

Example usage:
    template = MultiParameterOptimizationTemplate()

    # Check if applicable
    if template.is_applicable(hypothesis):
        # Generate protocol
        protocol = template.generate_protocol(
            TemplateCustomizationParams(
                hypothesis=hypothesis,
                custom_variables={
                    'data_path': 'experiments.xlsx',
                    'parameters': ['Pressure', 'Temperature', 'Time'],
                    'objective': 'Efficiency',
                    'maximize': True
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
    ValidationCheck,
)
from kosmos.models.hypothesis import Hypothesis


class MultiParameterOptimizationTemplate(TemplateBase):
    """
    Template for multi-parameter optimization experiments.

    Workflow:
    1. Load experimental data
    2. Train surrogate model (Random Forest or XGBoost)
    3. Global optimization (differential evolution)
    4. Report optimal parameters and predicted performance
    5. Generate recommended experimental conditions
    """

    def __init__(self):
        super().__init__(
            name="multi_parameter_optimization",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="materials",
            title="Multi-Parameter Optimization",
            description=(
                "Optimize multiple experimental parameters to maximize/minimize "
                "a performance metric using surrogate modeling and global optimization."
            ),
            suitable_for=[
                "Materials process optimization",
                "Multi-parameter tuning",
                "Efficiency maximization",
                "Cost/waste minimization"
            ],
            requirements=[
                "Experimental data with multiple parameters",
                "At least 50 experiments for reliable model",
                "Numerical parameters and objective"
            ],
            complexity_score=0.7,
            rigor_score=0.8
        )

    def is_applicable(self, hypothesis: Hypothesis) -> bool:
        """
        Check if hypothesis is suitable for multi-parameter optimization.

        Args:
            hypothesis: Hypothesis to check

        Returns:
            True if hypothesis involves optimization/maximization/minimization
        """
        statement_lower = hypothesis.statement.lower()

        # Check for materials/optimization keywords
        materials_keywords = [
            'material', 'process', 'fabrication', 'synthesis',
            'parameter', 'condition', 'experimental'
        ]

        # Check for optimization keywords
        optimization_keywords = [
            'optimize', 'optimization', 'maximize', 'minimize',
            'best', 'optimal', 'improve', 'enhance', 'reduce',
            'increase efficiency', 'reduce cost'
        ]

        has_materials = any(kw in statement_lower for kw in materials_keywords)
        has_optimization = any(kw in statement_lower for kw in optimization_keywords)

        return has_materials and has_optimization

    def generate_protocol(
        self,
        params: TemplateCustomizationParams
    ) -> ExperimentProtocol:
        """
        Generate experiment protocol for multi-parameter optimization.

        Args:
            params: Customization parameters

        Returns:
            ExperimentProtocol with optimization steps
        """
        # Extract custom variables
        data_path = params.custom_variables.get('data_path', 'data.xlsx')
        parameters = params.custom_variables.get('parameters', ['Parameter1', 'Parameter2'])
        objective = params.custom_variables.get('objective', 'Performance')
        maximize = params.custom_variables.get('maximize', True)
        model_type = params.custom_variables.get('model_type', 'RandomForest')
        sheet_name = params.custom_variables.get('sheet_name', None)

        # Define protocol steps
        steps = [
            ProtocolStep(
                name="load_data",
                description="Load experimental data",
                code_template=self._generate_load_data_code(data_path, sheet_name),
                expected_output="DataFrame with experimental data",
                validation=["Check parameter columns exist", "Verify data types"]
            ),
            ProtocolStep(
                name="exploratory_analysis",
                description="Explore parameter space and correlations",
                code_template=self._generate_exploratory_code(parameters, objective),
                expected_output="Summary statistics and correlation matrix",
                validation=["Check for missing values", "Identify outliers"]
            ),
            ProtocolStep(
                name="optimize_parameters",
                description="Run global optimization",
                code_template=self._generate_optimization_code(
                    parameters, objective, maximize, model_type
                ),
                expected_output="OptimizationResult with optimal parameters",
                validation=["Optimization converged", "Model R² > 0.5"]
            ),
            ProtocolStep(
                name="validate_recommendations",
                description="Cross-validate optimal parameters",
                code_template=self._generate_validation_code(),
                expected_output="Validation metrics and confidence intervals",
                validation=["Predictions within reasonable range"]
            ),
            ProtocolStep(
                name="generate_recommendations",
                description="Generate experimental recommendations",
                code_template=self._generate_recommendations_code(maximize),
                expected_output="Recommended experimental conditions",
                validation=["Parameters within feasible ranges"]
            )
        ]

        # Define variables
        variables = [
            Variable(
                name=param,
                description=f"Optimization parameter: {param}",
                type="numerical",
                values=None
            ) for param in parameters
        ]

        variables.append(Variable(
            name=objective,
            description=f"Objective to {'maximize' if maximize else 'minimize'}: {objective}",
            type="numerical",
            values=None
        ))

        # Resource requirements
        resources = ResourceRequirements(
            compute_hours=0.5,
            memory_gb=4.0,
            storage_gb=0.5,
            special_equipment=[]
        )

        # Validation checks
        validation_checks = [
            ValidationCheck(
                check_type="sample_size",
                threshold=50,
                description="At least 50 experiments for reliable optimization"
            ),
            ValidationCheck(
                check_type="model_quality",
                threshold=0.5,
                description="Surrogate model R² >= 0.5"
            )
        ]

        # Create protocol
        protocol = ExperimentProtocol(
            title=f"Optimize {', '.join(parameters)} to {'maximize' if maximize else 'minimize'} {objective}",
            domain="materials",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            hypothesis_id=params.hypothesis.id if params.hypothesis else None,
            steps=steps,
            variables=variables,
            statistical_tests=[],
            resource_requirements=resources,
            validation_checks=validation_checks,
            estimated_duration_hours=1.0,
            safety_considerations=["None - computational optimization only"],
            ethical_considerations=["Ensure data provenance documented"],
            reproducibility_notes=[
                "Set random seed for reproducibility",
                "Document model hyperparameters"
            ]
        )

        return protocol

    def _generate_load_data_code(
        self,
        data_path: str,
        sheet_name: Optional[str] = None
    ) -> str:
        """Generate code for loading data."""
        sheet_param = f", sheet_name='{sheet_name}'" if sheet_name else ""

        return f'''
import pandas as pd
import numpy as np

# Load experimental data
print(f"Loading data from: {data_path}")

if '{data_path}'.endswith('.csv'):
    df = pd.read_csv('{data_path}')
elif '{data_path}'.endswith(('.xlsx', '.xls')):
    df = pd.read_excel('{data_path}'{sheet_param})
else:
    raise ValueError("Unsupported file format")

print(f"Loaded {{len(df)}} experiments")
print(f"Columns: {{df.columns.tolist()}}")
print(f"\\nData preview:")
print(df.head())
'''

    def _generate_exploratory_code(
        self,
        parameters: List[str],
        objective: str
    ) -> str:
        """Generate code for exploratory analysis."""
        params_str = str(parameters)

        return f'''
import matplotlib.pyplot as plt
import seaborn as sns

# Summary statistics
print("\\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

all_cols = {params_str} + ['{objective}']
print(df[all_cols].describe())

# Correlation matrix
print("\\n" + "="*60)
print("CORRELATION MATRIX")
print("="*60)

corr_matrix = df[all_cols].corr()
print(corr_matrix)

# Visualize correlations
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
ax.set_title('Parameter Correlations')
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=300)
print("\\nCorrelation heatmap saved: correlation_heatmap.png")
plt.show()
'''

    def _generate_optimization_code(
        self,
        parameters: List[str],
        objective: str,
        maximize: bool,
        model_type: str
    ) -> str:
        """Generate code for optimization."""
        params_str = str(parameters)

        return f'''
from kosmos.domains.materials.optimization import MaterialsOptimizer

# Initialize optimizer
optimizer = MaterialsOptimizer()

# Run optimization
print("\\n" + "="*60)
print("MULTI-PARAMETER OPTIMIZATION")
print("="*60)
print(f"Parameters to optimize: {params_str}")
print(f"Objective: {objective}")
print(f"Goal: {'Maximize' if {maximize} else 'Minimize'}")
print(f"Model type: {model_type}")
print("\\nRunning global optimization...")

result = optimizer.parameter_space_optimization(
    data=df,
    parameters={params_str},
    objective='{objective}',
    maximize={maximize},
    model_type='{model_type}',
    n_estimators=100
)

# Display results
print("\\n" + "="*60)
print("OPTIMIZATION RESULTS")
print("="*60)
print(f"Success: {{result.optimization_success}}")
print(f"Iterations: {{result.n_iterations}}")
print(f"Surrogate model R²: {{result.model_r_squared:.4f}}")
print(f"\\nOptimal parameters:")
for param, value in result.optimal_parameters.items():
    bounds = result.parameter_bounds[param]
    print(f"  {{param}}: {{value:.4f}} (range: {{bounds[0]:.2f}} - {{bounds[1]:.2f}})")

print(f"\\nPredicted {objective}: {{result.predicted_value:.4f}}")
print(f"Convergence: {{result.convergence_message}}")
print("="*60)
'''

    def _generate_validation_code(self) -> str:
        """Generate code for validation."""
        return '''
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestRegressor
import numpy as np

# Cross-validation of surrogate model
print("\\n" + "="*60)
print("MODEL VALIDATION")
print("="*60)

# Prepare data
X = df[result.optimal_parameters.keys()].values
y = df[list(result.optimal_parameters.keys())[0]].values  # Get objective from df

# Cross-validation
model = RandomForestRegressor(n_estimators=100, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')

print(f"Cross-validation R² scores: {cv_scores}")
print(f"Mean R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Check if model is reliable
if cv_scores.mean() >= 0.5:
    print("✓ Model validation PASSED (R² >= 0.5)")
else:
    print("✗ WARNING: Model may be unreliable (R² < 0.5)")
    print("  Consider collecting more data or feature engineering")
'''

    def _generate_recommendations_code(self, maximize: bool) -> str:
        """Generate code for recommendations."""
        goal = "maximize" if maximize else "minimize"

        return f'''
# Generate experimental recommendations
print("\\n" + "="*60)
print("EXPERIMENTAL RECOMMENDATIONS")
print("="*60)

recommendations = f"""
RECOMMENDED EXPERIMENTAL CONDITIONS
====================================

To {goal} the objective metric, use the following parameters:

"""

for param, value in result.optimal_parameters.items():
    bounds = result.parameter_bounds[param]
    recommendations += f"{{param}}:\\n"
    recommendations += f"  Optimal value: {{value:.4f}}\\n"
    recommendations += f"  Feasible range: {{bounds[0]:.2f}} - {{bounds[1]:.2f}}\\n"
    recommendations += f"\\n"

recommendations += f"""
PREDICTED PERFORMANCE
=====================
Expected value: {{result.predicted_value:.4f}}

CONFIDENCE
==========
Surrogate model R²: {{result.model_r_squared:.4f}}
Optimization converged: {{result.optimization_success}}

NEXT STEPS
==========
1. Run experiments at recommended conditions
2. Validate predicted performance
3. If actual performance differs significantly, retrain model with new data
4. Consider sensitivity analysis around optimal point
"""

print(recommendations)

# Save to file
with open('optimization_recommendations.txt', 'w') as f:
    f.write(recommendations)

print("\\nRecommendations saved: optimization_recommendations.txt")
print("="*60)
'''
