"""
Unit tests for WorldModelService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from crucible.services.worldmodel_service import WorldModelService
from crucible.db.models import (
    Project, ChatSession, Message, ProblemSpec, WorldModel,
    ResolutionLevel, RunMode, MessageRole
)
from crucible.db.repositories import (
    create_project, create_chat_session, create_message,
    create_problem_spec, get_problem_spec,
    create_world_model, get_world_model
)


class TestWorldModelService:
    """Test suite for WorldModelService."""
    
    def test_service_initialization(self, test_db_session):
        """Test that WorldModelService initializes correctly."""
        service = WorldModelService(test_db_session)
        
        assert service.session == test_db_session
        assert hasattr(service, "agent")
        assert service.agent is not None
    
    def test_get_world_model_existing(self, test_db_session):
        """Test retrieving existing WorldModel."""
        # Create project and model
        project = create_project(test_db_session, "Test Project", "Test description")
        world_model = create_world_model(
            test_db_session,
            project.id,
            model_data={"actors": [{"id": "actor_1", "name": "Test Actor"}]}
        )
        
        service = WorldModelService(test_db_session)
        result = service.get_world_model(project.id)
        
        assert result is not None
        assert result["project_id"] == project.id
        assert "actors" in result["model_data"]
        assert len(result["model_data"]["actors"]) == 1
    
    def test_get_world_model_nonexistent(self, test_db_session):
        """Test retrieving WorldModel for project without one."""
        # Create project without model
        project = create_project(test_db_session, "Test Project", "Test description")
        
        service = WorldModelService(test_db_session)
        result = service.get_world_model(project.id)
        
        assert result is None
    
    @patch('crucible.services.worldmodel_service.WorldModellerAgent')
    def test_generate_or_refine_world_model_new_model(self, mock_agent_class, test_db_session):
        """Test generating WorldModel when none exists (creates new)."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[{"name": "Performance", "description": "Must be fast", "weight": 80}],
            goals=["Improve performance"],
            resolution="medium",
            mode="full_search"
        )
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        create_message(test_db_session, chat_session.id, "user", "I need to improve performance")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_model": {
                "actors": [{"id": "actor_1", "name": "API Server"}],
                "mechanisms": [],
                "resources": [],
                "constraints": [],
                "assumptions": [],
                "simplifications": []
            },
            "changes": [
                {"type": "add", "entity_type": "actor", "entity_id": "actor_1", "description": "Added actor"}
            ],
            "reasoning": "Created initial model",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = WorldModelService(test_db_session)
        service.agent = mock_agent
        
        result = service.generate_or_refine_world_model(project.id, chat_session.id)
        
        assert result["updated_model"] is not None
        assert len(result["changes"]) == 1
        assert result["applied"] is True
        
        # Verify model was created in database
        model = get_world_model(test_db_session, project.id)
        assert model is not None
        assert "actors" in model.model_data
        assert "provenance" in model.model_data
        assert len(model.model_data["provenance"]) == 1
    
    @patch('crucible.services.worldmodel_service.WorldModellerAgent')
    def test_generate_or_refine_world_model_update_existing(self, mock_agent_class, test_db_session):
        """Test refining WorldModel when one exists (updates)."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        create_world_model(
            test_db_session,
            project.id,
            model_data={"actors": [{"id": "actor_1", "name": "Old Actor"}]}
        )
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[{"name": "Performance", "description": "Must be fast", "weight": 80}],
            goals=["Improve performance"],
            resolution="medium",
            mode="full_search"
        )
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        create_message(test_db_session, chat_session.id, "user", "Add new mechanism")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_model": {
                "actors": [{"id": "actor_1", "name": "Old Actor"}],
                "mechanisms": [{"id": "mechanism_1", "name": "New Mechanism"}],
                "resources": [],
                "constraints": [],
                "assumptions": [],
                "simplifications": []
            },
            "changes": [
                {"type": "add", "entity_type": "mechanism", "entity_id": "mechanism_1", "description": "Added mechanism"}
            ],
            "reasoning": "Added new mechanism",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = WorldModelService(test_db_session)
        service.agent = mock_agent
        
        result = service.generate_or_refine_world_model(project.id, chat_session.id)
        
        assert result["applied"] is True
        
        # Verify model was updated in database
        model = get_world_model(test_db_session, project.id)
        assert "mechanisms" in model.model_data
        assert len(model.model_data["mechanisms"]) == 1
        assert len(model.model_data["provenance"]) == 1
    
    @patch('crucible.services.worldmodel_service.WorldModellerAgent')
    def test_generate_or_refine_world_model_with_problem_spec(self, mock_agent_class, test_db_session):
        """Test that ProblemSpec is passed to agent."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[{"name": "Performance", "description": "Must be fast", "weight": 80}],
            goals=["Improve performance"],
            resolution="medium",
            mode="full_search"
        )
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_model": {"actors": [], "mechanisms": [], "resources": [], "constraints": [], "assumptions": [], "simplifications": []},
            "changes": [],
            "reasoning": "",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = WorldModelService(test_db_session)
        service.agent = mock_agent
        
        service.generate_or_refine_world_model(project.id, chat_session.id)
        
        # Verify agent was called with ProblemSpec
        call_args = mock_agent.execute.call_args
        assert call_args is not None
        task = call_args[0][0]
        assert "problem_spec" in task
        assert task["problem_spec"]["constraints"][0]["name"] == "Performance"
    
    @patch('crucible.services.worldmodel_service.WorldModellerAgent')
    def test_generate_or_refine_world_model_with_chat_messages(self, mock_agent_class, test_db_session):
        """Test that chat messages are passed to agent."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        create_message(test_db_session, chat_session.id, "user", "Message 1")
        create_message(test_db_session, chat_session.id, "agent", "Message 2")
        create_message(test_db_session, chat_session.id, "user", "Message 3")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_model": {"actors": [], "mechanisms": [], "resources": [], "constraints": [], "assumptions": [], "simplifications": []},
            "changes": [],
            "reasoning": "",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = WorldModelService(test_db_session)
        service.agent = mock_agent
        
        service.generate_or_refine_world_model(project.id, chat_session.id, message_limit=20)
        
        # Verify agent was called with chat messages
        call_args = mock_agent.execute.call_args
        assert call_args is not None
        task = call_args[0][0]
        assert "chat_messages" in task
        assert len(task["chat_messages"]) == 3
        assert task["chat_messages"][0]["content"] == "Message 1"
    
    @patch('crucible.services.worldmodel_service.WorldModellerAgent')
    def test_generate_or_refine_world_model_provenance_tracking(self, mock_agent_class, test_db_session):
        """Test that provenance entries are added for changes."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_model": {
                "actors": [{"id": "actor_1", "name": "Test Actor"}],
                "mechanisms": [],
                "resources": [],
                "constraints": [],
                "assumptions": [],
                "simplifications": []
            },
            "changes": [
                {"type": "add", "entity_type": "actor", "entity_id": "actor_1", "description": "Added actor"}
            ],
            "reasoning": "Created initial model",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = WorldModelService(test_db_session)
        service.agent = mock_agent
        
        result = service.generate_or_refine_world_model(project.id, chat_session.id)
        
        assert result["applied"] is True
        
        # Verify provenance was added
        model = get_world_model(test_db_session, project.id)
        assert "provenance" in model.model_data
        assert len(model.model_data["provenance"]) == 1
        provenance_entry = model.model_data["provenance"][0]
        assert provenance_entry["type"] == "add"
        assert provenance_entry["entity_type"] == "actor"
        assert provenance_entry["actor"] == "agent"
        assert chat_session.id in provenance_entry["source"]
    
    def test_update_world_model_manual_creates_new(self, test_db_session):
        """Test that update_world_model_manual creates new model when none exists."""
        project = create_project(test_db_session, "Test Project", "Test description")
        
        model_data = {
            "actors": [{"id": "actor_1", "name": "Test Actor"}],
            "mechanisms": [],
            "resources": [],
            "constraints": [],
            "assumptions": [],
            "simplifications": []
        }
        
        service = WorldModelService(test_db_session)
        result = service.update_world_model_manual(project.id, model_data, source="manual_edit")
        
        assert result is True
        
        # Verify model was created
        model = get_world_model(test_db_session, project.id)
        assert model is not None
        assert "provenance" in model.model_data
        assert len(model.model_data["provenance"]) == 1
        assert model.model_data["provenance"][0]["actor"] == "user"
        assert model.model_data["provenance"][0]["source"] == "manual_edit"
    
    def test_update_world_model_manual_updates_existing(self, test_db_session):
        """Test that update_world_model_manual updates existing model."""
        project = create_project(test_db_session, "Test Project", "Test description")
        create_world_model(
            test_db_session,
            project.id,
            model_data={"actors": [{"id": "actor_1", "name": "Old Actor"}]}
        )
        
        model_data = {
            "actors": [{"id": "actor_1", "name": "Updated Actor"}],
            "mechanisms": [],
            "resources": [],
            "constraints": [],
            "assumptions": [],
            "simplifications": []
        }
        
        service = WorldModelService(test_db_session)
        result = service.update_world_model_manual(project.id, model_data, source="ui_edit")
        
        assert result is True
        
        # Verify model was updated
        model = get_world_model(test_db_session, project.id)
        assert model.model_data["actors"][0]["name"] == "Updated Actor"
        assert len(model.model_data["provenance"]) == 1
        assert model.model_data["provenance"][0]["source"] == "ui_edit"
    
    @patch('crucible.services.worldmodel_service.WorldModellerAgent')
    def test_generate_or_refine_world_model_agent_error(self, mock_agent_class, test_db_session):
        """Test error handling when agent raises exception."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        # Mock agent to raise error
        mock_agent = Mock()
        mock_agent.execute.side_effect = Exception("Agent error")
        mock_agent_class.return_value = mock_agent
        
        service = WorldModelService(test_db_session)
        service.agent = mock_agent
        
        with pytest.raises(Exception) as exc_info:
            service.generate_or_refine_world_model(project.id, chat_session.id)
        
        assert "Agent error" in str(exc_info.value)
    
    def test_apply_model_updates_creates_new(self, test_db_session):
        """Test that _apply_model_updates creates new model when none exists."""
        project = create_project(test_db_session, "Test Project", "Test description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        updated_model = {
            "actors": [{"id": "actor_1", "name": "Test Actor"}],
            "mechanisms": [],
            "resources": [],
            "constraints": [],
            "assumptions": [],
            "simplifications": []
        }
        
        changes = [
            {"type": "add", "entity_type": "actor", "entity_id": "actor_1", "description": "Added actor"}
        ]
        
        service = WorldModelService(test_db_session)
        result = service._apply_model_updates(project.id, None, updated_model, changes, chat_session.id)
        
        assert result is True
        
        # Verify model was created
        model = get_world_model(test_db_session, project.id)
        assert model is not None
        assert "provenance" in model.model_data
        assert len(model.model_data["provenance"]) == 1
    
    def test_apply_model_updates_updates_existing(self, test_db_session):
        """Test that _apply_model_updates updates existing model."""
        project = create_project(test_db_session, "Test Project", "Test description")
        create_world_model(
            test_db_session,
            project.id,
            model_data={"actors": [{"id": "actor_1", "name": "Old Actor"}]}
        )
        
        current_model = get_world_model(test_db_session, project.id)
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        updated_model = {
            "actors": [{"id": "actor_1", "name": "Updated Actor"}],
            "mechanisms": [],
            "resources": [],
            "constraints": [],
            "assumptions": [],
            "simplifications": []
        }
        
        changes = [
            {"type": "update", "entity_type": "actor", "entity_id": "actor_1", "description": "Updated actor"}
        ]
        
        service = WorldModelService(test_db_session)
        result = service._apply_model_updates(project.id, current_model, updated_model, changes, chat_session.id)
        
        assert result is True
        
        # Verify model was updated
        model = get_world_model(test_db_session, project.id)
        assert model.model_data["actors"][0]["name"] == "Updated Actor"
        assert len(model.model_data["provenance"]) == 1

