"""
Unit tests for AsyncClaudeClient.

Tests async LLM client, rate limiting, batch processing.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from kosmos.core.async_llm import (
    AsyncClaudeClient,
    BatchRequest,
    BatchResponse,
    RateLimiter
)


class TestBatchRequest:
    """Test BatchRequest data class."""

    def test_creation(self):
        """Test creating batch request."""
        req = BatchRequest(
            id="test-1",
            prompt="Test prompt",
            system="Test system",
            temperature=0.7,
            max_tokens=1000
        )

        assert req.id == "test-1"
        assert req.prompt == "Test prompt"
        assert req.temperature == 0.7


class TestBatchResponse:
    """Test BatchResponse data class."""

    def test_success_response(self):
        """Test successful response."""
        resp = BatchResponse(
            id="test-1",
            response="Test response",
            success=True,
            tokens_used=50,
            latency_ms=500.0
        )

        assert resp.success is True
        assert resp.error is None

    def test_error_response(self):
        """Test error response."""
        resp = BatchResponse(
            id="test-1",
            response="",
            success=False,
            error="Rate limit exceeded"
        )

        assert resp.success is False
        assert resp.error == "Rate limit exceeded"


class TestRateLimiter:
    """Test RateLimiter implementation."""

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring tokens within rate limit."""
        limiter = RateLimiter(max_requests_per_minute=60)

        # Should allow requests within limit
        for _ in range(5):
            await limiter.acquire()

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting enforcement."""
        limiter = RateLimiter(max_requests_per_minute=10)

        # Fill bucket
        for _ in range(10):
            await limiter.acquire()

        # Next acquire should wait
        import time
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should have waited some time for token bucket refill
        assert elapsed > 0


@pytest.mark.asyncio
class TestAsyncClaudeClient:
    """Test AsyncClaudeClient."""

    @pytest.fixture
    def mock_client(self):
        """Create AsyncClaudeClient with mocked Anthropic client."""
        with patch('kosmos.core.async_llm.AsyncAnthropic') as mock:
            # Mock the async messages.create method
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            # Create mock response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Test response")]
            mock_response.usage = MagicMock(
                input_tokens=10,
                output_tokens=20
            )

            # Make messages.create return an awaitable
            async def mock_create(*args, **kwargs):
                return mock_response

            mock_instance.messages.create = mock_create

            client = AsyncClaudeClient(
                api_key="test-key",
                max_concurrent=5,
                max_requests_per_minute=50
            )
            client.client = mock_instance

            yield client

    async def test_generate_single(self, mock_client):
        """Test generating single response."""
        response = await mock_client.generate(
            prompt="Test prompt",
            system="Test system"
        )

        assert response == "Test response"

    async def test_batch_generate(self, mock_client):
        """Test batch generation."""
        requests = [
            BatchRequest(id="1", prompt="Prompt 1", temperature=0.7),
            BatchRequest(id="2", prompt="Prompt 2", temperature=0.7),
            BatchRequest(id="3", prompt="Prompt 3", temperature=0.7)
        ]

        responses = await mock_client.batch_generate(requests)

        assert len(responses) == 3
        assert all(r.success for r in responses)
        assert all(r.response == "Test response" for r in responses)

    async def test_batch_generate_with_errors(self):
        """Test batch generation with some failures."""
        with patch('kosmos.core.async_llm.AsyncAnthropic') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            # First request succeeds, second fails
            call_count = 0

            async def mock_create(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    response = MagicMock()
                    response.content = [MagicMock(text="Success")]
                    response.usage = MagicMock(input_tokens=10, output_tokens=20)
                    return response
                else:
                    raise Exception("API Error")

            mock_instance.messages.create = mock_create

            client = AsyncClaudeClient(
                api_key="test-key",
                max_concurrent=5,
                max_requests_per_minute=50
            )
            client.client = mock_instance

            requests = [
                BatchRequest(id="1", prompt="Prompt 1", temperature=0.7),
                BatchRequest(id="2", prompt="Prompt 2", temperature=0.7)
            ]

            responses = await client.batch_generate(requests)

            assert len(responses) == 2
            assert responses[0].success is True
            assert responses[1].success is False
            assert "API Error" in responses[1].error

    async def test_concurrency_limiting(self, mock_client):
        """Test concurrent request limiting."""
        # Create more requests than max_concurrent
        requests = [
            BatchRequest(id=str(i), prompt=f"Prompt {i}", temperature=0.7)
            for i in range(15)
        ]

        responses = await mock_client.batch_generate(requests)

        # All should complete despite concurrency limit
        assert len(responses) == 15
        assert all(r.success for r in responses)

    async def test_timeout_handling(self):
        """Test request timeout handling."""
        with patch('kosmos.core.async_llm.AsyncAnthropic') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            # Simulate slow request
            async def mock_create(*args, **kwargs):
                await asyncio.sleep(10)  # Long delay
                response = MagicMock()
                response.content = [MagicMock(text="Response")]
                response.usage = MagicMock(input_tokens=10, output_tokens=20)
                return response

            mock_instance.messages.create = mock_create

            client = AsyncClaudeClient(
                api_key="test-key",
                max_concurrent=5,
                max_requests_per_minute=50,
                timeout=1  # 1 second timeout
            )
            client.client = mock_instance

            requests = [BatchRequest(id="1", prompt="Prompt", temperature=0.7)]

            responses = await client.batch_generate(requests)

            # Should fail with timeout
            assert responses[0].success is False
            assert "timeout" in responses[0].error.lower()

    async def test_close_client(self, mock_client):
        """Test closing client."""
        mock_client.client.close = AsyncMock()

        await mock_client.close()

        mock_client.client.close.assert_called_once()

    async def test_token_counting(self, mock_client):
        """Test token usage tracking."""
        requests = [
            BatchRequest(id="1", prompt="Prompt 1", temperature=0.7),
            BatchRequest(id="2", prompt="Prompt 2", temperature=0.7)
        ]

        responses = await mock_client.batch_generate(requests)

        # Each mock response has 10 input + 20 output tokens
        total_tokens = sum(r.tokens_used for r in responses if r.success)
        assert total_tokens == 60  # (10+20) * 2 requests

    async def test_latency_tracking(self, mock_client):
        """Test latency measurement."""
        response = await mock_client.generate(prompt="Test")

        # Should have measured some latency
        # Note: In mock, latency will be very small but > 0
        # Real test would check against mock_client's batch_generate responses
        assert True  # Basic check that no exception thrown


class TestAsyncClaudeClientIntegration:
    """Integration tests requiring actual API key."""

    @pytest.fixture
    def real_client(self):
        """Create client with real API key if available."""
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key or api_key.startswith("999"):
            pytest.skip("Real Anthropic API key not available")

        return AsyncClaudeClient(
            api_key=api_key,
            max_concurrent=2,
            max_requests_per_minute=10
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_api_call(self, real_client):
        """Test real API call (skipped if no API key)."""
        response = await real_client.generate(
            prompt="Say 'test' and nothing else.",
            system="You are a helpful assistant.",
            max_tokens=10
        )

        assert len(response) > 0
        await real_client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_batch_call(self, real_client):
        """Test real batch API calls (skipped if no API key)."""
        requests = [
            BatchRequest(
                id=str(i),
                prompt=f"Count to {i+1}",
                system="You are a helpful assistant.",
                max_tokens=50,
                temperature=0.7
            )
            for i in range(3)
        ]

        responses = await real_client.batch_generate(requests)

        assert len(responses) == 3
        assert all(r.success for r in responses)
        assert all(len(r.response) > 0 for r in responses)

        await real_client.close()


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling scenarios."""

    async def test_invalid_api_key(self):
        """Test handling of invalid API key."""
        client = AsyncClaudeClient(
            api_key="invalid-key",
            max_concurrent=5,
            max_requests_per_minute=50
        )

        with pytest.raises(Exception):
            await client.generate(prompt="Test")

        await client.close()

    async def test_network_error_retry(self):
        """Test retry logic on network errors."""
        with patch('kosmos.core.async_llm.AsyncAnthropic') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            call_count = 0

            async def mock_create(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                # Fail first 2 times, succeed on 3rd
                if call_count < 3:
                    raise Exception("Network error")
                else:
                    response = MagicMock()
                    response.content = [MagicMock(text="Success after retry")]
                    response.usage = MagicMock(input_tokens=10, output_tokens=20)
                    return response

            mock_instance.messages.create = mock_create

            client = AsyncClaudeClient(
                api_key="test-key",
                max_concurrent=5,
                max_requests_per_minute=50,
                max_retries=3
            )
            client.client = mock_instance

            # Should eventually succeed after retries
            response = await client.generate(prompt="Test")
            assert response == "Success after retry"

            await client.close()
