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
    candidate.provenance_log = []  # Initialize as empty list
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
@patch('crucible.services.ranker_service.append_candidate_provenance_entry')
def test_rank_candidates_success(
    mock_append_provenance,
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
@patch('crucible.services.ranker_service.append_candidate_provenance_entry')
def test_rank_candidates_hard_constraint_violation(
    mock_append_provenance,
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


def test_generate_ranking_explanation_clear_winner(ranker_service, sample_problem_spec):
    """Test explanation generation for clear winner candidate (high I, no violations)."""
    # Create a high-performing candidate
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.scores = {
        "I": 2.5,
        "P": {"overall": 0.9},
        "R": {"overall": 0.36},
        "constraint_satisfaction": {
            "constraint_1": {"satisfied": True, "score": 0.95},
            "constraint_2": {"satisfied": True, "score": 0.85}
        }
    }
    
    # Create ranked candidates list (this candidate is #1)
    all_ranked_candidates = [
        {"id": "candidate_1", "scores": candidate.scores},
        {"id": "candidate_2", "scores": {"I": 1.8, "P": {"overall": 0.7}, "R": {"overall": 0.39}}}
    ]
    
    constraint_weights = {"constraint_1": 80, "constraint_2": 100}
    
    result = ranker_service._generate_ranking_explanation(
        candidate=candidate,
        rank_index=0,
        all_ranked_candidates=all_ranked_candidates,
        constraint_weights=constraint_weights,
        problem_spec=sample_problem_spec
    )
    
    assert "ranking_explanation" in result
    assert "ranking_factors" in result
    assert "top_positive_factors" in result["ranking_factors"]
    assert "top_negative_factors" in result["ranking_factors"]
    
    # Should emphasize strengths
    explanation = result["ranking_explanation"]
    assert "Ranked #1" in explanation
    assert len(result["ranking_factors"]["top_positive_factors"]) > 0
    # Should mention high P or low R
    assert any("High" in f or "Low" in f for f in result["ranking_factors"]["top_positive_factors"])


def test_generate_ranking_explanation_hard_violation(ranker_service, sample_problem_spec):
    """Test explanation generation for candidate with hard constraint violation."""
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.scores = {
        "I": 1.2,
        "P": {"overall": 0.6},
        "R": {"overall": 0.5},
        "constraint_satisfaction": {
            "constraint_2": {"satisfied": False, "score": 0.2}  # Hard constraint violated
        }
    }
    
    all_ranked_candidates = [
        {"id": "candidate_1", "scores": candidate.scores}
    ]
    
    constraint_weights = {"constraint_2": 100}
    
    result = ranker_service._generate_ranking_explanation(
        candidate=candidate,
        rank_index=0,
        all_ranked_candidates=all_ranked_candidates,
        constraint_weights=constraint_weights,
        problem_spec=sample_problem_spec
    )
    
    explanation = result["ranking_explanation"]
    # Should mention violation prominently
    assert "Violates" in explanation or "violates" in explanation.lower()
    assert len(result["ranking_factors"]["top_negative_factors"]) > 0
    assert any("Violates hard constraint" in f for f in result["ranking_factors"]["top_negative_factors"])


def test_generate_ranking_explanation_similar_tradeoffs(ranker_service, sample_problem_spec):
    """Test explanation for candidates with similar P/R but different tradeoffs."""
    # Candidate with high P, high R
    candidate1 = Mock()
    candidate1.id = "candidate_1"
    candidate1.scores = {
        "I": 1.5,
        "P": {"overall": 0.9},
        "R": {"overall": 0.6},  # Higher R
        "constraint_satisfaction": {
            "constraint_1": {"satisfied": True, "score": 0.95}
        }
    }
    
    # Candidate with lower P, lower R
    candidate2 = Mock()
    candidate2.id = "candidate_2"
    candidate2.scores = {
        "I": 1.4,
        "P": {"overall": 0.7},
        "R": {"overall": 0.5},  # Lower R
        "constraint_satisfaction": {
            "constraint_1": {"satisfied": True, "score": 0.8}
        }
    }
    
    all_ranked_candidates = [
        {"id": "candidate_1", "scores": candidate1.scores},
        {"id": "candidate_2", "scores": candidate2.scores}
    ]
    
    constraint_weights = {"constraint_1": 80}
    
    # Test first candidate
    result1 = ranker_service._generate_ranking_explanation(
        candidate=candidate1,
        rank_index=0,
        all_ranked_candidates=all_ranked_candidates,
        constraint_weights=constraint_weights,
        problem_spec=sample_problem_spec
    )
    
    # Should highlight high P
    assert any("High" in f or "prediction" in f.lower() for f in result1["ranking_factors"]["top_positive_factors"])


def test_generate_ranking_explanation_single_candidate(ranker_service, sample_problem_spec):
    """Test explanation generation for single candidate (edge case)."""
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.scores = {
        "I": 1.5,
        "P": {"overall": 0.8},
        "R": {"overall": 0.53},
        "constraint_satisfaction": {
            "constraint_1": {"satisfied": True, "score": 0.9}
        }
    }
    
    all_ranked_candidates = [
        {"id": "candidate_1", "scores": candidate.scores}
    ]
    
    constraint_weights = {"constraint_1": 80}
    
    result = ranker_service._generate_ranking_explanation(
        candidate=candidate,
        rank_index=0,
        all_ranked_candidates=all_ranked_candidates,
        constraint_weights=constraint_weights,
        problem_spec=sample_problem_spec
    )
    
    # Should still generate explanation
    assert "ranking_explanation" in result
    assert "Ranked #1" in result["ranking_explanation"]
    # Should not crash when comparing to non-existent #2


def test_generate_ranking_explanation_missing_constraint_names(ranker_service):
    """Test explanation generation when constraint names are missing (fallback to IDs)."""
    # ProblemSpec with constraint that has no name
    problem_spec = Mock()
    problem_spec.constraints = [
        {"id": "unknown_constraint", "weight": 100}  # No name field
    ]
    
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.scores = {
        "I": 1.0,
        "P": {"overall": 0.7},
        "R": {"overall": 0.7},
        "constraint_satisfaction": {
            "unknown_constraint": {"satisfied": False, "score": 0.3}
        }
    }
    
    all_ranked_candidates = [
        {"id": "candidate_1", "scores": candidate.scores}
    ]
    
    constraint_weights = {"unknown_constraint": 100}
    
    result = ranker_service._generate_ranking_explanation(
        candidate=candidate,
        rank_index=0,
        all_ranked_candidates=all_ranked_candidates,
        constraint_weights=constraint_weights,
        problem_spec=problem_spec
    )
    
    # Should use constraint ID as fallback
    explanation = result["ranking_explanation"]
    assert "unknown_constraint" in explanation or "constraint" in explanation.lower()


def test_generate_ranking_explanation_all_rejected(ranker_service, sample_problem_spec):
    """Test explanation generation when all candidates are rejected (edge case)."""
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.scores = {
        "I": 0.5,
        "P": {"overall": 0.4},
        "R": {"overall": 0.8},
        "constraint_satisfaction": {
            "constraint_2": {"satisfied": False, "score": 0.2}  # Hard violation
        }
    }
    
    all_ranked_candidates = [
        {"id": "candidate_1", "scores": candidate.scores}
    ]
    
    constraint_weights = {"constraint_2": 100}
    
    result = ranker_service._generate_ranking_explanation(
        candidate=candidate,
        rank_index=0,
        all_ranked_candidates=all_ranked_candidates,
        constraint_weights=constraint_weights,
        problem_spec=sample_problem_spec
    )
    
    # Should still generate explanation, emphasizing violations
    assert "ranking_explanation" in result
    assert len(result["ranking_factors"]["top_negative_factors"]) > 0


def test_generate_ranking_explanation_with_ranking_factors(ranker_service, sample_problem_spec):
    """Test that ranking factors are properly limited and prioritized."""
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.scores = {
        "I": 2.0,
        "P": {"overall": 0.95},  # Very high P
        "R": {"overall": 0.3},   # Very low R
        "constraint_satisfaction": {
            "constraint_1": {"satisfied": True, "score": 0.95},
            "constraint_2": {"satisfied": True, "score": 0.9}
        }
    }
    
    all_ranked_candidates = [
        {"id": "candidate_1", "scores": candidate.scores},
        {"id": "candidate_2", "scores": {"I": 1.0, "P": {"overall": 0.5}, "R": {"overall": 0.5}}}
    ]
    
    constraint_weights = {"constraint_1": 80, "constraint_2": 100}
    
    result = ranker_service._generate_ranking_explanation(
        candidate=candidate,
        rank_index=0,
        all_ranked_candidates=all_ranked_candidates,
        constraint_weights=constraint_weights,
        problem_spec=sample_problem_spec
    )
    
    # Factors should be limited to 2-4 items
    assert len(result["ranking_factors"]["top_positive_factors"]) <= 4
    assert len(result["ranking_factors"]["top_negative_factors"]) <= 4
    
    # Should have positive factors
    assert len(result["ranking_factors"]["top_positive_factors"]) > 0

