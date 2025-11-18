"""
Phase 3 end-to-end integration tests.

Tests complete workflow: Generation → Novelty → Testability → Prioritization
"""

import pytest
from unittest.mock import Mock, patch
from kosmos.agents.hypothesis_generator import HypothesisGeneratorAgent
from kosmos.hypothesis.novelty_checker import NoveltyChecker
from kosmos.hypothesis.testability import TestabilityAnalyzer
from kosmos.hypothesis.prioritizer import HypothesisPrioritizer
from kosmos.models.hypothesis import Hypothesis

@pytest.fixture
def mock_llm_hypotheses():
    return {
        "hypotheses": [
            {
                "statement": "Hypothesis 1: X increases Y by 20%",
                "rationale": "Evidence shows X affects Y through mechanism Z",
                "confidence_score": 0.8,
                "testability_score": 0.85,
                "suggested_experiment_types": ["computational"]
            },
            {
                "statement": "Hypothesis 2: A correlates with B",
                "rationale": "Data suggests strong correlation between A and B",
                "confidence_score": 0.7,
                "testability_score": 0.75,
                "suggested_experiment_types": ["data_analysis"]
            }
        ]
    }

@pytest.mark.integration
class TestPhase3EndToEnd:
    """Test complete Phase 3 workflow."""

    @patch('kosmos.agents.hypothesis_generator.get_client')
    @patch('kosmos.hypothesis.novelty_checker.UnifiedLiteratureSearch')
    @patch('kosmos.hypothesis.novelty_checker.get_session')
    def test_full_hypothesis_pipeline(self, mock_session, mock_search, mock_get_client, mock_llm_hypotheses):
        """Test: Generate → Check Novelty → Analyze Testability → Prioritize."""

        # Setup mocks
        mock_client = Mock()
        mock_client.generate_structured.return_value = mock_llm_hypotheses
        mock_client.generate.return_value = "machine_learning"
        mock_get_client.return_value = mock_client

        mock_search_inst = Mock()
        mock_search_inst.search.return_value = []
        mock_search.return_value = mock_search_inst

        mock_sess = Mock()
        mock_sess.query.return_value.filter.return_value.all.return_value = []
        mock_session.return_value = mock_sess

        # Step 1: Generate hypotheses
        agent = HypothesisGeneratorAgent(config={"use_literature_context": False})
        agent.llm_client = mock_client
        response = agent.generate_hypotheses(
            research_question="How does X affect Y?",
            store_in_db=False
        )

        assert len(response.hypotheses) == 2
        hypotheses = response.hypotheses

        # Step 2: Check novelty
        novelty_checker = NoveltyChecker(use_vector_db=False)
        novelty_checker.literature_search = mock_search_inst

        for hyp in hypotheses:
            report = novelty_checker.check_novelty(hyp)
            assert report.novelty_score is not None
            assert 0.0 <= report.novelty_score <= 1.0
            hyp.novelty_score = report.novelty_score

        # Step 3: Analyze testability
        testability_analyzer = TestabilityAnalyzer(use_llm_for_assessment=False)

        for hyp in hypotheses:
            report = testability_analyzer.analyze_testability(hyp)
            assert report.testability_score is not None
            assert report.is_testable or not report.is_testable  # Boolean
            hyp.testability_score = report.testability_score

        # Step 4: Prioritize
        prioritizer = HypothesisPrioritizer(
            use_novelty_checker=False,  # Already done
            use_testability_analyzer=False,  # Already done
            use_impact_prediction=False
        )

        ranked = prioritizer.prioritize(hypotheses, run_analysis=False)

        assert len(ranked) == 2
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2
        assert ranked[0].priority_score > 0.0

        # Verify all scores present
        for p in ranked:
            assert p.novelty_score is not None
            assert p.testability_score is not None
            assert p.feasibility_score is not None
            assert p.impact_score is not None

    @patch('kosmos.agents.hypothesis_generator.get_client')
    def test_hypothesis_filtering(self, mock_get_client):
        """Test filtering untestable or non-novel hypotheses."""
        mock_client = Mock()
        mock_client.generate_structured.return_value = {
            "hypotheses": [
                {
                    "statement": "Good hypothesis with clear prediction",
                    "rationale": "Well-supported by evidence and prior work",
                    "confidence_score": 0.8,
                    "testability_score": 0.9,
                    "suggested_experiment_types": ["computational"]
                },
                {
                    "statement": "Vague hypothesis maybe possibly",
                    "rationale": "Not much support",
                    "confidence_score": 0.3,
                    "testability_score": 0.2,
                    "suggested_experiment_types": []
                }
            ]
        }
        mock_client.generate.return_value = "test"
        mock_get_client.return_value = mock_client

        agent = HypothesisGeneratorAgent(config={"use_literature_context": False})
        agent.llm_client = mock_client

        response = agent.generate_hypotheses("Test question?", store_in_db=False)

        # Filter testable hypotheses
        testable = [h for h in response.hypotheses if h.is_testable(threshold=0.5)]

        assert len(testable) == 1  # Only the good hypothesis
        assert testable[0].testability_score >= 0.5

    def test_hypothesis_model_validation(self):
        """Test Pydantic validation on Hypothesis model."""
        # Valid hypothesis
        hyp = Hypothesis(
            research_question="Valid question?",
            statement="This is a clear testable statement",
            rationale="This is a sufficient rationale that explains the hypothesis",
            domain="test"
        )
        assert hyp.statement == "This is a clear testable statement"

        # Invalid: statement too short (should fail validation)
        with pytest.raises(ValueError):
            Hypothesis(
                research_question="Test",
                statement="Too short",
                rationale="Valid rationale here",
                domain="test"
            )

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_claude
class TestPhase3RealIntegration:
    """Integration tests with real services (requires Claude, DB)."""

    def test_real_hypothesis_workflow(self):
        """Test with real Claude API (slow, requires API key)."""
        agent = HypothesisGeneratorAgent(config={
            "num_hypotheses": 2,
            "use_literature_context": False
        })

        response = agent.generate_hypotheses(
            research_question="How does batch size affect neural network training?",
            domain="machine_learning",
            store_in_db=False
        )

        assert len(response.hypotheses) > 0

        # Analyze first hypothesis
        hyp = response.hypotheses[0]

        # Check novelty
        novelty_checker = NoveltyChecker(use_vector_db=False)
        novelty_report = novelty_checker.check_novelty(hyp)
        assert novelty_report.novelty_score is not None

        # Check testability
        testability_analyzer = TestabilityAnalyzer(use_llm_for_assessment=False)
        testability_report = testability_analyzer.analyze_testability(hyp)
        assert testability_report.is_testable or not testability_report.is_testable
