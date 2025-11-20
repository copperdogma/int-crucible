# Tool Calling Architecture

This document describes the native LLM function calling implementation for the Guidance/Architect agent in Int Crucible.

## Overview

The Guidance/Architect agent uses native LLM function calling (OpenAI functions or Anthropic tool use) to dynamically query the system and provide accurate, real-time guidance. Instead of relying on prompt-based tool descriptions, the agent can:

1. Decide which tools to call based on user queries
2. Automatically invoke tools with correct parameters
3. Receive tool results and continue reasoning
4. Chain multiple tool calls in a single guidance session

## Architecture Components

### 1. Tool Schema Generation (`crucible/core/tools.py`)

Generates tool schemas from Python functions for LLM function calling.

**Key Functions:**
- `generate_tool_schema(func, tool_name=None)`: Generate tool schema from a Python function
- `generate_tool_schemas(tools)`: Generate schemas for multiple tools
- `convert_to_openai_format(schema)`: Convert to OpenAI function calling format
- `convert_to_anthropic_format(schema)`: Convert to Anthropic tool use format

**Features:**
- Automatic type extraction from function signatures (type hints)
- Parameter descriptions from docstrings (`:param param_name:`)
- Optional parameter detection and default values
- JSON schema type conversion (str → string, int → integer, etc.)

**Example:**
```python
def get_problem_spec(project_id: str) -> Optional[Dict[str, Any]]:
    """Get ProblemSpec for a project.
    
    :param project_id: The project ID
    """
    # ... implementation
    pass

schema = generate_tool_schema(get_problem_spec)
# Returns:
# {
#     "name": "get_problem_spec",
#     "description": "Get ProblemSpec for a project.",
#     "input_schema": {
#         "type": "object",
#         "properties": {
#             "project_id": {"type": "string", "description": "The project ID"}
#         },
#         "required": ["project_id"]
#     }
# }
```

### 2. Tool Calling Executor (`crucible/core/tool_calling.py`)

Executes multi-turn tool calling with LLM providers.

**Key Class:**
- `ToolCallingExecutor`: Manages tool execution and LLM interaction

**Features:**
- Multi-turn tool calling loop (agent can call multiple tools in sequence)
- Support for OpenAI function calling (primary) and Anthropic tool use (fallback)
- Tool call validation (allow/deny lists)
- Tool call audit logging
- Parameter validation and error handling
- Max iterations limit to prevent tool call loops

**Example:**
```python
from crucible.core.tool_calling import ToolCallingExecutor
from kosmos.core.llm import get_provider

provider = get_provider()
tools = {
    "get_problem_spec": lambda project_id: {...},
    "get_world_model": lambda project_id: {...},
}

executor = ToolCallingExecutor(
    llm_provider=provider,
    tools=tools,
    max_iterations=10,
    allowed_tools=["get_problem_spec", "get_world_model"]  # Optional allow list
)

response, tool_call_audits = executor.execute_with_tools(
    user_message="What constraints are in my ProblemSpec?",
    system_prompt="You are a helpful assistant.",
    max_tokens=2048,
    temperature=0.7
)
```

### 3. Updated Guidance Agent (`crucible/agents/guidance_agent.py`)

The GuidanceAgent now uses `ToolCallingExecutor` for native function calling.

**Changes:**
- Automatically initializes `ToolCallingExecutor` if tools are provided
- Falls back to prompt-based tool descriptions if function calling unavailable
- Includes tool call audits in result metadata

**Available Tools:**
- `get_workflow_state(project_id)`: Get current workflow state
- `get_problem_spec(project_id)`: Get ProblemSpec with constraints, goals, etc.
- `get_world_model(project_id)`: Get WorldModel with actors, mechanisms, etc.
- `list_runs(project_id)`: List all runs for a project
- `get_chat_history(chat_session_id, limit=10)`: Get recent chat messages

## Tool Call Audit Logging

Each tool call is logged with metadata for provenance and analysis.

**Audit Log Structure:**
```python
{
    "tool_name": "get_problem_spec",
    "arguments": {"project_id": "proj123"},  # Sensitive fields redacted
    "result_summary": '{"constraints": [...], "goals": [...]}',  # Concise summary
    "duration_ms": 42.5,
    "success": true,
    "error": null  # Only present if success is false
}
```

**Metadata Storage:**
- Tool call audits are stored in `message_metadata["tool_call_audits"]` when Architect messages are saved
- This enables full provenance tracking of agent reasoning steps

## Provider Support

### OpenAI (Primary)

**Format:**
- Uses OpenAI's function calling API (`tools` parameter)
- Response includes `tool_calls` in message object
- Tool results sent as `tool` role messages

