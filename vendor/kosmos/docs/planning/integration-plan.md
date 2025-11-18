# Kosmos Integration Plan

**Date:** 2025-11-06
**Purpose:** Strategy for integrating kosmos-figures analysis code into our Claude-powered Kosmos implementation

---

## Integration Philosophy

**Core Strategy:** **Proven Analysis + Claude Intelligence = Autonomous AI Scientist**

```
kosmos-figures          Our Kosmos Implementation
┌──────────────┐        ┌────────────────────────┐
│ Manual       │   +    │ Claude-powered         │
│ Analysis     │        │ Intelligence           │
│              │        │                        │
│ • Statistical│        │ • Hypothesis           │
│   methods    │        │   generation           │
│ • Visualiz-  │        │ • Experimental         │
│   ation      │        │   design               │
│ • Data       │        │ • Autonomous           │
│   processing │        │   iteration            │
│              │        │ • Literature           │
│              │        │   integration          │
└──────────────┘        └────────────────────────┘
        │                         │
        └──────────┬──────────────┘
                   ▼
        ┌──────────────────────┐
        │  Fully Autonomous    │
        │   Research System    │
        └──────────────────────┘
```

---

## Phase-by-Phase Integration Mapping

### Phase 5: Experiment Execution Engine

#### 5.2: Code Generation & Execution
**Integration from kosmos-figures:**

| Feature | Source | Implementation |
|---------|--------|----------------|
| Statistical test templates | All figures | Create code generation templates |
| Data loading patterns | All figures | Template: `pd.read_csv()` with validation |
| Cleaning workflows | Figures 2, 4 | Template: NaN removal, filtering |
| Analysis execution | All figures | Execute generated code in sandbox |

**Implementation:**
```python
# kosmos/execution/code_generator.py
class ExperimentCodeGenerator:
    def generate_statistical_comparison(self, hypothesis, data_info):
        """Generate t-test comparison code based on hypothesis"""
        # Template from Figure 2 pattern
        code = f'''
import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv('{data_info.path}')
group1 = df[df['{data_info.group_col}'] == '{hypothesis.group1}']['{data_info.measure_col}']
group2 = df[df['{data_info.group_col}'] == '{hypothesis.group2}']['{data_info.measure_col}']

t_stat, p_value = stats.ttest_ind(group1, group2)
mean_diff = np.mean(group1) - np.mean(group2)

results = {{
    't_statistic': t_stat,
    'p_value': p_value,
    'mean_difference': mean_diff,
    'group1_mean': np.mean(group1),
    'group2_mean': np.mean(group2)
}}
'''
        return code

    def generate_correlation_analysis(self, hypothesis, data_info):
        """Generate correlation analysis code"""
        # Template from Figure 3 pattern
        code = f'''
import pandas as pd
from scipy.stats import pearsonr, spearmanr

df = pd.read_csv('{data_info.path}')
df_clean = df[['{data_info.x_var}', '{data_info.y_var}']].dropna()

x = df_clean['{data_info.x_var}'].values
y = df_clean['{data_info.y_var}'].values

correlation, p_value = pearsonr(x, y)

results = {{
    'correlation': correlation,
    'p_value': p_value,
    'n_samples': len(x)
}}
'''
        return code
```

---

#### 5.3: Data Analysis Pipeline
**Integration from kosmos-figures:**

| Component | Source | Integration Priority |
|-----------|--------|---------------------|
| T-test implementation | Figure 2 | **P0 - Critical** |
| Correlation analysis | Figures 3, 4 | **P0 - Critical** |
| Linear regression | Figure 3 | **P1 - High** |
| Log transformation | Figures 2, 4 | **P0 - Critical** |
| Group-wise comparison | Figure 2 | **P0 - Critical** |

