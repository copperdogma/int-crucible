# Neuroscience Domain Roadmap

**Based on:** kosmos-figures Figure 4, 7, 8
**Last Updated:** 2025-11-06

---

## Overview

Neuroscience research in Kosmos encompasses:
- **Connectomics:** Neural network structure and scaling laws
- **Neurodegeneration:** Alzheimer's disease, aging-related changes
- **Systems Neuroscience:** Temporal dynamics, gene expression networks

---

## Proven Methodologies from kosmos-figures

### 1. Connectomics & Scaling Laws (Figure 4)

**Discovery:** Universal power-law scaling relationships across species connectomes

#### Data Types
- **Connectome datasets:** Neuron-level connectivity data
- **Properties:** Length (μm), Synapses (count), Degree (connections)
- **Species:** 8 organisms (C. elegans, fly larva, fly brain, zebrafish, mouse, human)
- **Scales:** 100 neurons (human H01) to 129,000 neurons (FlyWire)

#### Analysis Workflow

```python
# Step 1: Load and clean connectome data
datasets = {
    'Celegans': 'Celegans_AggregatedData.csv',
    'FlyWire': 'FlyWire_LocalDensity_AggregatedData.csv',
    'H01': 'H01_LocalDensity_AggregatedData.csv',
    # ... 8 total datasets
}

for name, filename in datasets.items():
    df = pd.read_csv(filename)

    # Step 2: Clean data
    df_clean = df[['Length', 'Synapses', 'Degree']].dropna()
    # Remove non-positive values (important for log-log analysis)
    df_clean = df_clean[(df_clean > 0).all(axis=1)]

    # Step 3: Spearman correlation (non-parametric for power laws)
    rho, p_value = spearmanr(df_clean['Length'], df_clean['Synapses'])

    # Step 4: Log-log analysis
    log_length = np.log10(df_clean['Length'])
    log_synapses = np.log10(df_clean['Synapses'])

    # Linear fit on log-log scale (y = a * x^b)
    slope, intercept, r_value, _, _ = linregress(log_length, log_synapses)
    power_law_exponent = slope  # b in y = a * x^b
    coefficient = 10**intercept  # a in y = a * x^b

    # Step 5: Visualization
    # Log-log scatter plot with large fonts (24pt)
    ax.scatter(df_clean['Length'], df_clean['Synapses'])
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Length (μm)', fontsize=24)
    ax.set_ylabel('Synapses (count)', fontsize=24)

# Step 6: Cross-species comparison
# Compare power law exponents across all 8 species
# Test for universality of scaling relationships
```

#### Key Insights from Figure 4

**Universal Scaling Pattern:**
- Length ∝ Synapses^b (power law relationship)
- Synapses ∝ Degree^c (power law relationship)
- Exponents relatively consistent across species
- Suggests fundamental organizational principles

**Statistical Rigor:**
- Spearman correlation (non-parametric, robust to outliers)
- Log-log visualization to assess linearity
- Multiple species validation (n=8 datasets)
- Sample sizes: 53 to 124,883 neurons

#### Key Tools & APIs

| Tool/Database | Purpose | Access Method |
|--------------|---------|---------------|
| **FlyWire** | Drosophila whole-brain connectome | API + download |
| **MICrONS** | Mouse cortex connectome | Download |
| **Neuroglancer** | 3D visualization | Web interface |
| **Allen Brain Atlas** | Gene expression, connectivity | REST API |
| **OpenConnectome** | Connectome data repository | Download |
| **WormBase** | C. elegans connectome | API |

**Implementation:**
```python
# kosmos/domains/neuroscience/connectomics.py
class ConnectomicsAnalyzer:
    def __init__(self):
        self.flywire_api = FlyWireAPI()
        self.allen_api = AllenBrainAPI()

    def analyze_scaling_laws(self, connectome_data: pd.DataFrame) -> Dict:
        """
        Analyze power law scaling relationships in connectome
        Pattern from: Figure_4_neural_network
        """
        # Clean data
        df = connectome_data[['Length', 'Synapses', 'Degree']].dropna()
        df = df[(df > 0).all(axis=1)]

        results = {}

        # Analyze each property pair
        pairs = [
            ('Length', 'Synapses'),
            ('Synapses', 'Degree'),
            ('Length', 'Degree')
        ]

        for x_var, y_var in pairs:
            # Spearman correlation
            rho, p_val = spearmanr(df[x_var], df[y_var])

            # Log-log linear fit
            log_x = np.log10(df[x_var])
            log_y = np.log10(df[y_var])
            slope, intercept, r_val, _, _ = linregress(log_x, log_y)

            # Power law: y = a * x^b
            exponent = slope
            coefficient = 10**intercept

            results[f'{x_var}_vs_{y_var}'] = {
                'spearman_rho': rho,
                'p_value': p_val,
                'power_law_exponent': exponent,
                'power_law_coefficient': coefficient,
                'r_squared': r_val**2,
                'equation': f'{y_var} = {coefficient:.3f} * {x_var}^{exponent:.3f}',
                'n_neurons': len(df)
            }

        return results

    def cross_species_comparison(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Compare scaling relationships across multiple species"""
        comparison = []

        for species_name, connectome_df in datasets.items():
            scaling = self.analyze_scaling_laws(connectome_df)

            comparison.append({
                'species': species_name,
                'n_neurons': len(connectome_df),
                'length_synapses_exponent': scaling['Length_vs_Synapses']['power_law_exponent'],
                'synapses_degree_exponent': scaling['Synapses_vs_Degree']['power_law_exponent'],
                'length_synapses_rho': scaling['Length_vs_Synapses']['spearman_rho'],
                'length_synapses_p': scaling['Length_vs_Synapses']['p_value']
            })

        return pd.DataFrame(comparison)
```

