"""
SHAP Feature Importance Analysis Template

Based on explainable AI pattern from Figure 3:
- Load experimental data with multiple features
- Train machine learning model (RandomForest or XGBoost)
- Apply SHAP (SHapley Additive exPlanations) analysis
- Identify most important features affecting performance
- Visualize feature importance

Example usage:
    template = SHAPAnalysisTemplate()

    # Check if applicable
    if template.is_applicable(hypothesis):
        # Generate protocol
        protocol = template.generate_protocol(
            TemplateCustomizationParams(
                hypothesis=hypothesis,
                custom_variables={
                    'data_path': 'experiments.xlsx',
                    'features': ['Pressure', 'Temperature', 'Time', 'Concentration'],
                    'target': 'Efficiency'
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


class SHAPAnalysisTemplate(TemplateBase):
    """
    Template for SHAP feature importance analysis.

    Workflow:
    1. Load experimental data
    2. Train surrogate ML model
    3. Apply SHAP analysis
    4. Rank features by importance
    5. Visualize SHAP values (summary plot, waterfall plot)
    6. Interpret results for experimental design
    """

    def __init__(self):
        super().__init__(
            name="shap_analysis",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="materials",
            title="SHAP Feature Importance Analysis",
            description=(
                "Identify which experimental parameters most influence "
                "performance using SHAP (SHapley Additive exPlanations), "
                "a game-theory based approach to explain ML models."
            ),
            suitable_for=[
                "Feature importance ranking",
                "Experimental parameter prioritization",
                "Model interpretation and explainability",
                "Design of Experiments guidance"
            ],
            requirements=[
                "Experimental data with multiple features",
                "At least 50 experiments for reliable analysis",
                "SHAP and scikit-learn packages installed"
            ],
            complexity_score=0.6,
            rigor_score=0.9
        )

    def is_applicable(self, hypothesis: Hypothesis) -> bool:
        """
        Check if hypothesis is suitable for SHAP analysis.

        Args:
            hypothesis: Hypothesis to check

        Returns:
            True if hypothesis involves feature importance or parameter ranking
        """
        statement_lower = hypothesis.statement.lower()

        # Check for materials/experimental keywords
        materials_keywords = [
            'material', 'parameter', 'feature', 'factor',
            'condition', 'variable', 'experimental'
        ]

        # Check for importance/ranking keywords
        importance_keywords = [
            'important', 'importance', 'significant', 'key',
            'critical', 'influence', 'affect', 'impact',
            'rank', 'prioritize', 'identify', 'determine',
            'which', 'what factors'
        ]

        has_materials = any(kw in statement_lower for kw in materials_keywords)
        has_importance = any(kw in statement_lower for kw in importance_keywords)

        return has_materials and has_importance

    def generate_protocol(
        self,
        params: TemplateCustomizationParams
    ) -> ExperimentProtocol:
        """
        Generate experiment protocol for SHAP analysis.

        Args:
            params: Customization parameters

        Returns:
            ExperimentProtocol with SHAP analysis steps
        """
        # Extract custom variables
        data_path = params.custom_variables.get('data_path', 'data.xlsx')
        features = params.custom_variables.get('features', ['Feature1', 'Feature2'])
        target = params.custom_variables.get('target', 'Target')
        model_type = params.custom_variables.get('model_type', 'RandomForest')
        sheet_name = params.custom_variables.get('sheet_name', None)

        # Define protocol steps
        steps = [
            ProtocolStep(
                name="load_data",
                description="Load experimental data",
                code_template=self._generate_load_data_code(data_path, sheet_name),
                expected_output="DataFrame with features and target",
                validation=["Check feature columns exist", "Verify target column"]
            ),
            ProtocolStep(
                name="data_preprocessing",
                description="Clean and prepare data for modeling",
                code_template=self._generate_preprocessing_code(features, target),
                expected_output="Clean dataset without missing values",
                validation=["No NaN values", "Sufficient sample size"]
            ),
            ProtocolStep(
                name="train_model",
                description="Train machine learning model",
                code_template=self._generate_training_code(features, target, model_type),
                expected_output="Trained model with performance metrics",
                validation=["Model R² > 0.5", "No overfitting"]
            ),
            ProtocolStep(
                name="shap_analysis",
                description="Compute SHAP values for feature importance",
                code_template=self._generate_shap_code(),
                expected_output="SHAP values and feature importance rankings",
                validation=["SHAP values computed for all samples"]
            ),
            ProtocolStep(
                name="visualize_importance",
                description="Create SHAP visualizations",
                code_template=self._generate_visualization_code(),
                expected_output="SHAP summary plot and waterfall plot",
                validation=["Figures saved successfully"]
            ),
            ProtocolStep(
                name="interpret_results",
                description="Interpret SHAP results for experimental design",
                code_template=self._generate_interpretation_code(target),
                expected_output="Feature ranking and recommendations",
                validation=["Top features identified"]
            )
        ]

        # Define variables
        variables = [
            Variable(
                name=feat,
                description=f"Feature: {feat}",
                type="numerical",
                values=None
            ) for feat in features
        ]

        variables.append(Variable(
            name=target,
            description=f"Target variable: {target}",
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
                description="At least 50 experiments for reliable SHAP"
            ),
            ValidationCheck(
                check_type="model_quality",
                threshold=0.5,
                description="Model R² >= 0.5"
            )
        ]

        # Create protocol
        protocol = ExperimentProtocol(
            title=f"SHAP Analysis: Feature Importance for {target}",
            domain="materials",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            hypothesis_id=params.hypothesis.id if params.hypothesis else None,
            steps=steps,
            variables=variables,
            statistical_tests=[],
            resource_requirements=resources,
            validation_checks=validation_checks,
            estimated_duration_hours=1.0,
            safety_considerations=["None - computational analysis only"],
            ethical_considerations=["Ensure model transparency and interpretability"],
            reproducibility_notes=[
                "Set random seed for reproducibility",
                "Document model hyperparameters and SHAP parameters"
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

# Load data
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

    def _generate_preprocessing_code(
        self,
        features: List[str],
        target: str
    ) -> str:
        """Generate code for data preprocessing."""
        all_cols = features + [target]
        all_cols_str = str(all_cols)

        return f'''
# Data preprocessing
print("\\n" + "="*60)
print("DATA PREPROCESSING")
print("="*60)

# Select features and target
all_columns = {all_cols_str}

# Check for missing columns
missing_cols = [col for col in all_columns if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns: {{missing_cols}}")

# Clean data: remove NaN
df_clean = df[all_columns].dropna()

print(f"Original samples: {{len(df)}}")
print(f"After removing NaN: {{len(df_clean)}}")
print(f"Data retained: {{len(df_clean)/len(df)*100:.1f}}%")

# Check minimum samples
if len(df_clean) < 50:
    print(f"\\n⚠️  WARNING: Only {{len(df_clean)}} samples. Recommend at least 50.")

print("\\nClean data summary:")
print(df_clean.describe())
'''

    def _generate_training_code(
        self,
        features: List[str],
        target: str,
        model_type: str
    ) -> str:
        """Generate code for model training."""
        features_str = str(features)

        return f'''
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

# Prepare data
print("\\n" + "="*60)
print("MODEL TRAINING")
print("="*60)

X = df_clean[{features_str}].values
y = df_clean['{target}'].values

print(f"Features: {features_str}")
print(f"Target: {target}")
print(f"Samples: {{len(X)}}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training samples: {{len(X_train)}}")
print(f"Test samples: {{len(X_test)}}")

# Train model
if '{model_type}' == 'XGBoost':
    try:
        from xgboost import XGBRegressor
        model = XGBRegressor(n_estimators=100, random_state=42)
        print("Using XGBoost")
    except ImportError:
        print("XGBoost not available, using RandomForest")
        model = RandomForestRegressor(n_estimators=100, random_state=42)
else:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    print("Using RandomForest")

print("\\nTraining model...")
model.fit(X_train, y_train)

# Evaluate
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

r2_train = r2_score(y_train, y_train_pred)
r2_test = r2_score(y_test, y_test_pred)
rmse_train = np.sqrt(mean_squared_error(y_train, y_train_pred))
rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))

print("\\nModel Performance:")
print(f"  Training R²: {{r2_train:.4f}}")
print(f"  Test R²: {{r2_test:.4f}}")
print(f"  Training RMSE: {{rmse_train:.4f}}")
print(f"  Test RMSE: {{rmse_test:.4f}}")

# Check for overfitting
if r2_train - r2_test > 0.2:
    print("\\n⚠️  WARNING: Possible overfitting (train-test R² gap > 0.2)")

if r2_test >= 0.5:
    print("✓ Model quality ACCEPTABLE (test R² >= 0.5)")
else:
    print("✗ WARNING: Model quality LOW (test R² < 0.5)")
    print("  SHAP analysis may be unreliable")
'''

    def _generate_shap_code(self) -> str:
        """Generate code for SHAP analysis."""
        return '''
import shap

# SHAP analysis
print("\\n" + "="*60)
print("SHAP ANALYSIS")
print("="*60)

print("Computing SHAP values...")

# Create SHAP explainer
explainer = shap.TreeExplainer(model)

# Compute SHAP values for training set
shap_values = explainer.shap_values(X_train)

print(f"SHAP values shape: {shap_values.shape}")

# Feature importance (mean absolute SHAP value)
mean_abs_shap = np.abs(shap_values).mean(axis=0)

# Create importance ranking
importance_df = pd.DataFrame({
    'Feature': features,
    'Importance': mean_abs_shap
}).sort_values('Importance', ascending=False)

print("\\n" + "="*60)
print("FEATURE IMPORTANCE RANKING")
print("="*60)
print(importance_df.to_string(index=False))
print("="*60)
'''

    def _generate_visualization_code(self) -> str:
        """Generate code for SHAP visualizations."""
        return '''
import matplotlib.pyplot as plt

# SHAP summary plot
print("\\nCreating SHAP visualizations...")

# Summary plot (beeswarm)
plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_train, feature_names=features, show=False)
plt.title('SHAP Summary Plot - Feature Importance', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('shap_summary_plot.png', dpi=300, bbox_inches='tight')
print("SHAP summary plot saved: shap_summary_plot.png")
plt.show()

# Bar plot
plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_train, feature_names=features, plot_type="bar", show=False)
plt.title('SHAP Feature Importance (Bar Plot)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('shap_bar_plot.png', dpi=300, bbox_inches='tight')
print("SHAP bar plot saved: shap_bar_plot.png")
plt.show()

# Waterfall plot for first sample
plt.figure(figsize=(10, 8))
shap.plots.waterfall(shap.Explanation(
    values=shap_values[0],
    base_values=explainer.expected_value,
    data=X_train[0],
    feature_names=features
), show=False)
plt.title('SHAP Waterfall Plot (First Sample)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('shap_waterfall_plot.png', dpi=300, bbox_inches='tight')
print("SHAP waterfall plot saved: shap_waterfall_plot.png")
plt.show()
'''

    def _generate_interpretation_code(self, target: str) -> str:
        """Generate code for interpreting results."""
        return f'''
# Interpret results
print("\\n" + "="*60)
print("INTERPRETATION & RECOMMENDATIONS")
print("="*60)

interpretation = f"""
SHAP FEATURE IMPORTANCE ANALYSIS
=================================

