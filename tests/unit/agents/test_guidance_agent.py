"""
Unit tests for GuidanceAgent.
"""

import json
import pytest
from unittest.mock import Mock, patch
from kosmos.core.providers.base import LLMResponse, UsageStats

from crucible.agents.guidance_agent import GuidanceAgent


class TestGuidanceAgent:
    """Test suite for GuidanceAgent."""
    
    def test_agent_initialization(self):
        """Test that GuidanceAgent initializes correctly."""
        agent = GuidanceAgent()
        
        assert agent.agent_type == "GuidanceAgent"
        assert agent.agent_id is not None
        assert hasattr(agent, "llm_provider")
    
    def test_execute_with_basic_state(self):
        """Test execute with basic project state."""
        agent = GuidanceAgent()
        
        # Mock LLM response
        mock_response = {
            "guidance_message": "Welcome to Int Crucible! Let's get started.",
            "suggested_actions": [
                "Start chatting about your problem",
                "Describe your constraints and goals"
            ],
            "explanations": {},
            "workflow_progress": {
                "current_stage": "setup",
                "completed_steps": [],
                "next_steps": ["Create ProblemSpec via chat"]
            }
        }
        
        agent.llm_provider = Mock()
        agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "user_query": None,
            "project_state": {
                "has_problem_spec": False,
                "has_world_model": False,
                "has_runs": False,
                "run_count": 0
            },
            "workflow_stage": "setup",
            "chat_context": []
        }
        
        result = agent.execute(task)
        
        assert "guidance_message" in result
        assert "suggested_actions" in result
        assert "explanations" in result
        assert "workflow_progress" in result
        assert isinstance(result["suggested_actions"], list)
        assert isinstance(result["workflow_progress"], dict)
    
    def test_execute_with_user_query(self):
        """Test execute with user query."""
        agent = GuidanceAgent()
        
        mock_response = {
            "guidance_message": "A ProblemSpec is a structured problem specification...",
            "suggested_actions": ["Continue chatting to refine your ProblemSpec"],
            "explanations": {
                "ProblemSpec": "A structured problem specification with constraints, goals, and resolution level"
            },
            "workflow_progress": {
                "current_stage": "setup",
                "completed_steps": [],
                "next_steps": ["Create ProblemSpec via chat"]
            }
        }
        
        agent.llm_provider = Mock()
        agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "user_query": "What is a ProblemSpec?",
            "project_state": {
                "has_problem_spec": False,
                "has_world_model": False,
                "has_runs": False,
                "run_count": 0
            },
            "workflow_stage": "setup",
            "chat_context": []
        }
        
        result = agent.execute(task)
        
        assert "guidance_message" in result
        assert "ProblemSpec" in result.get("explanations", {})
    
    def test_execute_with_advanced_state(self):
        """Test execute with project that has ProblemSpec and WorldModel."""
        agent = GuidanceAgent()
        
        mock_response = {
            "guidance_message": "Great! You're ready to run.",
            "suggested_actions": [
                "Configure and start your first run",
                "Review the ranked candidates after completion"
            ],
            "explanations": {},
            "workflow_progress": {
                "current_stage": "ready_to_run",
                "completed_steps": ["ProblemSpec created", "WorldModel created"],
                "next_steps": ["Configure and start a run"]
            }
        }
        
        agent.llm_provider = Mock()
        agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(mock_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "user_query": None,
            "project_state": {
                "has_problem_spec": True,
                "has_world_model": True,
                "has_runs": False,
                "run_count": 0
            },
            "workflow_stage": "ready_to_run",
            "chat_context": []
        }
        
        result = agent.execute(task)
        
        assert result["workflow_progress"]["current_stage"] == "ready_to_run"
        assert len(result["workflow_progress"]["completed_steps"]) > 0
    
    def test_execute_with_invalid_json_fallback(self):
        """Test that execute handles invalid JSON gracefully."""
        agent = GuidanceAgent()
        
        # Mock LLM response with invalid JSON (plain text)
        agent.llm_provider = Mock()
        agent.llm_provider.generate.return_value = LLMResponse(
            content="This is plain text, not JSON",
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "user_query": None,
            "project_state": {
                "has_problem_spec": False,
                "has_world_model": False,
                "has_runs": False,
                "run_count": 0
            },
            "workflow_stage": "setup",
            "chat_context": []
        }
        
        result = agent.execute(task)
        
        # Should still return valid structure with fallback values
        assert "guidance_message" in result
        assert "suggested_actions" in result
        assert isinstance(result["suggested_actions"], list)
    
    def test_compute_workflow_progress(self):
        """Test workflow progress computation."""
        agent = GuidanceAgent()
        
        # Test with no progress
        state = {
            "has_problem_spec": False,
            "has_world_model": False,
            "has_runs": False
        }
        progress = agent._compute_workflow_progress(state)
        assert progress["current_stage"] == "setup"
        assert len(progress["completed_steps"]) == 0
        
        # Test with ProblemSpec only
        state = {
            "has_problem_spec": True,
            "has_world_model": False,
            "has_runs": False
        }
        progress = agent._compute_workflow_progress(state)
        assert progress["current_stage"] == "setup"
        assert "ProblemSpec created" in progress["completed_steps"]
        
        # Test with ProblemSpec and WorldModel
        state = {
            "has_problem_spec": True,
            "has_world_model": True,
            "has_runs": False
        }
        progress = agent._compute_workflow_progress(state)
        assert progress["current_stage"] == "ready_to_run"
        assert "WorldModel created" in progress["completed_steps"]
        
        # Test with runs
        state = {
            "has_problem_spec": True,
            "has_world_model": True,
            "has_runs": True
        }
        progress = agent._compute_workflow_progress(state)
        assert progress["current_stage"] == "completed"
        assert "Run executed" in progress["completed_steps"]
    
    def test_get_default_suggestions(self):
        """Test default suggestions based on state."""
        agent = GuidanceAgent()
        
        # No ProblemSpec
        state = {"has_problem_spec": False, "has_world_model": False, "has_runs": False}
        suggestions = agent._get_default_suggestions(state)
        assert len(suggestions) > 0
        assert any("ProblemSpec" in s or "chat" in s.lower() for s in suggestions)
        
        # Has ProblemSpec, no WorldModel
        state = {"has_problem_spec": True, "has_world_model": False, "has_runs": False}
        suggestions = agent._get_default_suggestions(state)
        assert any("WorldModel" in s for s in suggestions)
        
        # Has both, no runs
        state = {"has_problem_spec": True, "has_world_model": True, "has_runs": False}
        suggestions = agent._get_default_suggestions(state)
        assert any("run" in s.lower() for s in suggestions)

