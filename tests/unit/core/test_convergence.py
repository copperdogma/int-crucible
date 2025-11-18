"""
Tests for ConvergenceDetector (Phase 7).

Tests convergence metrics, stopping criteria, and convergence reporting.
"""

from datetime import datetime
import pytest

from kosmos.core.convergence import (
    ConvergenceDetector,
    ConvergenceMetrics,
    StoppingDecision,
    StoppingReason,
    ConvergenceReport,
)
from kosmos.core.workflow import ResearchPlan
from kosmos.models.hypothesis import Hypothesis, HypothesisStatus
from kosmos.models.result import ExperimentResult, ResultStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def convergence_detector():
    """Create a ConvergenceDetector instance."""
    return ConvergenceDetector(
        mandatory_criteria=["iteration_limit", "no_testable_hypotheses"],
        optional_criteria=["novelty_decline", "diminishing_returns"],
        config={
            "novelty_decline_threshold": 0.3,
            "novelty_decline_window": 5,
            "cost_threshold": 100.0,
        },
    )


@pytest.fixture
def research_plan():
    """Create a sample research plan."""
    plan = ResearchPlan(
        research_question="Does caffeine improve cognitive performance?",
        max_iterations=10,
    )
    # Add some hypotheses
    plan.hypothesis_pool = ["hyp_001", "hyp_002", "hyp_003"]
    plan.tested_hypotheses = ["hyp_001"]
    plan.supported_hypotheses = ["hyp_001"]
    plan.rejected_hypotheses = []
    plan.iteration_count = 5
    return plan


@pytest.fixture
def sample_hypotheses():
    """Create sample hypotheses."""
    return [
        Hypothesis(
            id="hyp_001",
            research_question="Question",
            statement="Caffeine improves memory",
            rationale="Rationale 1",
            domain="neuroscience",
            novelty_score=0.8,
            status=HypothesisStatus.TESTED,
        ),
        Hypothesis(
            id="hyp_002",
            research_question="Question",
            statement="Caffeine enhances attention",
            rationale="Rationale 2",
            domain="neuroscience",
            novelty_score=0.6,
            status=HypothesisStatus.GENERATED,
        ),
        Hypothesis(
            id="hyp_003",
            research_question="Question",
            statement="Caffeine reduces fatigue",
            rationale="Rationale 3",
            domain="neuroscience",
            novelty_score=0.5,
            status=HypothesisStatus.GENERATED,
        ),
    ]


@pytest.fixture
def sample_results():
    """Create sample experiment results."""
    return [
        ExperimentResult(
            id="result_001",
            hypothesis_id="hyp_001",
            supports_hypothesis=True,
            primary_p_value=0.01,
            primary_effect_size=0.75,
            primary_test="t-test",
            status=ResultStatus.SUCCESS,
        ),
        ExperimentResult(
            id="result_002",
            hypothesis_id="hyp_002",
            supports_hypothesis=False,
            primary_p_value=0.65,
            primary_effect_size=0.12,
            primary_test="t-test",
            status=ResultStatus.SUCCESS,
        ),
    ]


# ============================================================================
# Test Class 1: Initialization
# ============================================================================

class TestConvergenceDetectorInitialization:
    """Test ConvergenceDetector initialization."""

    def test_initialization_default_config(self):
        """Test detector initializes with default configuration."""
        detector = ConvergenceDetector()

        assert detector.mandatory_criteria == ["iteration_limit", "no_testable_hypotheses"]
        assert detector.optional_criteria == ["novelty_decline", "diminishing_returns"]
        assert detector.novelty_decline_threshold == 0.3
        assert detector.novelty_decline_window == 5
        assert detector.cost_threshold == 100.0

    def test_initialization_custom_criteria(self):
        """Test detector initializes with custom criteria."""
        detector = ConvergenceDetector(
            mandatory_criteria=["iteration_limit"],
            optional_criteria=["novelty_decline"],
        )

        assert detector.mandatory_criteria == ["iteration_limit"]
        assert detector.optional_criteria == ["novelty_decline"]

    def test_initialization_custom_config(self):
        """Test detector initializes with custom configuration."""
        config = {
            "novelty_decline_threshold": 0.5,
            "novelty_decline_window": 10,
            "cost_threshold": 200.0,
        }

        detector = ConvergenceDetector(config=config)

        assert detector.novelty_decline_threshold == 0.5
        assert detector.novelty_decline_window == 10
        assert detector.cost_threshold == 200.0

    def test_metrics_initialization(self):
        """Test metrics are initialized."""
        detector = ConvergenceDetector()

        assert detector.metrics is not None
        assert isinstance(detector.metrics, ConvergenceMetrics)


