"""
Tool Schema Generation.

Generates tool schemas from Python functions for LLM function calling.
Supports both Anthropic tool use format and OpenAI function calling format.
"""

import inspect
import logging
from typing import Dict, Any, Callable, Optional, List, Type, get_type_hints, get_origin, get_args

logger = logging.getLogger(__name__)

# Type mapping from Python types to JSON schema types
PYTHON_TO_JSON_TYPE = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}

def get_json_schema_type(python_type: Type) -> Dict[str, Any]:
    """
    Convert Python type to JSON schema type definition.
    
    Args:
        python_type: Python type annotation
        
    Returns:
        JSON schema type definition dict
    """
    # Handle Optional/Union types
    origin = get_origin(python_type)
    if origin is Optional or (origin is type(None).__class__):
        # Extract the non-None type
        args = get_args(python_type)
        if args:
            non_none_type = [a for a in args if a is not type(None)]
            if non_none_type:
                schema = get_json_schema_type(non_none_type[0])
                schema["type"] = [schema["type"], "null"] if isinstance(schema.get("type"), str) else schema.get("type", []) + ["null"]
                return schema
    
    # Handle Union types (non-Optional)
    if origin is type(None).__class__ or (hasattr(python_type, '__origin__') and python_type.__origin__ is type(None).__class__):
        args = get_args(python_type)
        if args:
            types = [t for t in args if t is not type(None)]
            if types:
                json_types = [get_json_schema_type(t).get("type", "string") for t in types]
                return {"type": json_types[0] if len(json_types) == 1 else json_types}
    
    # Handle List types
    if origin is list or python_type is list:
        args = get_args(python_type)
        items_type = get_json_schema_type(args[0]) if args else {"type": "string"}
        return {"type": "array", "items": items_type}
    
    # Handle Dict types
    if origin is dict or python_type is dict:
        return {"type": "object"}
    
    # Map basic Python types
    if python_type in PYTHON_TO_JSON_TYPE:
        return {"type": PYTHON_TO_JSON_TYPE[python_type]}
    
    # Default to string for unknown types
    return {"type": "string"}


def generate_tool_schema(func: Callable, tool_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate tool schema from a Python function for LLM function calling.
    
    Extracts:
    - Function name and docstring (description)
    - Parameter types and descriptions
    - Required vs optional parameters
    
    Args:
        func: Python callable function
        tool_name: Optional custom name for the tool (defaults to function name)
        
    Returns:
        Tool schema dict in format compatible with Anthropic and OpenAI
    """
    if tool_name is None:
        tool_name = func.__name__
    
    # Get function signature
    sig = inspect.signature(func)
    
    # Get docstring for description
    description = inspect.getdoc(func) or f"Tool: {tool_name}"
    # Extract first line as short description
    short_description = description.split('\n')[0].strip()
    
    # Get type hints
    type_hints = get_type_hints(func)
    
    # Build parameters schema
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        # Skip self/cls parameters
        if param_name in ('self', 'cls'):
            continue
        
        # Get parameter type
        param_type = type_hints.get(param_name, str)
        
        # Convert to JSON schema
        param_schema = get_json_schema_type(param_type)
        
        # Get default value
        if param.default is not inspect.Parameter.empty:
            param_schema["default"] = param.default
        else:
            required.append(param_name)
        
        # Try to extract parameter description from docstring
        # Simple heuristic: look for ":param param_name:" in docstring
        param_desc = None
        if description:
            lines = description.split('\n')
            for i, line in enumerate(lines):
                if f':param {param_name}:' in line or f':param {param_name} ' in line:
                    param_desc = line.split(':', 2)[-1].strip()
                    # If next line is continuation, include it
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith((' ', '\t')):
                        param_desc += " " + lines[i + 1].strip()
                    break
        
        if param_desc:
            param_schema["description"] = param_desc
        
        properties[param_name] = param_schema
    
    # Build tool schema (Anthropic/OpenAI compatible format)
    tool_schema = {
        "name": tool_name,
        "description": short_description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }
    
    return tool_schema


def convert_to_anthropic_format(tool_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert tool schema to Anthropic tool use format.
    
    Anthropic format:
    {
        "name": "tool_name",
        "description": "...",
        "input_schema": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
    
    Args:
        tool_schema: Tool schema in standard format
        
    Returns:
        Tool schema in Anthropic format
    """
    # Anthropic format is the same as our standard format
    return tool_schema.copy()


def convert_to_openai_format(tool_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert tool schema to OpenAI function calling format.
    
    OpenAI format:
    {
        "type": "function",
        "function": {
            "name": "tool_name",
            "description": "...",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
    
    Args:
        tool_schema: Tool schema in standard format
        
    Returns:
        Tool schema in OpenAI format
    """
    return {
        "type": "function",
        "function": {
            "name": tool_schema["name"],
            "description": tool_schema["description"],
            "parameters": tool_schema["input_schema"]
        }
    }


def generate_tool_schemas(tools: Dict[str, Callable]) -> List[Dict[str, Any]]:
    """
    Generate tool schemas for multiple tools.
    
    Args:
        tools: Dict mapping tool names to callable functions
        
    Returns:
        List of tool schemas in standard format
    """
    schemas = []
    for tool_name, tool_func in tools.items():
        try:
            schema = generate_tool_schema(tool_func, tool_name=tool_name)
            schemas.append(schema)
        except Exception as e:
            logger.warning(f"Failed to generate schema for tool {tool_name}: {e}")
    
    return schemas

