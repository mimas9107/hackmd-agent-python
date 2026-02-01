#!/usr/bin/env python3
"""CLI entry point for HackMD Agent."""

import asyncio
import os
import sys

from google import genai

from .tools import create_hackmd_tools
from .agent import run_agent


def assert_env(name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.environ.get(name)
    if not value:
        print(f"Error: {name} environment variable is required", file=sys.stderr)
        sys.exit(1)
    return value


async def async_main() -> None:
    """Async main function."""
    api_key = assert_env("GEMINI_API_KEY")
    api_token = assert_env("HACKMD_API_TOKEN")

    # Create Gemini client
    client = genai.Client(api_key=api_key)

    tools = create_hackmd_tools(api_token)

    await run_agent(client, tools)


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