Target Variable: {target}
Model Performance: R² = {{r2_test:.4f}}

FEATURE RANKING (by mean absolute SHAP value):
------------------------------------------------
"""

for idx, row in importance_df.iterrows():
    interpretation += f"{{idx + 1}}. {{row['Feature']}}: {{row['Importance']:.4f}}\\n"

# Identify top features
top_3_features = importance_df.head(3)['Feature'].tolist()

interpretation += f"""

TOP 3 MOST IMPORTANT FEATURES:
-------------------------------
{', '.join(top_3_features)}

EXPERIMENTAL DESIGN RECOMMENDATIONS:
------------------------------------
1. PRIORITY PARAMETERS: Focus experimental effort on optimizing the top 3 features
   as they have the largest impact on {target}.

2. DESIGN OF EXPERIMENTS: When planning new experiments, ensure wide variation
   in top features while fixing or randomizing lower-importance parameters.

3. SENSITIVITY ANALYSIS: Perform sensitivity analysis on top features to understand
   their optimal ranges.

4. IGNORE LOW-IMPACT FEATURES: Features with very low SHAP values (< 0.1) can
   likely be fixed at convenient values without significant performance loss.

INTERPRETATION GUIDE:
---------------------
- SHAP values show the magnitude and direction of each feature's impact
- Positive SHAP = feature increases the target
- Negative SHAP = feature decreases the target
- Wide spread in summary plot = feature has variable impact depending on context

NEXT STEPS:
-----------
1. Validate top features with targeted experiments
2. Perform correlation analysis on top features
3. Optimize top features using multi-parameter optimization
4. Update model as new data becomes available
"""

print(interpretation)

# Save interpretation
with open('shap_interpretation.txt', 'w') as f:
    f.write(interpretation)

print("\\nInterpretation saved: shap_interpretation.txt")
print("="*60)
'''
