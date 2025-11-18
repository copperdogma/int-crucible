"""
Unit tests for RankerService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from crucible.services.ranker_service import RankerService
from crucible.db.models import CandidateStatus


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    session.commit = Mock()
    return session


@pytest.fixture
def ranker_service(mock_session):
    """Create RankerService with mocked session."""
    service = RankerService(mock_session)
    return service


@pytest.fixture
def sample_problem_spec():
    """Sample ProblemSpec."""
    spec = Mock()
    spec.constraints = [
        {"name": "constraint_1", "description": "Test", "weight": 80},
        {"name": "constraint_2", "description": "Hard constraint", "weight": 100}
    ]
    spec.goals = ["Goal 1"]
    return spec


@pytest.fixture
def sample_candidate():
    """Sample Candidate."""
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.mechanism_description = "Test mechanism"
    candidate.scores = None
    candidate.status = CandidateStatus.NEW
    return candidate


@pytest.fixture
def sample_evaluation():
    """Sample Evaluation."""
    evaluation = Mock()
    evaluation.candidate_id = "candidate_1"
    evaluation.scenario_id = "scenario_1"
    evaluation.P = {"overall": 0.8}
    evaluation.R = {"overall": 0.6}
    evaluation.constraint_satisfaction = {
        "constraint_1": {
            "satisfied": True,
            "score": 0.9,
            "explanation": "Satisfied"
        },
        "constraint_2": {
            "satisfied": True,
            "score": 0.8,
            "explanation": "Satisfied"
        }
    }
    return evaluation


def test_ranker_service_initialization(ranker_service):
    """Test RankerService initialization."""
    assert ranker_service.session is not None


@patch('crucible.services.ranker_service.get_run')
@patch('crucible.services.ranker_service.get_problem_spec')
@patch('crucible.services.ranker_service.list_candidates')
@patch('crucible.services.ranker_service.list_evaluations')
@patch('crucible.services.ranker_service.update_candidate')
def test_rank_candidates_success(
    mock_update_candidate,
    mock_list_evaluations,
    mock_list_candidates,
    mock_get_problem_spec,
    mock_get_run,
    ranker_service,
    sample_candidate,
    sample_evaluation,
    sample_problem_spec
):
    """Test successful candidate ranking."""
    # Setup mocks
    mock_run = Mock()
    mock_run.id = "run_1"
    mock_run.project_id = "project_1"
    mock_get_run.return_value = mock_run

    mock_get_problem_spec.return_value = sample_problem_spec
    mock_list_candidates.return_value = [sample_candidate]
    mock_list_evaluations.return_value = [sample_evaluation]

    result = ranker_service.rank_candidates(
        run_id="run_1",
        project_id="project_1"
    )

    assert "ranked_candidates" in result
    assert "count" in result
    assert "hard_constraint_violations" in result
    assert result["count"] == 1
    assert len(result["hard_constraint_violations"]) == 0  # No violations

    # Verify candidate was updated
    assert mock_update_candidate.call_count >= 1


@patch('crucible.services.ranker_service.get_run')
def test_rank_candidates_missing_run(
    mock_get_run,
    ranker_service
):
    """Test ranking with missing run."""
    mock_get_run.return_value = None

    with pytest.raises(ValueError, match="Run not found"):
        ranker_service.rank_candidates(
            run_id="run_1",
            project_id="project_1"
        )


@patch('crucible.services.ranker_service.get_run')
@patch('crucible.services.ranker_service.get_problem_spec')
def test_rank_candidates_missing_problem_spec(
    mock_get_problem_spec,
    mock_get_run,
    ranker_service
):
    """Test ranking with missing ProblemSpec."""
    mock_run = Mock()
    mock_run.id = "run_1"
    mock_run.project_id = "project_1"
    mock_get_run.return_value = mock_run

    mock_get_problem_spec.return_value = None

    with pytest.raises(ValueError, match="ProblemSpec not found"):
        ranker_service.rank_candidates(
            run_id="run_1",
            project_id="project_1"
        )


@patch('crucible.services.ranker_service.get_run')
@patch('crucible.services.ranker_service.get_problem_spec')
@patch('crucible.services.ranker_service.list_candidates')
def test_rank_candidates_no_candidates(
    mock_list_candidates,
    mock_get_problem_spec,
    mock_get_run,
    ranker_service,
    sample_problem_spec
):
    """Test ranking with no candidates."""
    mock_run = Mock()
    mock_run.id = "run_1"
    mock_run.project_id = "project_1"
    mock_get_run.return_value = mock_run

    mock_get_problem_spec.return_value = sample_problem_spec
    mock_list_candidates.return_value = []

    with pytest.raises(ValueError, match="No candidates found"):
        ranker_service.rank_candidates(
            run_id="run_1",
            project_id="project_1"
        )


@patch('crucible.services.ranker_service.get_run')
@patch('crucible.services.ranker_service.get_problem_spec')
@patch('crucible.services.ranker_service.list_candidates')
@patch('crucible.services.ranker_service.list_evaluations')
@patch('crucible.services.ranker_service.update_candidate')
def test_rank_candidates_hard_constraint_violation(
    mock_update_candidate,
    mock_list_evaluations,
    mock_list_candidates,
    mock_get_problem_spec,
    mock_get_run,
    ranker_service,
    sample_candidate,
    sample_problem_spec
):
    """Test ranking with hard constraint violation."""
    # Setup mocks
    mock_run = Mock()
    mock_run.id = "run_1"
    mock_run.project_id = "project_1"
    mock_get_run.return_value = mock_run

    mock_get_problem_spec.return_value = sample_problem_spec
    mock_list_candidates.return_value = [sample_candidate]

    # Create evaluation with hard constraint violation
    mock_evaluation = Mock()
    mock_evaluation.candidate_id = "candidate_1"
    mock_evaluation.scenario_id = "scenario_1"
    mock_evaluation.P = {"overall": 0.8}
    mock_evaluation.R = {"overall": 0.6}
    mock_evaluation.constraint_satisfaction = {
        "constraint_2": {  # Hard constraint (weight 100)
            "satisfied": False,  # Violated!
            "score": 0.2,
            "explanation": "Violated"
        }
    }
    mock_list_evaluations.return_value = [mock_evaluation]

    result = ranker_service.rank_candidates(
        run_id="run_1",
        project_id="project_1"
    )

    assert len(result["hard_constraint_violations"]) == 1
    assert "candidate_1" in result["hard_constraint_violations"]

