"""
Unit tests for ProblemSpecAgent.
"""

import json
import pytest
from unittest.mock import Mock, patch
from kosmos.core.providers.base import LLMResponse, UsageStats

from crucible.agents.problemspec_agent import ProblemSpecAgent


class TestProblemSpecAgent:
    """Test suite for ProblemSpecAgent."""
    
    def test_agent_initialization(self):
        """Test that ProblemSpecAgent initializes correctly."""
        agent = ProblemSpecAgent()
        
        assert agent.agent_type == "ProblemSpecAgent"
        assert agent.agent_id is not None
        assert hasattr(agent, "llm_provider")
    
    def test_execute_with_empty_chat(self, mock_problemspec_agent, sample_llm_response_json):
        """Test execute with empty chat messages."""
        # Setup mock response
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(sample_llm_response_json),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "chat_messages": [],
            "current_problem_spec": None,
            "project_description": None
        }
        
        result = mock_problemspec_agent.execute(task)
        
        assert "updated_spec" in result
        assert "follow_up_questions" in result
        assert "reasoning" in result
        assert "ready_to_run" in result
        assert result["updated_spec"]["constraints"] is not None
        assert isinstance(result["follow_up_questions"], list)
    
    def test_execute_with_chat_messages(self, mock_problemspec_agent, sample_chat_messages, sample_llm_response_json):
        """Test execute with chat messages."""
        # Setup mock response
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(sample_llm_response_json),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "chat_messages": sample_chat_messages,
            "current_problem_spec": None,
            "project_description": "Test project"
        }
        
        result = mock_problemspec_agent.execute(task)
        
        assert result["updated_spec"]["goals"] == ["Reduce response time to under 500ms", "Maintain system reliability"]
        assert len(result["follow_up_questions"]) == 2
        assert result["reasoning"] == "Added performance constraint based on user's response time requirements."
        
        # Verify LLM was called with chat messages
        call_args = mock_problemspec_agent.llm_provider.generate.call_args
        assert call_args is not None
        prompt = call_args[0][0]
        assert "API response times" in prompt
    
    def test_execute_with_current_spec(self, mock_problemspec_agent, sample_current_spec, sample_llm_response_json):
        """Test execute with existing ProblemSpec."""
        # Setup mock response that merges with existing spec
        response_json = sample_llm_response_json.copy()
        response_json["updated_spec"]["constraints"].append(sample_current_spec["constraints"][0])
        
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(response_json),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "chat_messages": [],
            "current_problem_spec": sample_current_spec,
            "project_description": None
        }
        
        result = mock_problemspec_agent.execute(task)
        
        # Should include both existing and new constraints
        constraints = result["updated_spec"]["constraints"]
        assert len(constraints) >= 1
        assert any(c["name"] == "Budget" for c in constraints)
    
    def test_json_parsing_with_markdown_code_block(self, mock_problemspec_agent, sample_llm_response_json):
        """Test JSON parsing when LLM returns markdown code block."""
        # LLM sometimes wraps JSON in markdown code blocks
        json_content = json.dumps(sample_llm_response_json)
        markdown_content = f"```json\n{json_content}\n```"
        
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content=markdown_content,
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "chat_messages": [],
            "current_problem_spec": None,
            "project_description": None
        }
        
        result = mock_problemspec_agent.execute(task)
        
        # Should successfully parse JSON from markdown
        assert "updated_spec" in result
        assert result["updated_spec"]["resolution"] == "medium"
    
    def test_json_parsing_with_plain_code_block(self, mock_problemspec_agent, sample_llm_response_json):
        """Test JSON parsing when LLM returns plain code block."""
        json_content = json.dumps(sample_llm_response_json)
        markdown_content = f"```\n{json_content}\n```"
        
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content=markdown_content,
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "chat_messages": [],
            "current_problem_spec": None,
            "project_description": None
        }
        
        result = mock_problemspec_agent.execute(task)
        
        # Should successfully parse JSON from plain code block
        assert "updated_spec" in result
    
    def test_json_parsing_invalid_json(self, mock_problemspec_agent):
        """Test error handling when LLM returns invalid JSON."""
        # Invalid JSON response
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content="This is not valid JSON at all!",
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "chat_messages": [],
            "current_problem_spec": None,
            "project_description": None
        }
        
        result = mock_problemspec_agent.execute(task)
        
        # Should return safe default on JSON parse error
        assert "updated_spec" in result
        assert "follow_up_questions" in result
        assert result["follow_up_questions"]  # Should have a default question
        assert result["ready_to_run"] is False
    
    def test_json_parsing_missing_fields(self, mock_problemspec_agent):
        """Test handling when LLM response is missing required fields."""
        # Partial JSON missing some fields
        incomplete_json = '{"updated_spec": {"constraints": []}}'
        
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content=incomplete_json,
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "chat_messages": [],
            "current_problem_spec": None,
            "project_description": None
        }
        
        result = mock_problemspec_agent.execute(task)
        
        # Should handle missing fields gracefully
        assert "updated_spec" in result
        assert "follow_up_questions" in result
        assert isinstance(result["follow_up_questions"], list)  # Default to empty list
        assert "ready_to_run" in result
    
    def test_prompt_construction(self, mock_problemspec_agent, sample_chat_messages, sample_current_spec):
        """Test that prompt is constructed correctly."""
        task = {
            "chat_messages": sample_chat_messages,
            "current_problem_spec": sample_current_spec,
            "project_description": "Test project description"
        }
        
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content='{"updated_spec": {}, "follow_up_questions": [], "reasoning": "", "ready_to_run": false}',
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        mock_problemspec_agent.execute(task)
        
        # Verify prompt contains expected elements
        call_args = mock_problemspec_agent.llm_provider.generate.call_args
        prompt = call_args[0][0]
        
        assert "ProblemSpec refinement agent" in prompt
        assert "Test project description" in prompt
        assert "API response times" in prompt  # From chat messages
        assert "Budget" in prompt  # From current spec
    
    def test_execute_propagates_llm_errors(self, mock_problemspec_agent):
        """Test that LLM provider errors are properly propagated."""
        # Make LLM provider raise an error
        mock_problemspec_agent.llm_provider.generate.side_effect = Exception("LLM API error")
        
        task = {
            "chat_messages": [],
            "current_problem_spec": None,
            "project_description": None
        }
        
        with pytest.raises(Exception) as exc_info:
            mock_problemspec_agent.execute(task)
        
        assert "LLM API error" in str(exc_info.value)
    
    def test_ready_to_run_flag(self, mock_problemspec_agent):
        """Test ready_to_run flag handling."""
        # Test with ready_to_run = true
        ready_json = {
            "updated_spec": {"constraints": [], "goals": ["Goal 1"], "resolution": "medium", "mode": "full_search"},
            "follow_up_questions": [],
            "reasoning": "Spec is complete",
            "ready_to_run": True
        }
        
        mock_problemspec_agent.llm_provider.generate.return_value = LLMResponse(
            content=json.dumps(ready_json),
            usage=UsageStats(input_tokens=100, output_tokens=50, total_tokens=150),
            model="test-model",
            finish_reason="stop"
        )
        
        task = {
            "chat_messages": [],
            "current_problem_spec": None,
            "project_description": None
        }
        
        result = mock_problemspec_agent.execute(task)
        assert result["ready_to_run"] is True

