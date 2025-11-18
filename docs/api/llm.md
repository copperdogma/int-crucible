# LLM Provider API Documentation

This document describes the LLM provider interface and how to use it in Kosmos.

## Overview

Kosmos uses a provider-agnostic LLM interface that works with multiple providers (Anthropic, OpenAI, local models, etc.) through a unified API.

## Quick Start

### Using the Default Provider

```python
from kosmos.core.llm import get_provider

# Get provider from configuration
provider = get_provider()

# Generate text
response = provider.generate("Explain quantum entanglement")
print(response.content)
print(f"Tokens: {response.usage.total_tokens}")
print(f"Cost: ${response.usage.cost_usd}")
```

### Using a Specific Provider

```python
from kosmos.core.providers import get_provider

# Anthropic/Claude
config = {
    'api_key': 'sk-ant-...',
    'model': 'claude-3-5-sonnet-20241022',
    'max_tokens': 4096,
    'temperature': 0.7
}
provider = get_provider("anthropic", config)

# OpenAI
config = {
    'api_key': 'sk-...',
    'model': 'gpt-4-turbo',
    'max_tokens': 4096
}
provider = get_provider("openai", config)
```

---

## Core Interface: `LLMProvider`

All providers implement the `LLMProvider` interface with these methods:

### `generate()`

Generate text from a prompt.

```python
def generate(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    stop_sequences: Optional[List[str]] = None,
    **kwargs
) -> LLMResponse
```

**Parameters:**
- `prompt` (str): The user prompt/question
- `system` (str, optional): System prompt for instructions
- `max_tokens` (int): Maximum tokens to generate
- `temperature` (float): Sampling temperature (0.0-1.0 for Anthropic, 0.0-2.0 for OpenAI)
- `stop_sequences` (List[str], optional): Sequences that stop generation
- `**kwargs`: Provider-specific parameters

**Returns:** `LLMResponse` object with:
- `content` (str): Generated text
- `usage` (UsageStats): Token usage and cost
- `model` (str): Model used
- `finish_reason` (str): Why generation stopped
- `raw_response`: Original provider response
- `metadata` (dict): Additional info

**Example:**

```python
response = provider.generate(
    prompt="Write a hypothesis about dark matter",
    system="You are a physics researcher",
    max_tokens=2000,
    temperature=0.7
)

print(response.content)
print(f"Used {response.usage.input_tokens} input tokens")
print(f"Generated {response.usage.output_tokens} output tokens")
if response.usage.cost_usd:
    print(f"Cost: ${response.usage.cost_usd:.4f}")
```

---

### `generate_async()`

Asynchronous version of `generate()`.

```python
async def generate_async(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    stop_sequences: Optional[List[str]] = None,
    **kwargs
) -> LLMResponse
```

**Example:**

```python
import asyncio

async def main():
    provider = get_provider()
    response = await provider.generate_async(
        prompt="Explain neural networks",
        max_tokens=1000
    )
    print(response.content)

asyncio.run(main())
```

---

### `generate_structured()`

Generate structured JSON output matching a schema.

```python
def generate_structured(
    prompt: str,
    schema: Dict[str, Any],
    system: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    **kwargs
) -> Dict[str, Any]
```

**Parameters:**
- `prompt` (str): The user prompt
- `schema` (dict): JSON schema or example structure
- Other parameters same as `generate()`

**Returns:** Parsed JSON dict matching the schema

**Example:**

```python
schema = {
    "hypothesis": "string",
    "confidence": "float (0.0-1.0)",
    "testable": "boolean",
    "required_experiments": ["string"]
}

result = provider.generate_structured(
    prompt="Generate a hypothesis about climate change",
    schema=schema,
    system="You are a climate scientist"
)

print(result["hypothesis"])
print(f"Confidence: {result['confidence']}")
print(f"Testable: {result['testable']}")
print(f"Experiments: {result['required_experiments']}")
```

---

### `generate_with_messages()`

Generate from multi-turn conversation history.

