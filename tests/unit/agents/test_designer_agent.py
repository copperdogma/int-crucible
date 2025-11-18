"""
Unit tests for DesignerAgent.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock

from crucible.agents.designer_agent import DesignerAgent


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    provider = Mock()
    return provider


@pytest.fixture
def designer_agent(mock_llm_provider):
    """Create DesignerAgent with mocked LLM provider."""
    agent = DesignerAgent()
    agent.llm_provider = mock_llm_provider
    return agent


def test_designer_agent_initialization():
    """Test DesignerAgent initialization."""
    agent = DesignerAgent()
    assert agent.agent_type == "DesignerAgent"
    assert agent.llm_provider is not None


def test_designer_agent_execute_success(designer_agent, mock_llm_provider):
    """Test successful candidate generation."""
    # Mock LLM response
    mock_response = Mock()
    mock_response.content = json.dumps({
        "candidates": [
            {
                "mechanism_description": "Test mechanism 1",
                "predicted_effects": {
                    "actors_affected": [{"actor_id": "actor_1", "impact": "positive", "description": "Test"}],
                    "resources_impacted": [],
                    "mechanisms_modified": []
                },
                "constraint_compliance": {"constraint_1": 0.8},
                "reasoning": "Test reasoning 1"
            },
            {
                "mechanism_description": "Test mechanism 2",
                "predicted_effects": {
                    "actors_affected": [],
                    "resources_impacted": [{"resource_id": "resource_1", "change": "increase", "magnitude": "medium", "description": "Test"}],
                    "mechanisms_modified": []
                },
                "constraint_compliance": {"constraint_1": 0.6},
                "reasoning": "Test reasoning 2"
            }
        ],
        "reasoning": "Overall strategy"
    })
    mock_llm_provider.generate.return_value = mock_response

    # Execute
    task = {
        "problem_spec": {
            "constraints": [{"name": "constraint_1", "description": "Test constraint", "weight": 80}],
            "goals": ["Goal 1"],
            "resolution": "medium",
            "mode": "full_search"
        },
        "world_model": {
            "actors": [{"id": "actor_1", "name": "Actor 1"}],
            "mechanisms": [],
            "resources": []
        },
        "num_candidates": 2
    }

    result = designer_agent.execute(task)

    # Verify
    assert "candidates" in result
    assert "reasoning" in result
    assert len(result["candidates"]) == 2
    assert result["reasoning"] == "Overall strategy"
    assert result["candidates"][0]["mechanism_description"] == "Test mechanism 1"
    mock_llm_provider.generate.assert_called_once()


def test_designer_agent_execute_with_markdown_code_block(designer_agent, mock_llm_provider):
    """Test parsing JSON from markdown code block."""
    mock_response = Mock()
    mock_response.content = "```json\n" + json.dumps({
        "candidates": [{
            "mechanism_description": "Test",
            "predicted_effects": {},
            "constraint_compliance": {},
            "reasoning": "Test"
        }],
        "reasoning": "Overall"
    }) + "\n```"
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "problem_spec": {},
        "world_model": {},
        "num_candidates": 1
    }

    result = designer_agent.execute(task)
    assert len(result["candidates"]) == 1


def test_designer_agent_execute_json_parse_error(designer_agent, mock_llm_provider):
    """Test handling of JSON parse errors."""
    mock_response = Mock()
    mock_response.content = "Invalid JSON response"
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "problem_spec": {},
        "world_model": {},
        "num_candidates": 1
    }

    result = designer_agent.execute(task)
    assert result["candidates"] == []
    assert "Failed to parse" in result["reasoning"]


def test_designer_agent_execute_empty_inputs(designer_agent, mock_llm_provider):
    """Test with empty inputs."""
    mock_response = Mock()
    mock_response.content = json.dumps({
        "candidates": [],
        "reasoning": "No inputs provided"
    })
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "problem_spec": None,
        "world_model": None,
        "num_candidates": 0
    }

    result = designer_agent.execute(task)
    assert result["candidates"] == []


def test_designer_agent_execute_with_existing_candidates(designer_agent, mock_llm_provider):
    """Test with existing candidates to avoid duplicates."""
    mock_response = Mock()
    mock_response.content = json.dumps({
        "candidates": [{
            "mechanism_description": "New distinct mechanism",
            "predicted_effects": {},
            "constraint_compliance": {},
            "reasoning": "Different approach"
        }],
        "reasoning": "Avoiding duplicates"
    })
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "problem_spec": {},
        "world_model": {},
        "num_candidates": 1,
        "existing_candidates": ["candidate_1", "candidate_2"]
    }

    result = designer_agent.execute(task)
    assert len(result["candidates"]) == 1
    # Verify prompt mentions existing candidates
    call_args = mock_llm_provider.generate.call_args
    assert "existing" in call_args[0][0].lower() or "existing" in str(call_args).lower()

