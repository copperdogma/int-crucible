# Biology Domain Roadmap

**Based on:** kosmos-figures Figure 2, 5, 6
**Last Updated:** 2025-11-06

---

## Overview

Biology research in Kosmos encompasses:
- **Metabolomics:** Small molecule profiling and pathway analysis
- **Genomics:** GWAS, QTL analysis, genetic variant interpretation
- **Systems Biology:** Multi-modal data integration
- **Disease Biology:** Cardiovascular, metabolic diseases

---

## Proven Methodologies from kosmos-figures

### 1. Metabolomics Analysis (Figure 2)

**Discovery:** Hypothermia enhances nucleotide salvage pathways over de novo synthesis

#### Data Types
- **Metabolomics profiling:** 245 polar metabolites
- **Sample groups:** Control, Treatment, Recovery
- **Format:** CSV with samples as columns, metabolites as rows
- **Typical size:** 200-500 metabolites × 10-50 samples

#### Analysis Workflow

```python
# Step 1: Data loading and organization
df = pd.read_csv('metabolomics_data.csv')
metadata_row = df.iloc[0, 1:]  # First row = group labels
df_data = df.iloc[1:].set_index('Compound Name')

# Step 2: Metabolite categorization
purines = ['Adenine', 'Adenosine', 'AMP', 'ADP', 'ATP', 'Guanine', ...]
pyrimidines = ['Cytosine', 'Cytidine', 'CMP', 'CDP', 'CTP', 'Uracil', ...]
salvage_precursors = ['Adenosine', 'Guanosine', 'Cytidine', ...]
synthesis_products = ['AMP', 'GMP', 'CMP', 'IMP', ...]

# Step 3: Statistical comparison
for metabolite in metabolites_of_interest:
    group1_values = df_log2.loc[metabolite, group1_samples]
    group2_values = df_log2.loc[metabolite, group2_samples]
    t_stat, p_value = stats.ttest_ind(group1_values, group2_values)
    log2fc = np.mean(group1_values) - np.mean(group2_values)

# Step 4: Pathway-level analysis
purine_salvage_decreased = count_decreased(salvage_precursors, purine_metabolites)
pyrimidine_synthesis_increased = count_increased(synthesis_products, pyrimidine_metabolites)

# Step 5: Visualization
# - Volcano plot: all metabolites
# - Heatmap: salvage→synthesis pairs
# - Pathway summary: bar charts by category
```

#### Key Tools & APIs

| Tool/Database | Purpose | Integration Method |
|--------------|---------|-------------------|
| **KEGG** | Pathway mapping | REST API |
| **MetaboLights** | Public metabolomics data | FTP/API |
| **HMDB** | Human metabolite database | Web scraping/download |
| **MetaCyc** | Metabolic pathways | BioCyc API |

**Implementation:**
```python
# kosmos/domains/biology/metabolomics.py
class MetabolomicsAnalyzer:
    def __init__(self):
        self.kegg_client = KEGGClient()
        self.hmdb_db = HMDBDatabase()

    def categorize_metabolite(self, compound_name: str) -> Dict:
        """Categorize metabolite by biochemical pathway"""
        # Query KEGG for pathway information
        pathways = self.kegg_client.get_pathways(compound_name)

        # Classify as purine/pyrimidine/other
        if any('purine' in p.lower() for p in pathways):
            category = 'purine'
        elif any('pyrimidine' in p.lower() for p in pathways):
            category = 'pyrimidine'
        else:
            category = 'other'

        # Determine salvage vs synthesis
        if compound_name.endswith('osine') or compound_name in ['Adenine', 'Guanine', ...]:
            metabolite_type = 'salvage_precursor'
        elif 'monophosphate' in compound_name.lower() or 'diphosphate' in compound_name.lower():
            metabolite_type = 'synthesis_product'
        else:
            metabolite_type = 'intermediate'

        return {
            'category': category,
            'metabolite_type': metabolite_type,
            'pathways': pathways
        }

    def analyze_pathway_pattern(self, results_df: pd.DataFrame) -> Dict:
        """Analyze pathway-level patterns (e.g., salvage vs synthesis)"""
        # Group by pathway categories
        purine_salvage = results_df[
            (results_df['category'] == 'purine') &
            (results_df['metabolite_type'] == 'salvage_precursor')
        ]
        purine_synthesis = results_df[
            (results_df['category'] == 'purine') &
            (results_df['metabolite_type'] == 'synthesis_product')
        ]

        # Calculate mean fold changes
        salvage_mean_fc = purine_salvage['log2_fc'].mean()
        synthesis_mean_fc = purine_synthesis['log2_fc'].mean()

        # Test for significant difference
        t_stat, p_val = stats.ttest_ind(
            purine_salvage['log2_fc'],
            purine_synthesis['log2_fc']
        )

        return {
            'salvage_mean_fc': salvage_mean_fc,
            'synthesis_mean_fc': synthesis_mean_fc,
            'pattern': 'salvage_decreased_synthesis_increased' if (
                salvage_mean_fc < 0 and synthesis_mean_fc > 0
            ) else 'other',
            'p_value': p_val
        }
```