---

### 2. Alzheimer's Disease Temporal Analysis (Figure 7)

**Discovery:** Temporal ordering of molecular events in AD progression

#### Data Types
- **RNA-seq:** Differential gene expression
- **Temporal data:** Time-series or disease stage data
- **Pathway focus:** Extracellular matrix (ECM), neuroinflammation

#### Analysis Workflow

```python
# Step 1: Differential expression analysis
# Compare AD vs control samples

deseq_results = run_differential_expression(
    counts_matrix=rnaseq_counts,
    sample_groups=['AD', 'Control']
)

# Step 2: Volcano plot
# Visualize log2(fold change) vs -log10(p-value)
volcano_plot(
    log2fc=deseq_results['log2FoldChange'],
    p_values=deseq_results['padj'],
    genes=deseq_results.index
)

# Step 3: Pathway enrichment
# Focus on ECM genes
ecm_genes = get_ecm_genes_from_go()
ecm_enrichment = pathway_enrichment_analysis(
    deg_list=deseq_results[deseq_results['padj'] < 0.05].index,
    pathway_genes=ecm_genes
)

# Step 4: Temporal trajectory
# Order events by effect size or temporal model
temporal_order = order_by_temporal_model(deseq_results)
```

#### Key Tools & APIs

| Tool/Database | Purpose | Access Method |
|--------------|---------|---------------|
| **GEO** | RNA-seq datasets | NCBI API |
| **AMP-AD** | AD omics data | Synapse platform |
| **Allen Brain** | Brain transcriptomics | REST API |
| **GO/KEGG** | Pathway databases | REST API |

**Implementation:**
```python
# kosmos/domains/neuroscience/neurodegeneration.py
class NeurodegenerationAnalyzer:
    def __init__(self):
        self.geo = GEODatabase()
        self.ampad = AMPADPlatform()

    def differential_expression_analysis(self, rnaseq_data: pd.DataFrame,
                                        groups: List[str]) -> pd.DataFrame:
        """
        Perform differential expression analysis
        Pattern from: Figure_7_temporal_events_AD
        """
        # Use DESeq2-like method via Python (pydeseq2 or rpy2)
        from pydeseq2.dds import DeseqDataSet
        from pydeseq2.ds import DeseqStats

        # Create DESeq2 dataset
        dds = DeseqDataSet(
            counts=rnaseq_data,
            metadata=create_metadata(groups),
            design_factors='condition'
        )

        dds.deseq2()
        stat_res = DeseqStats(dds)
        results = stat_res.summary()

        # Add significance flags
        results['significant_0.05'] = results['padj'] < 0.05
        results['significant_0.01'] = results['padj'] < 0.01

        return results

    def temporal_ordering(self, deg_results: pd.DataFrame) -> pd.DataFrame:
        """Order differentially expressed genes by temporal trajectory"""
        # Sort by effect size or temporal model
        deg_results = deg_results.sort_values('log2FoldChange', ascending=False)

        # Assign temporal stages
        deg_results['temporal_stage'] = pd.cut(
            deg_results['log2FoldChange'],
            bins=5,
            labels=['early_down', 'mild_down', 'stable', 'mild_up', 'late_up']
        )

        return deg_results
```

---

### 3. Aging & Neuronal Vulnerability (Figure 8)

**Discovery:** Age-related neuronal vulnerability patterns

#### Focus Areas
- **Differential expression in aging**
- **Cross-species validation** (mouse → human)
- **Replication across independent datasets**

#### Analysis Workflow

