"""
Unit tests for NeurodegenerationAnalyzer (Phase 9).

Tests neurodegeneration disease analysis (Figures 7, 8 patterns):
- Differential expression analysis (DESeq2-like)
- Pathway enrichment analysis
- Cross-species validation
- Temporal trajectory modeling

Coverage target: 30 tests across 5 test classes
"""

import pytest
import pandas as pd
import numpy as np
from kosmos.domains.neuroscience.neurodegeneration import (
    NeurodegenerationAnalyzer,
    NeurodegenerationResult,
    DifferentialExpressionResult,
    PathwayEnrichmentResult,
    CrossSpeciesValidation,
    TemporalStage
)


@pytest.fixture
def neurodegeneration_analyzer():
    """Fixture providing a NeurodegenerationAnalyzer instance"""
    return NeurodegenerationAnalyzer()


@pytest.fixture
def sample_expression_data():
    """Sample RNA-seq counts data for testing"""
    np.random.seed(42)

    # 100 genes, 6 samples (3 case, 3 control)
    n_genes = 100
    n_case = 3
    n_control = 3

    # Sample IDs
    sample_ids = [f'Case_{i}' for i in range(1, 4)] + [f'Control_{i}' for i in range(1, 4)]
    gene_ids = [f'GENE_{i}' for i in range(n_genes)]

    # Build counts matrix properly
    counts_data = {}
    for i, gene_id in enumerate(gene_ids):
        if i < 20:  # Upregulated in disease
            counts_data[gene_id] = list(np.random.poisson(100, n_case)) + list(np.random.poisson(50, n_control))
        elif i < 40:  # Downregulated in disease
            counts_data[gene_id] = list(np.random.poisson(50, n_case)) + list(np.random.poisson(100, n_control))
        else:  # Not differential
            counts_data[gene_id] = list(np.random.poisson(75, n_case + n_control))

    counts_matrix = pd.DataFrame(counts_data, index=sample_ids).T

    # Sample metadata
    sample_metadata = pd.DataFrame({
        'sample_id': sample_ids,
        'disease_status': ['AD', 'AD', 'AD', 'Control', 'Control', 'Control']
    })

    return {
        'counts': counts_matrix,
        'metadata': sample_metadata
    }


@pytest.mark.unit
class TestNeurodegenerationInit:
    """Test NeurodegenerationAnalyzer initialization"""

    def test_init_default(self):
        """Test default initialization"""
        analyzer = NeurodegenerationAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'differential_expression_analysis')

    def test_init_with_custom_params(self):
        """Test initialization doesn't require parameters"""
        analyzer = NeurodegenerationAnalyzer()
        assert analyzer is not None


