"""
Tests for code generation system.

Tests template matching, code generation, LLM fallback, and validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from kosmos.execution.code_generator import (
    ExperimentCodeGenerator,
    TTestComparisonCodeTemplate,
    CorrelationAnalysisCodeTemplate,
    LogLogScalingCodeTemplate,
    MLExperimentCodeTemplate,
    CodeTemplate
)
from kosmos.models.experiment import ExperimentProtocol, ExperimentType, Variable, VariableType


# Fixtures

@pytest.fixture
def ttest_protocol():
    """Create T-test experiment protocol."""
    return ExperimentProtocol(
        id="test-001",
        hypothesis_id="hyp-001",
        title="Test Experiment",
        description="T-test comparison",
        experiment_type=ExperimentType.DATA_ANALYSIS,
        statistical_tests=["t-test"],
        variables={
            "group": Variable(name="group", type=VariableType.INDEPENDENT, description="Group variable"),
            "measurement": Variable(name="measurement", type=VariableType.DEPENDENT, description="Measurement")
        },
        data_requirements={"format": "csv", "columns": ["group", "measurement"]},
        expected_duration_minutes=10
    )


@pytest.fixture
def correlation_protocol():
    """Create correlation analysis protocol."""
    return ExperimentProtocol(
        id="test-002",
        hypothesis_id="hyp-002",
        title="Correlation Test",
        description="Correlation analysis",
        experiment_type=ExperimentType.DATA_ANALYSIS,
        statistical_tests=["correlation"],
        variables={
            "x": Variable(name="x", type=VariableType.INDEPENDENT, description="X variable"),
            "y": Variable(name="y", type=VariableType.DEPENDENT, description="Y variable")
        },
        data_requirements={"format": "csv", "columns": ["x", "y"]},
        expected_duration_minutes=10
    )


@pytest.fixture
def loglog_protocol():
    """Create log-log scaling protocol."""
    return ExperimentProtocol(
        id="test-003",
        hypothesis_id="hyp-003",
        title="Log-Log Test",
        description="Power law analysis",
        experiment_type=ExperimentType.DATA_ANALYSIS,
        statistical_tests=["scaling", "power_law"],
        variables={
            "x": Variable(name="x", type=VariableType.INDEPENDENT, description="X variable"),
            "y": Variable(name="y", type=VariableType.DEPENDENT, description="Y variable")
        },
        data_requirements={"format": "csv", "columns": ["x", "y"]},
        expected_duration_minutes=10
    )


@pytest.fixture
def ml_protocol():
    """Create ML experiment protocol."""
    return ExperimentProtocol(
        id="test-004",
        hypothesis_id="hyp-004",
        title="ML Test",
        description="Machine learning classification",
        experiment_type=ExperimentType.ML_TRAINING,
        statistical_tests=["classification"],
        variables={
            "features": Variable(name="features", type=VariableType.INDEPENDENT, description="Features"),
            "target": Variable(name="target", type=VariableType.DEPENDENT, description="Target")
        },
        data_requirements={"format": "csv"},
        expected_duration_minutes=30
    )


@pytest.fixture
def code_generator():
    """Create code generator without LLM."""
    return ExperimentCodeGenerator(use_templates=True, use_llm=False)


@pytest.fixture
def code_generator_with_llm():
    """Create code generator with LLM."""
    mock_llm = Mock()
    mock_llm.generate.return_value = "import numpy as np\nresults = {'value': 42}"
    return ExperimentCodeGenerator(use_templates=True, use_llm=True, llm_client=mock_llm)


# Template Matching Tests

class TestTemplateMatching:
    """Tests for template matching logic."""

    def test_ttest_template_matches_ttest_protocol(self, ttest_protocol):
        """Test T-test template matches T-test protocol."""
        template = TTestComparisonCodeTemplate()
        assert template.matches(ttest_protocol)

    def test_correlation_template_matches_correlation_protocol(self, correlation_protocol):
        """Test correlation template matches correlation protocol."""
        template = CorrelationAnalysisCodeTemplate()
        assert template.matches(correlation_protocol)

    def test_loglog_template_matches_scaling_protocol(self, loglog_protocol):
        """Test log-log template matches scaling protocol."""
        template = LogLogScalingCodeTemplate()
        assert template.matches(loglog_protocol)

    def test_ml_template_matches_ml_protocol(self, ml_protocol):
        """Test ML template matches ML protocol."""
        template = MLExperimentCodeTemplate()
        assert template.matches(ml_protocol)

    def test_ttest_template_does_not_match_correlation(self, correlation_protocol):
        """Test T-test template doesn't match correlation protocol."""
        template = TTestComparisonCodeTemplate()
        assert not template.matches(correlation_protocol)

    def test_generator_selects_correct_template_for_ttest(self, code_generator, ttest_protocol):
        """Test generator selects T-test template."""
        template = code_generator._match_template(ttest_protocol)
        assert isinstance(template, TTestComparisonCodeTemplate)

    def test_generator_selects_correct_template_for_correlation(self, code_generator, correlation_protocol):
        """Test generator selects correlation template."""
        template = code_generator._match_template(correlation_protocol)
        assert isinstance(template, CorrelationAnalysisCodeTemplate)


