"""
GWAS Multi-Modal Integration Template

Based on kosmos-figures Figure 5 pattern:
- Integrate GWAS + eQTL + pQTL + ATAC-seq data
- Calculate composite scores (0-55 points)
- Validate effect concordance
- Rank SNP-gene mechanisms by evidence

Example usage:
    template = GWASMultiModalTemplate()

    # Check if applicable
    if template.is_applicable(hypothesis):
        # Generate protocol
        protocol = template.generate_protocol(
            TemplateCustomizationParams(
                hypothesis=hypothesis,
                custom_variables={
                    'snp_ids': ['rs7903146', 'rs12255372', ...],
                    'gene': 'TCF7L2',
                    'gwas_path': 'gwas_data.csv',
                    'eqtl_path': 'eqtl_data.csv',
                    'pqtl_path': 'pqtl_data.csv',
                    'atac_path': 'atac_data.csv'
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


class GWASMultiModalTemplate(TemplateBase):
    """
    Template for GWAS multi-modal integration experiments.

    Implements the Figure 5 analysis pattern:
    1. Load GWAS, eQTL, pQTL, ATAC-seq data
    2. Integrate data for SNP-gene pairs
    3. Calculate composite scores (0-55 points)
    4. Validate effect concordance
    5. Rank mechanisms by evidence strength
    """

    def __init__(self):
        super().__init__(
            name="gwas_multimodal",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="biology",
            title="GWAS Multi-Modal Integration",
            description=(
                "Integrate GWAS, eQTL, pQTL, and ATAC-seq data to identify "
                "and rank genetic mechanisms. Based on SSR1-T2D protective "
                "mechanism analysis pattern (Figure 5)."
            ),
            suitable_for=[
                "GWAS follow-up analysis",
                "Genetic variant interpretation",
                "Multi-modal genomic integration",
                "Disease mechanism discovery"
            ],
            requirements=[
                "GWAS summary statistics (SNP, p-value, beta)",
                "eQTL data (optional but recommended)",
                "pQTL data (optional)",
                "ATAC-seq peaks (optional)",
                "SNP-gene pairs to analyze"
            ],
            complexity_score=0.7,
            rigor_score=0.9
        )

    def is_applicable(self, hypothesis: Hypothesis) -> bool:
        """
        Check if hypothesis is suitable for GWAS multi-modal integration.

        Args:
            hypothesis: Hypothesis to check

        Returns:
            True if hypothesis involves genetic variants and gene function
        """
        statement_lower = hypothesis.statement.lower()

        # Check for genomics keywords
        genomics_keywords = [
            'gwas', 'snp', 'variant', 'genetic', 'gene',
            'eqtl', 'pqtl', 'qtl', 'association',
            'polymorphism', 'allele', 'locus'
        ]

        # Check for mechanism keywords
        mechanism_keywords = [
            'mechanism', 'regulation', 'expression',
            'protective', 'risk', 'effect', 'influence',
            'modulate', 'control', 'affect'
        ]

        has_genomics = any(kw in statement_lower for kw in genomics_keywords)
        has_mechanism = any(kw in statement_lower for kw in mechanism_keywords)

        return has_genomics and has_mechanism

    def generate_protocol(
        self,
        params: TemplateCustomizationParams
    ) -> ExperimentProtocol:
        """
        Generate GWAS multi-modal integration protocol.

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
        snp_ids = custom_vars.get('snp_ids', [])
        gene = custom_vars.get('gene', '')
        gwas_path = custom_vars.get('gwas_path', 'gwas_data.csv')
        eqtl_path = custom_vars.get('eqtl_path', None)
        pqtl_path = custom_vars.get('pqtl_path', None)
        atac_path = custom_vars.get('atac_path', None)
        min_score = custom_vars.get('min_composite_score', 10.0)
        top_n = custom_vars.get('top_n_mechanisms', 10)

        # Validate
        if not snp_ids:
            raise ValueError("Must specify snp_ids list")
        if not gene:
            raise ValueError("Must specify gene symbol")

        # Define variables
        variables = [
            Variable(
                name="snp_ids",
                description="List of SNP identifiers to analyze",
                value=snp_ids
            ),
            Variable(
                name="gene",
                description="Gene symbol for mechanism analysis",
                value=gene
            ),
            Variable(
                name="gwas_path",
                description="Path to GWAS summary statistics CSV",
                value=gwas_path
            ),
            Variable(
                name="eqtl_path",
                description="Path to eQTL data CSV (optional)",
                value=eqtl_path
            ),
            Variable(
                name="pqtl_path",
                description="Path to pQTL data CSV (optional)",
                value=pqtl_path
            ),
            Variable(
                name="atac_path",
                description="Path to ATAC-seq peaks CSV (optional)",
                value=atac_path
            ),
            Variable(
                name="min_composite_score",
                description="Minimum composite score for filtering",
                value=min_score
            ),
            Variable(
                name="top_n_mechanisms",
                description="Number of top mechanisms to report",
                value=top_n
            ),
        ]

        # Define protocol steps
        steps = [
            ProtocolStep(
                name="load_data",
                description="Load all genomic data modalities",
                code_template=self._generate_load_data_code(
                    gwas_path, eqtl_path, pqtl_path, atac_path
                ),
                expected_duration_minutes=3,
                required_resources=ResourceRequirements(
                    cpu_cores=1,
                    memory_gb=4.0
                )
            ),
            ProtocolStep(
                name="multimodal_integration",
                description="Integrate GWAS + eQTL + pQTL + ATAC data",
                code_template=self._generate_integration_code(
                    snp_ids, gene
                ),
                expected_duration_minutes=10,
                required_resources=ResourceRequirements(
                    cpu_cores=2,
                    memory_gb=4.0
                )
            ),
            ProtocolStep(
                name="rank_mechanisms",
                description="Rank SNP-gene mechanisms by composite score",
                code_template=self._generate_ranking_code(
                    min_score, top_n
                ),
                expected_duration_minutes=2,
                required_resources=ResourceRequirements(
                    cpu_cores=1,
                    memory_gb=2.0
                )
            ),
            ProtocolStep(
                name="visualize_results",
                description="Create evidence plots and mechanism summaries",
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
                test_name="Concordance Analysis",
                test_type="non-parametric",
                description="Check effect direction concordance across modalities",
                alpha=0.05,
                two_tailed=False
            )
        ]

        # Define validation checks
        validation_checks = [
            ValidationCheck(
                check_name="data_availability",
                description="Ensure GWAS data is available",
                validation_code="""
assert gwas_df is not None, "GWAS data is required"
assert len(gwas_df) > 0, "GWAS data is empty"
"""
            ),
            ValidationCheck(
                check_name="snp_coverage",
                description="Check SNP coverage in data",
                validation_code=f"""
n_snps_in_gwas = sum(1 for snp in {snp_ids} if snp in gwas_df.index)
coverage = n_snps_in_gwas / len({snp_ids})
print(f"SNP coverage in GWAS data: {{coverage:.1%}}")
assert coverage > 0.5, f"Low SNP coverage: {{coverage:.1%}}"
"""
            ),
        ]

        # Create protocol
        protocol = ExperimentProtocol(
            title=f"GWAS Multi-Modal: {gene} mechanisms",
            description=f"Multi-modal genomic integration to test: {hypothesis.statement}",
            hypothesis_id=str(hypothesis.id) if hasattr(hypothesis, 'id') else None,
            experiment_type=ExperimentType.DATA_ANALYSIS,
            domain="biology",
            variables=variables,
            steps=steps,
            control_groups=[],  # No control groups for this analysis type
            statistical_tests=statistical_tests,
            validation_checks=validation_checks,
            required_resources=ResourceRequirements(
                cpu_cores=2,
                memory_gb=4.0,
                storage_gb=2.0,
                estimated_duration_minutes=20
            )
        )

        return protocol

    def _generate_load_data_code(
        self,
        gwas_path: str,
        eqtl_path: Optional[str],
        pqtl_path: Optional[str],
        atac_path: Optional[str]
    ) -> str:
        """Generate code for loading genomic data"""
        return f"""
import pandas as pd
import numpy as np

# Load GWAS data (required)
gwas_df = pd.read_csv('{gwas_path}', index_col='snp_id')
print(f"Loaded GWAS data: {{len(gwas_df)}} variants")

# Load eQTL data (optional)
eqtl_df = None
if '{eqtl_path}' and '{eqtl_path}' != 'None':
    try:
        eqtl_df = pd.read_csv('{eqtl_path}', index_col='snp_id')
        print(f"Loaded eQTL data: {{len(eqtl_df)}} associations")
    except Exception as e:
        print(f"Could not load eQTL data: {{e}}")

# Load pQTL data (optional)
pqtl_df = None
if '{pqtl_path}' and '{pqtl_path}' != 'None':
    try:
        pqtl_df = pd.read_csv('{pqtl_path}', index_col='snp_id')
        print(f"Loaded pQTL data: {{len(pqtl_df)}} associations")
    except Exception as e:
        print(f"Could not load pQTL data: {{e}}")

# Load ATAC-seq data (optional)
atac_df = None
if '{atac_path}' and '{atac_path}' != 'None':
    try:
        atac_df = pd.read_csv('{atac_path}', index_col='snp_id')
        print(f"Loaded ATAC-seq data: {{len(atac_df)}} peaks")
    except Exception as e:
        print(f"Could not load ATAC data: {{e}}")
"""

    def _generate_integration_code(
        self,
        snp_ids: List[str],
        gene: str
    ) -> str:
        """Generate code for multi-modal integration"""
        return f"""
from kosmos.domains.biology.genomics import GenomicsAnalyzer

# Initialize analyzer
analyzer = GenomicsAnalyzer()

# Analyze SNP list with multi-modal integration
results = analyzer.analyze_snp_list(
    snp_ids={snp_ids},
    gene='{gene}',
    gwas_df=gwas_df,
    eqtl_df=eqtl_df,
    pqtl_df=pqtl_df,
    atac_df=atac_df
)

print(f"\\nAnalyzed {{len(results)}} SNP-gene pairs")

# Convert to DataFrame for analysis
results_df = pd.DataFrame([
    {{
        'snp_id': r.snp_id,
        'gene': r.gene,
        'gwas_p': r.gwas_p_value,
        'gwas_beta': r.gwas_beta,
        'has_eqtl': r.has_eqtl,
        'has_pqtl': r.has_pqtl,
        'has_atac': r.has_atac_peak,
        'concordant': r.concordant,
        'total_score': r.composite_score.total_score,
        'gwas_score': r.composite_score.gwas_score,
        'qtl_score': r.composite_score.qtl_score,
        'tf_score': r.composite_score.tf_score,
        'evidence_level': r.evidence_level,
        'effect_direction': r.effect_direction
    }}
    for r in results
])

# Display summary statistics
print(f"\\nComposite score summary:")
print(f"  Mean: {{results_df['total_score'].mean():.1f}}")
print(f"  Max: {{results_df['total_score'].max():.1f}}")
print(f"  Median: {{results_df['total_score'].median():.1f}}")

print(f"\\nData availability:")
print(f"  eQTL: {{results_df['has_eqtl'].sum()}}/{{len(results)}} ({{results_df['has_eqtl'].mean()*100:.0f}}%)")
print(f"  pQTL: {{results_df['has_pqtl'].sum()}}/{{len(results)}} ({{results_df['has_pqtl'].mean()*100:.0f}}%)")
print(f"  ATAC: {{results_df['has_atac'].sum()}}/{{len(results)}} ({{results_df['has_atac'].mean()*100:.0f}}%)")
print(f"  Concordant: {{results_df['concordant'].sum()}}/{{len(results)}} ({{results_df['concordant'].mean()*100:.0f}}%)")
"""

    def _generate_ranking_code(
        self,
        min_score: float,
        top_n: int
    ) -> str:
        """Generate code for mechanism ranking"""
        return f"""
# Rank mechanisms by composite score
rankings = analyzer.rank_mechanisms(
    results=results,
    top_n={top_n},
    min_score={min_score}
)

print(f"\\nTop {{len(rankings)}} mechanisms (min score {min_score}):")
print("-" * 80)

for ranking in rankings:
    print(f"\\n{{ranking.rank}}. {{ranking.snp_id}} → {{ranking.gene}}")
    print(f"   Score: {{ranking.total_score:.1f}}/55 ({{ranking.evidence_level}})")
    print(f"   Direction: {{ranking.effect_direction}}")
    print(f"   Evidence: {{', '.join(ranking.key_evidence)}}")

# Create rankings DataFrame
rankings_df = pd.DataFrame([
    {{
        'rank': r.rank,
        'snp_id': r.snp_id,
        'total_score': r.total_score,
        'evidence_level': r.evidence_level,
        'effect_direction': r.effect_direction,
        'n_evidence_types': len(r.key_evidence)
    }}
    for r in rankings
])
"""

    def _generate_visualization_code(self) -> str:
        """Generate code for visualizations"""
        return """
import matplotlib.pyplot as plt
import seaborn as sns

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 1. Composite score distribution
ax1 = axes[0, 0]
ax1.hist(results_df['total_score'], bins=20, edgecolor='black', alpha=0.7)
ax1.axvline(x=min_composite_score, color='red', linestyle='--', label=f'Min threshold ({min_composite_score})')
ax1.set_xlabel('Composite Score')
ax1.set_ylabel('Count')
ax1.set_title('Distribution of Composite Scores')
ax1.legend()

# 2. Score component breakdown (top mechanisms)
ax2 = axes[0, 1]
if len(rankings) > 0:
    top_rankings = rankings_df.head(10)
    top_results = results_df[results_df['snp_id'].isin(top_rankings['snp_id'])].copy()

    # Get score components
    score_components = pd.DataFrame([
        {
            'snp_id': r.snp_id,
            'GWAS': r.composite_score.gwas_score,
            'QTL': r.composite_score.qtl_score,
            'TF': r.composite_score.tf_score,
            'Expression': r.composite_score.expression_score,
            'Protective': r.composite_score.protective_score
        }
        for r in results if r.snp_id in top_rankings['snp_id'].values
    ]).set_index('snp_id')

    score_components.plot(kind='barh', stacked=True, ax=ax2)
    ax2.set_xlabel('Score')
    ax2.set_ylabel('SNP ID')
    ax2.set_title('Score Breakdown (Top 10 Mechanisms)')
    ax2.legend(title='Component', bbox_to_anchor=(1.05, 1), loc='upper left')

# 3. Evidence concordance
ax3 = axes[1, 0]
concordance_summary = pd.DataFrame({
    'Concordant': [results_df['concordant'].sum()],
    'Non-concordant': [(~results_df['concordant']).sum()]
}).T
concordance_summary.plot(kind='bar', ax=ax3, legend=False)
ax3.set_xlabel('Effect Concordance')
ax3.set_ylabel('Count')
ax3.set_title('eQTL/pQTL Concordance with GWAS')
ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)

# 4. Effect direction distribution
ax4 = axes[1, 1]
direction_counts = results_df['effect_direction'].value_counts()
ax4.pie(direction_counts.values, labels=direction_counts.index, autopct='%1.1f%%')
ax4.set_title('Effect Direction Distribution')

plt.tight_layout()
plt.savefig('gwas_multimodal_results.png', dpi=300, bbox_inches='tight')
print("\\nSaved visualization to gwas_multimodal_results.png")

# Save rankings to CSV
rankings_df.to_csv('mechanism_rankings.csv', index=False)
print("Saved rankings to mechanism_rankings.csv")
"""