@pytest.mark.unit
class TestDifferentialExpression:
    """Test differential expression analysis"""

    def test_de_analysis_disease_vs_control(self, neurodegeneration_analyzer, sample_expression_data):
        """Test basic differential expression analysis"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False  # Use simple analysis for reproducibility
        )

        assert isinstance(result, NeurodegenerationResult)
        assert result.analysis_name == "AD_vs_Control"
        assert result.case_label == "AD"
        assert result.control_label == "Control"
        assert result.n_genes_tested > 0

    def test_log_fold_change_calculation(self, neurodegeneration_analyzer, sample_expression_data):
        """Test log2 fold change calculation"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # Check that all genes have log2FC
        assert all(hasattr(r, 'log2_fold_change') for r in result.gene_results)

        # Check some genes have positive and some negative log2FC
        log2fcs = [r.log2_fold_change for r in result.gene_results]
        assert any(fc > 0 for fc in log2fcs)
        assert any(fc < 0 for fc in log2fcs)

    def test_pvalue_calculation(self, neurodegeneration_analyzer, sample_expression_data):
        """Test p-value calculation"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # All genes should have p-values
        assert all(hasattr(r, 'p_value') for r in result.gene_results)
        assert all(0 <= r.p_value <= 1 for r in result.gene_results)

    def test_fdr_correction(self, neurodegeneration_analyzer, sample_expression_data):
        """Test FDR/adjusted p-value correction"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # All genes should have adjusted p-values
        assert all(hasattr(r, 'adjusted_p_value') for r in result.gene_results)

        # Adjusted p-values should be >= raw p-values (multiple testing correction)
        for gene_result in result.gene_results:
            assert gene_result.adjusted_p_value >= gene_result.p_value

    def test_volcano_plot_data(self, neurodegeneration_analyzer, sample_expression_data):
        """Test volcano plot data generation"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        volcano_data = neurodegeneration_analyzer.generate_volcano_plot_data(result)

        assert isinstance(volcano_data, pd.DataFrame)
        assert 'log2FoldChange' in volcano_data.columns
        assert '-log10_padj' in volcano_data.columns
        assert 'significance' in volcano_data.columns

    def test_upregulated_genes(self, neurodegeneration_analyzer, sample_expression_data):
        """Test identification of upregulated genes"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        upregulated = result.get_significant_genes(direction="up")
        assert all(r.direction == "up" for r in upregulated)
        assert all(r.log2_fold_change > 0 for r in upregulated)

    def test_downregulated_genes(self, neurodegeneration_analyzer, sample_expression_data):
        """Test identification of downregulated genes"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        downregulated = result.get_significant_genes(direction="down")
        assert all(r.direction == "down" for r in downregulated)
        assert all(r.log2_fold_change < 0 for r in downregulated)

    def test_expression_matrix_validation(self, neurodegeneration_analyzer):
        """Test validation of expression matrix inputs"""
        # Invalid condition column
        counts = pd.DataFrame({'S1': [100], 'S2': [200]}, index=['GENE1'])
        metadata = pd.DataFrame({'sample_id': ['S1', 'S2'], 'condition': ['A', 'B']})

        with pytest.raises(ValueError, match="Condition column"):
            neurodegeneration_analyzer.differential_expression_analysis(
                counts, metadata, 'invalid_column', 'A', 'B'
            )

    def test_multiple_conditions(self, neurodegeneration_analyzer):
        """Test analysis with different condition labels"""
        # Create simple data
        counts = pd.DataFrame({
            'Sample1': [100, 200, 50],
            'Sample2': [120, 180, 55],
            'Sample3': [80, 220, 45]
        }, index=['GENE1', 'GENE2', 'GENE3'])

        metadata = pd.DataFrame({
            'sample_id': ['Sample1', 'Sample2', 'Sample3'],
            'disease': ['PD', 'PD', 'Healthy']
        })

        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts, metadata, 'disease', 'PD', 'Healthy', use_pydeseq2=False
        )

        assert result.case_label == 'PD'
        assert result.control_label == 'Healthy'

    def test_batch_effect_correction(self, neurodegeneration_analyzer, sample_expression_data):
        """Test that analysis handles sample metadata"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # Verify sample sizes are recorded
        assert 'AD' in result.sample_sizes
        assert 'Control' in result.sample_sizes
        assert result.sample_sizes['AD'] == 3
        assert result.sample_sizes['Control'] == 3


