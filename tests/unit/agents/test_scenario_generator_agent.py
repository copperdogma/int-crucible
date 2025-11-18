"""
Unit tests for ScenarioGeneratorAgent.
"""

import json
import pytest
from unittest.mock import Mock

from crucible.agents.scenario_generator_agent import ScenarioGeneratorAgent


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    provider = Mock()
    return provider


@pytest.fixture
def scenario_agent(mock_llm_provider):
    """Create ScenarioGeneratorAgent with mocked LLM provider."""
    agent = ScenarioGeneratorAgent()
    agent.llm_provider = mock_llm_provider
    return agent


def test_scenario_agent_initialization():
    """Test ScenarioGeneratorAgent initialization."""
    agent = ScenarioGeneratorAgent()
    assert agent.agent_type == "ScenarioGeneratorAgent"
    assert agent.llm_provider is not None


def test_scenario_agent_execute_success(scenario_agent, mock_llm_provider):
    """Test successful scenario generation."""
    # Mock LLM response
    mock_response = Mock()
    mock_response.content = json.dumps({
        "scenarios": [
            {
                "id": "scenario_1",
                "name": "Stress Test 1",
                "description": "Test scenario description",
                "type": "stress_test",
                "focus": {
                    "constraints": ["constraint_1"],
                    "assumptions": ["assumption_1"],
                    "actors": ["actor_1"],
                    "resources": []
                },
                "initial_state": {
                    "actors": {"actor_1": {"state": "initial"}},
                    "resources": {},
                    "mechanisms": {}
                },
                "events": [
                    {"step": 1, "description": "Event 1", "actor": "actor_1", "action": "action 1"}
                ],
                "expected_outcomes": {
                    "success_criteria": ["Criterion 1"],
                    "failure_modes": ["Failure mode 1"]
                },
                "weight": 0.9
            },
            {
                "id": "scenario_2",
                "name": "Edge Case 1",
                "description": "Edge case scenario",
                "type": "edge_case",
                "focus": {
                    "constraints": ["constraint_2"],
                    "assumptions": [],
                    "actors": [],
                    "resources": ["resource_1"]
                },
                "initial_state": {
                    "actors": {},
                    "resources": {"resource_1": {"quantity": 0, "units": "units"}},
                    "mechanisms": {}
                },
                "events": [],
                "expected_outcomes": {
                    "success_criteria": ["Criterion 2"],
                    "failure_modes": []
                },
                "weight": 0.7
            }
        ],
        "reasoning": "Scenario selection strategy"
    })
    mock_llm_provider.generate.return_value = mock_response

    # Execute
    task = {
        "problem_spec": {
            "constraints": [{"name": "constraint_1", "description": "Test", "weight": 80}],
            "goals": ["Goal 1"],
            "resolution": "medium",
            "mode": "full_search"
        },
        "world_model": {
            "actors": [{"id": "actor_1", "name": "Actor 1"}],
            "mechanisms": [],
            "resources": [],
            "constraints": [{"id": "constraint_1", "name": "Constraint 1"}],
            "assumptions": [{"id": "assumption_1", "description": "Assumption 1"}]
        },
        "candidates": [
            {"id": "candidate_1", "mechanism_description": "Test mechanism"}
        ],
        "num_scenarios": 2
    }

    result = scenario_agent.execute(task)

    # Verify
    assert "scenarios" in result
    assert "reasoning" in result
    assert len(result["scenarios"]) == 2
    assert result["reasoning"] == "Scenario selection strategy"
    assert result["scenarios"][0]["id"] == "scenario_1"
    assert result["scenarios"][0]["type"] == "stress_test"
    mock_llm_provider.generate.assert_called_once()


def test_scenario_agent_execute_with_markdown_code_block(scenario_agent, mock_llm_provider):
    """Test parsing JSON from markdown code block."""
    mock_response = Mock()
    mock_response.content = "```json\n" + json.dumps({
        "scenarios": [{
            "id": "scenario_1",
            "name": "Test",
            "description": "Test",
            "type": "stress_test",
            "focus": {},
            "initial_state": {},
            "events": [],
            "expected_outcomes": {},
            "weight": 0.5
        }],
        "reasoning": "Test"
    }) + "\n```"
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "problem_spec": {},
        "world_model": {},
        "candidates": [],
        "num_scenarios": 1
    }

    result = scenario_agent.execute(task)
    assert len(result["scenarios"]) == 1


def test_scenario_agent_execute_json_parse_error(scenario_agent, mock_llm_provider):
    """Test handling of JSON parse errors."""
    mock_response = Mock()
    mock_response.content = "Invalid JSON response"
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "problem_spec": {},
        "world_model": {},
        "candidates": [],
        "num_scenarios": 1
    }

    result = scenario_agent.execute(task)
    assert result["scenarios"] == []
    assert "Failed to parse" in result["reasoning"]


def test_scenario_agent_execute_empty_inputs(scenario_agent, mock_llm_provider):
    """Test with empty inputs."""
    mock_response = Mock()
    mock_response.content = json.dumps({
        "scenarios": [],
        "reasoning": "No inputs provided"
    })
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "problem_spec": None,
        "world_model": None,
        "candidates": [],
        "num_scenarios": 0
    }

    result = scenario_agent.execute(task)
    assert result["scenarios"] == []


def test_scenario_agent_execute_with_candidates(scenario_agent, mock_llm_provider):
    """Test with candidates for scenario targeting."""
    mock_response = Mock()
    mock_response.content = json.dumps({
        "scenarios": [{
            "id": "scenario_1",
            "name": "Targeted Test",
            "description": "Tests candidate weaknesses",
            "type": "stress_test",
            "focus": {"constraints": ["constraint_1"]},
            "initial_state": {},
            "events": [],
            "expected_outcomes": {},
            "weight": 0.8
        }],
        "reasoning": "Targeting candidate weaknesses"
    })
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "problem_spec": {},
        "world_model": {},
        "candidates": [
            {"id": "candidate_1", "mechanism_description": "Mechanism with potential weakness"}
        ],
        "num_scenarios": 1
    }

    result = scenario_agent.execute(task)
    assert len(result["scenarios"]) == 1
    # Verify prompt mentions candidates
    call_args = mock_llm_provider.generate.call_args
    assert "candidate" in call_args[0][0].lower() or "candidate" in str(call_args).lower()