**Implementation:**
```python
# kosmos/execution/data_analysis.py
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple

class DataAnalyzer:
    """Reusable analysis methods extracted from kosmos-figures"""

    @staticmethod
    def ttest_comparison(data: pd.DataFrame, group_col: str,
                        measure_col: str, groups: Tuple[str, str]) -> Dict:
        """
        Perform t-test comparison between two groups
        Pattern from: Figure_2_hypothermia_nucleotide_salvage
        """
        group1_data = data[data[group_col] == groups[0]][measure_col]
        group2_data = data[data[group_col] == groups[1]][measure_col]

        t_stat, p_value = stats.ttest_ind(group1_data, group2_data)

        return {
            't_statistic': t_stat,
            'p_value': p_value,
            'group1_mean': np.mean(group1_data),
            'group2_mean': np.mean(group2_data),
            'group1_std': np.std(group1_data),
            'group2_std': np.std(group2_data),
            'log2_fold_change': np.log2(np.mean(group1_data) / np.mean(group2_data)),
            'significant_0.05': p_value < 0.05
        }

    @staticmethod
    def correlation_analysis(data: pd.DataFrame, x_col: str, y_col: str,
                            method: str = 'pearson') -> Dict:
        """
        Perform correlation analysis with linear regression
        Pattern from: Figure_3_perovskite_solar_cell
        """
        # Remove missing values
        df_clean = data[[x_col, y_col]].dropna()
        x = df_clean[x_col].values
        y = df_clean[y_col].values

        # Correlation
        if method == 'pearson':
            corr, p_val = stats.pearsonr(x, y)
        else:
            corr, p_val = stats.spearmanr(x, y)

        # Linear regression
        slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)

        # Significance
        if p_val < 0.001:
            significance = "***"
        elif p_val < 0.01:
            significance = "**"
        elif p_val < 0.05:
            significance = "*"
        else:
            significance = "ns"

        return {
            'correlation': corr,
            'p_value': p_val,
            'r_squared': r_value**2,
            'slope': slope,
            'intercept': intercept,
            'std_err': std_err,
            'significance': significance,
            'n_samples': len(x)
        }

    @staticmethod
    def log_log_scaling_analysis(data: pd.DataFrame, x_col: str, y_col: str) -> Dict:
        """
        Analyze scaling relationships on log-log scale
        Pattern from: Figure_4_neural_network
        """
        # Clean data - remove NaN and non-positive values
        df_clean = data[[x_col, y_col]].dropna()
        df_clean = df_clean[(df_clean[x_col] > 0) & (df_clean[y_col] > 0)]

        x = df_clean[x_col].values
        y = df_clean[y_col].values

        # Log-transform
        log_x = np.log10(x)
        log_y = np.log10(y)

        # Spearman correlation (non-parametric)
        rho, p_value = stats.spearmanr(x, y)

        # Linear fit on log-log (power law: y = a * x^b)
        slope, intercept, r_value, _, _ = stats.linregress(log_x, log_y)

        # Convert back: log(y) = log(a) + b*log(x) => y = a * x^b
        a = 10**intercept
        b = slope

        return {
            'spearman_rho': rho,
            'p_value': p_value,
            'power_law_exponent': b,
            'power_law_coefficient': a,
            'r_squared': r_value**2,
            'equation': f'y = {a:.3f} * x^{b:.3f}',
            'n_samples': len(x)
        }
```

---

#### 5.4: Statistical Validation
**Integration from kosmos-figures:**

```python
# kosmos/execution/statistics.py
class StatisticalValidator:
    """Statistical validation methods from kosmos-figures"""

    @staticmethod
    def apply_significance_threshold(p_value: float) -> Dict:
        """Standard significance thresholding from kosmos-figures"""
        return {
            'p_value': p_value,
            'significant_0.05': p_value < 0.05,
            'significant_0.01': p_value < 0.01,
            'significant_0.001': p_value < 0.001,
            'significance_label': (
                '***' if p_value < 0.001 else
                '**' if p_value < 0.01 else
                '*' if p_value < 0.05 else
                'ns'
            )
        }

    @staticmethod
    def calculate_effect_size(group1: np.ndarray, group2: np.ndarray) -> float:
        """Cohen's d effect size calculation"""
        mean_diff = np.mean(group1) - np.mean(group2)
        pooled_std = np.sqrt((np.std(group1)**2 + np.std(group2)**2) / 2)
        return mean_diff / pooled_std if pooled_std > 0 else 0
```

