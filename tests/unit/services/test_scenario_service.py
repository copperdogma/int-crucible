"""
Unit tests for ScenarioService.
"""

import pytest
from unittest.mock import Mock, patch

from crucible.services.scenario_service import ScenarioService


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    return session


@pytest.fixture
def scenario_service(mock_session):
    """Create ScenarioService with mocked session."""
    service = ScenarioService(mock_session)
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
        "resources": [],
        "constraints": [{"id": "constraint_1", "name": "Constraint 1"}],
        "assumptions": [{"id": "assumption_1", "description": "Assumption 1"}]
    }
    return model


def test_scenario_service_initialization(mock_session):
    """Test ScenarioService initialization."""
    service = ScenarioService(mock_session)
    assert service.session == mock_session
    assert service.agent is not None


@patch('crucible.services.scenario_service.get_problem_spec')
@patch('crucible.services.scenario_service.get_world_model')
@patch('crucible.services.scenario_service.list_candidates')
@patch('crucible.services.scenario_service.get_scenario_suite')
@patch('crucible.services.scenario_service.create_scenario_suite')
def test_generate_scenario_suite_success(
    mock_create_scenario_suite,
    mock_get_scenario_suite,
    mock_list_candidates,
    mock_get_world_model,
    mock_get_problem_spec,
    scenario_service,
    sample_problem_spec,
    sample_world_model
):
    """Test successful scenario suite generation."""
    # Setup mocks
    mock_get_problem_spec.return_value = sample_problem_spec
    mock_get_world_model.return_value = sample_world_model
    mock_list_candidates.return_value = []
    mock_get_scenario_suite.return_value = None  # No existing suite

    # Mock agent response
    scenario_service.agent.execute.return_value = {
        "scenarios": [
            {
                "id": "scenario_1",
                "name": "Test Scenario",
                "description": "Test description",
                "type": "stress_test",
                "focus": {"constraints": ["constraint_1"]},
                "initial_state": {},
                "events": [],
                "expected_outcomes": {},
                "weight": 0.8
            }
        ],
        "reasoning": "Test reasoning"
    }

    # Mock scenario suite creation
    mock_suite = Mock()
    mock_suite.id = "suite_1"
    mock_suite.run_id = "run_1"
    mock_suite.scenarios = []
    mock_suite.created_at = None
    mock_create_scenario_suite.return_value = mock_suite

    # Execute
    result = scenario_service.generate_scenario_suite(
        run_id="run_1",
        project_id="project_1",
        num_scenarios=1
    )

    # Verify
    assert "scenario_suite" in result
    assert "scenarios" in result
    assert "reasoning" in result
    assert "count" in result
    assert result["count"] == 1
    mock_create_scenario_suite.assert_called_once()


@patch('crucible.services.scenario_service.get_problem_spec')
@patch('crucible.services.scenario_service.get_world_model')
@patch('crucible.services.scenario_service.list_candidates')
@patch('crucible.services.scenario_service.get_scenario_suite')
def test_generate_scenario_suite_update_existing(
    mock_get_scenario_suite,
    mock_list_candidates,
    mock_get_world_model,
    mock_get_problem_spec,
    scenario_service,
    sample_problem_spec,
    sample_world_model
):
    """Test updating existing scenario suite."""
    mock_get_problem_spec.return_value = sample_problem_spec
    mock_get_world_model.return_value = sample_world_model
    mock_list_candidates.return_value = []

    # Mock existing suite
    existing_suite = Mock()
    existing_suite.id = "suite_1"
    existing_suite.run_id = "run_1"
    existing_suite.scenarios = []
    existing_suite.created_at = None
    mock_get_scenario_suite.return_value = existing_suite

    scenario_service.agent.execute.return_value = {
        "scenarios": [{"id": "scenario_1", "name": "New Scenario", "description": "Test", "type": "stress_test", "focus": {}, "initial_state": {}, "events": [], "expected_outcomes": {}, "weight": 0.8}],
        "reasoning": "Updated scenarios"
    }

    result = scenario_service.generate_scenario_suite(
        run_id="run_1",
        project_id="project_1"
    )

    # Verify existing suite was updated
    assert existing_suite.scenarios == [{"id": "scenario_1", "name": "New Scenario", "description": "Test", "type": "stress_test", "focus": {}, "initial_state": {}, "events": [], "expected_outcomes": {}, "weight": 0.8}]


@patch('crucible.services.scenario_service.get_problem_spec')
@patch('crucible.services.scenario_service.get_world_model')
@patch('crucible.services.scenario_service.list_candidates')
def test_generate_scenario_suite_with_candidates(
    mock_list_candidates,
    mock_get_world_model,
    mock_get_problem_spec,
    scenario_service,
    sample_problem_spec,
    sample_world_model
):
    """Test scenario generation with candidates for targeting."""
    mock_get_problem_spec.return_value = sample_problem_spec
    mock_get_world_model.return_value = sample_world_model

    # Mock candidates
    candidate = Mock()
    candidate.id = "candidate_1"
    candidate.mechanism_description = "Test mechanism"
    candidate.predicted_effects = {}
    mock_list_candidates.return_value = [candidate]

    scenario_service.agent.execute.return_value = {
        "scenarios": [],
        "reasoning": "Targeting candidates"
    }

    result = scenario_service.generate_scenario_suite(
        run_id="run_1",
        project_id="project_1"
    )

    # Verify agent was called with candidates
    call_args = scenario_service.agent.execute.call_args[0][0]
    assert len(call_args["candidates"]) == 1
    assert call_args["candidates"][0]["id"] == "candidate_1"