# ============================================================================
# Test Class 2: Progress Metrics
# ============================================================================

class TestProgressMetrics:
    """Test progress metrics calculation."""

    def test_calculate_discovery_rate_all_supported(
        self, convergence_detector
    ):
        """Test discovery rate when all results support hypotheses."""
        results = [
            ExperimentResult(
                id=f"result_{i}",
                hypothesis_id=f"hyp_{i}",
                supports_hypothesis=True,
                primary_p_value=0.01,
                primary_effect_size=0.7,
                primary_test="t-test",
                status=ResultStatus.SUCCESS,
            )
            for i in range(5)
        ]

        rate = convergence_detector.calculate_discovery_rate(results)

        assert rate == 1.0  # 100% discovery rate

    def test_calculate_discovery_rate_mixed(
        self, convergence_detector
    ):
        """Test discovery rate with mixed results."""
        results = [
            ExperimentResult(
                id="result_1",
                hypothesis_id="hyp_1",
                supports_hypothesis=True,
                primary_p_value=0.01,
                primary_effect_size=0.7,
                primary_test="t-test",
                status=ResultStatus.SUCCESS,
            ),
            ExperimentResult(
                id="result_2",
                hypothesis_id="hyp_2",
                supports_hypothesis=False,
                primary_p_value=0.65,
                primary_effect_size=0.1,
                primary_test="t-test",
                status=ResultStatus.SUCCESS,
            ),
        ]

        rate = convergence_detector.calculate_discovery_rate(results)

        assert rate == 0.5  # 1 out of 2

    def test_calculate_discovery_rate_empty(
        self, convergence_detector
    ):
        """Test discovery rate with no results."""
        rate = convergence_detector.calculate_discovery_rate([])

        assert rate == 0.0

    def test_calculate_novelty_decline(
        self, convergence_detector
    ):
        """Test novelty decline calculation."""
        # Decreasing novelty scores
        hypotheses = [
            Hypothesis(
                id=f"hyp_{i}",
                research_question="Question",
                statement=f"Statement {i}",
                rationale="Rationale",
                domain="test",
                novelty_score=1.0 - (i * 0.1),  # 1.0, 0.9, 0.8, ...
            )
            for i in range(6)
        ]

        current_novelty, is_declining = convergence_detector.calculate_novelty_decline(hypotheses)

        assert 0.0 <= current_novelty <= 1.0
        assert isinstance(is_declining, bool)
        assert is_declining is True  # Should be declining

    def test_calculate_novelty_decline_increasing(
        self, convergence_detector
    ):
        """Test novelty decline with increasing novelty."""
        # Increasing novelty scores
        hypotheses = [
            Hypothesis(
                id=f"hyp_{i}",
                research_question="Question",
                statement=f"Statement {i}",
                rationale="Rationale",
                domain="test",
                novelty_score=0.5 + (i * 0.1),  # 0.5, 0.6, 0.7, ...
            )
            for i in range(6)
        ]

        current_novelty, is_declining = convergence_detector.calculate_novelty_decline(hypotheses)

        assert is_declining is False

    def test_calculate_saturation(
        self, convergence_detector, research_plan
    ):
        """Test saturation calculation."""
        # 1 tested out of 3 total
        saturation = convergence_detector.calculate_saturation(research_plan)

        assert saturation == pytest.approx(1.0 / 3.0)

    def test_calculate_saturation_all_tested(
        self, convergence_detector, research_plan
    ):
        """Test saturation when all hypotheses tested."""
        research_plan.tested_hypotheses = ["hyp_001", "hyp_002", "hyp_003"]

        saturation = convergence_detector.calculate_saturation(research_plan)

        assert saturation == 1.0

    def test_calculate_consistency(
        self, convergence_detector
    ):
        """Test consistency calculation."""
        # Mixed results
        results = [
            ExperimentResult(
                id="result_1",
                hypothesis_id="hyp_1",
                supports_hypothesis=True,
                primary_p_value=0.01,
                primary_effect_size=0.7,
                primary_test="t-test",
                status=ResultStatus.SUCCESS,
            ),
            ExperimentResult(
                id="result_2",
                hypothesis_id="hyp_2",
                supports_hypothesis=True,
                primary_p_value=0.02,
                primary_effect_size=0.6,
                primary_test="t-test",
                status=ResultStatus.SUCCESS,
            ),
            ExperimentResult(
                id="result_3",
                hypothesis_id="hyp_3",
                supports_hypothesis=False,
                primary_p_value=0.65,
                primary_effect_size=0.1,
                primary_test="t-test",
                status=ResultStatus.SUCCESS,
            ),
        ]

        consistency = convergence_detector.calculate_consistency(results)

        # 2 supported out of 3 = 2/3
        assert consistency == pytest.approx(2.0 / 3.0)

    def test_calculate_consistency_empty(
        self, convergence_detector
    ):
        """Test consistency with no results."""
        consistency = convergence_detector.calculate_consistency([])

        assert consistency == 0.0


