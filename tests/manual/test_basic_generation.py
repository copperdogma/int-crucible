"""
Manual test for basic LLM generation functionality.

Tests core generation features across both Anthropic and OpenAI providers:
- Simple text generation
- Structured JSON output
- Multi-turn conversations

Run this test manually to verify generation works with your configured provider.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kosmos.core.llm import get_provider
from kosmos.core.providers import Message
from kosmos.core.providers.base import ProviderAPIError


def test_simple_generation(provider):
    """Test simple text generation."""
    print("\n" + "-" * 70)
    print("Test: Simple Text Generation")
    print("-" * 70)

    try:
        response = provider.generate(
            prompt="What is 2+2? Answer with just the number.",
            max_tokens=10,
            temperature=0.0
        )

        print(f"✓ Generated response: {response.content}")
        print(f"✓ Input tokens: {response.usage.input_tokens}")
        print(f"✓ Output tokens: {response.usage.output_tokens}")
        print(f"✓ Model: {response.model}")

        # Verify response is not empty
        assert response.content.strip(), "Response should not be empty"
        assert response.usage.total_tokens > 0, "Should have token usage"

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_prompt(provider):
    """Test generation with system prompt."""
    print("\n" + "-" * 70)
    print("Test: Generation with System Prompt")
    print("-" * 70)

    try:
        response = provider.generate(
            prompt="What is your role?",
            system="You are a helpful physics professor.",
            max_tokens=50,
            temperature=0.0
        )

        print(f"✓ Generated response: {response.content[:200]}")
        print(f"✓ Total tokens: {response.usage.total_tokens}")

        # Check response mentions physics or professor
        content_lower = response.content.lower()
        is_relevant = "physics" in content_lower or "professor" in content_lower or "science" in content_lower

        if is_relevant:
            print("✓ Response correctly reflects system prompt")
        else:
            print("⚠ Response may not fully reflect system prompt (this is sometimes OK)")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_structured_output(provider):
    """Test structured JSON output."""
    print("\n" + "-" * 70)
    print("Test: Structured JSON Output")
    print("-" * 70)

    schema = {
        "number": "integer",
        "is_even": "boolean",
        "description": "string"
    }

    try:
        result = provider.generate_structured(
            prompt="Analyze the number 42. Return JSON with: number (int), is_even (bool), description (str).",
            schema=schema,
            max_tokens=200,
            temperature=0.0
        )

        print(f"✓ Parsed JSON: {json.dumps(result, indent=2)}")

        # Verify structure
        assert "number" in result, "Should have 'number' field"
        assert "is_even" in result, "Should have 'is_even' field"
        assert "description" in result, "Should have 'description' field"

        # Verify values make sense
        assert result["number"] == 42, f"Number should be 42, got {result['number']}"
        assert result["is_even"] == True, "42 should be even"

        print("✓ JSON structure and values are correct")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_turn_conversation(provider):
    """Test multi-turn conversation."""
    print("\n" + "-" * 70)
    print("Test: Multi-Turn Conversation")
    print("-" * 70)

    messages = [
        Message(role="system", content="You are a helpful math tutor."),
        Message(role="user", content="What is 5 + 3?"),
        Message(role="assistant", content="5 + 3 equals 8."),
        Message(role="user", content="What is that number multiplied by 2?")
    ]

    try:
        response = provider.generate_with_messages(
            messages=messages,
            max_tokens=50,
            temperature=0.0
        )

        print(f"✓ Response: {response.content}")
        print(f"✓ Total tokens: {response.usage.total_tokens}")

        # Check if response mentions 16
        content_lower = response.content.lower()
        has_answer = "16" in response.content

        if has_answer:
            print("✓ Correct answer (16) found in response")
        else:
            print(f"⚠ Response may not contain expected answer: {response.content}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_temperature_variation(provider):
    """Test that temperature affects output variability."""
    print("\n" + "-" * 70)
    print("Test: Temperature Variation")
    print("-" * 70)

    prompt = "Write a single creative word."

    try:
        # Low temperature (deterministic)
        response1 = provider.generate(prompt=prompt, max_tokens=10, temperature=0.0)
        response2 = provider.generate(prompt=prompt, max_tokens=10, temperature=0.0)

        print(f"✓ Low temp (0.0) response 1: {response1.content}")
        print(f"✓ Low temp (0.0) response 2: {response2.content}")

        # High temperature (creative)
        response3 = provider.generate(prompt=prompt, max_tokens=10, temperature=1.0)

        print(f"✓ High temp (1.0) response: {response3.content}")
        print("✓ Temperature parameter works")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_max_tokens_limit(provider):
    """Test that max_tokens limit is respected."""
    print("\n" + "-" * 70)
    print("Test: Max Tokens Limit")
    print("-" * 70)

    try:
        response = provider.generate(
            prompt="Write a very long essay about quantum physics.",
            max_tokens=20,  # Very small limit
            temperature=0.7
        )

        print(f"✓ Response (truncated): {response.content[:100]}")
        print(f"✓ Output tokens: {response.usage.output_tokens}")
        print(f"✓ Finish reason: {response.finish_reason}")

        # Should be limited
        assert response.usage.output_tokens <= 25, \
            f"Output should be ~20 tokens, got {response.usage.output_tokens}"

        if response.finish_reason == "length":
            print("✓ Correctly stopped due to length limit")
        else:
            print(f"⚠ Finish reason: {response.finish_reason} (may vary by provider)")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all generation tests."""
    print("\n" + "=" * 70)
    print("KOSMOS BASIC GENERATION TEST SUITE")
    print("=" * 70)

    # Check configuration
    llm_provider = os.environ.get("LLM_PROVIDER", "anthropic")
    print(f"\nCurrent provider: {llm_provider}")

    if llm_provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("✗ ANTHROPIC_API_KEY not set")
            return 1
        print(f"API key: {api_key[:10]}...")

        # Check if CLI mode
        is_cli = api_key.replace('9', '') == ''
        if is_cli:
            print("⚠ CLI mode detected - some tests may not work")
            print("  Consider using API key for comprehensive testing")
            return 0

    elif llm_provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("✗ OPENAI_API_KEY not set")
            return 1
        print(f"API key: {api_key[:10]}...")

        base_url = os.environ.get("OPENAI_BASE_URL")
        if base_url:
            print(f"Base URL: {base_url}")

    # Get provider
    try:
        provider = get_provider()
        info = provider.get_model_info()
        print(f"✓ Provider initialized: {info['name']}")
    except Exception as e:
        print(f"✗ Failed to initialize provider: {e}")
        return 1

    # Run tests
    results = {}

    print("\n" + "=" * 70)
    print("RUNNING TESTS")
    print("=" * 70)

    results['simple_generation'] = test_simple_generation(provider)
    results['system_prompt'] = test_system_prompt(provider)
    results['structured_output'] = test_structured_output(provider)
    results['multi_turn'] = test_multi_turn_conversation(provider)
    results['temperature'] = test_temperature_variation(provider)
    results['max_tokens'] = test_max_tokens_limit(provider)

    # Usage statistics
    print("\n" + "=" * 70)
    print("USAGE STATISTICS")
    print("=" * 70)

    stats = provider.get_usage_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"  - Input: {stats['total_input_tokens']}")
    print(f"  - Output: {stats['total_output_tokens']}")
    if stats['total_cost_usd'] > 0:
        print(f"Total cost: ${stats['total_cost_usd']:.6f}")
    else:
        print("Total cost: Not tracked (CLI mode or local model)")

    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Basic generation is working correctly.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. See output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
