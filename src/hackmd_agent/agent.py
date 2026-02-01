"""Agent logic for interactive and programmatic usage."""

from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types

from .types import Tool, to_gemini_tools, execute_tool


@dataclass
class AgentConfig:
    """Configuration for the agent."""

    model: str = "gemini-2.5-flash"
    max_tokens: int = 4096
    system_prompt: str = "You are a helpful agent for managing HackMD notes."


@dataclass
class ProcessResult:
    """Result of processing a message."""

    response: str
    conversation: list[dict[str, Any]]
    tools_used: list[str] = field(default_factory=list)


def _create_tools_config(tools: list[Tool]) -> list[types.Tool]:
    """Create Gemini tools configuration from Tool list."""
    function_declarations = []
    for tool_def in to_gemini_tools(tools):
        func_decl = types.FunctionDeclaration(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters_json_schema=tool_def.get("parameters_json_schema"),
        )
        function_declarations.append(func_decl)

    return [types.Tool(function_declarations=function_declarations)]


async def run_agent(
    client: genai.Client,
    tools: list[Tool],
    config: AgentConfig | None = None,
) -> None:
    """
    Run the HackMD agent in interactive CLI mode.
    Press Ctrl+C to quit.
    """
    cfg = config or AgentConfig()
    gemini_tools = _create_tools_config(tools)

    # Create async chat session
    chat = client.aio.chats.create(
        model=cfg.model,
        config=types.GenerateContentConfig(
            system_instruction=cfg.system_prompt,
            max_output_tokens=cfg.max_tokens,
            tools=gemini_tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True  # We handle function calling manually
            ),
        ),
    )

    print("Chat with HackMD Agent (ctrl-c to quit)\n")

    try:
        while True:
            try:
                user_input = input("😂: ")
            except EOFError:
                break
            if not user_input:
                continue

            # Send message and get response
            response = await chat.send_message(user_input)

            # Process response - handle function calls manually
            while True:
                has_function_call = False

                # Check for text response
                if response.text:
                    print(f"🤖: {response.text}")

                # Check for function calls
                if response.function_calls:
                    has_function_call = True
                    for fc in response.function_calls:
                        print(f"🔧 Using: {fc.name}...")

                        # Execute the tool
                        result = await execute_tool(
                            tools, fc.name, dict(fc.args) if fc.args else {}
                        )

                        # Send function response back
                        function_response = types.Part.from_function_response(
                            name=fc.name,
                            response={"result": result},
                        )
                        response = await chat.send_message(function_response)
                        break  # Process new response

                if not has_function_call:
                    break

    except KeyboardInterrupt:
        print("\nGoodbye!")


async def process_message(
    client: genai.Client,
    tools: list[Tool],
    user_message: str,
    conversation: list[dict[str, Any]] | None = None,
    config: AgentConfig | None = None,
) -> ProcessResult:
    """
    Process a single message programmatically.

    Returns:
        ProcessResult with response text, updated conversation, and tools used.
    """
    cfg = config or AgentConfig()
    gemini_tools = _create_tools_config(tools)
    tools_used: list[str] = []
    response_text = ""

    # Build history from conversation
    history: list[types.Content] = []
    if conversation:
        for msg in conversation:
            role = "user" if msg["role"] == "user" else "model"
            history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

    # Create async chat session with history
    chat = client.aio.chats.create(
        model=cfg.model,
        history=history,
        config=types.GenerateContentConfig(
            system_instruction=cfg.system_prompt,
            max_output_tokens=cfg.max_tokens,
            tools=gemini_tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        ),
    )

    # Track conversation
    conv = conversation.copy() if conversation else []
    conv.append({"role": "user", "content": user_message})

    # Send initial message
    response = await chat.send_message(user_message)

    # Process until no more function calls
    while True:
        has_function_call = False

        # Collect text response
        if response.text:
            response_text += response.text

        # Check for function calls
        if response.function_calls:
            has_function_call = True
            for fc in response.function_calls:
                tools_used.append(fc.name)

                # Execute the tool
                result = await execute_tool(
                    tools, fc.name, dict(fc.args) if fc.args else {}
                )

                # Send function response back
                function_response = types.Part.from_function_response(
                    name=fc.name,
                    response={"result": result},
                )
                response = await chat.send_message(function_response)
                break  # Process new response

        if not has_function_call:
            break

    conv.append({"role": "assistant", "content": response_text})

    return ProcessResult(
        response=response_text,
        conversation=conv,
        tools_used=tools_used,
    )