---

### Phase 6: Analysis & Interpretation

#### 6.3: Visualization Generation
**Integration from kosmos-figures:**

| Visualization | Source | Priority | Complexity |
|--------------|--------|----------|------------|
| Volcano plot | Figure 2, 7 | **P0** | Medium |
| Heatmap | Figure 2 | **P0** | Medium |
| Scatter + regression | Figure 3 | **P0** | Low |
| Log-log plot | Figure 4 | **P1** | Low |
| Box plot with points | Multiple | **P1** | Low |

**Implementation:**
```python
# kosmos/analysis/visualization.py
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Optional

class PublicationVisualizer:
    """Publication-quality visualization templates from kosmos-figures"""

    def __init__(self):
        # Set publication standards from kosmos-figures
        plt.rcParams.update({
            'font.family': 'Arial',
            'font.size': 10,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'pdf.fonttype': 42,  # TrueType for editability
            'ps.fonttype': 42
        })

    def volcano_plot(self, log2fc: np.ndarray, p_values: np.ndarray,
                    labels: Optional[np.ndarray] = None,
                    fc_threshold: float = 0.5, p_threshold: float = 0.05,
                    title: str = "Volcano Plot",
                    output_path: str = "volcano_plot.png"):
        """
        Create volcano plot: -log10(p) vs log2(fold change)
        Pattern from: Figure_2_hypothermia_nucleotide_salvage
        """
        fig, ax = plt.subplots(figsize=(8, 6))

        # Calculate -log10(p)
        log_p = -np.log10(p_values)

        # Color by significance
        colors = ['red' if (abs(fc) > fc_threshold and p < p_threshold)
                  else 'gray'
                  for fc, p in zip(log2fc, p_values)]

        # Scatter plot
        ax.scatter(log2fc, log_p, c=colors, alpha=0.7, s=60)

        # Threshold lines
        ax.axhline(y=-np.log10(p_threshold), color='black',
                  linestyle='--', alpha=0.7, label=f'p={p_threshold}')
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)

        # Labels
        ax.set_xlabel('Log2 Fold Change')
        ax.set_ylabel('-log10(p-value)')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Annotate significant points if labels provided
        if labels is not None:
            for i, (fc, p, label) in enumerate(zip(log2fc, p_values, labels)):
                if abs(fc) > fc_threshold and p < p_threshold:
                    ax.annotate(label, (fc, -np.log10(p)),
                              xytext=(5, 5), textcoords='offset points',
                              fontsize=8, ha='left')

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def custom_heatmap(self, data: np.ndarray, row_labels: list, col_labels: list,
                      title: str = "Heatmap",
                      cmap: str = 'RdBu_r',
                      vmin: float = None, vmax: float = None,
                      output_path: str = "heatmap.png"):
        """
        Create custom heatmap with publication formatting
        Pattern from: Figure_2_hypothermia_nucleotide_salvage
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        # Create heatmap
        im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=vmin, vmax=vmax)

        # Set ticks and labels
        ax.set_xticks(range(len(col_labels)))
        ax.set_yticks(range(len(row_labels)))
        ax.set_xticklabels(col_labels, fontsize=12)
        ax.set_yticklabels(row_labels, fontsize=12)
        ax.set_title(title, pad=12, fontsize=14)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Value', rotation=270, labelpad=20, fontsize=12)

        # Add text annotations
        for i in range(len(row_labels)):
            for j in range(len(col_labels)):
                text = f'{data[i, j]:.2f}'
                color = 'white' if abs(data[i, j]) > (vmax or 1) * 0.5 else 'black'
                ax.text(j, i, text, ha='center', va='center',
                       color=color, fontsize=10, weight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def scatter_with_regression(self, x: np.ndarray, y: np.ndarray,
                               x_label: str, y_label: str, title: str,
                               output_path: str = "scatter_regression.png"):
        """
        Scatter plot with linear regression fit
        Pattern from: Figure_3_perovskite_solar_cell
        """
        from scipy import stats as sp_stats

        fig, ax = plt.subplots(figsize=(6, 6))

        # Scatter plot - using kosmos-figures color scheme
        ax.scatter(x, y, alpha=0.7, s=60, color='#abd9e9',
                  edgecolors='black', linewidth=0.5)

        # Linear fit - using kosmos-figures red color
        slope, intercept, r_value, p_value, _ = sp_stats.linregress(x, y)
        x_trend = np.linspace(x.min(), x.max(), 100)
        y_trend = slope * x_trend + intercept

        ax.plot(x_trend, y_trend, color="#d7191c", linestyle="--",
               alpha=0.8, linewidth=2,
               label=f'Linear fit (r = {r_value:.3f}, p = {p_value:.4f})')

        # Formatting (kosmos-figures style)
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(title, fontsize=12, pad=20)
        ax.legend(fontsize=11)

        # Remove grid and top/right spines
        ax.grid(False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path

    def log_log_plot(self, x: np.ndarray, y: np.ndarray,
                    x_label: str, y_label: str, title: str,
                    color: str = '#0072B2',
                    output_path: str = "log_log_plot.png"):
        """
        Log-log scatter plot for power law relationships
        Pattern from: Figure_4_neural_network
        """
        fig, ax = plt.subplots(figsize=(6, 6))

        # Log-log scatter
        ax.scatter(x, y, alpha=0.6, s=40, color=color, edgecolors='none')

        # Set log scales
        ax.set_xscale('log')
        ax.set_yscale('log')

        # Labels with large fonts (kosmos-figures style for panels)
        ax.set_xlabel(x_label, fontsize=24)
        ax.set_ylabel(y_label, fontsize=24)
        ax.set_title(title, fontsize=24)
        ax.tick_params(labelsize=20, width=2, length=7)

        # Thicker spines
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # No grid
        ax.grid(False)

        plt.tight_layout()
        plt.savefig(output_path, dpi=600, bbox_inches='tight')  # High DPI for panels
        plt.close()

        return output_path
```

