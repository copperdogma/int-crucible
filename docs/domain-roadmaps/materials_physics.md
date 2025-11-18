# Materials Science & Physics Domain Roadmap

**Based on:** kosmos-figures Figure 3
**Last Updated:** 2025-11-06

---

## Overview

Materials science and physics research in Kosmos encompasses:
- **Materials optimization:** Parameter-performance relationships
- **Solar cells:** Perovskite and photovoltaic optimization
- **Parameter space exploration:** Multi-variable optimization
- **Machine learning interpretation:** SHAP analysis for feature importance

---

## Proven Methodologies from kosmos-figures

### 1. Perovskite Solar Cell Optimization (Figure 3)

**Discovery:** Solvent partial pressure negatively correlates with solar cell efficiency (Jsc)

#### Data Types
- **Experimental data:** Excel/CSV with multiple parameters
- **Parameters:** Solvent partial pressure, temperature, humidity, material composition
- **Output metrics:** Short-circuit current density (Jsc), efficiency, fill factor
- **Typical size:** 100-1000 experiments with 10-50 parameters

#### Analysis Workflow

```python
# Step 1: Load experimental data
df = pd.read_excel('Summary table analysis.xlsx')

# Step 2: Examine parameter space
print(f"Parameters: {df.columns.tolist()}")
print(f"Experiments: {len(df)}")

# Step 3: Correlation analysis
x_col = 'Spin coater: Solvent Partial Pressure [ppm]'
y_col = 'Short circuit current density, Jsc [mA/cm2]'

# Remove missing values
df_clean = df[[x_col, y_col]].dropna()
x = df_clean[x_col].values
y = df_clean[y_col].values

# Step 4: Statistical analysis
from scipy.stats import pearsonr, linregress

# Pearson correlation
correlation, p_value = pearsonr(x, y)

# Linear regression
slope, intercept, r_value, p_value_reg, std_err = linregress(x, y)

print(f"Correlation: r = {correlation:.4f}, p = {p_value:.4f}")
print(f"R²: {r_value**2:.4f}")
print(f"Equation: Jsc = {slope:.4f} * SPP + {intercept:.4f}")

# Step 5: Significance testing
if p_value < 0.001:
    significance = "***"
elif p_value < 0.01:
    significance = "**"
elif p_value < 0.05:
    significance = "*"
else:
    significance = "ns"

# Step 6: Visualization
# Scatter plot with linear fit
# Colors: data points = #abd9e9, regression line = #d7191c
ax.scatter(x, y, alpha=0.7, s=60, color='#abd9e9',
          edgecolors='black', linewidth=0.5)

# Linear trend
x_trend = np.linspace(x.min(), x.max(), 100)
y_trend = slope * x_trend + intercept
ax.plot(x_trend, y_trend, color="#d7191c", linestyle="--",
       alpha=0.8, linewidth=2, label=f'r = {correlation:.3f}')

# Clean formatting (no grid, remove top/right spines)
ax.grid(False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

#### Key Result from Figure 3

**Strong Negative Correlation:**
- Solvent partial pressure ↔ Jsc: **r = -0.708, p < 0.001**
- Interpretation: Higher solvent pressure → Lower solar cell efficiency
- Mechanism: Solvent vapor affects film formation during spin coating
- Actionable: Optimize coating environment for low solvent pressure

#### Additional Analyses in Figure 3

**SHAP Analysis (Feature Importance):**
```python
# Uses machine learning model (random forest, XGBoost) to predict Jsc
# Then applies SHAP (SHapley Additive exPlanations) to interpret model

import shap
from sklearn.ensemble import RandomForestRegressor

# Train ML model
X = df[feature_columns]  # All parameters
y = df['Jsc']

model = RandomForestRegressor(n_estimators=100)
model.fit(X, y)

# SHAP analysis
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# Visualize feature importance
shap.summary_plot(shap_values, X)

