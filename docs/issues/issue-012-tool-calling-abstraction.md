# Issue 012: Tool calling executor has leaky provider abstraction

**Status**: Open
**Priority**: Medium
**Category**: Architecture
**Discovered**: 2025-11-24
**Related Story**: (TBD)

## Description
The `ToolCallingExecutor` in `crucible/core/tool_calling.py` has provider-specific logic scattered throughout, making it difficult to add new LLM providers and creating brittle code that breaks when provider APIs change.

## Current Behavior

### Provider Logic Scattered Everywhere
```python
# crucible/core/tool_calling.py (763 lines)

# Lines 298-314: Provider branching in main loop
if self.provider_name == 'openai':
    response, tool_calls = self._call_openai_with_tools(...)
elif self.provider_name == 'anthropic':
    response, tool_calls = self._call_anthropic_with_tools(...)

# Lines 358-490: Anthropic-specific implementation (132 lines)
def _call_anthropic_with_tools(...):
    # Anthropic-specific message formatting
    # Anthropic-specific tool schema conversion
    # Anthropic-specific response parsing

# Lines 492-642: OpenAI-specific implementation (150 lines)
def _call_openai_with_tools(...):
    # OpenAI-specific message formatting
    # OpenAI-specific tool schema conversion
    # OpenAI-specific response parsing

# Lines 666-678: OpenAI-specific message formatting
def _format_tool_result_message_openai(...):
    # OpenAI format only

# Lines 732-761: Anthropic-specific message formatting
def _format_tool_results_message(...):
    # Anthropic format only
```

### Problems

1. **Adding new providers is hard**: Must modify executor core
2. **Provider coupling**: Business logic mixed with provider details
3. **Testing complexity**: Must mock multiple provider formats
4. **Brittle**: Provider API changes require deep modifications

## Impact

### Extensibility
```python
# Want to add OpenRouter? Must modify executor:
def execute_with_tools(...):
    if self.provider_name == 'openai':
        ...
    elif self.provider_name == 'anthropic':
        ...
    elif self.provider_name == 'openrouter':  # ❌ Modify core!
        response, tool_calls = self._call_openrouter_with_tools(...)
    elif self.provider_name == 'mistral':     # ❌ More modifications!
        response, tool_calls = self._call_mistral_with_tools(...)
```

### Maintainability
```python
# Anthropic changes message format?
# Must modify multiple methods:
def _call_anthropic_with_tools(...):
    # ❌ Update here

def _format_tool_results_message(...):
    # ❌ And here

def _format_assistant_message_with_tool_calls(...):
    # ❌ And here
```

## Investigation Notes

### Code Analysis

**Provider-Specific Code Distribution:**
- OpenAI-specific: ~250 lines (33%)
- Anthropic-specific: ~230 lines (30%)
- Provider-agnostic: ~280 lines (37%)

**Abstraction Violations:**
- Message formatting differs per provider
- Tool schema conversion differs per provider
- Response parsing differs per provider
- Tool result formatting differs per provider

### Root Cause
System was built with two providers (OpenAI, Anthropic) and used if/else branching rather than strategy pattern. This works for 2 providers but doesn't scale to N providers.

## Proposed Solution

### Strategy Pattern with Provider Adapters