# Code Generation Tests

class TestCodeGeneration:
    """Tests for code generation from templates."""

    def test_ttest_code_generation(self, code_generator, ttest_protocol):
        """Test T-test code generation."""
        code = code_generator.generate(ttest_protocol)

        assert code is not None
        assert "import pandas as pd" in code
        assert "DataAnalyzer" in code
        assert "ttest_comparison" in code
        assert "results" in code

    def test_correlation_code_generation(self, code_generator, correlation_protocol):
        """Test correlation code generation."""
        code = code_generator.generate(correlation_protocol)

        assert code is not None
        assert "import pandas as pd" in code
        assert "DataAnalyzer" in code
        assert "correlation_analysis" in code

    def test_loglog_code_generation(self, code_generator, loglog_protocol):
        """Test log-log scaling code generation."""
        code = code_generator.generate(loglog_protocol)

        assert code is not None
        assert "import pandas as pd" in code
        assert "DataAnalyzer" in code
        assert "log_log_scaling_analysis" in code

    def test_ml_code_generation(self, code_generator, ml_protocol):
        """Test ML code generation."""
        code = code_generator.generate(ml_protocol)

        assert code is not None
        assert "import pandas as pd" in code
        assert "MLAnalyzer" in code
        assert "run_experiment" in code or "cross_validate" in code

    def test_generated_code_is_valid_python(self, code_generator, ttest_protocol):
        """Test generated code is valid Python syntax."""
        import ast

        code = code_generator.generate(ttest_protocol)

        try:
            ast.parse(code)
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False

        assert syntax_valid, f"Generated code has syntax errors:\n{code}"

    def test_generated_code_contains_result_variable(self, code_generator, ttest_protocol):
        """Test generated code assigns to results variable."""
        code = code_generator.generate(ttest_protocol)
        assert "results" in code or "result" in code


# LLM Fallback Tests

class TestLLMFallback:
    """Tests for LLM-based code generation fallback."""

    def test_llm_used_when_no_template_matches(self, code_generator_with_llm):
        """Test LLM used when no template matches."""
        # Create custom protocol that doesn't match any template
        custom_protocol = ExperimentProtocol(
            id="custom-001",
            hypothesis_id="hyp-001",
            title="Custom Experiment",
            description="Novel experiment type",
            experiment_type=ExperimentType.COMPUTATIONAL,
            statistical_tests=["custom_test"],
            variables={},
            data_requirements={},
            expected_duration_minutes=10
        )

        code = code_generator_with_llm.generate(custom_protocol)

        # Should have called LLM
        assert code_generator_with_llm.llm_client.generate.called
        assert code is not None

    def test_template_preferred_over_llm_when_available(self, code_generator_with_llm, ttest_protocol):
        """Test template used instead of LLM when available."""
        code = code_generator_with_llm.generate(ttest_protocol)

        # Should use template, not LLM
        assert "ttest_comparison" in code
        # LLM might still be called if enhance mode is on, but template should be primary

    def test_llm_can_enhance_template_code(self):
        """Test LLM enhancement of template code."""
        mock_llm = Mock()
        mock_llm.generate.return_value = "# Enhanced\nimport pandas as pd\nresults = {}"

        generator = ExperimentCodeGenerator(
            use_templates=True,
            use_llm=True,
            llm_enhance_templates=True,
            llm_client=mock_llm
        )

        protocol = ExperimentProtocol(
            id="test-001",
            hypothesis_id="hyp-001",
            title="Test",
            description="Test experiment",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            statistical_tests=["t-test"],
            variables={},
            data_requirements={},
            expected_duration_minutes=10
        )

        code = generator.generate(protocol)

        # LLM should have been called for enhancement
        assert mock_llm.generate.called


# Validation Tests