---

### 2. Genomics & GWAS Analysis (Figure 5)

**Discovery:** SSR1 SNPs protective against Type 2 Diabetes via expression regulation

#### Data Types
- **GWAS data:** SNPs, p-values, beta coefficients, posterior probabilities
- **eQTL/pQTL:** Expression/protein quantitative trait loci
- **ATAC-seq:** Chromatin accessibility
- **TF binding predictions:** Transcription factor disruption
- **Typical sources:** UK Biobank, GTEx, ENCODE

#### Analysis Workflow

```python
# Multi-modal integration with composite scoring

# Step 1: Load all data modalities
gwas_df = load_gwas_data()
eqtl_df = load_eqtl_data()
pqtl_df = load_pqtl_data()
atac_df = load_atac_data()
tf_df = load_tf_predictions()

# Step 2: Calculate component scores
for snp in snps:
    # GWAS Evidence (0-10 points)
    gwas_score = calculate_gwas_score(
        posterior_prob=gwas_df.loc[snp, 'posterior'],
        effect_size=abs(gwas_df.loc[snp, 'beta'])
    )

    # QTL Evidence (0-15 points)
    qtl_score = calculate_qtl_score(
        has_eqtl=snp in eqtl_df.index,
        has_pqtl=snp in pqtl_df.index,
        concordant=check_concordance(gwas_df.loc[snp], eqtl_df.loc[snp])
    )

    # TF Disruption (0-10 points)
    tf_score = calculate_tf_score(
        n_tfs=len(tf_df[tf_df['snp'] == snp]),
        chip_validated=any(tf_df[tf_df['snp'] == snp]['remap_support'])
    )

    # Protective Evidence (0-15 points)
    protective_score = 15 if check_protective(snp) else 0

    # Total composite score (max 55)
    total_score = gwas_score + qtl_score + tf_score + protective_score + expression_score

# Step 3: Rank and filter
top_mechanisms = results_df.nlargest(10, 'total_score')

# Step 4: Validate concordance
for mechanism in top_mechanisms:
    gwas_direction = np.sign(mechanism['gwas_beta'])
    qtl_direction = np.sign(mechanism['eqtl_beta'])
    concordant = (gwas_direction == qtl_direction)
```

#### Key Tools & APIs

| Tool/Database | Purpose | API/Access |
|--------------|---------|------------|
| **GWAS Catalog** | GWAS summary statistics | REST API |
| **GTEx Portal** | eQTL/sQTL data | Portal API |
| **ENCODE** | ATAC-seq, ChIP-seq | REST API |
| **ReMap** | TF binding sites | Download |
| **UK Biobank** | Large-scale GWAS | Application required |
| **dbSNP** | SNP annotations | NCBI E-utilities |
| **Ensembl** | Variant effect prediction | REST API |

**Implementation:**
```python
# kosmos/domains/biology/genomics.py
class GenomicsAnalyzer:
    def __init__(self):
        self.gwas_catalog = GWASCatalogAPI()
        self.gtex = GTExAPI()
        self.encode = ENCODEAPI()

    def multi_modal_integration(self, snp_id: str, gene: str) -> Dict:
        """Integrate multiple genomic data modalities for SNP-gene pair"""

        # Fetch GWAS data
        gwas_data = self.gwas_catalog.get_variant(snp_id)

        # Fetch eQTL data
        eqtl_data = self.gtex.get_eqtl(snp_id, gene)

        # Fetch pQTL data
        pqtl_data = self.gtex.get_pqtl(snp_id, gene)

        # Fetch ATAC-seq data
        atac_data = self.encode.get_atac_peaks(snp_id)

        # Calculate composite score
        score = self.calculate_composite_score(
            gwas_data, eqtl_data, pqtl_data, atac_data
        )

        return {
            'snp': snp_id,
            'gene': gene,
            'gwas': gwas_data,
            'eqtl': eqtl_data,
            'pqtl': pqtl_data,
            'atac': atac_data,
            'composite_score': score,
            'concordant': self.check_concordance(gwas_data, eqtl_data)
        }

    def calculate_composite_score(self, gwas, eqtl, pqtl, atac) -> float:
        """
        Composite scoring framework from Figure 5
        Total: 55 points
        """
        score = 0

        # GWAS Evidence (0-10)
        if gwas:
            if gwas['posterior_prob'] > 0.1:
                score += 5
            elif gwas['posterior_prob'] > 0.01:
                score += 3
            if abs(gwas['beta']) > 0.05:
                score += 5

        # QTL Evidence (0-15)
        if eqtl:
            score += 5
        if pqtl:
            score += 5
        if eqtl and gwas and np.sign(eqtl['beta']) == np.sign(gwas['beta']):
            score += 5  # Concordance bonus

        # ATAC-seq (0-5)
        if atac and atac['significant']:
            score += 5

        return score
```

