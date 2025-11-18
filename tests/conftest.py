"""
Pytest configuration and fixtures for Int Crucible tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from crucible.db.models import Base as CrucibleBase
from crucible.db.session import get_session
from crucible.agents.problemspec_agent import ProblemSpecAgent
from crucible.agents.worldmodeller_agent import WorldModellerAgent
from crucible.services.problemspec_service import ProblemSpecService
from kosmos.core.providers.base import LLMResponse, UsageStats


@pytest.fixture
def test_db_session():
    """
    Create an in-memory SQLite database session for testing.
    
    Note: Uses check_same_thread=False to allow cross-thread access
    for FastAPI TestClient integration tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    CrucibleBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def mock_llm_provider():
    """
    Mock LLM provider for testing without actual API calls.
    """
    provider = Mock()
    
    # Default successful response
    provider.generate = Mock(return_value=LLMResponse(
        content='{"updated_spec": {"constraints": [], "goals": [], "resolution": "medium", "mode": "full_search"}, "follow_up_questions": [], "reasoning": "Test reasoning", "ready_to_run": false}',
        usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
        model="test-model",
        finish_reason="stop"
    ))
    
    provider.model = "test-model"
    provider.provider_name = "test"
    
    return provider


@pytest.fixture
def mock_problemspec_agent(mock_llm_provider):
    """
    Create a ProblemSpecAgent with mocked LLM provider.
    """
    agent = ProblemSpecAgent()
    agent.llm_provider = mock_llm_provider
    return agent


@pytest.fixture
def sample_chat_messages():
    """
    Sample chat messages for testing.
    """
    return [
        {"role": "user", "content": "I need to improve API response times."},
        {"role": "agent", "content": "What specific endpoints are slow?"},
        {"role": "user", "content": "The user profile endpoint takes 2-3 seconds."},
    ]


@pytest.fixture
def sample_current_spec():
    """
    Sample current ProblemSpec for testing.
    """
    return {
        "constraints": [
            {"name": "Budget", "description": "Limited budget", "weight": 60}
        ],
        "goals": ["Reduce response time to under 500ms"],
        "resolution": "medium",
        "mode": "full_search"
    }


@pytest.fixture
def sample_llm_response_json():
    """
    Sample LLM response JSON for testing.
    """
    return {
        "updated_spec": {
            "constraints": [
                {"name": "Performance", "description": "Response time must be under 500ms", "weight": 80},
                {"name": "Budget", "description": "Limited budget", "weight": 60}
            ],
            "goals": [
                "Reduce response time to under 500ms",
                "Maintain system reliability"
            ],
            "resolution": "medium",
            "mode": "full_search"
        },
        "follow_up_questions": [
            "What is the current infrastructure setup?",
            "Are there any hard constraints we must not violate?"
        ],
        "reasoning": "Added performance constraint based on user's response time requirements.",
        "ready_to_run": False
    }


@pytest.fixture
def mock_worldmodeller_agent(mock_llm_provider):
    """
    Create a WorldModellerAgent with mocked LLM provider.
    """
    agent = WorldModellerAgent()
    agent.llm_provider = mock_llm_provider
    return agent


@pytest.fixture
def sample_problem_spec():
    """
    Sample ProblemSpec for testing.
    """
    return {
        "constraints": [
            {"name": "Performance", "description": "Response time must be under 500ms", "weight": 80}
        ],
        "goals": ["Reduce response time to under 500ms"],
        "resolution": "medium",
        "mode": "full_search"
    }


@pytest.fixture
def sample_world_model():
    """
    Sample WorldModel for testing.
    """
    return {
        "actors": [
            {
                "id": "actor_1",
                "name": "API Server",
                "description": "Handles API requests",
                "type": "system",
                "capabilities": ["process_requests", "return_responses"],
                "constraints": []
            }
        ],
        "mechanisms": [],
        "resources": [],
        "constraints": [],
        "assumptions": [],
        "simplifications": [],
        "provenance": []
    }


@pytest.fixture
def sample_worldmodel_llm_response():
    """
    Sample LLM response JSON for WorldModeller testing.
    """
    return {
        "updated_model": {
            "actors": [
                {
                    "id": "actor_1",
                    "name": "API Server",
                    "description": "Handles API requests",
                    "type": "system",
                    "capabilities": ["process_requests"],
                    "constraints": []
                }
            ],
            "mechanisms": [
                {
                    "id": "mechanism_1",
                    "name": "Request Processing",
                    "description": "Processes incoming API requests",
                    "type": "process",
                    "inputs": ["request"],
                    "outputs": ["response"],
                    "actors_involved": ["actor_1"],
                    "resources_required": []
                }
            ],
            "resources": [],
            "constraints": [
                {
                    "id": "constraint_1",
                    "name": "Response Time",
                    "description": "Must respond within 500ms",
                    "type": "hard",
                    "weight": 80,
                    "applies_to": ["actor_1", "mechanism_1"]
                }
            ],
            "assumptions": [
                {
                    "id": "assumption_1",
                    "description": "Current infrastructure can be optimized",
                    "rationale": "Based on user's description",
                    "confidence": "medium",
                    "source": "user"
                }
            ],
            "simplifications": []
        },
        "changes": [
            {
                "type": "add",
                "entity_type": "actor",
                "entity_id": "actor_1",
                "description": "Added API Server actor based on ProblemSpec"
            }
        ],
        "reasoning": "Created initial world model from ProblemSpec constraints and goals.",
        "ready_to_run": False
    }

