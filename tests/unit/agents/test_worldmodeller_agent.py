"""
Unit tests for WorldModellerAgent.
"""

import json
import pytest
from unittest.mock import Mock, patch
from kosmos.core.providers.base import LLMResponse, UsageStats

from crucible.agents.worldmodeller_agent import WorldModellerAgent


class TestWorldModellerAgent:
    """Test suite for WorldModellerAgent."""
    
    def test_agent_initialization(self):
        """Test that WorldModellerAgent initializes correctly."""
        agent = WorldModellerAgent()
        
        assert agent.agent_type == "WorldModellerAgent"
        assert agent.agent_id is not None
        assert hasattr(agent, "llm_provider")
    
    def test_empty_model_structure(self):
        """Test that empty model has correct structure."""
        agent = WorldModellerAgent()
        empty = agent._empty_model()
        
        assert "actors" in empty
        assert "mechanisms" in empty
        assert "resources" in empty
        assert "constraints" in empty
        assert "assumptions" in empty
        assert "simplifications" in empty
        assert all(isinstance(empty[key], list) for key in empty)
    
    def test_execute_with_empty_context(self, mock_worldmodeller_agent, sample_worldmodel_llm_response):
        """Test execute with empty context."""
        # Setup mock response
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(sample_worldmodel_llm_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "problem_spec": None,
            "current_world_model": None,
            "chat_messages": [],
            "project_description": None
        }
        
        result = mock_worldmodeller_agent.execute(task)
        
        assert "updated_model" in result
        assert "changes" in result
        assert "reasoning" in result
        assert "ready_to_run" in result
        assert "actors" in result["updated_model"]
        assert isinstance(result["changes"], list)
    
    def test_execute_with_problem_spec(self, mock_worldmodeller_agent, sample_problem_spec, sample_worldmodel_llm_response):
        """Test execute with ProblemSpec."""
        # Setup mock response
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(sample_worldmodel_llm_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "problem_spec": sample_problem_spec,
            "current_world_model": None,
            "chat_messages": [],
            "project_description": "Test project"
        }
        
        result = mock_worldmodeller_agent.execute(task)
        
        assert len(result["updated_model"]["actors"]) > 0
        assert len(result["updated_model"]["constraints"]) > 0
        
        # Verify LLM was called with ProblemSpec
        call_args = mock_worldmodeller_agent.llm_provider.generate.call_args
        assert call_args is not None
        prompt = call_args[0][0]
        assert "Test project" in prompt
        assert "constraints" in prompt
    
    def test_execute_with_current_model(self, mock_worldmodeller_agent, sample_world_model, sample_worldmodel_llm_response):
        """Test execute with existing WorldModel."""
        # Setup mock response that merges with existing model
        response_json = sample_worldmodel_llm_response.copy()
        # Add existing actor to response
        response_json["updated_model"]["actors"].extend(sample_world_model["actors"])
        
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(response_json),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "problem_spec": None,
            "current_world_model": sample_world_model,
            "chat_messages": [],
            "project_description": None
        }
        
        result = mock_worldmodeller_agent.execute(task)
        
        # Should include both existing and new actors
        actors = result["updated_model"]["actors"]
        assert len(actors) >= len(sample_world_model["actors"])
    
    def test_execute_with_chat_messages(self, mock_worldmodeller_agent, sample_chat_messages, sample_worldmodel_llm_response):
        """Test execute with chat messages."""
        # Setup mock response
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(sample_worldmodel_llm_response),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "problem_spec": None,
            "current_world_model": None,
            "chat_messages": sample_chat_messages,
            "project_description": None
        }
        
        result = mock_worldmodeller_agent.execute(task)
        
        # Verify LLM was called with chat messages
        call_args = mock_worldmodeller_agent.llm_provider.generate.call_args
        assert call_args is not None
        prompt = call_args[0][0]
        assert "API response times" in prompt
    
    def test_json_parsing_with_markdown_code_block(self, mock_worldmodeller_agent, sample_worldmodel_llm_response):
        """Test JSON parsing when LLM returns markdown code block."""
        json_content = json.dumps(sample_worldmodel_llm_response)
        markdown_content = f"```json\n{json_content}\n```"
        
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content=markdown_content,
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "problem_spec": None,
            "current_world_model": None,
            "chat_messages": [],
            "project_description": None
        }
        
        result = mock_worldmodeller_agent.execute(task)
        
        # Should successfully parse JSON from markdown
        assert "updated_model" in result
        assert "actors" in result["updated_model"]
    
    def test_json_parsing_invalid_json(self, mock_worldmodeller_agent):
        """Test error handling when LLM returns invalid JSON."""
        # Invalid JSON response
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content="This is not valid JSON at all!",
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "problem_spec": None,
            "current_world_model": None,
            "chat_messages": [],
            "project_description": None
        }
        
        result = mock_worldmodeller_agent.execute(task)
        
        # Should return safe default on JSON parse error
        assert "updated_model" in result
        assert "changes" in result
        assert isinstance(result["changes"], list)
        assert result["ready_to_run"] is False
    
    def test_json_parsing_missing_fields(self, mock_worldmodeller_agent):
        """Test handling when LLM response is missing required fields."""
        # Partial JSON missing some fields
        incomplete_json = '{"updated_model": {"actors": []}}'
        
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content=incomplete_json,
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "problem_spec": None,
            "current_world_model": None,
            "chat_messages": [],
            "project_description": None
        }
        
        result = mock_worldmodeller_agent.execute(task)
        
        # Should handle missing fields gracefully
        assert "updated_model" in result
        assert "changes" in result
        assert isinstance(result["changes"], list)  # Default to empty list
        assert "ready_to_run" in result
    
    def test_prompt_construction(self, mock_worldmodeller_agent, sample_problem_spec, sample_world_model, sample_chat_messages):
        """Test that prompt is constructed correctly."""
        task = {
            "problem_spec": sample_problem_spec,
            "current_world_model": sample_world_model,
            "chat_messages": sample_chat_messages,
            "project_description": "Test project description"
        }
        
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content='{"updated_model": {"actors": [], "mechanisms": [], "resources": [], "constraints": [], "assumptions": [], "simplifications": []}, "changes": [], "reasoning": "", "ready_to_run": false}',
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        mock_worldmodeller_agent.execute(task)
        
        # Verify prompt contains expected elements
        call_args = mock_worldmodeller_agent.llm_provider.generate.call_args
        prompt = call_args[0][0]
        
        assert "WorldModeller agent" in prompt
        assert "Test project description" in prompt
        assert "constraints" in prompt  # From ProblemSpec
        assert "actors" in prompt  # From current model
        assert "API response times" in prompt  # From chat messages
    
    def test_execute_propagates_llm_errors(self, mock_worldmodeller_agent):
        """Test that LLM provider errors are properly propagated."""
        # Make LLM provider raise an error
        mock_worldmodeller_agent.llm_provider.generate.side_effect = Exception("LLM API error")
        
        task = {
            "problem_spec": None,
            "current_world_model": None,
            "chat_messages": [],
            "project_description": None
        }
        
        with pytest.raises(Exception) as exc_info:
            mock_worldmodeller_agent.execute(task)
        
        assert "LLM API error" in str(exc_info.value)
    
    def test_ready_to_run_flag(self, mock_worldmodeller_agent):
        """Test ready_to_run flag handling."""
        # Test with ready_to_run = true
        ready_json = {
            "updated_model": {
                "actors": [{"id": "actor_1", "name": "Test Actor"}],
                "mechanisms": [],
                "resources": [],
                "constraints": [],
                "assumptions": [],
                "simplifications": []
            },
            "changes": [],
            "reasoning": "Model is complete",
            "ready_to_run": True
        }
        
        mock_worldmodeller_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(ready_json),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "problem_spec": None,
            "current_world_model": None,
            "chat_messages": [],
            "project_description": None
        }
        
        result = mock_worldmodeller_agent.execute(task)
        assert result["ready_to_run"] is True