# Analyze individual predictions
shap.force_plot(explainer.expected_value, shap_values[0], X.iloc[0])
```

**2D Parameter Space Exploration:**
- Visualize Jsc as function of two parameters simultaneously
- Identify optimal regions in parameter space
- Contour plots or heatmaps

---

## Key Tools & Data Sources

### Experimental Databases

| Database | Purpose | Access Method |
|----------|---------|---------------|
| **Materials Project** | Computed material properties | REST API |
| **NOMAD** | Materials data repository | Web/API |
| **AFLOW** | Material property calculations | API |
| **Citrination** | Materials informatics | API (registration required) |
| **Perovskite Database** | Perovskite solar cell data | Download |

### Simulation Tools

| Tool | Purpose | Integration |
|------|---------|-------------|
| **ASE (Atomic Simulation Environment)** | Atomistic simulations | Python library |
| **Pymatgen** | Materials analysis | Python library |
| **VASP** | DFT calculations | Executable (license required) |
| **LAMMPS** | Molecular dynamics | Python interface |
| **OpenFOAM** | CFD simulations | Python wrapper |

### Machine Learning Libraries

| Library | Purpose | Use Case |
|---------|---------|----------|
| **scikit-learn** | Standard ML algorithms | Regression, classification |
| **SHAP** | Model interpretation | Feature importance |
| **XGBoost** | Gradient boosting | High-performance models |
| **PyTorch** | Deep learning | Neural networks |

---

## Implementation

```python
# kosmos/domains/materials/optimization.py
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List