# ============================================================================
# Test Class 3: Mandatory Criteria
# ============================================================================

class TestMandatoryCriteria:
    """Test mandatory stopping criteria."""

    def test_check_iteration_limit_not_reached(
        self, convergence_detector, research_plan
    ):
        """Test iteration limit check when not reached."""
        research_plan.iteration_count = 5
        research_plan.max_iterations = 10

        decision = convergence_detector.check_iteration_limit(research_plan)

        assert decision.should_stop is False
        assert decision.reason == StoppingReason.ITERATION_LIMIT
        assert decision.is_mandatory is True

    def test_check_iteration_limit_reached(
        self, convergence_detector, research_plan
    ):
        """Test iteration limit check when reached."""
        research_plan.iteration_count = 10
        research_plan.max_iterations = 10

        decision = convergence_detector.check_iteration_limit(research_plan)

        assert decision.should_stop is True
        assert decision.reason == StoppingReason.ITERATION_LIMIT

    def test_check_iteration_limit_exceeded(
        self, convergence_detector, research_plan
    ):
        """Test iteration limit check when exceeded."""
        research_plan.iteration_count = 12
        research_plan.max_iterations = 10

        decision = convergence_detector.check_iteration_limit(research_plan)

        assert decision.should_stop is True

    def test_check_hypothesis_exhaustion_not_exhausted(
        self, convergence_detector, research_plan, sample_hypotheses
    ):
        """Test hypothesis exhaustion when hypotheses remain."""
        # Has untested hypotheses
        research_plan.hypothesis_pool = ["hyp_001", "hyp_002", "hyp_003"]
        research_plan.tested_hypotheses = ["hyp_001"]

        decision = convergence_detector.check_hypothesis_exhaustion(research_plan, sample_hypotheses)

        assert decision.should_stop is False

    def test_check_hypothesis_exhaustion_all_tested(
        self, convergence_detector, research_plan, sample_hypotheses
    ):
        """Test hypothesis exhaustion when all tested."""
        # All hypotheses tested, no experiments queued
        research_plan.hypothesis_pool = ["hyp_001", "hyp_002", "hyp_003"]
        research_plan.tested_hypotheses = ["hyp_001", "hyp_002", "hyp_003"]
        research_plan.experiment_queue = []

        decision = convergence_detector.check_hypothesis_exhaustion(research_plan, sample_hypotheses)

        assert decision.should_stop is True
        assert decision.reason == StoppingReason.HYPOTHESIS_EXHAUSTION

    def test_check_hypothesis_exhaustion_with_queued_experiments(
        self, convergence_detector, research_plan, sample_hypotheses
    ):
        """Test hypothesis exhaustion with experiments still queued."""
        research_plan.hypothesis_pool = ["hyp_001"]
        research_plan.tested_hypotheses = ["hyp_001"]
        research_plan.experiment_queue = ["exp_001"]  # Has queued experiment

        decision = convergence_detector.check_hypothesis_exhaustion(research_plan, sample_hypotheses)

        assert decision.should_stop is False