```python
# Pattern from Figure 8

# Step 1: Discovery in mouse model
mouse_deg = differential_expression(mouse_rnaseq, ['young', 'aged'])

# Step 2: Identify candidates
candidates = mouse_deg[mouse_deg['padj'] < 0.05]

# Step 3: Validation in human AD data
human_deg = differential_expression(human_ad_rnaseq, ['control', 'AD'])

# Step 4: Cross-species concordance
concordant_genes = find_concordant(mouse_deg, human_deg)

# Step 5: Replication in independent cohort
replication_deg = differential_expression(replication_rnaseq, ['control', 'AD'])
replicated = validate_in_replication(concordant_genes, replication_deg)
```

---

## Experiment Templates for Neuroscience

### Template 1: Connectome Scaling Analysis

```python
# kosmos/experiments/templates/neuroscience/connectome_scaling.py
class ConnectomeScalingTemplate:
    def generate_experiment(self, hypothesis: Hypothesis) -> str:
        """
        Template for connectome power law analysis
        Based on: Figure_4 pattern
        """
        return f'''
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, linregress

# Load connectome data
df = pd.read_csv('{hypothesis.connectome_path}')

# Clean data
df_clean = df[['Length', 'Synapses', 'Degree']].dropna()
df_clean = df_clean[(df_clean > 0).all(axis=1)]

# Analyze scaling relationship
x_var = '{hypothesis.x_variable}'
y_var = '{hypothesis.y_variable}'

# Spearman correlation
rho, p_value = spearmanr(df_clean[x_var], df_clean[y_var])

# Log-log linear fit
log_x = np.log10(df_clean[x_var])
log_y = np.log10(df_clean[y_var])
slope, intercept, r_value, _, _ = linregress(log_x, log_y)

# Power law parameters
exponent = slope
coefficient = 10**intercept

results = {{
    'spearman_rho': rho,
    'p_value': p_value,
    'power_law_exponent': exponent,
    'power_law_coefficient': coefficient,
    'r_squared': r_value**2,
    'equation': f'{{y_var}} = {{coefficient:.3f}} * {{x_var}}^{{exponent:.3f}}'
}}
'''
```

### Template 2: Differential Expression Analysis

```python
# kosmos/experiments/templates/neuroscience/differential_expression.py
class DifferentialExpressionTemplate:
    def generate_experiment(self, hypothesis: Hypothesis) -> str:
        """
        Template for RNA-seq differential expression
        Based on: Figures 7, 8 pattern
        """
        return f'''
import pandas as pd
import numpy as np
from scipy import stats

# Load RNA-seq count data
counts = pd.read_csv('{hypothesis.counts_path}')
metadata = pd.read_csv('{hypothesis.metadata_path}')

# Normalize counts (simple TPM/CPM or use DESeq2)
normalized = counts.div(counts.sum(axis=0), axis=1) * 1e6  # CPM

# Group samples
group1 = metadata[metadata['condition'] == '{hypothesis.condition1}']['sample_id']
group2 = metadata[metadata['condition'] == '{hypothesis.condition2}']['sample_id']

# Differential expression
results = []
for gene in counts.index:
    g1_vals = normalized.loc[gene, group1]
    g2_vals = normalized.loc[gene, group2]

    # Log2 fold change
    log2fc = np.log2(g1_vals.mean() + 1) - np.log2(g2_vals.mean() + 1)

    # T-test
    t_stat, p_val = stats.ttest_ind(g1_vals, g2_vals)

    results.append({{
        'gene': gene,
        'log2_fold_change': log2fc,
        'p_value': p_val,
        'mean_group1': g1_vals.mean(),
        'mean_group2': g2_vals.mean()
    }})

deg_results = pd.DataFrame(results)

# FDR correction
from statsmodels.stats.multitest import multipletests
_, padj, _, _ = multipletests(deg_results['p_value'], method='fdr_bh')
deg_results['padj'] = padj
deg_results['significant'] = padj < 0.05
'''
```

---

## Success Criteria for Neuroscience Domain

### ✅ Connectomics
- [ ] Can analyze power law scaling across multiple datasets
- [ ] Performs log-log analysis with proper data cleaning
- [ ] Validates universality across species
- [ ] Generates publication-quality log-log plots

### ✅ Neurodegeneration
- [ ] Can perform differential expression analysis
- [ ] Generates volcano plots
- [ ] Performs pathway enrichment
- [ ] Validates across independent datasets

### ✅ General Neuroscience
- [ ] APIs integrated for FlyWire, Allen Brain, GEO
- [ ] Can propose novel hypotheses in connectomics and neurodegeneration
- [ ] Cross-species validation workflows

---

## Future Directions

1. **Electrophysiology:** Spike train analysis, LFP analysis
2. **Calcium imaging:** Time-series neural activity
3. **Single-cell transcriptomics:** scRNA-seq in brain
4. **Spatial transcriptomics:** Spatially-resolved gene expression
5. **Network dynamics:** Functional connectivity analysis

---

**Neuroscience Roadmap Complete**