---

### 3. Cardiovascular Biology (Figure 6)

**Discovery:** SOD2 role in myocardial fibrosis

#### Focus Areas
- Gene expression in cardiac tissue
- Fibrosis biomarkers
- ROS/oxidative stress pathways

#### Tools & Databases
- **GEO (Gene Expression Omnibus):** Public gene expression data
- **BioGPS:** Gene expression atlas
- **STRING:** Protein-protein interactions

---

## Experiment Templates for Biology

### Template 1: Metabolomics Group Comparison

```python
# kosmos/experiments/templates/biology/metabolomics_comparison.py
class MetabolomicsComparisonTemplate:
    def generate_experiment(self, hypothesis: Hypothesis) -> ExperimentCode:
        """
        Template for metabolomics group comparison
        Based on: Figure_2 pattern
        """
        return f'''
import pandas as pd
import numpy as np
from scipy import stats

# Load metabolomics data
df = pd.read_csv('{hypothesis.data_path}')

# Extract groups
group1_samples = {hypothesis.group1_samples}
group2_samples = {hypothesis.group2_samples}

# Metabolites to analyze
metabolites = {hypothesis.metabolites_of_interest}

# Log2 transformation
df_numeric = df.apply(pd.to_numeric, errors='coerce')
df_log2 = np.log2(df_numeric + 1)

# Statistical comparison
results = []
for metabolite in metabolites:
    group1_vals = df_log2.loc[metabolite, group1_samples]
    group2_vals = df_log2.loc[metabolite, group2_samples]

    t_stat, p_val = stats.ttest_ind(group1_vals, group2_vals)
    log2fc = np.mean(group1_vals) - np.mean(group2_vals)

    results.append({{
        'metabolite': metabolite,
        't_statistic': t_stat,
        'p_value': p_val,
        'log2_fold_change': log2fc,
        'significant': p_val < 0.05
    }})

results_df = pd.DataFrame(results)
'''
```

### Template 2: GWAS Multi-Modal Integration

```python
# kosmos/experiments/templates/biology/gwas_multimodal.py
class GWASMultiModalTemplate:
    def generate_experiment(self, hypothesis: Hypothesis) -> ExperimentCode:
        """
        Template for GWAS + eQTL + ATAC multi-modal integration
        Based on: Figure_5 pattern
        """
        return f'''
import pandas as pd
import numpy as np

# Load data modalities
gwas = pd.read_csv('{hypothesis.gwas_path}')
eqtl = pd.read_csv('{hypothesis.eqtl_path}')
atac = pd.read_csv('{hypothesis.atac_path}')

# Merge on SNP ID
merged = gwas.merge(eqtl, on='snp_id', how='left')
merged = merged.merge(atac, on='snp_id', how='left')

# Calculate composite scores
def composite_score(row):
    score = 0
    # GWAS evidence
    if row['gwas_p'] < 1e-8:
        score += 10
    # eQTL evidence
    if pd.notna(row['eqtl_beta']):
        score += 5
    # Concordance
    if np.sign(row['gwas_beta']) == np.sign(row['eqtl_beta']):
        score += 5
    return score

merged['score'] = merged.apply(composite_score, axis=1)

# Rank mechanisms
top_mechanisms = merged.nlargest(10, 'score')
'''
```

---

## Success Criteria for Biology Domain

### ✅ Metabolomics
- [ ] Can automatically categorize metabolites by pathway
- [ ] Can perform pathway-level statistical analysis
- [ ] Can detect salvage vs synthesis patterns
- [ ] Generates publication-quality heatmaps and volcano plots

### ✅ Genomics
- [ ] Can integrate GWAS + eQTL + ATAC data
- [ ] Implements composite scoring framework
- [ ] Validates effect concordance across modalities
- [ ] Ranks mechanisms by evidence strength

### ✅ General Biology
- [ ] APIs integrated for KEGG, GWAS Catalog, GTEx, ENCODE
- [ ] Can propose novel hypotheses in metabolomics and genomics
- [ ] Autonomous iteration from discovery to validation

---

## Future Directions

1. **Proteomics integration:** Mass spec data analysis
2. **Single-cell analysis:** scRNA-seq, scATAC-seq
3. **Spatial transcriptomics:** Tissue spatial patterns
4. **Multi-omics:** Integration across genomics, transcriptomics, proteomics, metabolomics

---

**Biology Roadmap Complete**