```python
def generate_with_messages(
    messages: List[Message],
    max_tokens: int = 4096,
    temperature: float = 0.7,
    **kwargs
) -> LLMResponse
```

**Parameters:**
- `messages` (List[Message]): Conversation history
- Other parameters same as `generate()`

**Example:**

```python
from kosmos.core.providers import Message

messages = [
    Message(role="system", content="You are a helpful research assistant"),
    Message(role="user", content="What is quantum computing?"),
    Message(role="assistant", content="Quantum computing uses quantum mechanics..."),
    Message(role="user", content="How does it differ from classical computing?")
]

response = provider.generate_with_messages(messages)
print(response.content)
```

---

### `get_model_info()`

Get information about the current model.

```python
def get_model_info() -> Dict[str, Any]
```

**Returns:** Dict with keys:
- `name` (str): Model name
- `max_tokens` (int): Context window size
- `provider` (str): Provider name
- `cost_per_million_input_tokens` (float, optional): Pricing
- `cost_per_million_output_tokens` (float, optional): Pricing

**Example:**

```python
info = provider.get_model_info()
print(f"Model: {info['name']}")
print(f"Max context: {info['max_tokens']} tokens")
if 'cost_per_million_input_tokens' in info:
    print(f"Input cost: ${info['cost_per_million_input_tokens']}/M tokens")
```

---

### `get_usage_stats()`

Get cumulative usage statistics.

```python
def get_usage_stats() -> Dict[str, Any]
```

**Returns:** Dict with usage metrics:
- `provider` (str): Provider name
- `total_requests` (int): Number of API calls
- `total_input_tokens` (int): Total input tokens
- `total_output_tokens` (int): Total output tokens
- `total_tokens` (int): Sum of input + output
- `total_cost_usd` (float): Cumulative cost

**Example:**

```python
# After several API calls
stats = provider.get_usage_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Total cost: ${stats['total_cost_usd']:.2f}")
```

---

### `reset_usage_stats()`

Reset usage statistics to zero.

```python
def reset_usage_stats()
```

**Example:**

```python
provider.reset_usage_stats()
print("Usage stats reset")
```

---

## Data Types

### `LLMResponse`

Response object from generation methods.

```python
@dataclass
class LLMResponse:
    content: str                    # Generated text
    usage: UsageStats              # Token usage
    model: str                     # Model name
    finish_reason: Optional[str]   # Why generation stopped
    raw_response: Optional[Any]    # Original response
    metadata: Optional[Dict]       # Additional data
```

### `UsageStats`

Token usage and cost information.

```python
@dataclass
class UsageStats:
    input_tokens: int              # Prompt tokens
    output_tokens: int             # Generated tokens
    total_tokens: int              # Sum of both
    cost_usd: Optional[float]      # Cost in USD (if available)
    model: Optional[str]           # Model used
    provider: Optional[str]        # Provider name
    timestamp: Optional[datetime]  # When request was made
```

### `Message`

Message in a conversation.

```python
@dataclass
class Message:
    role: str                      # "system", "user", or "assistant"
    content: str                   # Message text
    name: Optional[str]            # Sender name (optional)
    metadata: Optional[Dict]       # Additional data (optional)
```

### `ProviderAPIError`

Exception raised on API errors.

```python
class ProviderAPIError(Exception):
    provider: str                  # Provider name
    message: str                   # Error message
    status_code: Optional[int]     # HTTP status code (if applicable)
    raw_error: Optional[Exception] # Original error
```

---

## Provider-Specific Features

### Anthropic Provider

**Special kwargs for `generate()`:**
- `bypass_cache` (bool): Skip response cache
- `model_override` (str): Override model selection

**Example:**

```python
response = provider.generate(
    prompt="Complex analysis task",
    model_override="claude-3-opus-20240229",  # Use Opus instead of Sonnet
    bypass_cache=True  # Force fresh generation
)
```

**CLI Mode:**

Set `ANTHROPIC_API_KEY=999...` (all 9s) to route to Claude Code CLI.

### OpenAI Provider