# ============================================================================
# Test Class 4: Optional Criteria
# ============================================================================

class TestOptionalCriteria:
    """Test optional stopping criteria."""

    def test_check_novelty_decline_not_declining(
        self, convergence_detector
    ):
        """Test novelty decline when novelty is stable."""
        # Set metrics with high novelty
        convergence_detector.metrics.novelty_trend = [0.8, 0.75, 0.78, 0.77, 0.76]
        convergence_detector.metrics.novelty_score = 0.76

        decision = convergence_detector.check_novelty_decline()

        assert decision.should_stop is False

    def test_check_novelty_decline_all_below_threshold(
        self, convergence_detector
    ):
        """Test novelty decline when all recent values below threshold."""
        # All below 0.3 threshold
        convergence_detector.metrics.novelty_trend = [0.2, 0.25, 0.22, 0.23, 0.21]

        decision = convergence_detector.check_novelty_decline()

        assert decision.should_stop is True
        assert decision.reason == StoppingReason.NOVELTY_DECLINE

    def test_check_novelty_decline_strictly_declining(
        self, convergence_detector
    ):
        """Test novelty decline when strictly decreasing."""
        # Strictly declining
        convergence_detector.metrics.novelty_trend = [0.8, 0.7, 0.6, 0.5, 0.4]

        decision = convergence_detector.check_novelty_decline()

        assert decision.should_stop is True

    def test_check_novelty_decline_insufficient_data(
        self, convergence_detector
    ):
        """Test novelty decline with insufficient data."""
        # Not enough data points
        convergence_detector.metrics.novelty_trend = [0.8, 0.7]

        decision = convergence_detector.check_novelty_decline()

        assert decision.should_stop is False

    def test_check_diminishing_returns_below_threshold(
        self, convergence_detector
    ):
        """Test diminishing returns when below threshold."""
        convergence_detector.metrics.cost_per_discovery = 50.0  # Below 100 threshold

        decision = convergence_detector.check_diminishing_returns()

        assert decision.should_stop is False

    def test_check_diminishing_returns_above_threshold(
        self, convergence_detector
    ):
        """Test diminishing returns when above threshold."""
        convergence_detector.metrics.cost_per_discovery = 150.0  # Above 100 threshold

        decision = convergence_detector.check_diminishing_returns()

        assert decision.should_stop is True
        assert decision.reason == StoppingReason.DIMINISHING_RETURNS

    def test_check_diminishing_returns_no_cost_data(
        self, convergence_detector
    ):
        """Test diminishing returns with no cost data."""
        convergence_detector.metrics.cost_per_discovery = None

        decision = convergence_detector.check_diminishing_returns()

        assert decision.should_stop is False


# ============================================================================
# Test Class 5: Convergence Decision
# ============================================================================

