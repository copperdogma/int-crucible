"""
Manual test for provider switching functionality.

Tests that Kosmos can switch between providers (Anthropic/OpenAI) using
environment variable configuration only.

Run this test manually to verify provider switching works.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kosmos.core.providers import get_provider, list_providers
from kosmos.core.providers.base import ProviderAPIError


def test_list_providers():
    """Test that providers are registered."""
    print("\n" + "=" * 70)
    print("TEST: List Available Providers")
    print("=" * 70)

    providers = list_providers()
    print(f"✓ Registered providers: {providers}")

    assert "anthropic" in providers, "Anthropic provider not registered"
    assert "claude" in providers, "Claude alias not registered"
    assert "openai" in providers, "OpenAI provider not registered"

    print("✓ All expected providers are registered")
    return True


def test_anthropic_provider():
    """Test Anthropic provider instantiation."""
    print("\n" + "=" * 70)
    print("TEST: Anthropic Provider")
    print("=" * 70)

    # Check if API key is available
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set - skipping Anthropic test")
        return True

    print(f"API Key: {api_key[:10]}... (truncated)")

    try:
        config = {
            'api_key': api_key,
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 100,
            'temperature': 0.7
        }

        provider = get_provider("anthropic", config)
        print(f"✓ Provider instantiated: {provider}")
        print(f"✓ Provider type: {type(provider).__name__}")

        # Test model info
        info = provider.get_model_info()
        print(f"✓ Model: {info['name']}")
        print(f"✓ Provider: {info['provider']}")
        print(f"✓ Mode: {info.get('mode', 'N/A')}")

        # Test simple generation (if not CLI mode)
        is_cli_mode = api_key.replace('9', '') == ''
        if not is_cli_mode:
            print("\nTesting generation...")
            response = provider.generate(
                prompt="Say 'Hello from Anthropic' and nothing else",
                max_tokens=50,
                temperature=0.0
            )
            print(f"✓ Response: {response.content[:100]}")
            print(f"✓ Input tokens: {response.usage.input_tokens}")
            print(f"✓ Output tokens: {response.usage.output_tokens}")
            if response.usage.cost_usd:
                print(f"✓ Cost: ${response.usage.cost_usd:.6f}")
        else:
            print("⚠ CLI mode detected - skipping generation test")

        return True

    except ProviderAPIError as e:
        print(f"✗ Provider API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_openai_provider():
    """Test OpenAI provider instantiation."""
    print("\n" + "=" * 70)
    print("TEST: OpenAI Provider")
    print("=" * 70)

    # Check if API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("⚠ OPENAI_API_KEY not set - skipping OpenAI test")
        print("  To test OpenAI, set: export OPENAI_API_KEY=sk-...")
        return True

    print(f"API Key: {api_key[:10]}... (truncated)")

    base_url = os.environ.get("OPENAI_BASE_URL")
    if base_url:
        print(f"Base URL: {base_url}")

    try:
        config = {
            'api_key': api_key,
            'model': os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            'max_tokens': 100,
            'temperature': 0.7
        }
        if base_url:
            config['base_url'] = base_url

        provider = get_provider("openai", config)
        print(f"✓ Provider instantiated: {provider}")
        print(f"✓ Provider type: {type(provider).__name__}")

        # Test model info
        info = provider.get_model_info()
        print(f"✓ Model: {info['name']}")
        print(f"✓ Provider: {info['provider']}")
        print(f"✓ Provider type: {info.get('provider_type', 'N/A')}")

        # Test simple generation
        print("\nTesting generation...")
        response = provider.generate(
            prompt="Say 'Hello from OpenAI' and nothing else",
            max_tokens=50,
            temperature=0.0
        )
        print(f"✓ Response: {response.content[:100]}")
        print(f"✓ Input tokens: {response.usage.input_tokens}")
        print(f"✓ Output tokens: {response.usage.output_tokens}")
        if response.usage.cost_usd:
            print(f"✓ Cost: ${response.usage.cost_usd:.6f}")
        else:
            print("  (Cost tracking not available for this provider)")

        return True

    except ProviderAPIError as e:
        print(f"✗ Provider API error: {e}")
        print(f"  This is expected if API key is invalid or quota exceeded")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_from_config():
    """Test provider selection from Kosmos configuration."""
    print("\n" + "=" * 70)
    print("TEST: Provider from Config (Environment Variables)")
    print("=" * 70)

    try:
        from kosmos.config import get_config
        from kosmos.core.providers import get_provider_from_config

        config = get_config()
        print(f"✓ Configuration loaded")
        print(f"✓ LLM Provider: {config.llm_provider}")

        if config.llm_provider == "anthropic":
            print(f"✓ Anthropic model: {config.claude.model}")
        elif config.llm_provider == "openai":
            if config.openai:
                print(f"✓ OpenAI model: {config.openai.model}")
                if config.openai.base_url:
                    print(f"✓ Base URL: {config.openai.base_url}")
            else:
                print("✗ OpenAI config missing")
                return False

        # Get provider from config
        provider = get_provider_from_config(config)
        print(f"✓ Provider instantiated from config: {type(provider).__name__}")

        # Test that it works
        info = provider.get_model_info()
        print(f"✓ Model: {info['name']}")
        print(f"✓ Provider: {info['provider']}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_usage_tracking():
    """Test usage statistics tracking."""
    print("\n" + "=" * 70)
    print("TEST: Usage Statistics Tracking")
    print("=" * 70)

    # Use whichever provider is available
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("⚠ No API key available - skipping usage tracking test")
        return True

    try:
        # Determine provider
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider_name = "anthropic"
            config = {
                'api_key': os.environ.get("ANTHROPIC_API_KEY"),
                'model': 'claude-3-5-haiku-20241022',  # Use cheaper model
                'max_tokens': 50
            }
        else:
            provider_name = "openai"
            config = {
                'api_key': os.environ.get("OPENAI_API_KEY"),
                'model': os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
                'max_tokens': 50
            }
            if os.environ.get("OPENAI_BASE_URL"):
                config['base_url'] = os.environ.get("OPENAI_BASE_URL")

        provider = get_provider(provider_name, config)

        # Reset stats
        provider.reset_usage_stats()
        stats_before = provider.get_usage_stats()
        print(f"✓ Initial stats: {stats_before['total_requests']} requests")

        # Make a request (skip if CLI mode)
        is_cli = provider_name == "anthropic" and config['api_key'].replace('9', '') == ''
        if not is_cli:
            response = provider.generate(
                prompt="Say 'test' and nothing else",
                max_tokens=10,
                temperature=0.0
            )
            print(f"✓ Generated response: {response.content[:50]}")

            # Check stats updated
            stats_after = provider.get_usage_stats()
            print(f"✓ After 1 request:")
            print(f"  - Total requests: {stats_after['total_requests']}")
            print(f"  - Total tokens: {stats_after['total_tokens']}")
            print(f"  - Total cost: ${stats_after['total_cost_usd']:.6f}")

            assert stats_after['total_requests'] > stats_before['total_requests'], \
                "Request count should increase"
            assert stats_after['total_tokens'] > 0, "Should have token usage"
        else:
            print("⚠ CLI mode - skipping generation test")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("KOSMOS MULTI-PROVIDER SWITCHING TEST SUITE")
    print("=" * 70)
    print("\nThis test verifies that provider switching works correctly.")
    print("It will test whichever providers you have configured.\n")

    # Show current configuration
    print("Current Environment:")
    print(f"  ANTHROPIC_API_KEY: {'set' if os.environ.get('ANTHROPIC_API_KEY') else 'not set'}")
    print(f"  OPENAI_API_KEY: {'set' if os.environ.get('OPENAI_API_KEY') else 'not set'}")
    print(f"  LLM_PROVIDER: {os.environ.get('LLM_PROVIDER', 'not set (defaults to anthropic)')}")

    # Run tests
    results = {}

    results['list_providers'] = test_list_providers()
    results['anthropic'] = test_anthropic_provider()
    results['openai'] = test_openai_provider()
    results['from_config'] = test_provider_from_config()
    results['usage_tracking'] = test_usage_tracking()

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
        print("\n✓ All tests passed! Provider switching is working correctly.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. See output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