```python
# crucible/core/tool_calling/providers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class ToolCall:
    """Represents a tool call request."""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None

@dataclass
class ProviderResponse:
    """Standardized provider response."""
    content: str
    tool_calls: List[ToolCall]
    raw_response: Any
    usage: Optional[Dict[str, Any]] = None

class ToolCallProvider(ABC):
    """Base class for tool calling providers."""

    @abstractmethod
    def call_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> ProviderResponse:
        """
        Call LLM with tools.

        Each provider implements this method to handle:
        - Converting tool schemas to provider format
        - Converting messages to provider format
        - Calling provider API
        - Parsing response into standard format
        """
        pass

    @abstractmethod
    def format_tool_results(
        self,
        tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format tool results as message for next turn."""
        pass

    @abstractmethod
    def format_assistant_message(
        self,
        tool_calls: List[ToolCall],
        response: Any
    ) -> Dict[str, Any]:
        """Format assistant message with tool calls."""
        pass

# crucible/core/tool_calling/providers/anthropic.py
class AnthropicToolProvider(ToolCallProvider):
    """Anthropic-specific tool calling implementation."""

    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.client = self._get_client()

    def _get_client(self):
        """Get Anthropic client."""
        if hasattr(self.llm_provider, 'client'):
            return self.llm_provider.client

        from anthropic import Anthropic
        import os
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        return Anthropic(api_key=api_key)

    def call_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> ProviderResponse:
        """Call Anthropic with tools."""
        # Convert tools to Anthropic format
        anthropic_tools = [self._convert_tool_schema(t) for t in tools]

        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)

        # Get model
        model = getattr(self.llm_provider, 'model', 'claude-3-5-sonnet-20241022')

        # Call API
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=anthropic_messages,
            tools=anthropic_tools
        )

        # Parse response into standard format
        return self._parse_response(response)

    def format_tool_results(
        self,
        tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format tool results as Anthropic user message."""
        content = []
        for tr in tool_results:
            tool_call_id = tr.get("tool_call_id", f"call_{len(content)}")

            if "error" in tr:
                content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "is_error": True,
                    "content": tr["error"]
                })
            else:
                result_str = json.dumps(tr.get("result", {}), default=str)
                content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": result_str
                })

        return {"role": "user", "content": content}

    def format_assistant_message(
        self,
        tool_calls: List[ToolCall],
        response: Any
    ) -> Dict[str, Any]:
        """Format assistant message with tool calls (Anthropic format)."""
        # Anthropic-specific formatting
        content = []
        if hasattr(response, 'content'):
            for block in response.content:
                if block.type == "text":
                    content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })

        return {"role": "assistant", "content": content}

    def _convert_tool_schema(self, schema: Dict) -> Dict:
        """Convert generic schema to Anthropic format."""
        # ... conversion logic ...

    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """Convert generic messages to Anthropic format."""
        # ... conversion logic ...

    def _parse_response(self, response) -> ProviderResponse:
        """Parse Anthropic response into standard format."""
        tool_calls = []
        text_content = ""

        if hasattr(response, 'content'):
            for block in response.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        tool_name=block.name,
                        arguments=block.input,
                        call_id=block.id
                    ))

        return ProviderResponse(
            content=text_content,
            tool_calls=tool_calls,
            raw_response=response,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        )

# crucible/core/tool_calling/providers/openai.py
class OpenAIToolProvider(ToolCallProvider):
    """OpenAI-specific tool calling implementation."""

    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.client = self._get_client()

    def call_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> ProviderResponse:
        """Call OpenAI with tools."""
        # OpenAI-specific implementation
        # ... (similar structure to Anthropic but different details)

    def format_tool_results(
        self,
        tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format tool results as OpenAI tool messages."""
        # OpenAI uses separate tool role messages
        # Return list of messages, not single message
        messages = []
        for tr in tool_results:
            tool_call_id = tr.get("tool_call_id", "unknown")
            if "error" in tr:
                content = json.dumps({"error": tr["error"]}, default=str)
            else:
                content = json.dumps(tr.get("result", {}), default=str)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": content
            })

        return {"role": "tool", "messages": messages}  # Special format

    # ... other OpenAI-specific methods

# crucible/core/tool_calling/executor.py (simplified)
class ToolCallingExecutor:
    """Executes tool calls with LLM providers (provider-agnostic)."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        tools: Dict[str, Callable],
        max_iterations: int = 10,
        allowed_tools: Optional[List[str]] = None,
        denied_tools: Optional[List[str]] = None
    ):
        self.llm_provider = llm_provider
        self.tools = tools
        self.max_iterations = max_iterations
        self.allowed_tools = set(allowed_tools) if allowed_tools else None
        self.denied_tools = set(denied_tools) if denied_tools else None

        # Generate tool schemas (provider-agnostic)
        self.tool_schemas = generate_tool_schemas(tools)

        # Create provider adapter (factory pattern)
        self.provider = self._create_provider_adapter()

    def _create_provider_adapter(self) -> ToolCallProvider:
        """Factory method to create appropriate provider adapter."""
        provider_name = self._detect_provider_type()

        if provider_name == 'openai':
            from crucible.core.tool_calling.providers.openai import OpenAIToolProvider
            return OpenAIToolProvider(self.llm_provider)
        elif provider_name == 'anthropic':
            from crucible.core.tool_calling.providers.anthropic import AnthropicToolProvider
            return AnthropicToolProvider(self.llm_provider)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

    def execute_with_tools(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, List[ToolCallAudit]]:
        """Execute LLM generation with tool calling (provider-agnostic)."""
        messages = conversation_history or []
        messages.append({"role": "user", "content": user_message})

        audit_logs: List[ToolCallAudit] = []

        # Multi-turn tool calling loop (now provider-agnostic!)
        for iteration in range(self.max_iterations):
            try:
                # Call provider (delegated to adapter)
                response = self.provider.call_with_tools(
                    messages=messages,
                    tools=self.tool_schemas,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                # If no tool calls, we're done
                if not response.tool_calls:
                    return response.content, audit_logs

                # Execute tool calls (provider-agnostic)
                tool_results = []
                for tool_call in response.tool_calls:
                    tool_result = self._execute_tool(tool_call)
                    audit_log = self._create_audit_log(tool_call, tool_result)
                    audit_logs.append(audit_log)

                    formatted_result = self._format_tool_result(tool_call, tool_result)
                    formatted_result["tool_call_id"] = tool_call.call_id
                    tool_results.append(formatted_result)

                # Add assistant message (provider-specific formatting)
                assistant_msg = self.provider.format_assistant_message(
                    response.tool_calls,
                    response.raw_response
                )
                messages.append(assistant_msg)

                # Add tool results (provider-specific formatting)
                tool_msg = self.provider.format_tool_results(tool_results)
                messages.append(tool_msg)

                logger.debug(f"Tool calling iteration {iteration + 1}: executed {len(response.tool_calls)} tools")

            except Exception as e:
                logger.error(f"Error in tool calling iteration {iteration + 1}: {e}", exc_info=True)
                return f"Error during tool execution: {str(e)}", audit_logs

        # Max iterations reached
        logger.warning(f"Max tool calling iterations ({self.max_iterations}) reached")
        return "Max iterations reached", audit_logs
```