**Configuration:**
```python
# Set in environment or Kosmos config
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
```

### Anthropic (Fallback)

**Format:**
- Uses Anthropic's tool use API (`tools` parameter)
- Response content includes `tool_use` blocks
- Tool results sent as `tool_result` blocks in user message

**Configuration:**
```python
# Set in environment or Kosmos config
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

## Usage Example

### Basic Usage

```python
from crucible.services.guidance_service import GuidanceService
from crucible.db.session import get_db

db = next(get_db())
service = GuidanceService(db)

result = service.provide_guidance(
    project_id="proj123",
    user_query="What constraints are in my ProblemSpec?",
    chat_session_id="session456"
)

# Result includes:
# - guidance_message: The response text
# - suggested_actions: List of suggested next steps
# - workflow_progress: Current workflow progress
# - tool_call_audits: List of tool calls made (if any)
```

### Multi-Turn Tool Calling

The agent can chain tool calls automatically:

```python
# User asks: "Compare my ProblemSpec constraints with my WorldModel resources"
# Agent automatically:
# 1. Calls get_problem_spec(project_id) → gets constraints
# 2. Calls get_world_model(project_id) → gets resources
# 3. Compares and provides guidance
```

## Adding New Tools

To add a new tool for the Guidance agent:

1. **Define the tool function** in `GuidanceService._create_tools()`:

```python
def get_new_tool(project_id: str, param: Optional[str] = None) -> Dict[str, Any]:
    """Tool: Get new information for a project.
    
    :param project_id: The project ID
    :param param: Optional parameter
    """
    # Implementation here
    return {"data": "result"}
```

2. **Add to tools dict**:

```python
return {
    "get_workflow_state": get_workflow_state_tool,
    # ... other tools ...
    "get_new_tool": get_new_tool,  # Add new tool
}
```

3. **Tool schema is automatically generated** from function signature.

## Security Considerations

### Allow/Deny Lists

Control which tools can be called:

```python
executor = ToolCallingExecutor(
    llm_provider=provider,
    tools=tools,
    allowed_tools=["get_problem_spec", "get_world_model"],  # Only these tools allowed
    denied_tools=["dangerous_tool"]  # Explicitly deny this tool
)
```

### Parameter Validation

- Tool parameters are validated against schema before execution
- Type checking ensures correct parameter types
- Missing required parameters are caught

### Argument Redaction

Sensitive arguments are automatically redacted in audit logs:
- `password`, `api_key`, `secret`, `token`, `key`

Customize redaction by modifying `ToolCallingExecutor._redact_arguments()`.

### Max Iterations

Prevent infinite tool calling loops:

```python
executor = ToolCallingExecutor(
    llm_provider=provider,
    tools=tools,
    max_iterations=10  # Stop after 10 tool calling iterations
)
```

## Error Handling

### Tool Execution Errors

If a tool raises an exception:
- Error is caught and logged
- Tool result includes `success: false` and `error` message
- Agent receives error in tool result and can respond accordingly
- Audit log includes error details

### Provider Errors

If LLM provider doesn't support function calling:
- Falls back to prompt-based tool descriptions
- Agent can still "use" tools conceptually (less accurate)

### Missing Tools

If requested tool doesn't exist:
- Validation error returned
- Agent receives error and can try different approach

## Performance Considerations

### Tool Result Caching

Tool results are not cached by default. Consider adding caching for:
- Expensive tool calls (database queries, API calls)
- Frequently called tools
- Tools that return stable results

### Token Efficiency

- Tool result summaries are truncated to 200 characters in audit logs
- Tool results sent to LLM are JSON-serialized (consider summarization for large results)

### Async Execution

Tool execution is currently synchronous. For parallel tool execution, consider:
- Using `asyncio` for concurrent tool calls
- Batching multiple tool calls when possible

## Testing

### Unit Tests

See:
- `tests/unit/core/test_tools.py`: Tool schema generation tests
- `tests/unit/core/test_tool_calling.py`: Tool calling execution tests

### Integration Tests

Test with real LLM provider:
```python
# Set environment variables for LLM provider
# Run tests that exercise full tool calling flow
```

## Future Enhancements

- [ ] Tool result caching to avoid redundant queries
- [ ] Tool call analytics (which tools are used most, etc.)
- [ ] Dynamic tool discovery (agent can discover available tools)
- [ ] Tool composition (tools that call other tools)
- [ ] Async tool execution for parallel calls
- [ ] Tool result summarization for large results

## References

- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- Anthropic Tool Use: https://docs.anthropic.com/claude/docs/tool-use
- Story 011: `docs/stories/story-011-native-llm-function-calling-for-guidance.md`