**Automatic provider detection:**
- Official OpenAI: No `base_url` or `base_url` contains `openai.com`
- Ollama: `base_url` contains `localhost` or `ollama`
- OpenRouter: `base_url` contains `openrouter`
- Others: Generic OpenAI-compatible

**Token estimation:**

Local models without usage stats get token estimates:

```python
# For Ollama, cost_usd will be None or 0.0
response = provider.generate("Test")
print(response.usage.input_tokens)  # Estimated
print(response.usage.cost_usd)      # None or 0.0
```

---

## Advanced Usage

### Custom Provider Configuration

```python
from kosmos.core.providers import get_provider

# Anthropic with custom settings
provider = get_provider("anthropic", {
    'api_key': 'sk-ant-...',
    'model': 'claude-3-5-sonnet-20241022',
    'max_tokens': 8000,
    'temperature': 0.8,
    'enable_cache': True,
    'enable_auto_model_selection': True  # Auto-select Haiku/Sonnet
})

# OpenAI with custom base URL
provider = get_provider("openai", {
    'api_key': 'ollama',
    'base_url': 'http://localhost:11434/v1',
    'model': 'llama3.1:70b',
    'max_tokens': 4096
})
```

### Using Multiple Providers

```python
# Use different providers for different tasks
claude = get_provider("anthropic", {...})
gpt = get_provider("openai", {...})

# Complex reasoning with Claude
hypothesis = claude.generate_structured(
    prompt="Generate research hypotheses",
    schema=hypothesis_schema
)

# Fast extraction with GPT-3.5
summary = gpt.generate(
    prompt="Summarize this paper",
    max_tokens=500
)
```

### Error Handling

```python
from kosmos.core.providers import ProviderAPIError

try:
    response = provider.generate("Your prompt")
except ProviderAPIError as e:
    print(f"Provider error: {e.provider}")
    print(f"Message: {e.message}")
    if e.status_code:
        print(f"HTTP status: {e.status_code}")
    print(f"Original error: {e.raw_error}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Backward Compatibility

### Legacy `ClaudeClient`

The old `ClaudeClient` class still works:

```python
from kosmos.core.llm import ClaudeClient

# Old way - still works
client = ClaudeClient()
text = client.generate("Your prompt")

# Note: Returns str, not LLMResponse
```

### Legacy `get_client()`

```python
from kosmos.core.llm import get_client

# Gets provider from config
client = get_client()

# If provider is Anthropic, client is AnthropicProvider
# (which inherits from LLMProvider)
response = client.generate("Your prompt")

# If you need the old behavior:
client = get_client(use_provider_system=False)
# Returns ClaudeClient regardless of config
```

---

## Best Practices

### 1. Use the Provider Interface

```python
# Good: Provider-agnostic
from kosmos.core.llm import get_provider
provider = get_provider()

# Avoid: Provider-specific
from kosmos.core.llm import ClaudeClient
client = ClaudeClient()
```

### 2. Handle Errors

Always catch `ProviderAPIError` for graceful degradation.

### 3. Monitor Usage

```python
# Check usage periodically
stats = provider.get_usage_stats()
if stats['total_cost_usd'] > budget_limit:
    print("Warning: Approaching budget limit")
```

### 4. Use Structured Output

For JSON responses, always use `generate_structured()`:

```python
# Good: Validates JSON
data = provider.generate_structured(prompt, schema)

# Avoid: Manual JSON parsing
text = provider.generate(prompt)
data = json.loads(text)  # Can fail
```

### 5. System Prompts

Always use system prompts for instructions:

```python
# Good
response = provider.generate(
    prompt="Your question",
    system="You are a scientific researcher specializing in physics"
)

# Less effective
response = provider.generate(
    prompt="You are a researcher. Your question here..."
)
```

---

## See Also

- [Provider Setup Guide](../providers/README.md) - Detailed setup for each provider
- [Migration Guide](../MIGRATION_MULTI_PROVIDER.md) - Upgrading from v0.1.x
- [GitHub Issue #3](https://github.com/jimmc414/Kosmos/issues/3) - Multi-provider feature discussion