## Benefits

### Before (Current)
- **763 lines** in single file
- **If/else branching** for providers
- **Must modify executor** to add providers
- **Provider logic scattered** across 8+ methods
- **Hard to test** provider-specific logic

### After (Refactored)
- **~300 lines** in executor (60% reduction)
- **Strategy pattern** with adapters
- **Add providers** by implementing interface
- **Provider logic isolated** in adapter classes
- **Easy to test** - mock adapters

### Adding New Provider

**Before:**
```python
# Must modify ToolCallingExecutor in 8+ places
def execute_with_tools(...):
    if provider == 'openai': ...
    elif provider == 'anthropic': ...
    elif provider == 'mistral':  # ❌ Add here
        ...
```

**After:**
```python
# Just implement interface
class MistralToolProvider(ToolCallProvider):
    def call_with_tools(...): ...
    def format_tool_results(...): ...
    def format_assistant_message(...): ...

# Register in factory
def _create_provider_adapter(self):
    if provider_name == 'mistral':
        return MistralToolProvider(self.llm_provider)
```

## Implementation Plan

### Phase 1: Create Provider Abstraction (3 hours)
1. Create `crucible/core/tool_calling/providers/` directory
2. Create `base.py` with `ToolCallProvider` interface
3. Define `ProviderResponse` dataclass

### Phase 2: Extract Anthropic Provider (3 hours)
1. Create `anthropic.py` with `AnthropicToolProvider`
2. Move Anthropic-specific logic from executor
3. Test Anthropic provider in isolation

### Phase 3: Extract OpenAI Provider (3 hours)
1. Create `openai.py` with `OpenAIToolProvider`
2. Move OpenAI-specific logic from executor
3. Test OpenAI provider in isolation

### Phase 4: Simplify Executor (2 hours)
1. Refactor `ToolCallingExecutor` to use adapters
2. Remove provider-specific branching
3. Add provider factory

### Phase 5: Testing (2-3 hours)
1. Update unit tests to use mocked providers
2. Add integration tests for each provider
3. Verify backward compatibility

### Total Effort: 13-14 hours

## Testing Strategy

```python
# Test providers in isolation
def test_anthropic_provider():
    """Test Anthropic provider."""
    provider = AnthropicToolProvider(mock_llm_provider)
    response = provider.call_with_tools(
        messages=[{"role": "user", "content": "test"}],
        tools=[...],
        ...
    )
    assert isinstance(response, ProviderResponse)
    assert response.content

# Test executor with mocked provider
def test_executor_with_mock_provider():
    """Test executor delegates to provider."""
    mock_provider = Mock(spec=ToolCallProvider)
    executor = ToolCallingExecutor(...)
    executor.provider = mock_provider

    executor.execute_with_tools(...)

    mock_provider.call_with_tools.assert_called_once()
```

## Risk Assessment
- **Low risk**: Pure refactor, encapsulates existing logic
- **Testing**: Thorough testing of adapters
- **Rollback**: Can keep old code as fallback

## Estimated Impact
- **Extensibility**: Easy to add new providers (OpenRouter, Mistral, etc.)
- **Maintainability**: Provider changes isolated to adapter
- **Testing**: Much easier to test providers in isolation
- **Code quality**: 60% reduction in executor complexity

## Related Issues
- None directly, but improves system extensibility

## Notes
- This is **#5 priority** for extensibility
- Can be done after higher-priority issues
- Synergizes well with multi-provider support goals
- Consider adding provider registry for dynamic provider loading
