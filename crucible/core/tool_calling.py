"""
Tool Calling Execution Loop.

Handles multi-turn tool calling with LLM providers.
Supports both Anthropic tool use and OpenAI function calling.
"""

import json
import logging
import time
from typing import Dict, Any, List, Callable, Optional, Tuple
from dataclasses import dataclass

from kosmos.core.providers.base import LLMProvider, LLMResponse
from crucible.core.tools import generate_tool_schemas, convert_to_anthropic_format, convert_to_openai_format

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a tool call request."""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None  # For Anthropic tool use


@dataclass
class ToolResult:
    """Represents the result of a tool call."""
    tool_name: str
    result: Any
    success: bool = True
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class ToolCallAudit:
    """Audit log entry for a tool call."""
    tool_name: str
    arguments: Dict[str, Any]  # May be redacted
    result_summary: str  # Concise summary
    duration_ms: float
    success: bool
    error: Optional[str] = None


class ToolCallingExecutor:
    """
    Executes tool calls with LLM providers.
    
    Supports multi-turn tool calling where the LLM can:
    1. Request tool calls
    2. Receive tool results
    3. Continue reasoning and potentially make more tool calls
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        tools: Dict[str, Callable],
        max_iterations: int = 10,
        allowed_tools: Optional[List[str]] = None,
        denied_tools: Optional[List[str]] = None
    ):
        """
        Initialize tool calling executor.
        
        Args:
            llm_provider: LLM provider instance
            tools: Dict mapping tool names to callable functions
            max_iterations: Maximum number of tool calling iterations
            allowed_tools: Optional whitelist of allowed tool names (None = all allowed)
            denied_tools: Optional blacklist of denied tool names
        """
        self.llm_provider = llm_provider
        self.tools = tools
        self.max_iterations = max_iterations
        self.allowed_tools = set(allowed_tools) if allowed_tools else None
        self.denied_tools = set(denied_tools) if denied_tools else None
        
        # Generate tool schemas
        self.tool_schemas = generate_tool_schemas(tools)
        
        # Detect provider type
        self.provider_name = self._detect_provider_type()
        logger.info(f"ToolCallingExecutor initialized with {len(tools)} tools for {self.provider_name} provider")
    
    def _detect_provider_type(self) -> str:
        """
        Detect the LLM provider type.
        
        Checks both class name and provider_name attribute for accurate detection.
        """
        # Check provider_name attribute first (most reliable)
        if hasattr(self.llm_provider, 'provider_name'):
            provider_name = self.llm_provider.provider_name.lower()
            if provider_name in ('anthropic', 'openai'):
                return provider_name
        
        # Fall back to class name detection
        class_name = self.llm_provider.__class__.__name__.lower()
        if 'anthropic' in class_name or 'claude' in class_name:
            return 'anthropic'
        elif 'openai' in class_name:
            return 'openai'
        else:
            # Default to OpenAI if unknown (since that's what the user is using)
            logger.warning(f"Unknown provider type for {class_name}, defaulting to OpenAI")
            return 'openai'
    
    def _validate_tool_call(self, tool_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a tool can be called.
        
        Args:
            tool_name: Name of the tool to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if tool exists
        if tool_name not in self.tools:
            return False, f"Tool '{tool_name}' not found"
        
        # Check allow/deny lists
        if self.denied_tools and tool_name in self.denied_tools:
            return False, f"Tool '{tool_name}' is denied"
        
        if self.allowed_tools and tool_name not in self.allowed_tools:
            return False, f"Tool '{tool_name}' is not in allowed list"
        
        return True, None
    
    def _execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a single tool call.
        
        Args:
            tool_call: Tool call request
            
        Returns:
            ToolResult with execution result
        """
        start_time = time.time()
        
        # Validate tool call
        is_valid, error = self._validate_tool_call(tool_call.tool_name)
        if not is_valid:
            return ToolResult(
                tool_name=tool_call.tool_name,
                result=None,
                success=False,
                error=error,
                duration_ms=(time.time() - start_time) * 1000
            )
        
        # Execute tool
        try:
            tool_func = self.tools[tool_call.tool_name]
            result = tool_func(**tool_call.arguments)
            duration_ms = (time.time() - start_time) * 1000
            
            return ToolResult(
                tool_name=tool_call.tool_name,
                result=result,
                success=True,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Tool execution failed for {tool_call.tool_name}: {e}", exc_info=True)
            return ToolResult(
                tool_name=tool_call.tool_name,
                result=None,
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )
    
    def _create_audit_log(self, tool_call: ToolCall, tool_result: ToolResult) -> ToolCallAudit:
        """
        Create audit log entry for a tool call.
        
        Args:
            tool_call: Original tool call request
            tool_result: Tool execution result
            
        Returns:
            ToolCallAudit entry
        """
        # Create concise result summary
        result_summary = self._summarize_result(tool_result.result) if tool_result.success else f"Error: {tool_result.error}"
        
        # Redact sensitive arguments if needed (simplified - can be enhanced)
        arguments = self._redact_arguments(tool_call.arguments)
        
        return ToolCallAudit(
            tool_name=tool_call.tool_name,
            arguments=arguments,
            result_summary=result_summary,
            duration_ms=tool_result.duration_ms,
            success=tool_result.success,
            error=tool_result.error if not tool_result.success else None
        )
    
    def _summarize_result(self, result: Any) -> str:
        """Create a concise summary of tool result for audit log."""
        if result is None:
            return "null"
        
        if isinstance(result, str):
            # Truncate long strings
            return result[:200] + "..." if len(result) > 200 else result
        
        if isinstance(result, (dict, list)):
            # Convert to JSON string and truncate
            json_str = json.dumps(result, default=str)
            return json_str[:200] + "..." if len(json_str) > 200 else json_str
        
        # For other types, convert to string
        result_str = str(result)
        return result_str[:200] + "..." if len(result_str) > 200 else result_str
    
    def _redact_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive arguments from audit log.
        
        Args:
            arguments: Original arguments dict
            
        Returns:
            Redacted arguments dict
        """
        # Sensitive field names (can be enhanced with config)
        sensitive_fields = {'password', 'api_key', 'secret', 'token', 'key'}
        
        redacted = {}
        for key, value in arguments.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = value
        
        return redacted
    
    def execute_with_tools(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, List[ToolCallAudit]]:
        """
        Execute LLM generation with tool calling support.
        
        This method handles multi-turn tool calling:
        1. Send user message to LLM with available tools
        2. If LLM requests tool calls, execute them
        3. Send tool results back to LLM
        4. Continue until LLM provides final response
        
        Args:
            user_message: User's message/query
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            conversation_history: Optional previous conversation messages
            
        Returns:
            Tuple of (final_response_text, list_of_tool_call_audits)
        """
        if not self.tool_schemas:
            # No tools available, fall back to regular generation
            logger.warning("No tools available, falling back to regular generation")
            response = self.llm_provider.generate(
                user_message,
                system=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.content, []
        
        # Build conversation messages
        messages = conversation_history or []
        messages.append({"role": "user", "content": user_message})
        
        audit_logs: List[ToolCallAudit] = []
        
        # Multi-turn tool calling loop
        for iteration in range(self.max_iterations):
            try:
                # Call LLM with tools
                # Prioritize OpenAI since that's the primary provider
                if self.provider_name == 'openai':
                    response, tool_calls = self._call_openai_with_tools(
                        messages, system_prompt, max_tokens, temperature
                    )
                elif self.provider_name == 'anthropic':
                    response, tool_calls = self._call_anthropic_with_tools(
                        messages, system_prompt, max_tokens, temperature
                    )
                else:
                    # Unknown provider - fall back to regular generation
                    logger.warning(f"Provider {self.provider_name} doesn't support tool calling, falling back to regular generation")
                    response = self.llm_provider.generate(
                        "\n".join([msg.get("content", "") if isinstance(msg.get("content"), str) else str(msg.get("content", "")) for msg in messages]),
                        system=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    return response.content, audit_logs
                
                # If no tool calls, we're done
                if not tool_calls:
                    # Extract final response text
                    final_text = self._extract_response_text(response)
                    return final_text, audit_logs
                
                # Execute tool calls
                tool_results = []
                for tool_call in tool_calls:
                    tool_result = self._execute_tool(tool_call)
                    audit_log = self._create_audit_log(tool_call, tool_result)
                    audit_logs.append(audit_log)
                    
                    # Format tool result for LLM (include call_id for matching)
                    formatted_result = self._format_tool_result(tool_call, tool_result)
                    formatted_result["tool_call_id"] = tool_call.call_id
                    tool_results.append(formatted_result)
                
                # Add assistant message with tool calls
                messages.append(self._format_assistant_message_with_tool_calls(tool_calls, response))
                
                # Add tool results (provider-specific format)
                if self.provider_name == 'openai':
                    # OpenAI expects separate tool role messages
                    for tool_result in tool_results:
                        messages.append(self._format_tool_result_message_openai(tool_result))
                else:
                    # Anthropic uses a single user message with tool_result blocks
                    messages.append(self._format_tool_results_message(tool_results))
                
                logger.debug(f"Tool calling iteration {iteration + 1}: executed {len(tool_calls)} tools")
                
            except Exception as e:
                logger.error(f"Error in tool calling iteration {iteration + 1}: {e}", exc_info=True)
                # Return what we have so far
                return f"Error during tool execution: {str(e)}", audit_logs
        
        # Max iterations reached
        logger.warning(f"Max tool calling iterations ({self.max_iterations}) reached")
        final_text = self._extract_response_text(response) if 'response' in locals() else "Max iterations reached"
        return final_text, audit_logs
    
    def _call_anthropic_with_tools(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Tuple[Any, List[ToolCall]]:
        """
        Call Anthropic API with tools.
        
        Anthropic tool use format:
        - tools parameter: list of tool definitions
        - Response content can contain tool_use blocks
        - We need to execute tools and send results back
        """
        try:
            from anthropic import Anthropic
            import os
            
            # Get the client from the provider if available
            if hasattr(self.llm_provider, 'client'):
                client = self.llm_provider.client
            else:
                # Create new client
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found")
                client = Anthropic(api_key=api_key)
            
            # Convert tool schemas to Anthropic format
            anthropic_tools = [convert_to_anthropic_format(schema) for schema in self.tool_schemas]
            
            # Convert messages to Anthropic format (handle tool_use blocks)
            anthropic_messages = []
            for msg in messages:
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    # Handle assistant message with tool calls
                    # Anthropic uses tool_use blocks in content
                    content = []
                    if msg.get("content"):
                        content.append({"type": "text", "text": msg["content"]})
                    
                    for tc in msg["tool_calls"]:
                        content.append({
                            "type": "tool_use",
                            "id": tc.get("id", f"call_{len(anthropic_messages)}"),
                            "name": tc["name"],
                            "input": tc["arguments"]
                        })
                    anthropic_messages.append({"role": "assistant", "content": content})
                elif msg.get("role") == "user" and isinstance(msg.get("content"), dict):
                    # Handle tool results as user message
                    tool_results = msg["content"].get("tool_results", [])
                    content = []
                    for tr in tool_results:
                        tool_use_id = tr.get("id", f"result_{len(content)}")
                        if "result" in tr:
                            content.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps(tr["result"], default=str)
                            })
                        elif "error" in tr:
                            content.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "is_error": True,
                                "content": tr["error"]
                            })
                    anthropic_messages.append({"role": "user", "content": content})
                else:
                    # Regular message
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg.get("content", "")
                    })
            
            # Get model from provider
            model = getattr(self.llm_provider, 'model', 'claude-3-5-sonnet-20241022')
            
            # Call API with tools
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=anthropic_messages,
                tools=anthropic_tools
            )
            
            # Extract tool calls from response
            tool_calls = []
            text_content = ""
            
            # Anthropic response content is a list of content blocks
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
            
            # Create LLMResponse-like object
            from kosmos.core.providers.base import LLMResponse, UsageStats
            from datetime import datetime
            
            usage = UsageStats(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                cost_usd=None,  # Cost calculation can be added if needed
                model=model,
                provider="anthropic",
                timestamp=datetime.now()
            )
            
            llm_response = LLMResponse(
                content=text_content,
                usage=usage,
                model=model,
                finish_reason=getattr(response, 'stop_reason', 'stop'),
                raw_response=response
            )
            
            return llm_response, tool_calls
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API with tools: {e}", exc_info=True)
            raise
    
    def _call_openai_with_tools(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Tuple[Any, List[ToolCall]]:
        """
        Call OpenAI API with tools.
        
        OpenAI function calling format:
        - tools parameter: list of tool definitions
        - Response can contain tool_calls in choices
        - We need to execute tools and send results back
        """
        try:
            from openai import OpenAI
            import os
            
            # Get the client from the provider if available
            if hasattr(self.llm_provider, 'client'):
                client = self.llm_provider.client
            else:
                # Create new client
                api_key = os.environ.get('OPENAI_API_KEY')
                base_url = getattr(self.llm_provider, 'base_url', None)
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found")
                client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            
            # Convert tool schemas to OpenAI format
            openai_tools = [convert_to_openai_format(schema) for schema in self.tool_schemas]
            
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in messages:
                role = msg.get("role")
                if role == "system":
                    # System messages are handled separately in OpenAI
                    continue
                elif role == "assistant" and msg.get("tool_calls"):
                    # Assistant message with tool calls
                    message = {
                        "role": "assistant",
                        "content": msg.get("content") or None,
                        "tool_calls": [
                            {
                                "id": tc.get("id", f"call_{i}"),
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["arguments"])
                                }
                            }
                            for i, tc in enumerate(msg.get("tool_calls", []))
                        ]
                    }
                    openai_messages.append(message)
                elif role == "tool":
                    # Tool result message
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": msg.get("tool_call_id"),
                        "content": json.dumps(msg.get("content", {}), default=str)
                    })
                else:
                    # Regular user message
                    if isinstance(msg.get("content"), dict):
                        # Handle tool results embedded in user message (legacy format)
                        tool_results = msg.get("content", {}).get("tool_results", [])
                        for tr in tool_results:
                            tool_call_id = tr.get("tool_call_id", tr.get("id", f"call_{len(openai_messages)}"))
                            if "error" in tr:
                                content = json.dumps({"error": tr["error"]}, default=str)
                            else:
                                content = json.dumps(tr.get("result", {}), default=str)
                            openai_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": content
                            })
                    else:
                        openai_messages.append({
                            "role": role,
                            "content": msg.get("content", "")
                        })
            
            # Add system prompt as first message if provided
            if system_prompt:
                openai_messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Get model from provider
            model = getattr(self.llm_provider, 'model', 'gpt-4-turbo')
            
            # Call API with tools
            response = client.chat.completions.create(
                model=model,
                messages=openai_messages,
                tools=openai_tools,
                tool_choice="auto",  # Let model decide when to call tools
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            choice = response.choices[0]
            message = choice.message
            
            # Extract tool calls
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    # Parse arguments JSON
                    try:
                        arguments = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    tool_calls.append(ToolCall(
                        tool_name=tc.function.name,
                        arguments=arguments,
                        call_id=tc.id
                    ))
            
            # Create LLMResponse-like object
            from kosmos.core.providers.base import LLMResponse, UsageStats
            from datetime import datetime
            
            usage = UsageStats(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cost_usd=None,  # Cost calculation can be added if needed
                model=model,
                provider="openai",
                timestamp=datetime.now()
            )
            
            llm_response = LLMResponse(
                content=message.content or "",
                usage=usage,
                model=model,
                finish_reason=choice.finish_reason,
                raw_response=response
            )
            
            return llm_response, tool_calls
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API with tools: {e}", exc_info=True)
            raise
    
    def _extract_response_text(self, response: Any) -> str:
        """Extract text content from LLM response."""
        if isinstance(response, LLMResponse):
            return response.content
        elif isinstance(response, str):
            return response
        elif hasattr(response, 'content'):
            return str(response.content)
        else:
            return str(response)
    
    def _format_tool_result(self, tool_call: ToolCall, tool_result: ToolResult) -> Dict[str, Any]:
        """Format tool result for LLM response."""
        result = {
            "tool_name": tool_call.tool_name,
        }
        if tool_result.success:
            result["result"] = tool_result.result
        else:
            result["error"] = tool_result.error
        return result
    
    def _format_tool_result_message_openai(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool result as OpenAI tool role message."""
        tool_call_id = tool_result.get("tool_call_id", "unknown")
        if "error" in tool_result:
            content = json.dumps({"error": tool_result["error"]}, default=str)
        else:
            content = json.dumps(tool_result.get("result", {}), default=str)
        
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        }
    
    def _format_assistant_message_with_tool_calls(
        self,
        tool_calls: List[ToolCall],
        response: Any
    ) -> Dict[str, Any]:
        """Format assistant message with tool calls."""
        # For OpenAI, we need to preserve the exact tool call structure from the response
        if self.provider_name == 'openai' and hasattr(response, 'raw_response'):
            try:
                # Extract tool calls from raw OpenAI response
                raw_response = response.raw_response
                if hasattr(raw_response, 'choices') and raw_response.choices:
                    choice = raw_response.choices[0]
                    message = choice.message
                    if message.tool_calls:
                        # Use the exact tool calls from OpenAI response
                        tool_calls_list = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments  # Keep as JSON string
                                }
                            }
                            for tc in message.tool_calls
                        ]
                        return {
                            "role": "assistant",
                            "content": message.content if message.content else None,
                            "tool_calls": tool_calls_list
                        }
            except Exception as e:
                logger.warning(f"Could not extract tool calls from raw response: {e}, using fallback")
        
        # Fallback: construct tool calls from our ToolCall objects
        return {
            "role": "assistant",
            "content": self._extract_response_text(response) if response else None,
            "tool_calls": [
                {
                    "id": tc.call_id or f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": tc.tool_name,
                        "arguments": json.dumps(tc.arguments)
                    }
                }
                for i, tc in enumerate(tool_calls)
            ]
        }
    
    def _format_tool_results_message(self, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format tool results as Anthropic user message with tool_result blocks.
        
        This is only called for Anthropic provider.
        """
        # Anthropic format: user message with tool_result content blocks
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
        
        return {
            "role": "user",
            "content": content
        }

