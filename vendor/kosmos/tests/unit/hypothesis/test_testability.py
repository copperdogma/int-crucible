"""Tests for testability analyzer."""

import pytest
from unittest.mock import Mock, patch
from kosmos.hypothesis.testability import TestabilityAnalyzer
from kosmos.models.hypothesis import Hypothesis, ExperimentType

@pytest.fixture
def testability_analyzer():
    return TestabilityAnalyzer(testability_threshold=0.3, use_llm_for_assessment=False)

@pytest.fixture
def testable_hypothesis():
    return Hypothesis(
        research_question="How does X affect Y?",
        statement="Increasing parameter X will improve metric Y by 20%",
        rationale="Prior work shows X affects Y through mechanism Z with measurable effects",
        domain="machine_learning"
    )

@pytest.mark.unit
class TestTestabilityAnalyzer:
    def test_init(self, testability_analyzer):
        assert testability_analyzer.testability_threshold == 0.3

    def test_analyze_testable_hypothesis(self, testability_analyzer, testable_hypothesis):
        report = testability_analyzer.analyze_testability(testable_hypothesis)

        assert report.testability_score > 0.3
        assert report.is_testable is True
        assert len(report.suggested_experiments) > 0
        assert report.primary_experiment_type in [ExperimentType.COMPUTATIONAL, ExperimentType.DATA_ANALYSIS]

    def test_suggest_experiment_types(self, testability_analyzer, testable_hypothesis):
        experiments = testability_analyzer._suggest_experiment_types(testable_hypothesis)

        assert len(experiments) == 3  # All 3 types scored
        assert all("score" in exp for exp in experiments)
        assert experiments[0]["score"] >= experiments[1]["score"]  # Sorted by score
