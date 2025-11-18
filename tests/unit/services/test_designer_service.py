"""
Unit tests for DesignerService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from crucible.services.designer_service import DesignerService
from crucible.db.models import CandidateOrigin, CandidateStatus


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    return session


@pytest.fixture
def designer_service(mock_session):
    """Create DesignerService with mocked session."""
    service = DesignerService(mock_session)
    service.agent = Mock()
    return service


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


def test_designer_service_initialization(mock_session):
    """Test DesignerService initialization."""
    service = DesignerService(mock_session)
    assert service.session == mock_session
    assert service.agent is not None


@patch('crucible.services.designer_service.get_problem_spec')
@patch('crucible.services.designer_service.get_world_model')
@patch('crucible.services.designer_service.list_candidates')
@patch('crucible.services.designer_service.create_candidate')
def test_generate_candidates_success(
    mock_create_candidate,
    mock_list_candidates,
    mock_get_world_model,
    mock_get_problem_spec,
    designer_service,
    mock_session,
    sample_problem_spec,
    sample_world_model
):
    """Test successful candidate generation."""
    # Setup mocks
    mock_get_problem_spec.return_value = sample_problem_spec
    mock_get_world_model.return_value = sample_world_model
    mock_list_candidates.return_value = []

    # Mock agent response
    designer_service.agent.execute.return_value = {
        "candidates": [
            {
                "mechanism_description": "Test mechanism 1",
                "predicted_effects": {
                    "actors_affected": [{"actor_id": "actor_1", "impact": "positive", "description": "Test"}]
                },
                "constraint_compliance": {"constraint_1": 0.8},
                "reasoning": "Test reasoning"
            }
        ],
        "reasoning": "Overall strategy"
    }

    # Mock candidate creation
    mock_candidate = Mock()
    mock_candidate.id = "candidate_1"
    mock_candidate.mechanism_description = "Test mechanism 1"
    mock_candidate.predicted_effects = {}
    mock_candidate.scores = {}
    mock_candidate.status = Mock()
    mock_candidate.status.value = "new"
    mock_create_candidate.return_value = mock_candidate

    # Execute
    result = designer_service.generate_candidates(
        run_id="run_1",
        project_id="project_1",
        num_candidates=1
    )

    # Verify
    assert "candidates" in result
    assert "reasoning" in result
    assert "count" in result
    assert result["count"] == 1
    assert len(result["candidates"]) == 1
    mock_create_candidate.assert_called_once()


@patch('crucible.services.designer_service.get_problem_spec')
@patch('crucible.services.designer_service.get_world_model')
@patch('crucible.services.designer_service.list_candidates')
def test_generate_candidates_with_existing(
    mock_list_candidates,
    mock_get_world_model,
    mock_get_problem_spec,
    designer_service,
    sample_problem_spec,
    sample_world_model
):
    """Test candidate generation with existing candidates."""
    mock_get_problem_spec.return_value = sample_problem_spec
    mock_get_world_model.return_value = sample_world_model

    # Mock existing candidates
    existing_candidate = Mock()
    existing_candidate.id = "existing_1"
    mock_list_candidates.return_value = [existing_candidate]

    designer_service.agent.execute.return_value = {
        "candidates": [],
        "reasoning": "Avoiding duplicates"
    }

    result = designer_service.generate_candidates(
        run_id="run_1",
        project_id="project_1",
        num_candidates=1
    )

    # Verify agent was called with existing candidate IDs
    call_args = designer_service.agent.execute.call_args[0][0]
    assert "existing_1" in call_args["existing_candidates"]


@patch('crucible.services.designer_service.get_problem_spec')
@patch('crucible.services.designer_service.get_world_model')
def test_generate_candidates_no_problem_spec(
    mock_get_world_model,
    mock_get_problem_spec,
    designer_service,
    sample_world_model
):
    """Test candidate generation without ProblemSpec."""
    mock_get_problem_spec.return_value = None
    mock_get_world_model.return_value = sample_world_model

    designer_service.agent.execute.return_value = {
        "candidates": [],
        "reasoning": "No ProblemSpec"
    }

    result = designer_service.generate_candidates(
        run_id="run_1",
        project_id="project_1"
    )

    # Should still work, just with None ProblemSpec
    assert result["candidates"] == []