class TestCodeValidation:
    """Tests for code validation and syntax checking."""

    def test_validate_syntax_valid_code(self, code_generator):
        """Test validation accepts valid code."""
        valid_code = "import numpy as np\nx = np.array([1, 2, 3])\nresults = {'mean': np.mean(x)}"

        try:
            code_generator._validate_syntax(valid_code)
            is_valid = True
        except Exception:
            is_valid = False

        assert is_valid

    def test_validate_syntax_invalid_code(self, code_generator):
        """Test validation rejects invalid code."""
        invalid_code = "import numpy as np\nx = [1, 2, 3\nresults = {'mean': x}"

        with pytest.raises(SyntaxError):
            code_generator._validate_syntax(invalid_code)

    def test_generated_code_passes_validation(self, code_generator, ttest_protocol):
        """Test all generated code passes validation."""
        code = code_generator.generate(ttest_protocol)

        try:
            code_generator._validate_syntax(code)
            is_valid = True
        except Exception:
            is_valid = False

        assert is_valid


# Variable Extraction Tests

class TestVariableExtraction:
    """Tests for extracting variables from protocols."""

    def test_extract_dependent_variable(self, ttest_protocol):
        """Test extraction of dependent variable."""
        template = TTestComparisonCodeTemplate()

        dependent_vars = [
            var for var in ttest_protocol.variables.values()
            if var.type == VariableType.DEPENDENT
        ]

        assert len(dependent_vars) > 0
        assert dependent_vars[0].name == "measurement"

    def test_extract_independent_variable(self, ttest_protocol):
        """Test extraction of independent variable."""
        template = TTestComparisonCodeTemplate()

        independent_vars = [
            var for var in ttest_protocol.variables.values()
            if var.type == VariableType.INDEPENDENT
        ]

        assert len(independent_vars) > 0
        assert independent_vars[0].name == "group"


# Integration Tests

class TestCodeGeneratorIntegration:
    """Integration tests for code generator."""

    def test_end_to_end_ttest_generation(self, code_generator, ttest_protocol):
        """Test complete T-test code generation pipeline."""
        code = code_generator.generate(ttest_protocol)

        # Verify code structure
        assert "import" in code
        assert "DataAnalyzer" in code
        assert "ttest_comparison" in code
        assert "results" in code

        # Verify valid syntax
        import ast
        ast.parse(code)

    def test_end_to_end_ml_generation(self, code_generator, ml_protocol):
        """Test complete ML code generation pipeline."""
        code = code_generator.generate(ml_protocol)

        assert "import" in code
        assert "MLAnalyzer" in code
        assert "results" in code

        # Verify valid syntax
        import ast
        ast.parse(code)

    def test_generator_handles_minimal_protocol(self, code_generator):
        """Test generator handles minimal protocol gracefully."""
        minimal_protocol = ExperimentProtocol(
            id="minimal-001",
            hypothesis_id="hyp-001",
            title="Minimal",
            description="Minimal protocol",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            statistical_tests=[],
            variables={},
            data_requirements={},
            expected_duration_minutes=5
        )

        code = code_generator.generate(minimal_protocol)

        # Should generate fallback code
        assert code is not None
        assert len(code) > 0


# Edge Cases and Error Handling

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_generator_with_no_templates_and_no_llm(self):
        """Test generator behavior when both templates and LLM disabled."""
        generator = ExperimentCodeGenerator(use_templates=False, use_llm=False)

        protocol = ExperimentProtocol(
            id="test-001",
            hypothesis_id="hyp-001",
            title="Test",
            description="Test",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            statistical_tests=[],
            variables={},
            data_requirements={},
            expected_duration_minutes=5
        )

        code = generator.generate(protocol)

        # Should generate basic fallback
        assert code is not None
        assert "import" in code

    def test_generator_handles_empty_variables(self, code_generator):
        """Test generator handles protocol with no variables."""
        protocol = ExperimentProtocol(
            id="test-001",
            hypothesis_id="hyp-001",
            title="Test",
            description="Test",
            experiment_type=ExperimentType.LITERATURE_REVIEW,
            statistical_tests=[],
            variables={},  # Empty
            data_requirements={},
            expected_duration_minutes=5
        )

        code = code_generator.generate(protocol)
        assert code is not None

    def test_generator_handles_missing_data_requirements(self, code_generator):
        """Test generator handles missing data requirements."""
        protocol = ExperimentProtocol(
            id="test-001",
            hypothesis_id="hyp-001",
            title="Test",
            description="Test",
            experiment_type=ExperimentType.DATA_ANALYSIS,
            statistical_tests=["t-test"],
            variables={},
            data_requirements={},  # Empty
            expected_duration_minutes=5
        )

        code = code_generator.generate(protocol)
        assert code is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
