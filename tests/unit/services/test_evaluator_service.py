"""
Unit tests for EvaluatorService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from crucible.services.evaluator_service import EvaluatorService
from crucible.db.models import CandidateOrigin, CandidateStatus


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    return session


@pytest.fixture
def evaluator_service(mock_session):
    """Create EvaluatorService with mocked session."""
    service = EvaluatorService(mock_session)
    service.agent = Mock()
    return service


@pytest.fixture
def sample_candidate():
    """Sample Candidate."""
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.mechanism_description = "Test mechanism"
    candidate.predicted_effects = {
        "actors_affected": [{"actor_id": "actor_1", "impact": "positive"}]
    }
    candidate.scores = {}
    return candidate


@pytest.fixture
def sample_problem_spec():
    """Sample ProblemSpec."""
    spec = Mock()
    spec.constraints = [{"name": "constraint_1", "description": "Test", "weight": 80}]
    spec.goals = ["Goal 1"]
    spec.resolution = Mock()
    spec.resolution.value = "medium"
    spec.mode = Mock()
    spec.mode.value = "full_search"
    return spec


@pytest.fixture
def sample_world_model():
    """Sample WorldModel."""
    model = Mock()
    model.model_data = {
        "actors": [{"id": "actor_1", "name": "Actor 1"}],
        "mechanisms": [],
        "resources": []
    }
    return model


@pytest.fixture
def sample_scenario():
    """Sample scenario."""
    return {
        "id": "scenario_1",
        "name": "Test scenario",
        "description": "Test description",
        "type": "stress_test",
        "focus": {"constraints": ["constraint_1"]},
        "initial_state": {},
        "events": [],
        "expected_outcomes": {}
    }


def test_evaluator_service_initialization(evaluator_service):
    """Test EvaluatorService initialization."""
    assert evaluator_service.session is not None
    assert evaluator_service.agent is not None


@patch('crucible.services.evaluator_service.get_candidate')
@patch('crucible.services.evaluator_service.get_problem_spec')
@patch('crucible.services.evaluator_service.get_world_model')
@patch('crucible.services.evaluator_service.create_evaluation')
def test_evaluate_candidate_against_scenario_success(
    mock_create_evaluation,
    mock_get_world_model,
    mock_get_problem_spec,
    mock_get_candidate,
    evaluator_service,
    sample_candidate,
    sample_problem_spec,
    sample_world_model,
    sample_scenario
):
    """Test successful candidate evaluation."""
    # Setup mocks
    mock_get_candidate.return_value = sample_candidate
    mock_get_problem_spec.return_value = sample_problem_spec
    mock_get_world_model.return_value = sample_world_model

    # Mock agent response
    evaluator_service.agent.execute.return_value = {
        "P": {"overall": 0.8},
        "R": {"overall": 0.6},
        "constraint_satisfaction": {
            "constraint_1": {
                "satisfied": True,
                "score": 0.9,
                "explanation": "Satisfied"
            }
        },
        "explanation": "Good performance"
    }

    # Mock evaluation creation
    mock_evaluation = Mock()
    mock_evaluation.id = "eval_1"
    mock_evaluation.candidate_id = "candidate_1"
    mock_evaluation.scenario_id = "scenario_1"
    mock_evaluation.P = {"overall": 0.8}
    mock_evaluation.R = {"overall": 0.6}
    mock_evaluation.constraint_satisfaction = {"constraint_1": {"satisfied": True, "score": 0.9, "explanation": "Satisfied"}}
    mock_evaluation.explanation = "Good performance"
    mock_create_evaluation.return_value = mock_evaluation

    result = evaluator_service.evaluate_candidate_against_scenario(
        candidate_id="candidate_1",
        scenario=sample_scenario,
        run_id="run_1",
        project_id="project_1"
    )

    assert "evaluation" in result
    assert "P" in result
    assert "R" in result
    assert result["evaluation"]["id"] == "eval_1"


@patch('crucible.services.evaluator_service.get_candidate')
def test_evaluate_candidate_against_scenario_missing_candidate(
    mock_get_candidate,
    evaluator_service,
    sample_scenario
):
    """Test evaluation with missing candidate."""
    mock_get_candidate.return_value = None

    with pytest.raises(ValueError, match="Candidate not found"):
        evaluator_service.evaluate_candidate_against_scenario(
            candidate_id="candidate_1",
            scenario=sample_scenario,
            run_id="run_1",
            project_id="project_1"
        )


@patch('crucible.services.evaluator_service.get_run')
@patch('crucible.services.evaluator_service.list_candidates')
@patch('crucible.services.evaluator_service.get_scenario_suite')
@patch('crucible.services.evaluator_service.list_evaluations')
def test_evaluate_all_candidates_success(
    mock_list_evaluations,
    mock_get_scenario_suite,
    mock_list_candidates,
    mock_get_run,
    evaluator_service,
    sample_candidate,
    sample_scenario
):
    """Test successful evaluation of all candidates."""
    # Setup mocks
    mock_run = Mock()
    mock_run.id = "run_1"
    mock_run.project_id = "project_1"
    mock_get_run.return_value = mock_run

    mock_list_candidates.return_value = [sample_candidate]

    mock_scenario_suite = Mock()
    mock_scenario_suite.scenarios = [sample_scenario]
    mock_get_scenario_suite.return_value = mock_scenario_suite

    mock_list_evaluations.return_value = []  # No existing evaluations

    # Mock agent response
    evaluator_service.agent.execute.return_value = {
        "P": {"overall": 0.8},
        "R": {"overall": 0.6},
        "constraint_satisfaction": {},
        "explanation": "Test"
    }

    # Mock evaluation creation
    mock_evaluation = Mock()
    mock_evaluation.id = "eval_1"
    mock_evaluation.candidate_id = "candidate_1"
    mock_evaluation.scenario_id = "scenario_1"
    mock_evaluation.P = {"overall": 0.8}
    mock_evaluation.R = {"overall": 0.6}
    mock_evaluation.constraint_satisfaction = {}
    mock_evaluation.explanation = "Test"

    with patch('crucible.services.evaluator_service.create_evaluation', return_value=mock_evaluation):
        result = evaluator_service.evaluate_all_candidates(
            run_id="run_1",
            project_id="project_1"
        )

        assert "evaluations" in result
        assert "count" in result
        assert result["count"] == 1
        assert result["candidates_evaluated"] == 1
        assert result["scenarios_used"] == 1


@patch('crucible.services.evaluator_service.get_run')
def test_evaluate_all_candidates_missing_run(
    mock_get_run,
    evaluator_service
):
    """Test evaluation with missing run."""
    mock_get_run.return_value = None

    with pytest.raises(ValueError, match="Run not found"):
        evaluator_service.evaluate_all_candidates(
            run_id="run_1",
            project_id="project_1"
        )