class MaterialsOptimizer:
    """Materials optimization and parameter exploration"""

    def __init__(self):
        self.materials_project = MaterialsProjectAPI()

    def correlation_analysis(self, data: pd.DataFrame,
                            parameter: str, metric: str) -> Dict:
        """
        Analyze correlation between experimental parameter and performance metric
        Pattern from: Figure_3_perovskite_solar_cell
        """
        # Clean data
        df_clean = data[[parameter, metric]].dropna()
        x = df_clean[parameter].values
        y = df_clean[metric].values

        # Pearson correlation
        correlation, p_value = stats.pearsonr(x, y)

        # Linear regression
        slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)

        # Statistical significance
        if p_value < 0.001:
            significance = "***"
        elif p_value < 0.01:
            significance = "**"
        elif p_value < 0.05:
            significance = "*"
        else:
            significance = "ns"

        return {
            'correlation': correlation,
            'p_value': p_value,
            'r_squared': r_value**2,
            'slope': slope,
            'intercept': intercept,
            'std_err': std_err,
            'significance': significance,
            'n_samples': len(x),
            'equation': f'{metric} = {slope:.4f} * {parameter} + {intercept:.4f}'
        }

    def parameter_space_optimization(self, data: pd.DataFrame,
                                    parameters: List[str],
                                    objective: str,
                                    maximize: bool = True) -> Dict:
        """
        Multi-parameter optimization to find optimal conditions
        """
        from sklearn.ensemble import RandomForestRegressor
        from scipy.optimize import differential_evolution

        # Train surrogate model
        X = data[parameters]
        y = data[objective]

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        # Define objective function
        def objective_function(params):
            prediction = model.predict([params])[0]
            return -prediction if maximize else prediction

        # Optimization bounds (use data min/max)
        bounds = [(X[p].min(), X[p].max()) for p in parameters]

        # Global optimization
        result = differential_evolution(objective_function, bounds)

        optimal_params = {p: val for p, val in zip(parameters, result.x)}
        optimal_value = -result.fun if maximize else result.fun

        return {
            'optimal_parameters': optimal_params,
            'predicted_value': optimal_value,
            'optimization_success': result.success
        }

    def shap_analysis(self, data: pd.DataFrame,
                     features: List[str], target: str) -> Dict:
        """
        SHAP analysis for feature importance
        Pattern from: Figure_3 SHAP analysis
        """
        import shap
        from sklearn.ensemble import RandomForestRegressor

        # Prepare data
        X = data[features]
        y = data[target]

        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        # SHAP analysis
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        # Calculate mean absolute SHAP values (feature importance)
        feature_importance = np.abs(shap_values).mean(axis=0)
        importance_df = pd.DataFrame({
            'feature': features,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)

        return {
            'shap_values': shap_values,
            'feature_importance': importance_df,
            'model_performance': {
                'r_squared': model.score(X, y),
                'n_features': len(features),
                'n_samples': len(X)
            }
        }

    def design_of_experiments(self, parameter_ranges: Dict[str, tuple],
                             n_experiments: int) -> pd.DataFrame:
        """
        Generate optimal experimental design (Latin Hypercube Sampling)
        """
        from scipy.stats import qmc

        # Latin Hypercube Sampling
        sampler = qmc.LatinHypercube(d=len(parameter_ranges))
        sample = sampler.random(n=n_experiments)

        # Scale to parameter ranges
        lower_bounds = [bounds[0] for bounds in parameter_ranges.values()]
        upper_bounds = [bounds[1] for bounds in parameter_ranges.values()]

        scaled_sample = qmc.scale(sample, lower_bounds, upper_bounds)

        # Create DataFrame
        experiments = pd.DataFrame(
            scaled_sample,
            columns=list(parameter_ranges.keys())
        )

        return experiments
```

---

## Experiment Templates for Materials Science

### Template 1: Parameter-Performance Correlation

```python
# kosmos/experiments/templates/materials/parameter_correlation.py
class ParameterCorrelationTemplate:
    def generate_experiment(self, hypothesis: Hypothesis) -> str:
        """
        Template for parameter-performance correlation analysis
        Based on: Figure_3 pattern
        """
        return f'''
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, linregress

# Load experimental data
df = pd.read_excel('{hypothesis.data_path}')

# Define parameter and metric
parameter = '{hypothesis.parameter}'
metric = '{hypothesis.metric}'

# Clean data
df_clean = df[[parameter, metric]].dropna()
x = df_clean[parameter].values
y = df_clean[metric].values

# Correlation analysis
correlation, p_value = pearsonr(x, y)

# Linear regression
slope, intercept, r_value, p_value_reg, std_err = linregress(x, y)

# Significance
significance = (
    "***" if p_value < 0.001 else
    "**" if p_value < 0.01 else
    "*" if p_value < 0.05 else
    "ns"
)

results = {{
    'correlation': correlation,
    'p_value': p_value,
    'r_squared': r_value**2,
    'slope': slope,
    'intercept': intercept,
    'significance': significance,
    'equation': f'{{metric}} = {{slope:.4f}} * {{parameter}} + {{intercept:.4f}}'
}}
'''
```

### Template 2: Multi-Parameter Optimization

```python
# kosmos/experiments/templates/materials/optimization.py
class OptimizationTemplate:
    def generate_experiment(self, hypothesis: Hypothesis) -> str:
        """
        Template for multi-parameter optimization
        """
        return f'''
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from scipy.optimize import differential_evolution

# Load data
df = pd.read_csv('{hypothesis.data_path}')

# Define parameters and objective
parameters = {hypothesis.parameters}
objective = '{hypothesis.objective}'

# Train surrogate model
X = df[parameters]
y = df[objective]

model = RandomForestRegressor(n_estimators=100)
model.fit(X, y)

# Optimization
def objective_function(params):
    pred = model.predict([params])[0]
    return -pred  # Maximize (minimize negative)

bounds = [(X[p].min(), X[p].max()) for p in parameters]
result = differential_evolution(objective_function, bounds)

optimal_params = {{p: val for p, val in zip(parameters, result.x)}}
predicted_value = -result.fun

results = {{
    'optimal_parameters': optimal_params,
    'predicted_value': predicted_value,
    'success': result.success
}}
'''
```

### Template 3: SHAP Feature Importance

```python
# kosmos/experiments/templates/materials/shap_analysis.py
class SHAPAnalysisTemplate:
    def generate_experiment(self, hypothesis: Hypothesis) -> str:
        """
        Template for SHAP feature importance analysis
        Based on: Figure_3 SHAP analysis
        """
        return f'''
import pandas as pd
import numpy as np
import shap
from sklearn.ensemble import RandomForestRegressor

# Load data
df = pd.read_csv('{hypothesis.data_path}')

# Features and target
features = {hypothesis.features}
target = '{hypothesis.target}'

X = df[features]
y = df[target]

# Train model
model = RandomForestRegressor(n_estimators=100)
model.fit(X, y)

# SHAP analysis
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# Feature importance
importance = np.abs(shap_values).mean(axis=0)
importance_df = pd.DataFrame({{
    'feature': features,
    'importance': importance
}}).sort_values('importance', ascending=False)

results = {{
    'feature_importance': importance_df.to_dict('records'),
    'model_r_squared': model.score(X, y)
}}
'''
```

---

## Success Criteria for Materials Science Domain

### ✅ Parameter Optimization
- [ ] Can analyze parameter-performance correlations
- [ ] Performs multi-parameter optimization
- [ ] Generates publication-quality scatter plots with regression fits
- [ ] Provides statistical significance assessment

### ✅ Machine Learning Integration
- [ ] SHAP analysis for feature importance
- [ ] Surrogate modeling for expensive simulations
- [ ] Design of experiments (DoE) generation

### ✅ General Materials Science
- [ ] APIs integrated for Materials Project, NOMAD
- [ ] Can propose novel material compositions
- [ ] Autonomous optimization loops

---

## Future Directions

1. **High-throughput DFT:** Automated quantum chemistry calculations
2. **Crystal structure prediction:** Generative models for new materials
3. **Process optimization:** Manufacturing parameter optimization
4. **Multi-objective optimization:** Pareto front exploration
5. **Active learning:** Bayesian optimization for experimental design

---

**Materials Science & Physics Roadmap Complete**
