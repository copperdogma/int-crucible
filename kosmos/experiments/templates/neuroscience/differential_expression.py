"""
Differential Expression Analysis Template

Based on kosmos-figures Figures 7, 8 patterns:
- Load RNA-seq count data
- Perform differential expression analysis (DESeq2-like)
- Temporal trajectory modeling
- Pathway enrichment analysis
- Volcano plot visualization
- Cross-species validation (optional)

Example usage:
    template = DifferentialExpressionTemplate()

    # Check if applicable
    if template.is_applicable(hypothesis):
        # Generate protocol
        protocol = template.generate_protocol(
            TemplateCustomizationParams(
                hypothesis=hypothesis,
                custom_variables={
                    'counts_data_path': 'rnaseq_counts.csv',
                    'metadata_path': 'sample_metadata.csv',
                    'condition_column': 'disease_status',
                    'case_label': 'AD',
                    'control_label': 'Control'
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


class DifferentialExpressionTemplate(TemplateBase):
    """
    Template for differential gene expression analysis.

    Implements Figures 7, 8 patterns:
    1. Load RNA-seq count data and metadata
    2. Differential expression analysis (DESeq2 or t-test)
    3. Multiple testing correction
    4. Temporal trajectory modeling (optional)
    5. Pathway enrichment analysis (optional)
    6. Volcano plot visualization
    7. Cross-species validation (optional)
    """

    def __init__(self):
        super().__init__(
            name="differential_expression",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="neuroscience",
            title="Differential Gene Expression Analysis",
            description=(
                "Identify differentially expressed genes between conditions "
                "(e.g., disease vs control). Supports temporal trajectory modeling "
                "and pathway enrichment. Based on Figures 7, 8 patterns."
            ),
            suitable_for=[
                "RNA-seq differential expression",
                "Alzheimer's disease gene expression",
                "Neurodegeneration studies",
                "Temporal gene expression changes",
                "Cross-species validation"
            ],
            requirements=[
                "RNA-seq count matrix (genes × samples)",
                "Sample metadata with condition labels",
                "At least 3 samples per condition for reliable statistics",
                "Count data (not normalized FPKM/TPM)"
            ],
            complexity_score=0.8,
            rigor_score=0.9
        )

    def is_applicable(self, hypothesis: Hypothesis) -> bool:
        """
        Check if hypothesis is suitable for differential expression analysis.

        Args:
            hypothesis: Hypothesis to check

        Returns:
            True if hypothesis involves gene expression comparison
        """
        statement_lower = hypothesis.statement.lower()

        # Check for gene expression keywords
        expression_keywords = [
            'gene expression', 'differential expression', 'rna-seq',
            'transcriptom', 'mrna', 'gene', 'expressed'
        ]

        # Check for comparison keywords
        comparison_keywords = [
            'compare', 'comparison', 'difference', 'vs', 'versus',
            'between', 'change', 'altered', 'dysregulated'
        ]

        # Check for neuroscience context
        neuro_keywords = [
            'alzheimer', 'parkinson', 'neurodegener', 'brain',
            'neuron', 'neural', 'aging', 'dementia', 'cognitive'
        ]

        has_expression = any(kw in statement_lower for kw in expression_keywords)
        has_comparison = any(kw in statement_lower for kw in comparison_keywords)
        has_neuro = any(kw in statement_lower for kw in neuro_keywords)

        # Require expression + comparison, neuroscience context is helpful but not required
        return has_expression and has_comparison

    def generate_protocol(self, params: TemplateCustomizationParams) -> ExperimentProtocol:
        """
        Generate differential expression analysis protocol.

        Args:
            params: Customization parameters

        Returns:
            Complete experiment protocol

        Required custom_variables:
            - counts_data_path: Path to RNA-seq counts CSV (genes × samples)
            - metadata_path: Path to sample metadata CSV
            - condition_column: Column name in metadata with condition labels
            - case_label: Label for case samples (e.g., "AD")
            - control_label: Label for control samples (e.g., "Control")

        Optional custom_variables:
            - use_pydeseq2: Use pydeseq2 if available (default: True)
            - p_threshold: Adjusted p-value threshold (default: 0.05)
            - fc_threshold: Log2 fold change threshold (default: 1.0)
            - perform_temporal: Perform temporal ordering (default: False)
            - pathway_genes: Dict of pathway genes for enrichment (default: None)
            - mouse_data_path: Mouse data for cross-species validation (default: None)
        """
        # Extract parameters
        counts_path = params.custom_variables.get('counts_data_path', 'rnaseq_counts.csv')
        metadata_path = params.custom_variables.get('metadata_path', 'sample_metadata.csv')
        condition_column = params.custom_variables.get('condition_column', 'condition')
        case_label = params.custom_variables.get('case_label', 'Case')
        control_label = params.custom_variables.get('control_label', 'Control')

        use_pydeseq2 = params.custom_variables.get('use_pydeseq2', True)
        p_threshold = params.custom_variables.get('p_threshold', 0.05)
        fc_threshold = params.custom_variables.get('fc_threshold', 1.0)
        perform_temporal = params.custom_variables.get('perform_temporal', False)
        pathway_genes = params.custom_variables.get('pathway_genes', None)
        mouse_data_path = params.custom_variables.get('mouse_data_path', None)

        # Create protocol steps
        steps = [
            ProtocolStep(
                name="load_data",
                description="Load RNA-seq counts and sample metadata",
                code_template=self._generate_load_data_code(
                    counts_path, metadata_path, condition_column
                ),
                expected_output="Counts matrix and metadata DataFrames",
                validation=[
                    "Counts matrix has genes as rows, samples as columns",
                    "Metadata has sample_id column matching counts columns",
                    f"Metadata has '{condition_column}' column"
                ]
            ),
            ProtocolStep(
                name="differential_expression",
                description="Perform differential expression analysis",
                code_template=self._generate_deg_analysis_code(
                    condition_column, case_label, control_label, use_pydeseq2
                ),
                expected_output="NeurodegenerationResult with gene-level statistics",
                validation=[
                    "All genes have log2 fold change and p-values",
                    "Adjusted p-values calculated (FDR correction)",
                    "At least some significant genes found"
                ]
            ),
            ProtocolStep(
                name="summarize_results",
                description="Summarize differential expression results",
                code_template=self._generate_summary_code(p_threshold, fc_threshold),
                expected_output="Summary statistics and significant gene lists",
                validation=["Summary statistics computed"]
            ),
            ProtocolStep(
                name="volcano_plot",
                description="Generate volcano plot visualization",
                code_template=self._generate_volcano_code(p_threshold, fc_threshold),
                expected_output="Volcano plot PNG file",
                validation=["Volcano plot created"]
            )
        ]

        # Add temporal ordering if requested
        if perform_temporal:
            steps.append(
                ProtocolStep(
                    name="temporal_ordering",
                    description="Order genes by temporal trajectory",
                    code_template=self._generate_temporal_code(),
                    expected_output="Genes assigned to temporal stages",
                    validation=["Temporal stages assigned to significant genes"]
                )
            )

        # Add pathway enrichment if pathway genes provided
        if pathway_genes:
            steps.append(
                ProtocolStep(
                    name="pathway_enrichment",
                    description="Test pathway enrichment in DEGs",
                    code_template=self._generate_enrichment_code(pathway_genes),
                    expected_output="PathwayEnrichmentResult with Fisher's test",
                    validation=["Enrichment p-value calculated"]
                )
            )

        # Add cross-species validation if mouse data provided
        if mouse_data_path:
            steps.append(
                ProtocolStep(
                    name="cross_species_validation",
                    description="Validate findings in mouse model",
                    code_template=self._generate_cross_species_code(
                        mouse_data_path, metadata_path, condition_column,
                        case_label, control_label
                    ),
                    expected_output="CrossSpeciesValidation results",
                    validation=["Concordance calculated for common genes"]
                )
            )

        # Variables
        variables = [
            Variable(
                name="condition_column",
                type="string",
                value=condition_column,
                description="Metadata column with condition labels"
            ),
            Variable(
                name="case_label",
                type="string",
                value=case_label,
                description="Label for case samples"
            ),
            Variable(
                name="control_label",
                type="string",
                value=control_label,
                description="Label for control samples"
            ),
            Variable(
                name="p_threshold",
                type="float",
                value=str(p_threshold),
                description="Adjusted p-value significance threshold"
            )
        ]

        # Statistical tests
        statistical_tests = [
            StatisticalTestSpec(
                test_type="differential_expression",
                parameters={
                    "method": "DESeq2" if use_pydeseq2 else "t-test",
                    "correction": "Benjamini-Hochberg",
                    "significance_level": p_threshold
                },
                description="Differential expression with multiple testing correction"
            )
        ]

        if pathway_genes:
            statistical_tests.append(
                StatisticalTestSpec(
                    test_type="fisher_exact",
                    parameters={"alternative": "greater"},
                    description="Pathway enrichment test"
                )
            )

        # Validation checks
        validation_checks = [
            ValidationCheck(
                check_type="sample_size",
                parameters={"min_samples_per_group": 3},
                description="Ensure sufficient samples per condition"
            ),
            ValidationCheck(
                check_type="data_quality",
                parameters={
                    "count_data": True,
                    "non_negative": True
                },
                description="Ensure count data is valid"
            ),
            ValidationCheck(
                check_type="statistical_significance",
                parameters={"p_threshold": p_threshold},
                description="Check for significant genes"
            )
        ]

        # Resource requirements
        resources = ResourceRequirements(
            estimated_runtime_seconds=300,  # 5 minutes
            memory_mb=2048,  # 2 GB for DESeq2
            cpu_cores=2,
            requires_gpu=False
        )

        # Create protocol
        protocol = ExperimentProtocol(
            title=f"Differential Expression: {case_label} vs {control_label}",
            hypothesis_id=params.hypothesis.id if params.hypothesis else "unknown",
            experiment_type=self.experiment_type,
            domain=self.domain,
            steps=steps,
            variables=variables,
            statistical_tests=statistical_tests,
            validation_checks=validation_checks,
            resource_requirements=resources,
            expected_duration_hours=0.5,
            reproducibility_notes=[
                "DESeq2 analysis is deterministic with same random seed",
                "Results depend on count filtering thresholds",
                "Multiple testing correction uses Benjamini-Hochberg FDR"
            ]
        )

        return protocol

    def _generate_load_data_code(
        self,
        counts_path: str,
        metadata_path: str,
        condition_column: str
    ) -> str:
        """Generate code to load RNA-seq data"""
        return f'''
import pandas as pd
import numpy as np
from kosmos.domains.neuroscience.neurodegeneration import NeurodegenerationAnalyzer

# Load RNA-seq counts (genes × samples)
counts_df = pd.read_csv('{counts_path}', index_col=0)

# Load sample metadata
metadata_df = pd.read_csv('{metadata_path}')

# Ensure sample_id column exists
if 'sample_id' not in metadata_df.columns:
    if metadata_df.index.name == 'sample_id':
        metadata_df = metadata_df.reset_index()
    else:
        # Use first column as sample_id
        metadata_df['sample_id'] = metadata_df.iloc[:, 0]

print(f"Loaded counts: {{counts_df.shape[0]}} genes × {{counts_df.shape[1]}} samples")
print(f"Loaded metadata: {{len(metadata_df)}} samples")

# Verify condition column
if '{condition_column}' not in metadata_df.columns:
    raise ValueError(f"Condition column '{{'{condition_column}'}}' not found in metadata. Available: {{list(metadata_df.columns)}}")

print(f"\\nCondition distribution:")
print(metadata_df['{condition_column}'].value_counts())

# Verify sample overlap
counts_samples = set(counts_df.columns)
metadata_samples = set(metadata_df['sample_id'])
overlap = counts_samples & metadata_samples

print(f"\\nSample overlap: {{len(overlap)}} / {{len(counts_samples)}} counts samples")

if len(overlap) < len(counts_samples):
    print(f"Warning: {{len(counts_samples) - len(overlap)}} samples in counts not in metadata")
'''

    def _generate_deg_analysis_code(
        self,
        condition_column: str,
        case_label: str,
        control_label: str,
        use_pydeseq2: bool
    ) -> str:
        """Generate code for differential expression analysis"""
        return f'''
from kosmos.domains.neuroscience.neurodegeneration import NeurodegenerationAnalyzer

# Initialize analyzer
analyzer = NeurodegenerationAnalyzer()

# Run differential expression analysis
deg_results = analyzer.differential_expression_analysis(
    counts_matrix=counts_df,
    sample_metadata=metadata_df,
    condition_column='{condition_column}',
    case_label='{case_label}',
    control_label='{control_label}',
    min_count=10,
    use_pydeseq2={use_pydeseq2}
)

# Display summary
print(f"\\n=== Differential Expression Results ===")
summary = deg_results.get_summary()
for key, value in summary.items():
    print(f"{{key}}: {{value}}")
'''

    def _generate_summary_code(self, p_threshold: float, fc_threshold: float) -> str:
        """Generate code to summarize results"""
        return f'''
# Get significant genes
sig_genes = deg_results.get_significant_genes(p_threshold={p_threshold})
sig_up = deg_results.get_significant_genes(p_threshold={p_threshold}, direction='up')
sig_down = deg_results.get_significant_genes(p_threshold={p_threshold}, direction='down')

print(f"\\n=== Significant Genes (padj < {p_threshold}) ===")
print(f"Total significant: {{len(sig_genes)}}")
print(f"Upregulated: {{len(sig_up)}}")
print(f"Downregulated: {{len(sig_down)}}")

# Top upregulated genes
if sig_up:
    print(f"\\nTop 10 Upregulated:")
    top_up = sorted(sig_up, key=lambda x: x.log2_fold_change, reverse=True)[:10]
    for gene in top_up:
        print(f"  {{gene.gene_id}}: log2FC={{gene.log2_fold_change:.2f}}, padj={{gene.adjusted_p_value:.2e}}")

# Top downregulated genes
if sig_down:
    print(f"\\nTop 10 Downregulated:")
    top_down = sorted(sig_down, key=lambda x: x.log2_fold_change)[:10]
    for gene in top_down:
        print(f"  {{gene.gene_id}}: log2FC={{gene.log2_fold_change:.2f}}, padj={{gene.adjusted_p_value:.2e}}")

# Convert to DataFrame for export
deg_df = deg_results.to_dataframe()
deg_df.to_csv('differential_expression_results.csv', index=False)
print(f"\\nSaved results to: differential_expression_results.csv")
'''

    def _generate_volcano_code(self, p_threshold: float, fc_threshold: float) -> str:
        """Generate code for volcano plot"""
        return f'''
import matplotlib.pyplot as plt
import seaborn as sns

# Generate volcano plot data
volcano_data = analyzer.generate_volcano_plot_data(
    deg_results=deg_results,
    p_threshold={p_threshold},
    fc_threshold={fc_threshold}
)

# Create volcano plot
fig, ax = plt.subplots(figsize=(10, 8))

# Color map
colors = {{
    'upregulated': 'red',
    'downregulated': 'blue',
    'not_significant': 'gray'
}}

for sig_type in ['not_significant', 'downregulated', 'upregulated']:
    data_subset = volcano_data[volcano_data['significance'] == sig_type]
    ax.scatter(
        data_subset['log2FoldChange'],
        data_subset['-log10_padj'],
        c=colors[sig_type],
        alpha=0.5,
        s=20,
        label=sig_type.replace('_', ' ').title()
    )

# Add significance threshold lines
ax.axhline(y=-np.log10({p_threshold}), color='black', linestyle='--', linewidth=1, alpha=0.7)
ax.axvline(x={fc_threshold}, color='black', linestyle='--', linewidth=1, alpha=0.7)
ax.axvline(x=-{fc_threshold}, color='black', linestyle='--', linewidth=1, alpha=0.7)

ax.set_xlabel('Log2 Fold Change', fontsize=14)
ax.set_ylabel('-Log10 Adjusted P-value', fontsize=14)
ax.set_title('Volcano Plot: Differential Gene Expression', fontsize=16)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('volcano_plot.png', dpi=300, bbox_inches='tight')
print(f"\\nSaved volcano plot: volcano_plot.png")
plt.show()
'''

    def _generate_temporal_code(self) -> str:
        """Generate code for temporal ordering"""
        return f'''
# Temporal ordering of genes
deg_results_temporal = analyzer.temporal_ordering(deg_results, n_stages=5)

# Summarize temporal stages
temporal_df = deg_results_temporal.to_dataframe()
temporal_sig = temporal_df[temporal_df['significant_0.05']]

print(f"\\n=== Temporal Trajectory Analysis ===")
print(f"\\nGenes by temporal stage:")
stage_counts = temporal_sig['temporal_stage'].value_counts()
print(stage_counts)

# Save temporal results
temporal_sig.to_csv('temporal_gene_expression.csv', index=False)
print(f"\\nSaved temporal results: temporal_gene_expression.csv")
'''

    def _generate_enrichment_code(self, pathway_genes: Dict[str, List[str]]) -> str:
        """Generate code for pathway enrichment"""
        pathway_genes_str = str(pathway_genes)

        return f'''
# Pathway enrichment analysis
pathway_genes_dict = {pathway_genes_str}

enrichment_results = {{}}

for pathway_name, gene_list in pathway_genes_dict.items():
    result = analyzer.pathway_enrichment(
        deg_results=deg_results,
        pathway_genes=gene_list,
        pathway_name=pathway_name,
        pathway_id=pathway_name.lower().replace(' ', '_')
    )
    enrichment_results[pathway_name] = result

# Display enrichment results
print(f"\\n=== Pathway Enrichment Results ===")
for pathway_name, result in enrichment_results.items():
    print(f"\\n{{pathway_name}}:")
    print(f"  Genes in pathway: {{result.n_genes_in_pathway}}")
    print(f"  Significant genes: {{result.n_genes_significant}}")
    print(f"  Enrichment p-value: {{result.enrichment_pvalue:.2e}}")
    print(f"  Odds ratio: {{result.odds_ratio:.2f}}")
    print(f"  Enriched: {{result.is_enriched}}")

pathway_enrichment = enrichment_results
'''

    def _generate_cross_species_code(
        self,
        mouse_data_path: str,
        metadata_path: str,
        condition_column: str,
        case_label: str,
        control_label: str
    ) -> str:
        """Generate code for cross-species validation"""
        return f'''
# Load mouse data for cross-species validation
mouse_counts = pd.read_csv('{mouse_data_path}', index_col=0)
mouse_metadata = pd.read_csv('{metadata_path}')  # Assumes same metadata structure

# Analyze mouse data
mouse_results = analyzer.differential_expression_analysis(
    counts_matrix=mouse_counts,
    sample_metadata=mouse_metadata,
    condition_column='{condition_column}',
    case_label='{case_label}',
    control_label='{control_label}'
)

print(f"\\nMouse analysis: {{mouse_results.n_significant}} significant genes")

# Cross-species validation
validation_results = analyzer.cross_species_validation(
    mouse_results=mouse_results,
    human_results=deg_results,
    gene_mapping=None  # Assumes same gene IDs; provide mapping if needed
)

# Summarize concordance
concordant = [v for v in validation_results if v.is_concordant]
strong_concordant = [v for v in concordant if v.concordance_strength == 'strong']

print(f"\\n=== Cross-Species Validation ===")
print(f"Genes compared: {{len(validation_results)}}")
print(f"Concordant genes: {{len(concordant)}} ({{len(concordant)/len(validation_results)*100:.1f}}%)")
print(f"Strong concordance: {{len(strong_concordant)}}")

# Top concordant genes
if concordant:
    print(f"\\nTop 10 Concordant Genes:")
    top_concordant = sorted(concordant, key=lambda v: abs(v.human_log2fc or 0), reverse=True)[:10]
    for v in top_concordant:
        print(f"  {{v.gene_id}}: Human log2FC={{v.human_log2fc:.2f}}, Mouse log2FC={{v.mouse_log2fc:.2f}}")

cross_species_validation = validation_results
'''