---

## Custom Claude-Powered Enhancements

### What kosmos-figures CANNOT do (our value-add):

#### 1. **Hypothesis Generation (Phase 3)**
```python
# kosmos/agents/hypothesis_generator.py
class HypothesisGeneratorAgent:
    def generate_from_literature(self, research_question: str) -> List[Hypothesis]:
        """Use Claude to generate testable hypotheses"""
        prompt = f'''
        Given this research question: "{research_question}"

        And these recent papers: {self.literature_context}

        Generate 5 testable hypotheses that:
        1. Are novel (not directly tested in existing literature)
        2. Can be tested with available data/methods
        3. Follow from logical reasoning about the domain

        For each hypothesis, specify:
        - The hypothesis statement
        - Expected experimental approach
        - Required data type
        - Predicted outcome
        '''
        # Claude generates hypotheses
        # We can then use kosmos-figures patterns to TEST them
```

#### 2. **Experiment Design (Phase 4)**
```python
# kosmos/agents/experiment_designer.py
class ExperimentDesignerAgent:
    def design_experiment(self, hypothesis: Hypothesis) -> ExperimentProtocol:
        """Use Claude to design experiment, then generate code from kosmos-figures templates"""

        # Claude determines experiment type
        experiment_type = self.classify_experiment(hypothesis)

        # Map to kosmos-figures template
        if experiment_type == "group_comparison":
            template = self.templates.get_ttest_template()  # From Figure 2
        elif experiment_type == "correlation":
            template = self.templates.get_correlation_template()  # From Figure 3
        elif experiment_type == "scaling_law":
            template = self.templates.get_scaling_template()  # From Figure 4

        # Fill template with hypothesis-specific parameters
        return template.instantiate(hypothesis.parameters)
```

