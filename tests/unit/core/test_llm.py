"""
Unit tests for Claude LLM client.

Tests both API and CLI modes with mocking.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


# Mock the anthropic module for testing
@pytest.fixture
def mock_anthropic():
    """Mock anthropic module."""
    with patch('kosmos.core.llm.Anthropic') as mock:
        # Create mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response from Claude")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        # Configure mock client
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock.return_value = mock_client

        yield mock


@pytest.fixture
def api_env():
    """Set up API mode environment."""
    original = os.environ.get('ANTHROPIC_API_KEY')
    os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key-123'
    yield
    if original:
        os.environ['ANTHROPIC_API_KEY'] = original
    else:
        del os.environ['ANTHROPIC_API_KEY']


@pytest.fixture
def cli_env():
    """Set up CLI mode environment."""
    original = os.environ.get('ANTHROPIC_API_KEY')
    os.environ['ANTHROPIC_API_KEY'] = '999999999999999999999999999999999999999999999999'
    yield
    if original:
        os.environ['ANTHROPIC_API_KEY'] = original
    else:
        del os.environ['ANTHROPIC_API_KEY']


class TestClaudeClientInitialization:
    """Test Claude client initialization."""

    def test_init_with_api_key(self, mock_anthropic, api_env):
        """Test initialization with API key."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()

        assert client.api_key == 'sk-ant-test-key-123'
        assert not client.is_cli_mode
        assert client.model == "claude-3-5-sonnet-20241022"
        assert client.max_tokens == 4096

    def test_init_with_cli_mode(self, mock_anthropic, cli_env):
        """Test initialization in CLI mode."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()

        assert client.is_cli_mode
        assert client.api_key == '999999999999999999999999999999999999999999999999'

    def test_init_without_api_key(self, mock_anthropic):
        """Test initialization fails without API key."""
        from kosmos.core.llm import ClaudeClient

        if 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable not set"):
            ClaudeClient()

    def test_custom_parameters(self, mock_anthropic, api_env):
        """Test initialization with custom parameters."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient(
            model="claude-3-opus-20240229",
            max_tokens=8192,
            temperature=0.5
        )

        assert client.model == "claude-3-opus-20240229"
        assert client.max_tokens == 8192
        assert client.temperature == 0.5


class TestClaudeClientGeneration:
    """Test Claude text generation."""

    def test_generate_basic(self, mock_anthropic, api_env):
        """Test basic text generation."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()
        response = client.generate("Test prompt")

        assert response == "Test response from Claude"
        assert client.total_requests == 1
        assert client.total_input_tokens == 100
        assert client.total_output_tokens == 50

    def test_generate_with_system_prompt(self, mock_anthropic, api_env):
        """Test generation with system prompt."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()
        response = client.generate(
            prompt="User prompt",
            system="System instructions"
        )

        # Verify system prompt was passed
        call_args = mock_anthropic.return_value.messages.create.call_args
        assert call_args[1]['system'] == "System instructions"

    def test_generate_with_overrides(self, mock_anthropic, api_env):
        """Test generation with parameter overrides."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()
        response = client.generate(
            prompt="Test",
            max_tokens=2000,
            temperature=0.9
        )

        call_args = mock_anthropic.return_value.messages.create.call_args
        assert call_args[1]['max_tokens'] == 2000
        assert call_args[1]['temperature'] == 0.9

    def test_generate_with_messages(self, mock_anthropic, api_env):
        """Test multi-turn generation."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        response = client.generate_with_messages(messages)

        assert response == "Test response from Claude"
        call_args = mock_anthropic.return_value.messages.create.call_args
        assert call_args[1]['messages'] == messages


class TestClaudeClientStructured:
    """Test structured output generation."""

    def test_generate_structured_json(self, mock_anthropic, api_env):
        """Test structured JSON output."""
        from kosmos.core.llm import ClaudeClient

        # Mock JSON response
        json_response = {"hypothesis": "Test hypothesis", "confidence": 0.8}
        mock_anthropic.return_value.messages.create.return_value.content[0].text = json.dumps(json_response)

        client = ClaudeClient()
        schema = {
            "type": "object",
            "properties": {
                "hypothesis": {"type": "string"},
                "confidence": {"type": "number"}
            }
        }

        result = client.generate_structured(
            prompt="Generate hypothesis",
            output_schema=schema
        )

        assert result == json_response
        assert result["hypothesis"] == "Test hypothesis"
        assert result["confidence"] == 0.8

    def test_generate_structured_with_markdown(self, mock_anthropic, api_env):
        """Test structured output extraction from markdown code block."""
        from kosmos.core.llm import ClaudeClient

        # Mock response with markdown code block
        json_data = {"result": "value"}
        markdown_response = f"```json\n{json.dumps(json_data)}\n```"
        mock_anthropic.return_value.messages.create.return_value.content[0].text = markdown_response

        client = ClaudeClient()
        result = client.generate_structured(
            prompt="Test",
            output_schema={"type": "object"}
        )

        assert result == json_data

    def test_generate_structured_invalid_json(self, mock_anthropic, api_env):
        """Test error handling for invalid JSON."""
        from kosmos.core.llm import ClaudeClient

        mock_anthropic.return_value.messages.create.return_value.content[0].text = "Not valid JSON"

        client = ClaudeClient()

        with pytest.raises(ValueError, match="Claude did not return valid JSON"):
            client.generate_structured(
                prompt="Test",
                output_schema={"type": "object"}
            )


class TestClaudeClientStatistics:
    """Test usage statistics tracking."""

    def test_get_usage_stats(self, mock_anthropic, api_env):
        """Test getting usage statistics."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()
        client.generate("Test 1")
        client.generate("Test 2")

        stats = client.get_usage_stats()

        assert stats["total_requests"] == 2
        assert stats["total_input_tokens"] == 200  # 100 per request
        assert stats["total_output_tokens"] == 100  # 50 per request
        assert "estimated_cost_usd" in stats

    def test_cost_estimation_api_mode(self, mock_anthropic, api_env):
        """Test cost estimation in API mode."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()
        client.generate("Test")

        stats = client.get_usage_stats()

        # Should have non-zero cost in API mode
        assert stats["estimated_cost_usd"] > 0

    def test_cost_estimation_cli_mode(self, mock_anthropic, cli_env):
        """Test cost estimation in CLI mode (should be 0)."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()
        client.generate("Test")

        stats = client.get_usage_stats()

        # Should be zero cost in CLI mode
        assert stats["estimated_cost_usd"] == 0.0

    def test_reset_stats(self, mock_anthropic, api_env):
        """Test resetting statistics."""
        from kosmos.core.llm import ClaudeClient

        client = ClaudeClient()
        client.generate("Test")

        assert client.total_requests == 1

        client.reset_stats()

        assert client.total_requests == 0
        assert client.total_input_tokens == 0
        assert client.total_output_tokens == 0


class TestClaudeClientSingleton:
    """Test singleton client instance."""

    def test_get_client(self, mock_anthropic, api_env):
        """Test getting default client."""
        from kosmos.core.llm import get_client

        client1 = get_client()
        client2 = get_client()

        # Should return same instance
        assert client1 is client2

    def test_get_client_reset(self, mock_anthropic, api_env):
        """Test resetting default client."""
        from kosmos.core.llm import get_client

        client1 = get_client()
        client2 = get_client(reset=True)

        # Should return different instance after reset
        assert client1 is not client2
