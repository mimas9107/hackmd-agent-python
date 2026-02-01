"""Tests for types module."""

import pytest
from hackmd_agent.types import Tool, to_gemini_tools, to_anthropic_tools, execute_tool


def test_to_gemini_tools():
    """Test converting Tool list to Gemini format."""

    async def mock_call(_: dict) -> str:
        return '{"result": "ok"}'

    tools = [
        Tool(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
            call=mock_call,
        )
    ]

    result = to_gemini_tools(tools)

    assert len(result) == 1
    assert result[0]["name"] == "test_tool"
    assert result[0]["description"] == "A test tool"
    # google-genai uses parameters_json_schema
    assert "parameters_json_schema" in result[0]
    assert result[0]["parameters_json_schema"]["type"] == "object"
    assert "call" not in result[0]


def test_to_anthropic_tools_backward_compat():
    """Test that to_anthropic_tools still works for backward compatibility."""

    async def mock_call(_: dict) -> str:
        return '{"result": "ok"}'

    tools = [
        Tool(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
            call=mock_call,
        )
    ]

    result = to_anthropic_tools(tools)

    assert len(result) == 1
    assert result[0]["name"] == "test_tool"
    assert result[0]["description"] == "A test tool"
    assert "input_schema" in result[0]


@pytest.mark.asyncio
async def test_execute_tool_success():
    """Test executing a tool successfully."""

    async def mock_call(input_data: dict) -> str:
        return f'{{"received": "{input_data.get("foo")}"}}'

    tools = [
        Tool(
            name="test_tool",
            description="Test",
            input_schema={"type": "object"},
            call=mock_call,
        )
    ]

    result = await execute_tool(tools, "test_tool", {"foo": "bar"})
    assert '"received": "bar"' in result


@pytest.mark.asyncio
async def test_execute_tool_not_found():
    """Test executing a non-existent tool."""
    result = await execute_tool([], "unknown_tool", {})
    assert "Tool not found" in result


@pytest.mark.asyncio
async def test_execute_tool_error():
    """Test tool error handling."""

    async def error_call(_: dict) -> str:
        raise ValueError("Something failed")

    tools = [
        Tool(
            name="error_tool",
            description="Test",
            input_schema={"type": "object"},
            call=error_call,
        )
    ]

    result = await execute_tool(tools, "error_tool", {})
    assert "Something failed" in result