#### 3. **Result Interpretation (Phase 6)**
```python
# kosmos/agents/data_analyst.py
class DataAnalystAgent:
    def interpret_results(self, results: Dict, hypothesis: Hypothesis) -> Interpretation:
        """Use Claude to interpret statistical results in scientific context"""

        prompt = f'''
        Hypothesis: {hypothesis.statement}

        Statistical Results:
        - T-statistic: {results['t_statistic']}
        - P-value: {results['p_value']}
        - Mean difference: {results['mean_diff']}
        - Effect size: {results['effect_size']}

        Context from literature: {self.lit_context}

        Interpret these results:
        1. Do they support or reject the hypothesis?
        2. What is the biological/physical significance?
        3. How do they compare to prior work?
        4. What are potential confounds?
        5. What follow-up experiments are needed?
        '''

        # Claude provides nuanced interpretation
        # Not just "p < 0.05 = significant" but scientific reasoning
```

#### 4. **Iterative Refinement (Phase 7)**
```python
# kosmos/core/feedback.py
class FeedbackLoop:
    def refine_hypothesis(self, original_hypothesis: Hypothesis,
                         results: Dict, interpretation: Interpretation) -> Hypothesis:
        """Use Claude to refine hypothesis based on results"""

        # kosmos-figures had manual iterations (r1, r2, r11, r23...)
        # We automate this with Claude

        prompt = f'''
        Original hypothesis: {original_hypothesis}
        Results: {results}
        Interpretation: {interpretation}

        Based on these findings, propose a refined hypothesis that:
        1. Addresses limitations discovered
        2. Explores unexpected findings
        3. Tests alternative explanations
        4. Builds on successful results
        '''

        return claude_refine(prompt)
```

---

## Integration Timeline

### Week 1-2: Core Analysis Library
- [ ] Extract statistical functions (t-test, correlation, regression)
- [ ] Implement data cleaning utilities
- [ ] Create visualization templates (volcano, heatmap, scatter)
- [ ] Unit tests for all functions

### Week 3-4: Code Generation Templates
- [ ] Template: Group comparison (Figure 2 pattern)
- [ ] Template: Correlation analysis (Figure 3 pattern)
- [ ] Template: Scaling analysis (Figure 4 pattern)
- [ ] Template: Multi-modal integration (Figure 5 pattern)
- [ ] Template instantiation from hypothesis

### Week 5-6: Claude Integration
- [ ] Hypothesis → Experiment mapping logic
- [ ] Result → Interpretation pipeline
- [ ] Feedback loop for refinement
- [ ] Test on simple research questions

### Week 7-8: Domain-Specific Extensions
- [ ] Biology: Pathway categorization (from Figure 2)
- [ ] Materials: Parameter optimization (from Figure 3)
- [ ] Neuroscience: Network analysis (from Figure 4)
- [ ] Genomics: Multi-modal scoring (from Figure 5)

---

## Success Criteria

### ✅ Phase 5-6 Complete When:
1. Can execute all statistical methods from kosmos-figures autonomously
2. Can generate publication-quality figures automatically
3. Results match kosmos-figures outputs when given same data
4. Code generation works for 4+ experiment types

### ✅ Full Integration Complete When:
1. System can replicate ANY kosmos-figures discovery autonomously
2. Claude can propose novel experiments in same domains
3. Iterative refinement produces better hypotheses than initial
4. Publication-quality outputs without manual intervention

---

## Risk Mitigation

### Risk 1: Code generation produces invalid code
**Mitigation:**
- Extensive template testing
- Sandbox execution with error handling
- Validation before execution

### Risk 2: Statistical methods don't match edge cases
**Mitigation:**
- Comprehensive unit tests against kosmos-figures notebooks
- Edge case testing (NaN, zeros, single values)
- Graceful degradation

### Risk 3: Visualizations not publication-quality
**Mitigation:**
- Exact replication of kosmos-figures formatting
- Visual regression testing
- User review step for important figures

---

## Next Steps

1. **Immediate:** Begin extracting core statistical functions
2. **This week:** Create visualization template library
3. **Next week:** Implement first code generation template
4. **Month 1:** Integration with Claude for hypothesis → experiment pipeline

---

**Integration Plan Complete** | Next: Domain Roadmaps
