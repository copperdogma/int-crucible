"""
Unit tests for EvaluatorAgent.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock

from crucible.agents.evaluator_agent import EvaluatorAgent


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    provider = Mock()
    return provider


@pytest.fixture
def evaluator_agent(mock_llm_provider):
    """Create EvaluatorAgent with mocked LLM provider."""
    agent = EvaluatorAgent()
    agent.llm_provider = mock_llm_provider
    return agent


def test_evaluator_agent_initialization():
    """Test EvaluatorAgent initialization."""
    agent = EvaluatorAgent()
    assert agent.agent_type == "EvaluatorAgent"
    assert agent.llm_provider is not None


def test_evaluator_agent_execute_success(evaluator_agent, mock_llm_provider):
    """Test successful evaluation."""
    # Mock LLM response
    mock_response = Mock()
    mock_response.content = json.dumps({
        "P": {
            "overall": 0.8,
            "components": {
                "prediction_accuracy": 0.85,
                "scenario_coverage": 0.75
            }
        },
        "R": {
            "overall": 0.6,
            "components": {
                "cost": 0.7,
                "complexity": 0.5,
                "resource_usage": 0.6
            }
        },
        "constraint_satisfaction": {
            "constraint_1": {
                "satisfied": True,
                "score": 0.9,
                "explanation": "Constraint satisfied"
            }
        },
        "explanation": "Candidate performs well in this scenario"
    })
    mock_llm_provider.generate.return_value = mock_response

    # Test task
    task = {
        "candidate": {
            "id": "candidate_1",
            "mechanism_description": "Test mechanism",
            "predicted_effects": {}
        },
        "scenario": {
            "id": "scenario_1",
            "name": "Test scenario",
            "description": "Test description",
            "type": "stress_test"
        }
    }

    result = evaluator_agent.execute(task)

    assert "P" in result
    assert "R" in result
    assert "constraint_satisfaction" in result
    assert "explanation" in result
    assert result["P"]["overall"] == 0.8
    assert result["R"]["overall"] == 0.6


def test_evaluator_agent_execute_missing_candidate(evaluator_agent):
    """Test evaluation with missing candidate."""
    task = {
        "scenario": {
            "id": "scenario_1",
            "name": "Test scenario"
        }
    }

    with pytest.raises(ValueError, match="Both candidate and scenario are required"):
        evaluator_agent.execute(task)


def test_evaluator_agent_execute_missing_scenario(evaluator_agent):
    """Test evaluation with missing scenario."""
    task = {
        "candidate": {
            "id": "candidate_1",
            "mechanism_description": "Test mechanism"
        }
    }

    with pytest.raises(ValueError, match="Both candidate and scenario are required"):
        evaluator_agent.execute(task)


def test_evaluator_agent_execute_json_parsing_error(evaluator_agent, mock_llm_provider):
    """Test evaluation with JSON parsing error."""
    # Mock LLM response with invalid JSON
    mock_response = Mock()
    mock_response.content = "Invalid JSON response"
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "candidate": {
            "id": "candidate_1",
            "mechanism_description": "Test mechanism"
        },
        "scenario": {
            "id": "scenario_1",
            "name": "Test scenario"
        }
    }

    result = evaluator_agent.execute(task)

    # Should return safe defaults
    assert "P" in result
    assert "R" in result
    assert result["P"]["overall"] == 0.5
    assert result["R"]["overall"] == 0.5


def test_evaluator_agent_execute_markdown_code_block(evaluator_agent, mock_llm_provider):
    """Test evaluation with JSON in markdown code block."""
    # Mock LLM response with JSON in markdown
    mock_response = Mock()
    mock_response.content = "```json\n" + json.dumps({
        "P": {"overall": 0.7},
        "R": {"overall": 0.5},
        "constraint_satisfaction": {},
        "explanation": "Test"
    }) + "\n```"
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "candidate": {
            "id": "candidate_1",
            "mechanism_description": "Test mechanism"
        },
        "scenario": {
            "id": "scenario_1",
            "name": "Test scenario"
        }
    }

    result = evaluator_agent.execute(task)

    assert result["P"]["overall"] == 0.7
    assert result["R"]["overall"] == 0.5


def test_evaluator_agent_execute_missing_fields(evaluator_agent, mock_llm_provider):
    """Test evaluation with missing required fields in response."""
    # Mock LLM response missing some fields
    mock_response = Mock()
    mock_response.content = json.dumps({
        "P": {"overall": 0.8}
        # Missing R, constraint_satisfaction, explanation
    })
    mock_llm_provider.generate.return_value = mock_response

    task = {
        "candidate": {
            "id": "candidate_1",
            "mechanism_description": "Test mechanism"
        },
        "scenario": {
            "id": "scenario_1",
            "name": "Test scenario"
        }
    }

    result = evaluator_agent.execute(task)

    # Should have defaults for missing fields
    assert "P" in result
    assert "R" in result
    assert "constraint_satisfaction" in result
    assert "explanation" in result
    assert result["R"]["overall"] == 0.5  # Default