class TestConvergenceDecision:
    """Test overall convergence decision logic."""

    def test_check_convergence_not_converged(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test convergence check when not converged."""
        # Normal state: not at limits
        research_plan.iteration_count = 5
        research_plan.max_iterations = 10

        decision = convergence_detector.check_convergence(research_plan, sample_hypotheses, sample_results)

        assert decision.should_stop is False

    def test_check_convergence_iteration_limit(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test convergence due to iteration limit."""
        research_plan.iteration_count = 10
        research_plan.max_iterations = 10

        decision = convergence_detector.check_convergence(research_plan, sample_hypotheses, sample_results)

        assert decision.should_stop is True
        assert decision.reason == StoppingReason.ITERATION_LIMIT
        assert decision.is_mandatory is True

    def test_check_convergence_hypothesis_exhaustion(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test convergence due to hypothesis exhaustion."""
        research_plan.hypothesis_pool = ["hyp_001", "hyp_002", "hyp_003"]
        research_plan.tested_hypotheses = ["hyp_001", "hyp_002", "hyp_003"]
        research_plan.experiment_queue = []

        decision = convergence_detector.check_convergence(research_plan, sample_hypotheses, sample_results)

        assert decision.should_stop is True
        assert decision.reason == StoppingReason.HYPOTHESIS_EXHAUSTION

    def test_check_convergence_optional_criteria(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test convergence due to optional criteria."""
        # Set up novelty decline
        convergence_detector.metrics.novelty_trend = [0.2, 0.22, 0.21, 0.19, 0.18]

        decision = convergence_detector.check_convergence(research_plan, sample_hypotheses, sample_results)

        if decision.should_stop:
            assert decision.reason == StoppingReason.NOVELTY_DECLINE
            assert decision.is_mandatory is False

    def test_check_convergence_mandatory_takes_precedence(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test mandatory criteria checked before optional."""
        # Set both mandatory and optional to trigger
        research_plan.iteration_count = 10
        research_plan.max_iterations = 10
        convergence_detector.metrics.novelty_trend = [0.2, 0.22, 0.21, 0.19, 0.18]

        decision = convergence_detector.check_convergence(research_plan, sample_hypotheses, sample_results)

        assert decision.should_stop is True
        # Should be mandatory (iteration limit), not optional (novelty)
        assert decision.is_mandatory is True

    def test_check_convergence_updates_metrics(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test convergence check updates metrics."""
        initial_timestamp = convergence_detector.metrics.last_updated

        convergence_detector.check_convergence(research_plan, sample_hypotheses, sample_results)

        # Metrics should be updated
        assert convergence_detector.metrics.last_updated >= initial_timestamp
        assert convergence_detector.metrics.iteration_count == research_plan.iteration_count


# ============================================================================
# Test Class 6: Convergence Report
# ============================================================================

class TestConvergenceReport:
    """Test convergence report generation."""

    def test_generate_convergence_report(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test generating convergence report."""
        decision = StoppingDecision(
            should_stop=True,
            reason=StoppingReason.ITERATION_LIMIT,
            is_mandatory=True,
            confidence=1.0,
            details="Reached max iterations",
        )

        report = convergence_detector.generate_convergence_report(
            decision, research_plan, sample_hypotheses, sample_results
        )

        assert isinstance(report, ConvergenceReport)
        assert report.research_question == research_plan.research_question
        assert report.converged is True
        assert report.stopping_reason == StoppingReason.ITERATION_LIMIT
        assert report.total_iterations == research_plan.iteration_count
        assert report.hypotheses_generated > 0
        assert report.hypotheses_tested > 0

    def test_convergence_report_to_markdown(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test exporting convergence report to markdown."""
        decision = StoppingDecision(
            should_stop=True,
            reason=StoppingReason.ITERATION_LIMIT,
            is_mandatory=True,
            confidence=1.0,
            details="Test details",
        )

        report = convergence_detector.generate_convergence_report(
            decision, research_plan, sample_hypotheses, sample_results
        )

        markdown = report.to_markdown()

        assert isinstance(markdown, str)
        assert "# Convergence Report" in markdown
        assert research_plan.research_question in markdown
        assert "ITERATION_LIMIT" in markdown or "iteration limit" in markdown.lower()
        assert "## Summary" in markdown
        assert "## Progress Metrics" in markdown

    def test_report_includes_metrics(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test report includes final metrics."""
        decision = StoppingDecision(
            should_stop=True,
            reason=StoppingReason.ITERATION_LIMIT,
            is_mandatory=True,
            confidence=1.0,
            details="Test",
        )

        report = convergence_detector.generate_convergence_report(
            decision, research_plan, sample_hypotheses, sample_results
        )

        assert report.final_metrics is not None
        assert isinstance(report.final_metrics, ConvergenceMetrics)

    def test_report_includes_recommendations(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test report includes recommended next steps."""
        decision = StoppingDecision(
            should_stop=True,
            reason=StoppingReason.NOVELTY_DECLINE,
            is_mandatory=False,
            confidence=0.85,
            details="Novelty declining",
        )

        report = convergence_detector.generate_convergence_report(
            decision, research_plan, sample_hypotheses, sample_results
        )

        assert len(report.recommended_next_steps) > 0

    def test_report_not_converged(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test report generation when not converged."""
        decision = StoppingDecision(
            should_stop=False,
            reason=None,
            is_mandatory=False,
            confidence=0.0,
            details="Not converged",
        )

        report = convergence_detector.generate_convergence_report(
            decision, research_plan, sample_hypotheses, sample_results
        )

        assert report.converged is False
        assert report.stopping_reason is None


# ============================================================================
# Test Class 7: Recommended Next Steps
# ============================================================================

class TestRecommendedNextSteps:
    """Test recommended next steps generation."""

    def test_recommend_next_steps_iteration_limit(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test recommendations for iteration limit."""
        decision = StoppingDecision(
            should_stop=True,
            reason=StoppingReason.ITERATION_LIMIT,
            is_mandatory=True,
            confidence=1.0,
            details="Reached limit",
        )

        steps = convergence_detector._recommend_next_steps(
            decision, research_plan, sample_hypotheses, sample_results
        )

        assert isinstance(steps, list)
        assert len(steps) > 0
        # Should recommend reviewing or continuing with more iterations
        recommendations_text = " ".join(steps).lower()
        assert any(word in recommendations_text for word in ["review", "iteration", "continue"])

    def test_recommend_next_steps_hypothesis_exhaustion(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test recommendations for hypothesis exhaustion."""
        decision = StoppingDecision(
            should_stop=True,
            reason=StoppingReason.HYPOTHESIS_EXHAUSTION,
            is_mandatory=True,
            confidence=1.0,
            details="No more hypotheses",
        )

        steps = convergence_detector._recommend_next_steps(
            decision, research_plan, sample_hypotheses, sample_results
        )

        assert len(steps) > 0
        recommendations_text = " ".join(steps).lower()
        assert any(word in recommendations_text for word in ["hypothesis", "new", "generate"])

    def test_recommend_next_steps_novelty_decline(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test recommendations for novelty decline."""
        decision = StoppingDecision(
            should_stop=True,
            reason=StoppingReason.NOVELTY_DECLINE,
            is_mandatory=False,
            confidence=0.85,
            details="Novelty declining",
        )

        steps = convergence_detector._recommend_next_steps(
            decision, research_plan, sample_hypotheses, sample_results
        )

        assert len(steps) > 0
        recommendations_text = " ".join(steps).lower()
        assert any(word in recommendations_text for word in ["novel", "domain", "direction"])

    def test_recommend_next_steps_diminishing_returns(
        self, convergence_detector, research_plan, sample_hypotheses, sample_results
    ):
        """Test recommendations for diminishing returns."""
        decision = StoppingDecision(
            should_stop=True,
            reason=StoppingReason.DIMINISHING_RETURNS,
            is_mandatory=False,
            confidence=0.9,
            details="Cost too high",
        )

        steps = convergence_detector._recommend_next_steps(
            decision, research_plan, sample_hypotheses, sample_results
        )

        assert len(steps) > 0
        recommendations_text = " ".join(steps).lower()
        assert any(word in recommendations_text for word in ["cost", "efficient", "optimize"])

    def test_get_metrics(self, convergence_detector):
        """Test getting current metrics."""
        metrics = convergence_detector.get_metrics()

        assert isinstance(metrics, ConvergenceMetrics)

    def test_get_metrics_dict(self, convergence_detector):
        """Test getting metrics as dictionary."""
        metrics_dict = convergence_detector.get_metrics_dict()

        assert isinstance(metrics_dict, dict)
        assert "discovery_rate" in metrics_dict
        assert "novelty_score" in metrics_dict
        assert "saturation_ratio" in metrics_dict
        assert "consistency_score" in metrics_dict
