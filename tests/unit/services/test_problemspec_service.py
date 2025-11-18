"""
Unit tests for ProblemSpecService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from crucible.services.problemspec_service import ProblemSpecService
from crucible.db.models import (
    Project, ChatSession, Message, ProblemSpec,
    ResolutionLevel, RunMode, MessageRole
)
from crucible.db.repositories import (
    create_project, create_chat_session, create_message,
    create_problem_spec, get_problem_spec
)


class TestProblemSpecService:
    """Test suite for ProblemSpecService."""
    
    def test_service_initialization(self, test_db_session):
        """Test that ProblemSpecService initializes correctly."""
        service = ProblemSpecService(test_db_session)
        
        assert service.session == test_db_session
        assert hasattr(service, "agent")
        assert service.agent is not None
    
    def test_get_problem_spec_existing(self, test_db_session):
        """Test retrieving existing ProblemSpec."""
        # Create project and spec
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[{"name": "Budget", "description": "Limited", "weight": 60}],
            goals=["Goal 1"],
            resolution="medium",
            mode="full_search"
        )
        
        service = ProblemSpecService(test_db_session)
        result = service.get_problem_spec(project.id)
        
        assert result is not None
        assert result["project_id"] == project.id
        assert len(result["constraints"]) == 1
        assert result["constraints"][0]["name"] == "Budget"
        assert result["goals"] == ["Goal 1"]
        assert result["resolution"] == "medium"
        assert result["mode"] == "full_search"
    
    def test_get_problem_spec_nonexistent(self, test_db_session):
        """Test retrieving ProblemSpec for project without one."""
        # Create project without spec
        project = create_project(test_db_session, "Test Project", "Test description")
        
        service = ProblemSpecService(test_db_session)
        result = service.get_problem_spec(project.id)
        
        assert result is None
    
    @patch('crucible.services.problemspec_service.ProblemSpecAgent')
    def test_refine_problem_spec_new_spec(self, mock_agent_class, test_db_session):
        """Test refining ProblemSpec when none exists (creates new)."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        create_message(test_db_session, chat_session.id, "user", "I need to improve performance")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_spec": {
                "constraints": [{"name": "Performance", "description": "Must be fast", "weight": 80}],
                "goals": ["Improve performance"],
                "resolution": "medium",
                "mode": "full_search"
            },
            "follow_up_questions": ["What is the target response time?"],
            "reasoning": "Created initial spec",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = ProblemSpecService(test_db_session)
        service.agent = mock_agent
        
        result = service.refine_problem_spec(project.id, chat_session.id)
        
        assert result["updated_spec"] is not None
        assert len(result["follow_up_questions"]) == 1
        assert result["applied"] is True
        
        # Verify spec was created in database
        spec = get_problem_spec(test_db_session, project.id)
        assert spec is not None
        assert len(spec.constraints) == 1
    
    @patch('crucible.services.problemspec_service.ProblemSpecAgent')
    def test_refine_problem_spec_update_existing(self, mock_agent_class, test_db_session):
        """Test refining ProblemSpec when one exists (updates)."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[{"name": "Budget", "description": "Limited", "weight": 60}],
            goals=["Goal 1"],
            resolution="medium",
            mode="full_search"
        )
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        create_message(test_db_session, chat_session.id, "user", "Add performance constraint")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_spec": {
                "constraints": [
                    {"name": "Budget", "description": "Limited", "weight": 60},
                    {"name": "Performance", "description": "Must be fast", "weight": 80}
                ],
                "goals": ["Goal 1", "Improve performance"],
                "resolution": "medium",
                "mode": "full_search"
            },
            "follow_up_questions": [],
            "reasoning": "Added performance constraint",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = ProblemSpecService(test_db_session)
        service.agent = mock_agent
        
        result = service.refine_problem_spec(project.id, chat_session.id)
        
        assert result["applied"] is True
        
        # Verify spec was updated in database
        spec = get_problem_spec(test_db_session, project.id)
        assert len(spec.constraints) == 2
        assert any(c["name"] == "Performance" for c in spec.constraints)
    
    @patch('crucible.services.problemspec_service.ProblemSpecAgent')
    def test_refine_problem_spec_with_chat_messages(self, mock_agent_class, test_db_session):
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
            "updated_spec": {"constraints": [], "goals": [], "resolution": "medium", "mode": "full_search"},
            "follow_up_questions": [],
            "reasoning": "",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = ProblemSpecService(test_db_session)
        service.agent = mock_agent
        
        service.refine_problem_spec(project.id, chat_session.id, message_limit=20)
        
        # Verify agent was called with chat messages
        call_args = mock_agent.execute.call_args
        assert call_args is not None
        task = call_args[0][0]
        assert "chat_messages" in task
        assert len(task["chat_messages"]) == 3
        assert task["chat_messages"][0]["content"] == "Message 1"
    
    @patch('crucible.services.problemspec_service.ProblemSpecAgent')
    def test_refine_problem_spec_message_limit(self, mock_agent_class, test_db_session):
        """Test that message_limit limits chat messages passed to agent."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        # Create 10 messages
        for i in range(10):
            create_message(test_db_session, chat_session.id, "user", f"Message {i}")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_spec": {"constraints": [], "goals": [], "resolution": "medium", "mode": "full_search"},
            "follow_up_questions": [],
            "reasoning": "",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = ProblemSpecService(test_db_session)
        service.agent = mock_agent
        
        service.refine_problem_spec(project.id, chat_session.id, message_limit=5)
        
        # Verify only 5 messages were passed (should be last 5)
        call_args = mock_agent.execute.call_args
        task = call_args[0][0]
        assert len(task["chat_messages"]) == 5
        assert task["chat_messages"][-1]["content"] == "Message 9"  # Most recent
    
    @patch('crucible.services.problemspec_service.ProblemSpecAgent')
    def test_refine_problem_spec_with_project_description(self, mock_agent_class, test_db_session):
        """Test that project description is passed to agent."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test project description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_spec": {"constraints": [], "goals": [], "resolution": "medium", "mode": "full_search"},
            "follow_up_questions": [],
            "reasoning": "",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = ProblemSpecService(test_db_session)
        service.agent = mock_agent
        
        service.refine_problem_spec(project.id, chat_session.id)
        
        # Verify project description was passed
        call_args = mock_agent.execute.call_args
        task = call_args[0][0]
        assert task["project_description"] == "Test project description"
    
    @patch('crucible.services.problemspec_service.ProblemSpecAgent')
    def test_refine_problem_spec_invalid_enum_values(self, mock_agent_class, test_db_session):
        """Test handling of invalid enum values from agent."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        # Mock agent returning invalid enum values
        mock_agent = Mock()
        mock_agent.execute.return_value = {
            "updated_spec": {
                "constraints": [],
                "goals": [],
                "resolution": "invalid_resolution",  # Invalid
                "mode": "invalid_mode"  # Invalid
            },
            "follow_up_questions": [],
            "reasoning": "",
            "ready_to_run": False
        }
        mock_agent_class.return_value = mock_agent
        
        service = ProblemSpecService(test_db_session)
        service.agent = mock_agent
        
        result = service.refine_problem_spec(project.id, chat_session.id)
        
        # Should handle invalid enums gracefully (warnings logged, defaults used)
        assert result["applied"] is True
        # Should still create/update spec with defaults
        spec = get_problem_spec(test_db_session, project.id)
        assert spec is not None
    
    @patch('crucible.services.problemspec_service.ProblemSpecAgent')
    def test_refine_problem_spec_agent_error(self, mock_agent_class, test_db_session):
        """Test error handling when agent raises exception."""
        # Setup
        project = create_project(test_db_session, "Test Project", "Test description")
        chat_session = create_chat_session(test_db_session, project.id, "Test Chat")
        
        # Mock agent to raise error
        mock_agent = Mock()
        mock_agent.execute.side_effect = Exception("Agent error")
        mock_agent_class.return_value = mock_agent
        
        service = ProblemSpecService(test_db_session)
        service.agent = mock_agent
        
        with pytest.raises(Exception) as exc_info:
            service.refine_problem_spec(project.id, chat_session.id)
        
        assert "Agent error" in str(exc_info.value)
    
    def test_apply_spec_updates_creates_new(self, test_db_session):
        """Test that _apply_spec_updates creates new spec when none exists."""
        project = create_project(test_db_session, "Test Project", "Test description")
        
        updated_spec = {
            "constraints": [{"name": "Test", "description": "Test", "weight": 50}],
            "goals": ["Test goal"],
            "resolution": "medium",
            "mode": "full_search"
        }
        
        service = ProblemSpecService(test_db_session)
        result = service._apply_spec_updates(project.id, None, updated_spec)
        
        assert result is True
        
        # Verify spec was created
        spec = get_problem_spec(test_db_session, project.id)
        assert spec is not None
        assert len(spec.constraints) == 1
    
    def test_apply_spec_updates_updates_existing(self, test_db_session):
        """Test that _apply_spec_updates updates existing spec."""
        project = create_project(test_db_session, "Test Project", "Test description")
        create_problem_spec(
            test_db_session,
            project.id,
            constraints=[{"name": "Old", "description": "Old", "weight": 50}],
            goals=["Old goal"],
            resolution="coarse",
            mode="eval_only"
        )
        
        current_spec = get_problem_spec(test_db_session, project.id)
        
        updated_spec = {
            "constraints": [{"name": "New", "description": "New", "weight": 80}],
            "goals": ["New goal"],
            "resolution": "fine",
            "mode": "full_search"
        }
        
        service = ProblemSpecService(test_db_session)
        result = service._apply_spec_updates(project.id, current_spec, updated_spec)
        
        assert result is True
        
        # Verify spec was updated
        spec = get_problem_spec(test_db_session, project.id)
        assert len(spec.constraints) == 1
        assert spec.constraints[0]["name"] == "New"
        assert spec.goals == ["New goal"]
        assert spec.resolution == ResolutionLevel.FINE
        assert spec.mode == RunMode.FULL_SEARCH

