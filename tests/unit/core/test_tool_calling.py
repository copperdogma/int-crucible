"""
Unit tests for tool calling execution.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from kosmos.core.providers.base import LLMProvider, LLMResponse, UsageStats
from datetime import datetime

from crucible.core.tool_calling import (
    ToolCallingExecutor,
    ToolCall,
    ToolResult,
    ToolCallAudit
)


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, provider_name: str = "openai"):
        super().__init__({})
        self.provider_name = provider_name
        self.client = Mock()
    
    def generate(self, prompt, system=None, max_tokens=4096, temperature=0.7, **kwargs):
        return LLMResponse(
            content="Test response",
            usage=UsageStats(10, 20, 30),
            model="test-model",
            finish_reason="stop"
        )
    
    async def generate_async(self, prompt, system=None, max_tokens=4096, temperature=0.7, **kwargs):
        return self.generate(prompt, system, max_tokens, temperature, **kwargs)
    
    def generate_with_messages(self, messages, max_tokens=4096, temperature=0.7, **kwargs):
        return self.generate("", None, max_tokens, temperature)
    
    def generate_structured(self, prompt, schema, system=None, max_tokens=4096, temperature=0.7, **kwargs):
        return {}
    
    def get_model_info(self):
        return {"name": "test-model", "max_tokens": 4096}


class TestToolCallingExecutor:
    """Test suite for ToolCallingExecutor."""
    
    def test_executor_initialization(self):
        """Test that executor initializes correctly."""
        provider = MockLLMProvider("openai")
        tools = {
            "test_tool": lambda x: f"result_{x}"
        }
        
        executor = ToolCallingExecutor(provider, tools)
        
        assert executor.llm_provider == provider
        assert executor.tools == tools
        assert len(executor.tool_schemas) == 1
        assert executor.max_iterations == 10
        assert executor.provider_name == "openai"
    
    def test_validate_tool_call_valid(self):
        """Test validating a valid tool call."""
        provider = MockLLMProvider()
        tools = {"valid_tool": lambda x: x}
        executor = ToolCallingExecutor(provider, tools)
        
        is_valid, error = executor._validate_tool_call("valid_tool")
        
        assert is_valid is True
        assert error is None
    
    def test_validate_tool_call_invalid(self):
        """Test validating an invalid tool call."""
        provider = MockLLMProvider()
        tools = {"valid_tool": lambda x: x}
        executor = ToolCallingExecutor(provider, tools)
        
        is_valid, error = executor._validate_tool_call("invalid_tool")
        
        assert is_valid is False
        assert "not found" in error.lower()
    
    def test_validate_tool_call_denied(self):
        """Test validating a denied tool call."""
        provider = MockLLMProvider()
        tools = {"tool1": lambda x: x, "tool2": lambda x: x}
        executor = ToolCallingExecutor(provider, tools, denied_tools=["tool1"])
        
        is_valid, error = executor._validate_tool_call("tool1")
        
        assert is_valid is False
        assert "denied" in error.lower()
    
    def test_validate_tool_call_allowed_list(self):
        """Test validating with allowed list."""
        provider = MockLLMProvider()
        tools = {"tool1": lambda x: x, "tool2": lambda x: x}
        executor = ToolCallingExecutor(provider, tools, allowed_tools=["tool1"])
        
        is_valid, _ = executor._validate_tool_call("tool1")
        assert is_valid is True
        
        is_valid, _ = executor._validate_tool_call("tool2")
        assert is_valid is False
    
    def test_execute_tool_success(self):
        """Test executing a tool successfully."""
        provider = MockLLMProvider()
        
        def test_tool(param: str) -> str:
            return f"result_{param}"
        
        tools = {"test_tool": test_tool}
        executor = ToolCallingExecutor(provider, tools)
        
        tool_call = ToolCall(tool_name="test_tool", arguments={"param": "value"})
        result = executor._execute_tool(tool_call)
        
        assert result.success is True
        assert result.result == "result_value"
        assert result.tool_name == "test_tool"
        assert result.duration_ms > 0
        assert result.error is None
    
    def test_execute_tool_error(self):
        """Test executing a tool that raises an error."""
        provider = MockLLMProvider()
        
        def failing_tool(param: str) -> str:
            raise ValueError("Test error")
        
        tools = {"failing_tool": failing_tool}
        executor = ToolCallingExecutor(provider, tools)
        
        tool_call = ToolCall(tool_name="failing_tool", arguments={"param": "value"})
        result = executor._execute_tool(tool_call)
        
        assert result.success is False
        assert result.error is not None
        assert "error" in result.error.lower() or "Test error" in result.error
        assert result.result is None
    
    def test_create_audit_log(self):
        """Test creating audit log entry."""
        provider = MockLLMProvider()
        tools = {"test_tool": lambda x: {"result": x}}
        executor = ToolCallingExecutor(provider, tools)
        
        tool_call = ToolCall(tool_name="test_tool", arguments={"param": "value"})
        tool_result = ToolResult(
            tool_name="test_tool",
            result={"data": "result"},
            success=True,
            duration_ms=42.5
        )
        
        audit = executor._create_audit_log(tool_call, tool_result)
        
        assert audit.tool_name == "test_tool"
        assert audit.arguments == {"param": "value"}  # No redaction needed for this param
        assert audit.success is True
        assert audit.duration_ms == 42.5
        assert audit.result_summary is not None
        assert audit.error is None
    
    def test_redact_arguments(self):
        """Test redacting sensitive arguments."""
        provider = MockLLMProvider()
        tools = {"test_tool": lambda x: x}
        executor = ToolCallingExecutor(provider, tools)
        
        arguments = {
            "project_id": "proj123",
            "api_key": "secret_key",
            "password": "mypassword",
            "normal_param": "value"
        }
        
        redacted = executor._redact_arguments(arguments)
        
        assert redacted["project_id"] == "proj123"
        assert redacted["normal_param"] == "value"
        assert redacted["api_key"] == "[REDACTED]"
        assert redacted["password"] == "[REDACTED]"
    
    def test_summarize_result_string(self):
        """Test summarizing string result."""
        provider = MockLLMProvider()
        tools = {"test_tool": lambda x: x}
        executor = ToolCallingExecutor(provider, tools)
        
        summary = executor._summarize_result("Short result")
        assert summary == "Short result"
        
        long_result = "x" * 300
        summary = executor._summarize_result(long_result)
        assert len(summary) <= 203  # 200 + "..."
        assert summary.endswith("...")
    
    def test_summarize_result_dict(self):
        """Test summarizing dict result."""
        provider = MockLLMProvider()
        tools = {"test_tool": lambda x: x}
        executor = ToolCallingExecutor(provider, tools)
        
        result = {"key1": "value1", "key2": "value2"}
        summary = executor._summarize_result(result)
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_execute_with_tools_no_tools(self):
        """Test executing with no tools available."""
        provider = MockLLMProvider()
        executor = ToolCallingExecutor(provider, {})
        
        response, audits = executor.execute_with_tools(
            user_message="Test message",
            system_prompt="System prompt"
        )
        
        assert isinstance(response, str)
        assert len(audits) == 0
    
    @patch('crucible.core.tool_calling.OpenAI')
    def test_execute_with_tools_openai_success(self, mock_openai_class):
        """Test executing with OpenAI tool calling (successful)."""
        # Mock OpenAI response with tool calls
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_message.tool_calls = []
        
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = '{"param": "value"}'
        
        mock_message.tool_calls = [mock_tool_call]
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = MockLLMProvider("openai")
        provider.client = mock_client
        provider.model = "gpt-4-turbo"
        
        def test_tool(param: str) -> str:
            return f"result_{param}"
        
        tools = {"test_tool": test_tool}
        executor = ToolCallingExecutor(provider, tools, max_iterations=2)
        
        # First call: tool is requested
        # Second call: no tools (finished)
        mock_message2 = MagicMock()
        mock_message2.content = "Final response"
        mock_message2.tool_calls = None
        mock_choice2 = MagicMock()
        mock_choice2.message = mock_message2
        mock_choice2.finish_reason = "stop"
        mock_response2 = MagicMock()
        mock_response2.choices = [mock_choice2]
        mock_response2.usage = mock_response.usage
        
        mock_client.chat.completions.create.side_effect = [mock_response, mock_response2]
        
        response, audits = executor.execute_with_tools(
            user_message="Test message",
            system_prompt="System prompt",
            max_tokens=2048,
            temperature=0.7
        )
        
        # Should have executed the tool and gotten final response
        assert "Final response" in response
        assert len(audits) == 1
        assert audits[0].tool_name == "test_tool"
        assert audits[0].success is True

