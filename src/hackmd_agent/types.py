"""Type definitions and utilities for AI agent tools."""

from dataclasses import dataclass
from typing import Any, Callable, Awaitable, TypedDict
import json


class InputSchema(TypedDict, total=False):
    """JSON Schema for tool input."""

    type: str
    properties: dict[str, Any]
    required: list[str]


@dataclass
class Tool:
    """
    Tool interface for AI agents.
    Compatible with Google Gemini's function calling format.
    """

    name: str
    description: str
    input_schema: InputSchema
    call: Callable[[Any], Awaitable[str]]


def to_gemini_tools(tools: list[Tool]) -> list[dict[str, Any]]:
    """Convert Tool list to Gemini function declarations format."""
    function_declarations = []
    for tool in tools:
        func_decl: dict[str, Any] = {
            "name": tool.name,
            "description": tool.description,
        }
        # Gemini uses 'parameters' instead of 'input_schema'
        if tool.input_schema:
            func_decl["parameters"] = tool.input_schema
        function_declarations.append(func_decl)

    return function_declarations


# Keep backward compatibility alias
def to_anthropic_tools(tools: list[Tool]) -> list[dict[str, Any]]:
    """
    Convert Tool list to Anthropic tool format.
    Deprecated: Use to_gemini_tools() instead.
    """
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }
        for tool in tools
    ]


async def execute_tool(
    tools: list[Tool],
    name: str,
    input_data: Any,
) -> str:
    """Find and execute a tool by name."""
    tool = next((t for t in tools if t.name == name), None)
    if not tool:
        return json.dumps({"error": "Tool not found", "name": name})
    try:
        return await tool.call(input_data)
    except Exception as e:
        return json.dumps({"error": str(e)})
