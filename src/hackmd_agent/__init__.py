"""HackMD Agent - Tools for AI agents to manage HackMD notes."""

from .tools import create_hackmd_tools
from .types import Tool, execute_tool, to_gemini_tools, to_anthropic_tools
from .agent import run_agent, process_message, AgentConfig, ProcessResult

__all__ = [
    "create_hackmd_tools",
    "Tool",
    "execute_tool",
    "to_gemini_tools",
    "to_anthropic_tools",  # Backward compatibility
    "run_agent",
    "process_message",
    "AgentConfig",
    "ProcessResult",
]

__version__ = "1.1.0"
