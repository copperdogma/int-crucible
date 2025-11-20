"""
Unit tests for tool schema generation.
"""

import pytest
from typing import Optional, List, Dict, Any
from crucible.core.tools import (
    generate_tool_schema,
    generate_tool_schemas,
    convert_to_anthropic_format,
    convert_to_openai_format,
    get_json_schema_type
)


class TestToolSchemaGeneration:
    """Test suite for tool schema generation."""
    
    def test_generate_simple_tool_schema(self):
        """Test generating schema for a simple tool function."""
        
        def get_project_info(project_id: str) -> Dict[str, Any]:
            """Get information about a project."""
            return {"id": project_id, "name": "Test Project"}
        
        schema = generate_tool_schema(get_project_info)
        
        assert schema["name"] == "get_project_info"
        assert "Get information about a project." in schema["description"]
        assert "input_schema" in schema
        assert schema["input_schema"]["type"] == "object"
        assert "project_id" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["properties"]["project_id"]["type"] == "string"
        assert "project_id" in schema["input_schema"]["required"]
    
    def test_generate_tool_schema_with_optional_param(self):
        """Test generating schema for tool with optional parameter."""
        
        def list_items(project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
            """List items for a project.
            
            :param project_id: The project ID
            :param limit: Maximum number of items to return
            """
            return []
        
        schema = generate_tool_schema(list_items)
        
        assert "project_id" in schema["input_schema"]["required"]
        assert "limit" not in schema["input_schema"]["required"]
        assert "limit" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["properties"]["limit"]["default"] == 10
    
    def test_generate_tool_schema_custom_name(self):
        """Test generating schema with custom tool name."""
        
        def my_function(param: str) -> str:
            """A test function."""
            return param
        
        schema = generate_tool_schema(my_function, tool_name="custom_name")
        
        assert schema["name"] == "custom_name"
        assert schema["description"] == "A test function."
    
    def test_generate_tool_schemas_multiple(self):
        """Test generating schemas for multiple tools."""
        
        def tool1(param1: str) -> str:
            """First tool."""
            return param1
        
        def tool2(param2: int) -> int:
            """Second tool."""
            return param2
        
        tools = {"tool1": tool1, "tool2": tool2}
        schemas = generate_tool_schemas(tools)
        
        assert len(schemas) == 2
        assert any(s["name"] == "tool1" for s in schemas)
        assert any(s["name"] == "tool2" for s in schemas)
    
    def test_convert_to_anthropic_format(self):
        """Test converting schema to Anthropic format."""
        schema = {
            "name": "test_tool",
            "description": "Test tool",
            "input_schema": {
                "type": "object",
                "properties": {"param": {"type": "string"}},
                "required": ["param"]
            }
        }
        
        anthropic_schema = convert_to_anthropic_format(schema)
        
        assert anthropic_schema == schema  # Anthropic format is the same
    
    def test_convert_to_openai_format(self):
        """Test converting schema to OpenAI format."""
        schema = {
            "name": "test_tool",
            "description": "Test tool",
            "input_schema": {
                "type": "object",
                "properties": {"param": {"type": "string"}},
                "required": ["param"]
            }
        }
        
        openai_schema = convert_to_openai_format(schema)
        
        assert openai_schema["type"] == "function"
        assert "function" in openai_schema
        assert openai_schema["function"]["name"] == "test_tool"
        assert openai_schema["function"]["description"] == "Test tool"
        assert "parameters" in openai_schema["function"]
        assert openai_schema["function"]["parameters"] == schema["input_schema"]
    
    def test_json_schema_type_string(self):
        """Test JSON schema type conversion for string."""
        schema = get_json_schema_type(str)
        assert schema["type"] == "string"
    
    def test_json_schema_type_int(self):
        """Test JSON schema type conversion for int."""
        schema = get_json_schema_type(int)
        assert schema["type"] == "integer"
    
    def test_json_schema_type_optional(self):
        """Test JSON schema type conversion for Optional."""
        schema = get_json_schema_type(Optional[str])
        # Should handle Optional/Union[Type, None]
        assert "type" in schema
    
    def test_json_schema_type_list(self):
        """Test JSON schema type conversion for list."""
        schema = get_json_schema_type(List[str])
        assert schema["type"] == "array"
        assert "items" in schema

