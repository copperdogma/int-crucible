"""
Tests for HypothesisRefiner (Phase 7).

Tests hybrid retirement logic, hypothesis evolution, contradiction detection, and lineage tracking.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch
import pytest

from kosmos.hypothesis.refiner import (
    HypothesisRefiner,
    RetirementDecision,
    RefinerAction,
    HypothesisLineage,
)
from kosmos.models.hypothesis import Hypothesis, HypothesisStatus
from kosmos.models.result import ExperimentResult, ResultStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_hypothesis():
    """Create a sample hypothesis for testing."""
    return Hypothesis(
        research_question="Does caffeine improve cognitive performance?",
        statement="Caffeine consumption improves working memory performance in young adults",
        rationale="Studies show stimulant effects on cognitive function",
        domain="neuroscience",
        status=HypothesisStatus.GENERATED,
        testability_score=0.9,
        novelty_score=0.6,
        confidence_score=0.5,
        priority_score=0.7,
    )


@pytest.fixture
def sample_supported_result():
    """Create a sample supported experiment result."""
    return ExperimentResult(
        id="result_001",
        hypothesis_id="hyp_001",
        supports_hypothesis=True,
        primary_p_value=0.01,
        primary_effect_size=0.75,
        primary_test="t-test",
        status=ResultStatus.SUCCESS,
    )


@pytest.fixture
def sample_rejected_result():
    """Create a sample rejected experiment result."""
    return ExperimentResult(
        id="result_002",
        hypothesis_id="hyp_001",
        supports_hypothesis=False,
        primary_p_value=0.65,
        primary_effect_size=0.12,
        primary_test="t-test",
        status=ResultStatus.SUCCESS,
    )


@pytest.fixture
def sample_inconclusive_result():
    """Create a sample inconclusive experiment result."""
    return ExperimentResult(
        id="result_003",
        hypothesis_id="hyp_001",
        supports_hypothesis=None,
        primary_p_value=0.08,
        primary_effect_size=0.35,
        primary_test="t-test",
        status=ResultStatus.SUCCESS,
    )


@pytest.fixture
def sample_failed_result():
    """Create a sample failed execution result."""
    return ExperimentResult(
        id="result_004",
        hypothesis_id="hyp_001",
        supports_hypothesis=None,
        primary_p_value=None,
        primary_effect_size=None,
        primary_test="t-test",
        status=ResultStatus.FAILURE,
    )


@pytest.fixture
def refiner(mock_llm_client):
    """Create a HypothesisRefiner instance."""
    return HypothesisRefiner(
        llm_client=mock_llm_client,
        vector_db=None,
        config={
            "failure_threshold": 3,
            "confidence_retirement_threshold": 0.1,
            "similarity_threshold": 0.8,
        },
    )


# ============================================================================
# Test Class 1: Initialization
# ============================================================================

class TestHypothesisRefinerInitialization:
    """Test HypothesisRefiner initialization."""

    def test_initialization_default_config(self, mock_llm_client):
        """Test refiner initializes with default configuration."""
        refiner = HypothesisRefiner(llm_client=mock_llm_client)

        assert refiner.llm_client is mock_llm_client
        assert refiner.failure_threshold == 3
        assert refiner.confidence_retirement_threshold == 0.1
        assert refiner.similarity_threshold == 0.8
        assert refiner.lineage_tracking == {}

    def test_initialization_custom_config(self, mock_llm_client):
        """Test refiner initializes with custom configuration."""
        custom_config = {
            "failure_threshold": 5,
            "confidence_retirement_threshold": 0.2,
            "similarity_threshold": 0.9,
        }

        refiner = HypothesisRefiner(llm_client=mock_llm_client, config=custom_config)

        assert refiner.failure_threshold == 5
        assert refiner.confidence_retirement_threshold == 0.2
        assert refiner.similarity_threshold == 0.9

    def test_initialization_with_vector_db(self, mock_llm_client, mock_vector_db):
        """Test refiner initializes with vector database."""
        refiner = HypothesisRefiner(llm_client=mock_llm_client, vector_db=mock_vector_db)

        assert refiner.vector_db is mock_vector_db


# ============================================================================
# Test Class 2: Rule-Based Retirement
# ============================================================================

class TestRetirementDecisionRuleBased:
    """Test rule-based retirement decisions (consecutive failures)."""

    def test_consecutive_failures_below_threshold(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test hypothesis continues when failures below threshold."""
        # 2 consecutive failures (threshold is 3)
        results = [sample_rejected_result, sample_rejected_result]

        decision = refiner.evaluate_hypothesis_status(
            hypothesis=sample_hypothesis,
            result=sample_rejected_result,
            results_history=results[:-1],
        )

        # Should refine, not retire (below threshold)
        assert decision == RetirementDecision.REFINE

    def test_consecutive_failures_at_threshold(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test hypothesis retires when failures reach threshold."""
        # 3 consecutive failures (at threshold)
        results = [
            sample_rejected_result,
            sample_rejected_result,
            sample_rejected_result,
        ]

        decision = refiner.evaluate_hypothesis_status(
            hypothesis=sample_hypothesis,
            result=sample_rejected_result,
            results_history=results[:-1],
        )

        assert decision == RetirementDecision.RETIRE

    def test_consecutive_failures_reset_on_success(
        self, refiner, sample_hypothesis, sample_rejected_result, sample_supported_result
    ):
        """Test consecutive failure count resets after success."""
        # 2 failures, 1 success, 2 failures (not consecutive)
        results = [
            sample_rejected_result,
            sample_rejected_result,
            sample_supported_result,
            sample_rejected_result,
            sample_rejected_result,
        ]

        decision = refiner.evaluate_hypothesis_status(
            hypothesis=sample_hypothesis,
            result=sample_rejected_result,
            results_history=results[:-1],
        )

        # Only 2 consecutive failures from end, should refine not retire
        assert decision == RetirementDecision.REFINE

    def test_execution_failures_count_as_failures(
        self, refiner, sample_hypothesis, sample_failed_result
    ):
        """Test execution failures count toward consecutive failure threshold."""
        # 3 execution failures
        results = [sample_failed_result, sample_failed_result, sample_failed_result]

        decision = refiner.evaluate_hypothesis_status(
            hypothesis=sample_hypothesis,
            result=sample_failed_result,
            results_history=results[:-1],
        )

        assert decision == RetirementDecision.RETIRE

    def test_count_consecutive_failures(self, refiner, sample_rejected_result, sample_supported_result):
        """Test _count_consecutive_failures helper method."""
        # Test various patterns
        results_1 = [sample_rejected_result, sample_rejected_result]
        assert refiner._count_consecutive_failures(results_1) == 2

        results_2 = [sample_supported_result, sample_rejected_result, sample_rejected_result]
        assert refiner._count_consecutive_failures(results_2) == 2

        results_3 = [sample_supported_result, sample_supported_result]
        assert refiner._count_consecutive_failures(results_3) == 0


# ============================================================================
# Test Class 3: Bayesian Retirement
# ============================================================================

class TestRetirementDecisionBayesian:
    """Test Bayesian confidence-based retirement decisions."""

    def test_bayesian_update_with_supporting_evidence(
        self, refiner, sample_hypothesis, sample_supported_result
    ):
        """Test Bayesian update increases confidence with supporting evidence."""
        initial_confidence = sample_hypothesis.confidence_score  # 0.5

        # Strong support (p=0.01, effect=0.75)
        updated_confidence = refiner._bayesian_confidence_update(
            sample_hypothesis, [sample_supported_result]
        )

        # Should increase confidence
        assert updated_confidence > initial_confidence
        assert 0.0 <= updated_confidence <= 1.0

    def test_bayesian_update_with_rejecting_evidence(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test Bayesian update decreases confidence with rejecting evidence."""
        initial_confidence = sample_hypothesis.confidence_score  # 0.5

        # Weak rejection (p=0.65, effect=0.12)
        updated_confidence = refiner._bayesian_confidence_update(
            sample_hypothesis, [sample_rejected_result]
        )

        # Should decrease confidence
        assert updated_confidence < initial_confidence
        assert 0.0 <= updated_confidence <= 1.0

    def test_bayesian_update_multiple_results(
        self, refiner, sample_hypothesis, sample_supported_result, sample_rejected_result
    ):
        """Test Bayesian update with mixed evidence."""
        # 2 supports, 1 rejection
        results = [
            sample_supported_result,
            sample_supported_result,
            sample_rejected_result,
        ]

        updated_confidence = refiner._bayesian_confidence_update(
            sample_hypothesis, results
        )

        # Net support should increase confidence
        assert updated_confidence > sample_hypothesis.confidence_score
        assert 0.0 <= updated_confidence <= 1.0

    def test_bayesian_retirement_low_confidence(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test hypothesis retires when Bayesian confidence drops below threshold."""
        # Create many weak rejections to drive confidence down
        weak_rejections = []
        for i in range(10):
            weak_rejections.append(
                ExperimentResult(
                    id=f"result_{i}",
                    hypothesis_id="hyp_001",
                    supports_hypothesis=False,
                    primary_p_value=0.02,  # Significant
                    primary_effect_size=0.6,  # Medium effect
                    primary_test="t-test",
                    status=ResultStatus.SUCCESS,
                )
            )

        decision = refiner.evaluate_hypothesis_status(
            hypothesis=sample_hypothesis,
            result=weak_rejections[-1],
            results_history=weak_rejections[:-1],
        )

        # Should retire due to low confidence
        assert decision == RetirementDecision.RETIRE

    def test_bayesian_update_bounds(self, refiner, sample_hypothesis, sample_supported_result):
        """Test Bayesian confidence stays within [0, 1]."""
        # Many strong supports shouldn't exceed 1.0
        strong_supports = [sample_supported_result] * 20

        confidence = refiner._bayesian_confidence_update(sample_hypothesis, strong_supports)

        assert 0.0 <= confidence <= 1.0

    def test_bayesian_update_with_none_prior(self, refiner, sample_supported_result):
        """Test Bayesian update handles None confidence_score."""
        hyp = Hypothesis(
            research_question="Test question",
            statement="Test statement",
            rationale="Test rationale",
            domain="test",
            confidence_score=None,  # None should default to 0.5
        )

        confidence = refiner._bayesian_confidence_update(hyp, [sample_supported_result])

        # Should use 0.5 as prior and increase
        assert confidence > 0.5


# ============================================================================
# Test Class 4: Claude-Powered Retirement
# ============================================================================

class TestRetirementDecisionClaude:
    """Test Claude-powered retirement decisions."""

    def test_claude_retirement_decision_retire(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test Claude decides to retire hypothesis."""
        # Mock Claude response
        refiner.llm_client.generate.return_value = json.dumps({
            "decision": "retire",
            "confidence": 0.85,
            "rationale": "Consistent evidence against hypothesis",
            "suggested_action": "Consider alternative mechanisms",
        })

        should_retire, rationale = refiner.should_retire_hypothesis_claude(
            sample_hypothesis, [sample_rejected_result]
        )

        assert should_retire is True
        assert "Consistent evidence" in rationale

    def test_claude_retirement_decision_continue(
        self, refiner, sample_hypothesis, sample_supported_result
    ):
        """Test Claude decides to continue testing."""
        refiner.llm_client.generate.return_value = json.dumps({
            "decision": "continue",
            "confidence": 0.9,
            "rationale": "Strong supporting evidence warrants more investigation",
            "suggested_action": "Test boundary conditions",
        })

        should_retire, rationale = refiner.should_retire_hypothesis_claude(
            sample_hypothesis, [sample_supported_result]
        )

        assert should_retire is False
        assert "supporting evidence" in rationale

    def test_claude_retirement_decision_refine(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test Claude decides to refine hypothesis."""
        refiner.llm_client.generate.return_value = json.dumps({
            "decision": "refine",
            "confidence": 0.75,
            "rationale": "Core idea has merit but needs refinement",
            "suggested_action": "Narrow scope or adjust variables",
        })

        should_retire, rationale = refiner.should_retire_hypothesis_claude(
            sample_hypothesis, [sample_rejected_result]
        )

        # Refine means don't retire
        assert should_retire is False
        assert "refinement" in rationale

    def test_claude_retirement_handles_parsing_error(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test Claude retirement handles invalid JSON response."""
        refiner.llm_client.generate.return_value = "This is not valid JSON"

        should_retire, rationale = refiner.should_retire_hypothesis_claude(
            sample_hypothesis, [sample_rejected_result]
        )

        # Should default to not retiring on error
        assert should_retire is False
        assert "Parsing error" in rationale or "error" in rationale.lower()


# ============================================================================
# Test Class 5: Hypothesis Refinement
# ============================================================================

class TestHypothesisRefinement:
    """Test hypothesis refinement logic."""

    def test_refine_hypothesis(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test hypothesis refinement creates new refined hypothesis."""
        refiner.llm_client.generate.return_value = json.dumps({
            "refined_statement": "Caffeine (200mg) improves working memory performance in young adults aged 18-25",
            "refined_rationale": "Evidence suggests specific dosage and age range matter",
            "changes_made": "Added dosage specificity and age range",
            "confidence": 0.6,
        })

        refined = refiner.refine_hypothesis(sample_hypothesis, sample_rejected_result)

        assert refined is not None
        assert refined.id != sample_hypothesis.id
        assert "200mg" in refined.statement
        assert refined.parent_hypothesis_id == sample_hypothesis.id
        assert refined.generation == sample_hypothesis.generation + 1
        assert len(refined.evolution_history) > 0
        assert refined.evolution_history[0]["action"] == "refined"

    def test_refine_hypothesis_tracks_lineage(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test refinement tracks lineage correctly."""
        refiner.llm_client.generate.return_value = json.dumps({
            "refined_statement": "Refined statement",
            "refined_rationale": "Refined rationale",
            "changes_made": "Changes",
            "confidence": 0.6,
        })

        refined = refiner.refine_hypothesis(sample_hypothesis, sample_rejected_result)

        # Check lineage was tracked
        lineage = refiner.get_lineage(refined.id)
        assert lineage is not None
        assert lineage.parent_id == sample_hypothesis.id
        assert lineage.refinement_reason == "refined"

    def test_refine_hypothesis_increments_generation(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test refinement increments generation number."""
        refiner.llm_client.generate.return_value = json.dumps({
            "refined_statement": "Refined statement",
            "refined_rationale": "Refined rationale",
            "changes_made": "Changes",
            "confidence": 0.6,
        })

        sample_hypothesis.generation = 2  # Start at generation 2

        refined = refiner.refine_hypothesis(sample_hypothesis, sample_rejected_result)

        assert refined.generation == 3

    def test_refine_hypothesis_handles_error(
        self, refiner, sample_hypothesis, sample_rejected_result
    ):
        """Test refinement handles Claude API errors gracefully."""
        refiner.llm_client.generate.side_effect = Exception("API error")

        refined = refiner.refine_hypothesis(sample_hypothesis, sample_rejected_result)

        # Should return original hypothesis on error
        assert refined.id == sample_hypothesis.id


# ============================================================================
# Test Class 6: Contradiction Detection
# ============================================================================

class TestContradictionDetection:
    """Test contradiction detection between hypotheses."""

    def test_detect_contradictions_similar_opposite_outcomes(
        self, refiner
    ):
        """Test detects contradictions when similar hypotheses have opposite outcomes."""
        hyp1 = Hypothesis(
            research_question="Question",
            statement="Caffeine improves memory performance",
            rationale="Rationale 1",
            domain="neuroscience",
        )

        hyp2 = Hypothesis(
            research_question="Question",
            statement="Caffeine enhances memory performance",  # Very similar
            rationale="Rationale 2",
            domain="neuroscience",
        )

        # Opposite outcomes
        result1_supported = ExperimentResult(
            id="r1",
            hypothesis_id=hyp1.id,
            supports_hypothesis=True,
            primary_p_value=0.01,
            primary_effect_size=0.7,
            primary_test="t-test",
            status=ResultStatus.SUCCESS,
        )

        result2_rejected = ExperimentResult(
            id="r2",
            hypothesis_id=hyp2.id,
            supports_hypothesis=False,
            primary_p_value=0.65,
            primary_effect_size=0.1,
            primary_test="t-test",
            status=ResultStatus.SUCCESS,
        )

        results = {
            hyp1.id: [result1_supported],
            hyp2.id: [result2_rejected],
        }

        contradictions = refiner.detect_contradictions([hyp1, hyp2], results)

        # Should detect contradiction
        assert len(contradictions) > 0
        assert contradictions[0]["hypothesis1_id"] in [hyp1.id, hyp2.id]
        assert contradictions[0]["hypothesis2_id"] in [hyp1.id, hyp2.id]
        assert contradictions[0]["similarity"] >= refiner.similarity_threshold

    def test_no_contradiction_dissimilar_hypotheses(self, refiner):
        """Test no contradiction for dissimilar hypotheses even with opposite outcomes."""
        hyp1 = Hypothesis(
            research_question="Question",
            statement="Caffeine improves memory performance",
            rationale="Rationale 1",
            domain="neuroscience",
        )

        hyp2 = Hypothesis(
            research_question="Question",
            statement="Exercise reduces stress levels",  # Completely different
            rationale="Rationale 2",
            domain="psychology",
        )

        result1 = ExperimentResult(
            id="r1",
            hypothesis_id=hyp1.id,
            supports_hypothesis=True,
            primary_p_value=0.01,
            primary_effect_size=0.7,
            primary_test="t-test",
            status=ResultStatus.SUCCESS,
        )

        result2 = ExperimentResult(
            id="r2",
            hypothesis_id=hyp2.id,
            supports_hypothesis=False,
            primary_p_value=0.65,
            primary_effect_size=0.1,
            primary_test="t-test",
            status=ResultStatus.SUCCESS,
        )

        results = {hyp1.id: [result1], hyp2.id: [result2]}

        contradictions = refiner.detect_contradictions([hyp1, hyp2], results)

        # Should not detect contradiction (too dissimilar)
        assert len(contradictions) == 0

    def test_no_contradiction_same_outcome(self, refiner):
        """Test no contradiction when similar hypotheses have same outcome."""
        hyp1 = Hypothesis(
            research_question="Question",
            statement="Caffeine improves memory performance",
            rationale="Rationale 1",
            domain="neuroscience",
        )

        hyp2 = Hypothesis(
            research_question="Question",
            statement="Caffeine enhances memory ability",
            rationale="Rationale 2",
            domain="neuroscience",
        )

        # Same outcome (both supported)
        result1 = ExperimentResult(
            id="r1",
            hypothesis_id=hyp1.id,
            supports_hypothesis=True,
            primary_p_value=0.01,
            primary_effect_size=0.7,
            primary_test="t-test",
            status=ResultStatus.SUCCESS,
        )

        result2 = ExperimentResult(
            id="r2",
            hypothesis_id=hyp2.id,
            supports_hypothesis=True,
            primary_p_value=0.02,
            primary_effect_size=0.6,
            primary_test="t-test",
            status=ResultStatus.SUCCESS,
        )

        results = {hyp1.id: [result1], hyp2.id: [result2]}

        contradictions = refiner.detect_contradictions([hyp1, hyp2], results)

        # Should not detect contradiction (same outcome)
        assert len(contradictions) == 0


# ============================================================================
# Test Class 7: Hypothesis Merging
# ============================================================================

class TestHypothesisMerging:
    """Test hypothesis merging logic."""

    def test_merge_hypotheses(self, refiner):
        """Test merging multiple similar hypotheses."""
        hyp1 = Hypothesis(
            research_question="Question",
            statement="Caffeine improves memory",
            rationale="Rationale 1",
            domain="neuroscience",
            generation=1,
        )

        hyp2 = Hypothesis(
            research_question="Question",
            statement="Caffeine enhances attention",
            rationale="Rationale 2",
            domain="neuroscience",
            generation=1,
        )

        refiner.llm_client.generate.return_value = json.dumps({
            "merged_statement": "Caffeine improves both memory and attention in cognitive tasks",
            "merged_rationale": "Combined evidence shows multi-faceted cognitive benefits",
            "synthesis_explanation": "Merged memory and attention effects",
        })

        merged = refiner.merge_hypotheses([hyp1, hyp2])

        assert merged is not None
        assert "memory and attention" in merged.statement
        assert merged.parent_hypothesis_id == hyp1.id
        assert merged.generation == 2  # max(1, 1) + 1
        assert len(merged.evolution_history) > 0
        assert merged.evolution_history[0]["action"] == "merged"
        assert hyp1.id in merged.evolution_history[0]["merged_from"]
        assert hyp2.id in merged.evolution_history[0]["merged_from"]

    def test_merge_handles_different_generations(self, refiner):
        """Test merging hypotheses from different generations."""
        hyp1 = Hypothesis(
            research_question="Question",
            statement="Statement 1",
            rationale="Rationale 1",
            domain="test",
            generation=1,
        )

        hyp2 = Hypothesis(
            research_question="Question",
            statement="Statement 2",
            rationale="Rationale 2",
            domain="test",
            generation=3,
        )

        refiner.llm_client.generate.return_value = json.dumps({
            "merged_statement": "Merged statement",
            "merged_rationale": "Merged rationale",
            "synthesis_explanation": "Synthesis",
        })

        merged = refiner.merge_hypotheses([hyp1, hyp2])

        # Should be max(1, 3) + 1 = 4
        assert merged.generation == 4


# ============================================================================
# Test Class 8: Lineage Tracking
# ============================================================================

class TestLineageTracking:
    """Test hypothesis lineage and family tree tracking."""

    def test_track_lineage(self, refiner):
        """Test lineage is tracked for refined hypotheses."""
        parent = Hypothesis(
            research_question="Question",
            statement="Parent statement",
            rationale="Parent rationale",
            domain="test",
            generation=1,
        )

        child = Hypothesis(
            research_question="Question",
            statement="Child statement",
            rationale="Child rationale",
            domain="test",
            parent_hypothesis_id=parent.id,
            generation=2,
        )

        refiner._track_lineage(child, parent, "refined", ["result_001"])

        lineage = refiner.get_lineage(child.id)
        assert lineage is not None
        assert lineage.hypothesis_id == child.id
        assert lineage.parent_id == parent.id
        assert lineage.generation == 2
        assert lineage.refinement_reason == "refined"
        assert "result_001" in lineage.evidence_basis

    def test_get_family_tree_no_relatives(self, refiner):
        """Test family tree for hypothesis with no relatives."""
        hyp = Hypothesis(
            research_question="Question",
            statement="Statement",
            rationale="Rationale",
            domain="test",
        )

        # Don't track it - should return empty tree
        tree = refiner.get_family_tree(hyp.id)

        assert tree["hypothesis_id"] == hyp.id
        assert tree["ancestors"] == []
        assert tree["descendants"] == []

    def test_get_family_tree_with_parent(self, refiner):
        """Test family tree includes parent."""
        parent = Hypothesis(
            research_question="Question",
            statement="Parent",
            rationale="Rationale",
            domain="test",
            generation=1,
        )

        child = Hypothesis(
            research_question="Question",
            statement="Child",
            rationale="Rationale",
            domain="test",
            parent_hypothesis_id=parent.id,
            generation=2,
        )

        # Track both
        refiner.lineage_tracking[parent.id] = HypothesisLineage(
            hypothesis_id=parent.id,
            parent_id=None,
            generation=1,
        )

        refiner._track_lineage(child, parent, "refined", [])

        tree = refiner.get_family_tree(child.id)

        assert tree["hypothesis_id"] == child.id
        assert parent.id in tree["ancestors"]
        assert tree["total_family_size"] == 2  # child + parent

    def test_get_family_tree_with_children(self, refiner):
        """Test family tree includes children."""
        parent = Hypothesis(
            research_question="Question",
            statement="Parent",
            rationale="Rationale",
            domain="test",
            generation=1,
        )

        child1 = Hypothesis(
            research_question="Question",
            statement="Child 1",
            rationale="Rationale",
            domain="test",
            parent_hypothesis_id=parent.id,
            generation=2,
        )

        child2 = Hypothesis(
            research_question="Question",
            statement="Child 2",
            rationale="Rationale",
            domain="test",
            parent_hypothesis_id=parent.id,
            generation=2,
        )

        # Track lineage
        refiner.lineage_tracking[parent.id] = HypothesisLineage(
            hypothesis_id=parent.id,
            parent_id=None,
            generation=1,
            children_ids=[],
        )

        refiner._track_lineage(child1, parent, "spawned", [])
        refiner._track_lineage(child2, parent, "spawned", [])

        tree = refiner.get_family_tree(parent.id)

        assert tree["hypothesis_id"] == parent.id
        assert child1.id in tree["descendants"]
        assert child2.id in tree["descendants"]
        assert tree["total_family_size"] == 3  # parent + 2 children

    def test_get_family_tree_multi_generation(self, refiner):
        """Test family tree with multiple generations."""
        gen1 = Hypothesis(
            research_question="Question",
            statement="Gen 1",
            rationale="Rationale",
            domain="test",
            generation=1,
        )

        gen2 = Hypothesis(
            research_question="Question",
            statement="Gen 2",
            rationale="Rationale",
            domain="test",
            parent_hypothesis_id=gen1.id,
            generation=2,
        )

        gen3 = Hypothesis(
            research_question="Question",
            statement="Gen 3",
            rationale="Rationale",
            domain="test",
            parent_hypothesis_id=gen2.id,
            generation=3,
        )

        # Track all
        refiner.lineage_tracking[gen1.id] = HypothesisLineage(
            hypothesis_id=gen1.id,
            parent_id=None,
            generation=1,
            children_ids=[],
        )

        refiner._track_lineage(gen2, gen1, "refined", [])
        refiner._track_lineage(gen3, gen2, "refined", [])

        # Get tree for gen2
        tree = refiner.get_family_tree(gen2.id)

        assert tree["hypothesis_id"] == gen2.id
        assert tree["generation"] == 2
        assert gen1.id in tree["ancestors"]
        assert gen3.id in tree["descendants"]
        assert tree["total_family_size"] == 3
