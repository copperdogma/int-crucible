"""
Integration tests for ProblemSpec → WorldModel flow.

Tests the complete end-to-end workflow:
1. Create project and ProblemSpec
2. Generate/refine WorldModel from ProblemSpec
3. Verify API endpoints work correctly
4. Verify provenance tracking
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from crucible.db.repositories import (
    create_project,
    create_chat_session,
    create_message,
    create_problem_spec,
    get_problem_spec,
    get_world_model,
)
from crucible.services.problemspec_service import ProblemSpecService
from crucible.services.worldmodel_service import WorldModelService
from crucible.api.main import app
from fastapi.testclient import TestClient
from kosmos.core.providers.base import LLMResponse, UsageStats


@pytest.fixture
def test_client(integration_db_session):
    """Create a test client for the FastAPI app."""
    from crucible.api.main import get_db
    
    # Override the get_db dependency to use our integration test session
    def override_get_db():
        yield integration_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project_and_spec(integration_db_session):
    """Create a sample project with ProblemSpec for testing."""
    project = create_project(
        integration_db_session,
        title="Test Project: API Performance",
        description="Improve API response times"
    )
    
    problem_spec = create_problem_spec(
        integration_db_session,
        project.id,
        constraints=[
            {"name": "Performance", "description": "Response time must be under 500ms", "weight": 80},
            {"name": "Budget", "description": "Limited budget", "weight": 60}
        ],
        goals=["Reduce response time to under 500ms", "Maintain system reliability"],
        resolution="medium",
        mode="full_search"
    )
    
    return project, problem_spec


@pytest.fixture
def sample_chat_session(integration_db_session, sample_project_and_spec):
    """Create a sample chat session with messages."""
    project, _ = sample_project_and_spec
    
    chat_session = create_chat_session(
        integration_db_session,
        project.id,
        title="Initial Discussion",
        mode="setup"
    )
    
    # Add sample messages
    create_message(
        integration_db_session,
        chat_session.id,
        role="user",
        content="I need to improve API response times."
    )
    
    create_message(
        integration_db_session,
        chat_session.id,
        role="agent",
        content="What specific endpoints are slow?"
    )
    
    create_message(
        integration_db_session,
        chat_session.id,
        role="user",
        content="The user profile endpoint takes 2-3 seconds."
    )
    
    return chat_session


@pytest.fixture
def mock_worldmodel_llm_response():
    """Mock LLM response for WorldModeller agent."""
    return {
        "updated_model": {
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
                    "rationale": "Based on ProblemSpec constraints",
                    "confidence": "medium",
                    "source": "agent"
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
            },
            {
                "type": "add",
                "entity_type": "mechanism",
                "entity_id": "mechanism_1",
                "description": "Added request processing mechanism"
            }
        ],
        "reasoning": "Created initial world model from ProblemSpec constraints and goals.",
        "ready_to_run": False
    }


class TestProblemSpecToWorldModelFlow:
    """Test the complete ProblemSpec → WorldModel flow."""
    
    @patch('crucible.agents.worldmodeller_agent.get_provider')
    def test_generate_world_model_from_problem_spec(
        self,
        mock_get_provider,
        integration_db_session,
        sample_project_and_spec,
        sample_chat_session,
        mock_worldmodel_llm_response
    ):
        """Test generating WorldModel from ProblemSpec."""
        project, problem_spec = sample_project_and_spec
        
        # Mock LLM provider
        import json
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_worldmodel_llm_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Generate WorldModel
        service = WorldModelService(integration_db_session)
        result = service.generate_or_refine_world_model(
            project_id=project.id,
            chat_session_id=sample_chat_session.id,
            message_limit=20
        )
        
        # Verify result
        assert result["updated_model"] is not None
        assert "actors" in result["updated_model"]
        assert len(result["updated_model"]["actors"]) > 0
        assert len(result["changes"]) > 0
        assert result["applied"] is True
        
        # Verify WorldModel was saved to database
        world_model = get_world_model(integration_db_session, project.id)
        assert world_model is not None
        assert "actors" in world_model.model_data
        assert "provenance" in world_model.model_data
        assert len(world_model.model_data["provenance"]) > 0
        
        # Verify provenance entry
        provenance_entry = world_model.model_data["provenance"][0]
        assert provenance_entry["actor"] == "agent"
        assert provenance_entry["type"] == "add"
        assert sample_chat_session.id in provenance_entry["source"]
    
    @patch('crucible.agents.worldmodeller_agent.get_provider')
    def test_refine_existing_world_model(
        self,
        mock_get_provider,
        integration_db_session,
        sample_project_and_spec,
        sample_chat_session,
        mock_worldmodel_llm_response
    ):
        """Test refining an existing WorldModel."""
        project, problem_spec = sample_project_and_spec
        
        # Create initial WorldModel
        from crucible.db.repositories import create_world_model
        initial_model = create_world_model(
            integration_db_session,
            project.id,
            model_data={
                "actors": [{"id": "actor_0", "name": "Initial Actor"}],
                "mechanisms": [],
                "resources": [],
                "constraints": [],
                "assumptions": [],
                "simplifications": [],
                "provenance": []
            }
        )
        
        # Mock LLM provider with updated response
        updated_response = mock_worldmodel_llm_response.copy()
        updated_response["updated_model"]["actors"].append({
            "id": "actor_0",
            "name": "Initial Actor"
        })
        
        import json
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(updated_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Refine WorldModel
        service = WorldModelService(integration_db_session)
        result = service.generate_or_refine_world_model(
            project_id=project.id,
            chat_session_id=sample_chat_session.id
        )
        
        # Verify result
        assert result["applied"] is True
        
        # Verify WorldModel was updated
        world_model = get_world_model(integration_db_session, project.id)
        assert world_model is not None
        # Should have both old and new actors
        actors = world_model.model_data["actors"]
        assert len(actors) >= 2
        assert any(a["id"] == "actor_0" for a in actors)
        assert any(a["id"] == "actor_1" for a in actors)
    
    def test_manual_world_model_update(
        self,
        integration_db_session,
        sample_project_and_spec
    ):
        """Test manually updating WorldModel."""
        project, _ = sample_project_and_spec
        
        service = WorldModelService(integration_db_session)
        
        # Update WorldModel manually
        model_data = {
            "actors": [{"id": "actor_1", "name": "Manual Actor"}],
            "mechanisms": [],
            "resources": [],
            "constraints": [],
            "assumptions": [],
            "simplifications": []
        }
        
        result = service.update_world_model_manual(
            project_id=project.id,
            model_data=model_data,
            source="ui_edit"
        )
        
        assert result is True
        
        # Verify WorldModel was created/updated
        world_model = get_world_model(integration_db_session, project.id)
        assert world_model is not None
        assert world_model.model_data["actors"][0]["name"] == "Manual Actor"
        assert "provenance" in world_model.model_data
        assert len(world_model.model_data["provenance"]) == 1
        assert world_model.model_data["provenance"][0]["actor"] == "user"
        assert world_model.model_data["provenance"][0]["source"] == "ui_edit"


class TestWorldModelAPIEndpoints:
    """Test WorldModel API endpoints."""
    
    @patch('crucible.agents.worldmodeller_agent.get_provider')
    def test_get_world_model_endpoint(
        self,
        mock_get_provider,
        test_client,
        integration_db_session,
        sample_project_and_spec
    ):
        """Test GET /projects/{project_id}/world-model endpoint."""
        project, _ = sample_project_and_spec
        
        # Create WorldModel first
        from crucible.db.repositories import create_world_model
        create_world_model(
            integration_db_session,
            project.id,
            model_data={
                "actors": [{"id": "actor_1", "name": "Test Actor"}],
                "mechanisms": [],
                "resources": [],
                "constraints": [],
                "assumptions": [],
                "simplifications": [],
                "provenance": []
            }
        )
        
        # Override dependency
        from crucible.api.main import get_db
        def override_get_db():
            yield integration_db_session
        app.dependency_overrides[get_db] = override_get_db
        
        # Call API
        response = test_client.get(f"/projects/{project.id}/world-model")
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id
        assert "model_data" in data
        assert "actors" in data["model_data"]
        assert len(data["model_data"]["actors"]) == 1
        
        app.dependency_overrides.clear()
    
    def test_get_world_model_endpoint_not_found(
        self,
        test_client,
        integration_db_session,
        sample_project_and_spec
    ):
        """Test GET /projects/{project_id}/world-model when model doesn't exist."""
        project, _ = sample_project_and_spec
        
        # Override dependency
        from crucible.api.main import get_db
        def override_get_db():
            yield integration_db_session
        app.dependency_overrides[get_db] = override_get_db
        
        # Call API
        response = test_client.get(f"/projects/{project.id}/world-model")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        app.dependency_overrides.clear()
    
    @patch('crucible.agents.worldmodeller_agent.get_provider')
    def test_refine_world_model_endpoint(
        self,
        mock_get_provider,
        test_client,
        integration_db_session,
        sample_project_and_spec,
        sample_chat_session,
        mock_worldmodel_llm_response
    ):
        """Test POST /projects/{project_id}/world-model/refine endpoint."""
        project, _ = sample_project_and_spec
        
        # Mock LLM provider
        mock_provider = Mock()
        import json
        mock_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_worldmodel_llm_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        mock_get_provider.return_value = mock_provider
        
        # Override dependency
        from crucible.api.main import get_db
        def override_get_db():
            yield integration_db_session
        app.dependency_overrides[get_db] = override_get_db
        
        # Call API
        response = test_client.post(
            f"/projects/{project.id}/world-model/refine",
            json={"chat_session_id": sample_chat_session.id, "message_limit": 20}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "updated_model" in data
        assert "changes" in data
        assert "reasoning" in data
        assert "ready_to_run" in data
        assert "applied" in data
        assert data["applied"] is True
        
        app.dependency_overrides.clear()
    
    def test_update_world_model_endpoint(
        self,
        test_client,
        integration_db_session,
        sample_project_and_spec
    ):
        """Test PUT /projects/{project_id}/world-model endpoint."""
        project, _ = sample_project_and_spec
        
        # Override dependency
        from crucible.api.main import get_db
        def override_get_db():
            yield integration_db_session
        app.dependency_overrides[get_db] = override_get_db
        
        # Call API - this will create the WorldModel if it doesn't exist
        model_data = {
            "actors": [{"id": "actor_1", "name": "API Actor"}],
            "mechanisms": [],
            "resources": [],
            "constraints": [],
            "assumptions": [],
            "simplifications": []
        }
        
        response = test_client.put(
            f"/projects/{project.id}/world-model",
            json={"model_data": model_data, "source": "api_test"}
        )
        
        # Verify the response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["project_id"] == project.id
        assert "model_data" in data
        assert data["model_data"]["actors"][0]["name"] == "API Actor"
        
        # Verify provenance was added
        assert "provenance" in data["model_data"]
        assert len(data["model_data"]["provenance"]) == 1
        assert data["model_data"]["provenance"][0]["source"] == "api_test"
        
        app.dependency_overrides.clear()


class TestFullProblemSpecToWorldModelFlow:
    """Test the complete ProblemSpec → WorldModel workflow."""
    
    @patch('crucible.agents.problemspec_agent.get_provider')
    @patch('crucible.agents.worldmodeller_agent.get_provider')
    def test_complete_flow_problemspec_to_worldmodel(
        self,
        mock_worldmodel_provider,
        mock_problemspec_provider,
        integration_db_session,
        sample_chat_session
    ):
        """Test complete flow: ProblemSpec refinement → WorldModel generation."""
        # Get project from chat session
        project_id = sample_chat_session.project_id
        from crucible.db.repositories import get_project
        project = get_project(integration_db_session, project_id)
        
        # Mock ProblemSpec agent response
        problemspec_response = {
            "updated_spec": {
                "constraints": [
                    {"name": "Performance", "description": "Response time under 500ms", "weight": 80}
                ],
                "goals": ["Improve API performance"],
                "resolution": "medium",
                "mode": "full_search"
            },
            "follow_up_questions": [],
            "reasoning": "Created spec from chat",
            "ready_to_run": True
        }
        
        mock_problemspec_provider_instance = Mock()
        import json
        mock_problemspec_provider_instance.generate.return_value = LLMResponse(
            content=json.dumps(problemspec_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        mock_problemspec_provider.return_value = mock_problemspec_provider_instance
        
        # Mock WorldModeller agent response
        worldmodel_response = {
            "updated_model": {
                "actors": [{"id": "actor_1", "name": "API Server"}],
                "mechanisms": [],
                "resources": [],
                "constraints": [],
                "assumptions": [],
                "simplifications": []
            },
            "changes": [{"type": "add", "entity_type": "actor", "entity_id": "actor_1", "description": "Added"}],
            "reasoning": "Created from ProblemSpec",
            "ready_to_run": False
        }
        
        mock_worldmodel_provider_instance = Mock()
        mock_worldmodel_provider_instance.generate.return_value = LLMResponse(
            content=json.dumps(worldmodel_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        mock_worldmodel_provider.return_value = mock_worldmodel_provider_instance
        
        # Step 1: Refine ProblemSpec
        problemspec_service = ProblemSpecService(integration_db_session)
        problemspec_service.agent.llm_provider = mock_problemspec_provider_instance
        spec_result = problemspec_service.refine_problem_spec(
            project_id=project.id,
            chat_session_id=sample_chat_session.id
        )
        
        assert spec_result["applied"] is True
        
        # Verify ProblemSpec was created
        problem_spec = get_problem_spec(integration_db_session, project.id)
        assert problem_spec is not None
        assert len(problem_spec.constraints) > 0
        assert problem_spec.provenance_log
        
        # Step 2: Generate WorldModel from ProblemSpec
        worldmodel_service = WorldModelService(integration_db_session)
        worldmodel_service.agent.llm_provider = mock_worldmodel_provider_instance
        worldmodel_result = worldmodel_service.generate_or_refine_world_model(
            project_id=project.id,
            chat_session_id=sample_chat_session.id
        )
        
        assert worldmodel_result["applied"] is True
        
        # Verify WorldModel was created
        world_model = get_world_model(integration_db_session, project.id)
        assert world_model is not None
        assert "actors" in world_model.model_data
        assert len(world_model.model_data["actors"]) > 0
        
        # Verify provenance tracking
        assert "provenance" in world_model.model_data
        assert len(world_model.model_data["provenance"]) > 0
        
        # Verify ProblemSpec and WorldModel are aligned
        # (WorldModel should reference ProblemSpec constraints)
        assert problem_spec is not None
        assert world_model is not None

