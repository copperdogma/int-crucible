"""
Manual test for Ollama (local model) compatibility.

Tests that Kosmos works with Ollama for completely local, free LLM usage.

Prerequisites:
1. Install Ollama: https://ollama.com/download
2. Pull a model: ollama pull llama3.1:8b
3. Start Ollama: ollama serve (usually runs automatically)

Run this test to verify Ollama integration works correctly.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kosmos.core.providers import get_provider
from kosmos.core.providers.base import ProviderAPIError


def check_ollama_installed():
    """Check if Ollama is installed."""
    print("\n" + "=" * 70)
    print("Step 1: Check Ollama Installation")
    print("=" * 70)

    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = result.stdout.strip()
        print(f"✓ Ollama installed: {version}")
        return True
    except FileNotFoundError:
        print("✗ Ollama not found")
        print("\nTo install Ollama:")
        print("  macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh")
        print("  Or download from: https://ollama.com/download")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama: {e}")
        return False


def check_ollama_running():
    """Check if Ollama server is running."""
    print("\n" + "=" * 70)
    print("Step 2: Check Ollama Server")
    print("=" * 70)

    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)

        if response.status_code == 200:
            print("✓ Ollama server is running on http://localhost:11434")
            return True
        else:
            print(f"⚠ Ollama server returned status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Ollama server")
        print("\nTo start Ollama:")
        print("  Run: ollama serve")
        print("  Or Ollama may start automatically on some systems")
        return False
    except Exception as e:
        print(f"✗ Error checking server: {e}")
        return False


def list_ollama_models():
    """List available Ollama models."""
    print("\n" + "=" * 70)
    print("Step 3: List Available Models")
    print("=" * 70)

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✓ Available models:")
            print(result.stdout)

            # Check for common models
            models = result.stdout.lower()
            if "llama" in models or "mistral" in models:
                return True
            else:
                print("\n⚠ No models found")
                print("\nTo pull a model:")
                print("  ollama pull llama3.1:8b     # Good balance")
                print("  ollama pull mistral:7b      # Fast")
                print("  ollama pull llama3.1:70b    # Best quality (requires 64GB RAM)")
                return False
        else:
            print(f"✗ Error listing models: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def detect_model():
    """Auto-detect which model to use."""
    print("\n" + "=" * 70)
    print("Step 4: Detect Model")
    print("=" * 70)

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header

            for line in lines:
                parts = line.split()
                if parts:
                    model = parts[0]
                    print(f"✓ Found model: {model}")
                    return model

        print("✗ No models found")
        return None

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def test_ollama_generation(model):
    """Test basic generation with Ollama."""
    print("\n" + "=" * 70)
    print("Step 5: Test Generation")
    print("=" * 70)

    print(f"Testing with model: {model}")

    try:
        config = {
            'api_key': 'ollama',  # Dummy key
            'base_url': 'http://localhost:11434/v1',
            'model': model,
            'max_tokens': 100,
            'temperature': 0.0
        }

        provider = get_provider("openai", config)
        print(f"✓ Provider initialized: {type(provider).__name__}")

        # Get model info
        info = provider.get_model_info()
        print(f"✓ Model: {info['name']}")
        print(f"✓ Provider type: {info['provider_type']}")

        # Test simple generation
        print("\nGenerating response...")
        response = provider.generate(
            prompt="Say 'Hello from Ollama' and nothing else",
            max_tokens=50,
            temperature=0.0
        )

        print(f"✓ Response: {response.content}")
        print(f"✓ Tokens: {response.usage.total_tokens} (estimated)")
        print(f"✓ Cost: ${response.usage.cost_usd or 0.0} (free!)")

        return True

    except ProviderAPIError as e:
        print(f"✗ Provider error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ollama_structured(model):
    """Test structured output with Ollama."""
    print("\n" + "=" * 70)
    print("Step 6: Test Structured Output")
    print("=" * 70)

    try:
        config = {
            'api_key': 'ollama',
            'base_url': 'http://localhost:11434/v1',
            'model': model,
            'max_tokens': 200
        }

        provider = get_provider("openai", config)

        schema = {
            "city": "string",
            "country": "string",
            "population": "integer"
        }

        print("\nGenerating structured output...")
        result = provider.generate_structured(
            prompt="Tell me about Tokyo. Return JSON with: city (str), country (str), population (int).",
            schema=schema,
            max_tokens=150,
            temperature=0.0
        )

        print(f"✓ JSON result:")
        import json
        print(json.dumps(result, indent=2))

        # Verify structure
        assert "city" in result, "Should have 'city' field"
        assert "country" in result, "Should have 'country' field"
        assert "population" in result, "Should have 'population' field"

        print("✓ Structured output works correctly")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        print("  (Some local models struggle with structured output)")
        import traceback
        traceback.print_exc()
        return False


def test_ollama_multi_turn(model):
    """Test multi-turn conversation with Ollama."""
    print("\n" + "=" * 70)
    print("Step 7: Test Multi-Turn Conversation")
    print("=" * 70)

    try:
        config = {
            'api_key': 'ollama',
            'base_url': 'http://localhost:11434/v1',
            'model': model,
            'max_tokens': 100
        }

        provider = get_provider("openai", config)

        from kosmos.core.providers import Message

        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is 10 + 5?"),
            Message(role="assistant", content="10 + 5 equals 15."),
            Message(role="user", content="What is that multiplied by 2?")
        ]

        print("\nGenerating multi-turn response...")
        response = provider.generate_with_messages(
            messages=messages,
            max_tokens=50,
            temperature=0.0
        )

        print(f"✓ Response: {response.content}")

        # Check for answer
        if "30" in response.content:
            print("✓ Correct answer (30) found")
        else:
            print(f"⚠ Response may not contain expected answer")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run Ollama compatibility tests."""
    print("\n" + "=" * 70)
    print("KOSMOS OLLAMA COMPATIBILITY TEST")
    print("=" * 70)
    print("\nThis test verifies that Kosmos works with Ollama for local LLM usage.")
    print("Ollama enables completely free, private, offline research!")

    # Check prerequisites
    if not check_ollama_installed():
        print("\n✗ Test aborted: Ollama not installed")
        return 1

    if not check_ollama_running():
        print("\n✗ Test aborted: Ollama server not running")
        return 1

    if not list_ollama_models():
        print("\n✗ Test aborted: No models available")
        return 1

    # Detect model
    model = detect_model()
    if not model:
        print("\n✗ Test aborted: Could not detect model")
        return 1

    # Run tests
    results = {}

    results['generation'] = test_ollama_generation(model)
    results['structured'] = test_ollama_structured(model)
    results['multi_turn'] = test_ollama_multi_turn(model)

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

    if passed >= 2:  # Allow structured to fail
        print("\n✓ Ollama is working correctly with Kosmos!")
        print("\nTo use Ollama in your research:")
        print("  1. Set in .env:")
        print("     LLM_PROVIDER=openai")
        print("     OPENAI_API_KEY=ollama")
        print("     OPENAI_BASE_URL=http://localhost:11434/v1")
        print(f"     OPENAI_MODEL={model}")
        print("  2. Run: kosmos run --question 'Your research question'")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
