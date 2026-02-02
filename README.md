# HackMD Agent for Python

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](./CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

A Python library that provides HackMD tools for AI agents, compatible with Google Gemini's function calling format.

> Ported from [tiny-hackmd-agent](https://github.com/user/tiny-hackmd-agent) (Deno version)

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [CLI Mode](#cli-mode)
  - [MCP Server Mode (New)](#mcp-server-mode-new)
  - [Programmatic Usage](#programmatic-usage)
  - [Using Tools with Other AI Providers](#using-tools-with-other-ai-providers)
- [API Reference](#api-reference)
- [Available Tools](#available-tools)
- [Development](#development)
- [Version History](#version-history)
- [License](#license)

## Features

- **6 HackMD Tools** for AI agents:
  - `hackmd_list_notes` - List all notes
  - `hackmd_read_note` - Read note content
  - `hackmd_create_note` - Create new notes
  - `hackmd_update_note` - Update existing notes
  - `hackmd_delete_note` - Delete notes
  - `hackmd_search_notes` - Search notes by title

- **Interactive CLI** for testing and manual interaction
- **Async API** for high-performance integration
- **Full type hints** for better IDE support
- **Native HackMD client** using httpx (no external HackMD SDK dependency)
- **New Google Gen AI SDK** support (`google-genai`)

## Requirements

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [HackMD API Token](https://hackmd.io/settings#api)
- [Google Gemini API Key](https://aistudio.google.com/app/apikey) (Free tier available!)

## Installation

### Using uv (Recommended)

```bash
# Clone or copy the project
cd hackmd-agent-python

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# With development dependencies
uv pip install -e ".[dev]"
```

### Using pip

```bash
cd hackmd-agent-python
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

```bash
# Set environment variables
export HACKMD_API_TOKEN=<YOUR_HACKMD_TOKEN>
export GEMINI_API_KEY=<YOUR_GEMINI_KEY>

# Run the agent
hackmd-agent
```

## Usage

### CLI Mode

Interactive chat with the HackMD agent:

```bash
export HACKMD_API_TOKEN=xxx
export GEMINI_API_KEY=xxx

hackmd-agent
```

Example conversation:
```
Chat with HackMD Agent (ctrl-c to quit)

😂: List my notes
🔧 Using: hackmd_list_notes...
🤖: Here are your notes:
1. Meeting Notes (id: abc123)
2. Project Plan (id: def456)

😂: Create a note titled "TODO" with content "# My Tasks\n- Task 1\n- Task 2"
🔧 Using: hackmd_create_note...
🤖: I've created your note "TODO". You can access it at https://hackmd.io/xyz789
```

### MCP Server Mode (New)

The agent now includes a Model Context Protocol (MCP) server, allowing it to be used directly by MCP-compatible clients like Claude Desktop or Cursor.

**Prerequisites:**
- `HACKMD_API_TOKEN` environment variable must be set.

**Run the server:**

```bash
# Using the installed script
hackmd-mcp

# Or using fastmcp CLI (for development)
uv run fastmcp run src/hackmd_agent/mcp_server.py:mcp
```

**Run as SSE Server (Remote Mode):**

If your client (e.g., OpenCode) requires a remote connection:

```bash
# Start the SSE server on port 8000
uv run fastmcp run src/hackmd_agent/mcp_server.py:mcp --transport sse --port 8000
```

The SSE endpoint will be available at: `http://127.0.0.1:8000/sse`

**Configuration for Claude Desktop (Local Stdio):**

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hackmd": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "hackmd-agent-python", 
        "hackmd-mcp"
      ],
      "env": {
        "HACKMD_API_TOKEN": "YOUR_TOKEN_HERE"
      }
    }
  }
}
```

**Configuration for OpenCode (Remote SSE):**

Since OpenCode requires a remote connection, first start the server in SSE mode (see above), then configure OpenCode to connect to `http://127.0.0.1:8000/sse`.

If OpenCode uses a config file (`opencode.json`), it might look like this (depends on specific OpenCode version implementation of remote MCP):

```json
{
  "mcpServers": {
    "hackmd": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```
*(Note: Check OpenCode documentation for exact remote server configuration syntax)*

### Programmatic Usage

```python
import asyncio
import os
from google import genai
from hackmd_agent import create_hackmd_tools, process_message

async def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    tools = create_hackmd_tools(os.environ["HACKMD_API_TOKEN"])

    # Process a single message
    result = await process_message(
        client,
        tools,
        "Create a note titled 'Meeting Notes' with content '# Today Meeting\n\n- Discuss roadmap'"
    )

    print("Response:", result.response)
    print("Tools used:", result.tools_used)
    # Continue conversation with result.conversation

asyncio.run(main())
```

### Using Tools with Other AI Providers

The tools are designed to be framework-agnostic:

```python
import asyncio
from hackmd_agent import create_hackmd_tools, to_gemini_tools, execute_tool

async def main():
    # Create tools
    tools = create_hackmd_tools("your-token")

    # Get tool definitions (Gemini function calling format)
    tool_definitions = to_gemini_tools(tools)

    # Execute a tool manually
    result = await execute_tool(tools, "hackmd_create_note", {
        "title": "New Note",
        "content": "# Hello World"
    })

    import json
    print(json.loads(result))
    # { "id": "xxx", "title": "New Note", "publishLink": "https://hackmd.io/xxx" }

asyncio.run(main())
```

## API Reference

### `create_hackmd_tools(api_token, base_url=None) -> list[Tool]`

Create HackMD tools for AI agents.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_token` | `str` | Yes | Your HackMD API token |
| `base_url` | `str` | No | Custom API base URL |

**Returns:** List of `Tool` objects

---

### `run_agent(client, tools, config=None) -> None`

Run interactive CLI agent.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client` | `genai.Client` | Yes | Google Gen AI Client |
| `tools` | `list[Tool]` | Yes | List of tools |
| `config` | `AgentConfig` | No | Agent configuration |

**AgentConfig:**
| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `model` | `str` | `"gemini-2.5-flash"` | LLM model to use |
| `max_tokens` | `int` | `4096` | Max tokens for response |
| `system_prompt` | `str` | `"You are a helpful agent..."` | System prompt |

---

### `process_message(client, tools, message, conversation=None, config=None) -> ProcessResult`

Process a single message programmatically.

**Returns:** `ProcessResult` dataclass with:,
```python
@dataclass
class ProcessResult:
    response: str              # Text response from the AI
    conversation: list[dict]   # Updated conversation history
    tools_used: list[str]      # List of tool names used
```

---

### `to_gemini_tools(tools) -> list[dict]`

Convert Tool list to Gemini function declarations format.

---

### `execute_tool(tools, name, input_data) -> str`

Find and execute a tool by name. Returns JSON string.

## Available Tools

| Tool Name | Description | Required Parameters |
|-----------|-------------|---------------------|
| `hackmd_list_notes` | List all notes from HackMD | None |
| `hackmd_read_note` | Read a note's content by ID | `noteId: str` |
| `hackmd_create_note` | Create a new note | `title: str`, `content: str` |
| `hackmd_update_note` | Update an existing note | `noteId: str`, `content: str` |
| `hackmd_delete_note` | Delete a note | `noteId: str` |
| `hackmd_search_notes` | Search notes by title | `keyword: str` |

### Optional Parameters for Create/Update

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `readPermission` | `str` | `"owner"`, `"signed_in"`, `"guest"` | Who can read |
| `writePermission` | `str` | `"owner"`, `"signed_in"`, `"guest"` | Who can write |

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=hackmd_agent

# Type check
mypy src/

# Lint
ruff check src/

# Format code
ruff format src/
```

### Project Structure

```
hackmd-agent-python/
├── src/hackmd_agent/
│   ├── __init__.py       # Main exports
│   ├── types.py          # Tool interface definitions
│   ├── hackmd_client.py  # Native HackMD API client
│   ├── tools.py          # HackMD tool implementations
│   ├── agent.py          # Agent logic (CLI & programmatic)
│   └── cli.py            # CLI entry point
├── tests/
│   ├── test_types.py
│   └── test_tools.py
├── pyproject.toml
├── CHANGELOG.md
├── AGENTS.md
└── README.md
```

## Version History

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history.

| Version | Date | Description |
|---------|------|-------------|
| 1.1.0 | 2024-02-01 | Migrated to Google Gemini |
| 1.0.0 | 2024-02-01 | Initial release |

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Credits

- Original Deno version: [tiny-hackmd-agent](https://hackmd.io/@EastSun5566/building-a-tiny-hackmd-agent)
- HackMD API: [HackMD Developer Portal](https://hackmd.io/@hackmd-api/developer-portal)