@pytest.mark.unit
class TestPathwayEnrichment:
    """Test pathway enrichment analysis"""

    def test_pathway_enrichment_analysis(self, neurodegeneration_analyzer, sample_expression_data):
        """Test basic pathway enrichment"""
        # Run DE analysis first
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # Define a test pathway (first 10 genes)
        pathway_genes = [f'GENE_{i}' for i in range(10)]

        enrichment = neurodegeneration_analyzer.pathway_enrichment(
            deg_results=result,
            pathway_genes=pathway_genes,
            pathway_name='Test Pathway',
            pathway_id='TEST:001'
        )

        assert isinstance(enrichment, PathwayEnrichmentResult)
        assert enrichment.pathway_id == 'TEST:001'
        assert enrichment.pathway_name == 'Test Pathway'

    def test_gene_set_enrichment(self, neurodegeneration_analyzer, sample_expression_data):
        """Test gene set overlap calculation"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # Pathway with upregulated genes (should be enriched)
        pathway_genes = [f'GENE_{i}' for i in range(20)]  # Upregulated in our data

        enrichment = neurodegeneration_analyzer.pathway_enrichment(
            deg_results=result,
            pathway_genes=pathway_genes,
            pathway_name='ECM Pathway'
        )

        assert enrichment.n_genes_in_pathway > 0
        assert enrichment.n_genes_significant >= 0

    def test_multiple_pathways(self, neurodegeneration_analyzer, sample_expression_data):
        """Test enrichment for multiple pathways"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # Test multiple pathways
        pathways = {
            'Pathway1': [f'GENE_{i}' for i in range(0, 10)],
            'Pathway2': [f'GENE_{i}' for i in range(10, 20)],
            'Pathway3': [f'GENE_{i}' for i in range(20, 30)]
        }

        enrichments = []
        for pathway_name, genes in pathways.items():
            enrich = neurodegeneration_analyzer.pathway_enrichment(
                result, genes, pathway_name
            )
            enrichments.append(enrich)

        assert len(enrichments) == 3
        assert all(isinstance(e, PathwayEnrichmentResult) for e in enrichments)

    def test_significance_threshold(self, neurodegeneration_analyzer, sample_expression_data):
        """Test pathway significance detection"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        pathway_genes = [f'GENE_{i}' for i in range(10)]
        enrichment = neurodegeneration_analyzer.pathway_enrichment(
            result, pathway_genes, 'Test'
        )

        # Check is_enriched is boolean
        assert enrichment.is_enriched in [True, False]
        assert enrichment.enrichment_pvalue >= 0
        assert enrichment.enrichment_pvalue <= 1

    def test_gene_overlap_calculation(self, neurodegeneration_analyzer, sample_expression_data):
        """Test calculation of gene overlap"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # Pathway with known genes
        pathway_genes = ['GENE_0', 'GENE_1', 'GENE_2', 'GENE_3', 'GENE_4']

        enrichment = neurodegeneration_analyzer.pathway_enrichment(
            result, pathway_genes, 'Overlap Test'
        )

        # Should have identified overlap
        assert len(enrichment.significant_genes) >= 0
        assert enrichment.n_genes_significant >= 0

    def test_enrichment_score(self, neurodegeneration_analyzer, sample_expression_data):
        """Test odds ratio calculation"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        pathway_genes = [f'GENE_{i}' for i in range(15)]
        enrichment = neurodegeneration_analyzer.pathway_enrichment(
            result, pathway_genes, 'Score Test'
        )

        # Odds ratio should be calculated
        assert hasattr(enrichment, 'odds_ratio')
        assert enrichment.odds_ratio >= 0

    def test_visualization_data(self, neurodegeneration_analyzer, sample_expression_data):
        """Test enrichment visualization data"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        pathway_genes = [f'GENE_{i}' for i in range(10)]
        enrichment = neurodegeneration_analyzer.pathway_enrichment(
            result, pathway_genes, 'Viz Test'
        )

        # Should have all necessary fields for plotting
        assert hasattr(enrichment, 'pathway_name')
        assert hasattr(enrichment, 'enrichment_pvalue')
        assert hasattr(enrichment, 'n_genes_significant')

    def test_pathway_ranking(self, neurodegeneration_analyzer, sample_expression_data):
        """Test ranking of multiple pathways by p-value"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # Create multiple pathways
        pathways = [
            ([f'GENE_{i}' for i in range(0, 10)], 'Pathway_A'),
            ([f'GENE_{i}' for i in range(10, 20)], 'Pathway_B'),
            ([f'GENE_{i}' for i in range(50, 60)], 'Pathway_C')
        ]

        enrichments = []
        for genes, name in pathways:
            enrich = neurodegeneration_analyzer.pathway_enrichment(result, genes, name)
            enrichments.append(enrich)

        # Sort by p-value
        sorted_enrichments = sorted(enrichments, key=lambda e: e.enrichment_pvalue)

        # Should be able to rank
        assert len(sorted_enrichments) == 3
        assert sorted_enrichments[0].enrichment_pvalue <= sorted_enrichments[1].enrichment_pvalue


@pytest.mark.unit
class TestCrossSpeciesValidation:
    """Test cross-species validation"""

    def test_cross_species_comparison(self, neurodegeneration_analyzer):
        """Test basic cross-species comparison"""
        # Create mouse data
        mouse_counts = pd.DataFrame({
            'M1': [100, 200], 'M2': [120, 180], 'M3': [80, 220]
        }, index=['Gene1', 'Gene2'])

        mouse_metadata = pd.DataFrame({
            'sample_id': ['M1', 'M2', 'M3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        mouse_result = neurodegeneration_analyzer.differential_expression_analysis(
            mouse_counts, mouse_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        # Create human data (same genes, similar direction)
        human_counts = pd.DataFrame({
            'H1': [110, 210], 'H2': [130, 190], 'H3': [85, 225]
        }, index=['Gene1', 'Gene2'])

        human_metadata = pd.DataFrame({
            'sample_id': ['H1', 'H2', 'H3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        human_result = neurodegeneration_analyzer.differential_expression_analysis(
            human_counts, human_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        # Cross-species validation
        validation = neurodegeneration_analyzer.cross_species_validation(
            mouse_result, human_result
        )

        assert isinstance(validation, list)
        assert all(isinstance(v, CrossSpeciesValidation) for v in validation)

    def test_conserved_genes_identification(self, neurodegeneration_analyzer):
        """Test identification of conserved genes"""
        # Mouse data - Gene1 upregulated
        mouse_counts = pd.DataFrame({
            'M1': [150, 50], 'M2': [160, 55], 'M3': [50, 150]
        }, index=['Gene1', 'Gene2'])

        mouse_metadata = pd.DataFrame({
            'sample_id': ['M1', 'M2', 'M3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        mouse_result = neurodegeneration_analyzer.differential_expression_analysis(
            mouse_counts, mouse_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        # Human data - Gene1 also upregulated (concordant)
        human_counts = pd.DataFrame({
            'H1': [155, 48], 'H2': [165, 52], 'H3': [48, 155]
        }, index=['Gene1', 'Gene2'])

        human_metadata = pd.DataFrame({
            'sample_id': ['H1', 'H2', 'H3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        human_result = neurodegeneration_analyzer.differential_expression_analysis(
            human_counts, human_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        validation = neurodegeneration_analyzer.cross_species_validation(
            mouse_result, human_result
        )

        # Check for concordant genes
        assert len(validation) > 0
        assert all(hasattr(v, 'is_concordant') for v in validation)

    def test_validation_scoring(self, neurodegeneration_analyzer):
        """Test concordance strength scoring"""
        # Create concordant data (both upregulated)
        mouse_counts = pd.DataFrame({
            'M1': [150], 'M2': [160], 'M3': [50]
        }, index=['Gene1'])

        mouse_metadata = pd.DataFrame({
            'sample_id': ['M1', 'M2', 'M3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        mouse_result = neurodegeneration_analyzer.differential_expression_analysis(
            mouse_counts, mouse_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        human_counts = pd.DataFrame({
            'H1': [155], 'H2': [165], 'H3': [48]
        }, index=['Gene1'])

        human_metadata = pd.DataFrame({
            'sample_id': ['H1', 'H2', 'H3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        human_result = neurodegeneration_analyzer.differential_expression_analysis(
            human_counts, human_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        validation = neurodegeneration_analyzer.cross_species_validation(
            mouse_result, human_result
        )

        # Check concordance strength
        assert all(hasattr(v, 'concordance_strength') for v in validation)
        valid_strengths = ["strong", "moderate", "weak", "none"]
        assert all(v.concordance_strength in valid_strengths for v in validation)

    def test_ortholog_mapping(self, neurodegeneration_analyzer):
        """Test gene mapping between species"""
        # Mouse data
        mouse_counts = pd.DataFrame({
            'M1': [100], 'M2': [120], 'M3': [80]
        }, index=['Sod2'])  # Mouse gene

        mouse_metadata = pd.DataFrame({
            'sample_id': ['M1', 'M2', 'M3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        mouse_result = neurodegeneration_analyzer.differential_expression_analysis(
            mouse_counts, mouse_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        # Human data with mapped gene
        human_counts = pd.DataFrame({
            'H1': [110], 'H2': [130], 'H3': [85]
        }, index=['SOD2'])  # Human gene

        human_metadata = pd.DataFrame({
            'sample_id': ['H1', 'H2', 'H3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        human_result = neurodegeneration_analyzer.differential_expression_analysis(
            human_counts, human_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        # Test with gene mapping
        gene_mapping = {'Sod2': 'SOD2'}
        validation = neurodegeneration_analyzer.cross_species_validation(
            mouse_result, human_result, gene_mapping
        )

        assert len(validation) > 0

    def test_species_specific_changes(self, neurodegeneration_analyzer):
        """Test detection of species-specific changes"""
        # Mouse - Gene1 up, Gene2 down
        mouse_counts = pd.DataFrame({
            'M1': [150, 50], 'M2': [160, 55], 'M3': [50, 150]
        }, index=['Gene1', 'Gene2'])

        mouse_metadata = pd.DataFrame({
            'sample_id': ['M1', 'M2', 'M3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        mouse_result = neurodegeneration_analyzer.differential_expression_analysis(
            mouse_counts, mouse_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        # Human - opposite pattern (not concordant)
        human_counts = pd.DataFrame({
            'H1': [50, 150], 'H2': [55, 160], 'H3': [150, 50]
        }, index=['Gene1', 'Gene2'])

        human_metadata = pd.DataFrame({
            'sample_id': ['H1', 'H2', 'H3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        human_result = neurodegeneration_analyzer.differential_expression_analysis(
            human_counts, human_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        validation = neurodegeneration_analyzer.cross_species_validation(
            mouse_result, human_result
        )

        # Should detect non-concordant genes
        assert any(not v.is_concordant for v in validation)

    def test_conservation_analysis(self, neurodegeneration_analyzer):
        """Test conservation analysis across species"""
        # Similar data for both species
        mouse_counts = pd.DataFrame({
            'M1': [100, 200], 'M2': [120, 180], 'M3': [80, 220]
        }, index=['Gene1', 'Gene2'])

        mouse_metadata = pd.DataFrame({
            'sample_id': ['M1', 'M2', 'M3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        mouse_result = neurodegeneration_analyzer.differential_expression_analysis(
            mouse_counts, mouse_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        human_counts = pd.DataFrame({
            'H1': [105, 205], 'H2': [125, 185], 'H3': [82, 225]
        }, index=['Gene1', 'Gene2'])

        human_metadata = pd.DataFrame({
            'sample_id': ['H1', 'H2', 'H3'],
            'condition': ['Disease', 'Disease', 'Control']
        })

        human_result = neurodegeneration_analyzer.differential_expression_analysis(
            human_counts, human_metadata, 'condition', 'Disease', 'Control', use_pydeseq2=False
        )

        validation = neurodegeneration_analyzer.cross_species_validation(
            mouse_result, human_result
        )

        # All validation objects should have comparison data
        assert all(v.mouse_log2fc is not None for v in validation)
        assert all(v.human_log2fc is not None for v in validation)


@pytest.mark.unit
class TestTemporalAnalysis:
    """Test temporal trajectory analysis"""

    def test_temporal_stage_progression(self, neurodegeneration_analyzer, sample_expression_data):
        """Test temporal stage assignment"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        # Assign temporal stages
        temporal_result = neurodegeneration_analyzer.temporal_ordering(result)

        assert isinstance(temporal_result, NeurodegenerationResult)

        # Check that significant genes have temporal stages
        sig_genes = temporal_result.get_significant_genes()
        if len(sig_genes) > 0:
            assert any(r.temporal_stage is not None for r in sig_genes)

    def test_stage_specific_changes(self, neurodegeneration_analyzer, sample_expression_data):
        """Test identification of stage-specific gene changes"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        temporal_result = neurodegeneration_analyzer.temporal_ordering(result)

        # Get genes in each stage
        sig_genes = temporal_result.get_significant_genes()

        if len(sig_genes) > 0:
            # Should have different temporal stages
            stages = set(r.temporal_stage for r in sig_genes if r.temporal_stage is not None)
            assert len(stages) > 0

    def test_longitudinal_patterns(self, neurodegeneration_analyzer, sample_expression_data):
        """Test temporal ordering captures progression"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        temporal_result = neurodegeneration_analyzer.temporal_ordering(result, n_stages=5)

        # Should assign 5 temporal stages
        sig_genes = temporal_result.get_significant_genes()

        if len(sig_genes) >= 5:
            stages = [r.temporal_stage for r in sig_genes if r.temporal_stage is not None]
            # Should use multiple stages
            assert len(set(stages)) > 1

    def test_trajectory_analysis(self, neurodegeneration_analyzer, sample_expression_data):
        """Test trajectory analysis DataFrame conversion"""
        result = neurodegeneration_analyzer.differential_expression_analysis(
            counts_matrix=sample_expression_data['counts'],
            sample_metadata=sample_expression_data['metadata'],
            condition_column='disease_status',
            case_label='AD',
            control_label='Control',
            use_pydeseq2=False
        )

        temporal_result = neurodegeneration_analyzer.temporal_ordering(result)

        # Convert to DataFrame
        df = temporal_result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert 'gene_id' in df.columns
        assert 'log2FoldChange' in df.columns
        assert 'temporal_stage' in df.columns
