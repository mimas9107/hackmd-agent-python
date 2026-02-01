"""Agent logic for interactive and programmatic usage."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool as GeminiTool

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


def _create_gemini_model(
    tools: list[Tool],
    config: AgentConfig,
) -> genai.GenerativeModel:
    """Create a Gemini model with tools configured."""
    function_declarations = to_gemini_tools(tools)

    return genai.GenerativeModel(
        model_name=config.model,
        system_instruction=config.system_prompt,
        tools=[{"function_declarations": function_declarations}],
        generation_config=genai.GenerationConfig(
            max_output_tokens=config.max_tokens,
        ),
    )


async def run_agent(
    tools: list[Tool],
    config: AgentConfig | None = None,
) -> None:
    """
    Run the HackMD agent in interactive CLI mode.
    Press Ctrl+C to quit.
    """
    cfg = config or AgentConfig()
    model = _create_gemini_model(tools, cfg)
    chat = model.start_chat()

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
            response = await asyncio.to_thread(
                chat.send_message, user_input
            )

            # Process response
            while True:
                has_function_call = False

                for part in response.parts:
                    if part.text:
                        print(f"🤖: {part.text}")
                    elif part.function_call:
                        has_function_call = True
                        fn = part.function_call
                        print(f"🔧 Using: {fn.name}...")

                        # Execute the tool
                        result = await execute_tool(
                            tools, fn.name, dict(fn.args)
                        )

                        # Send function response back
                        response = await asyncio.to_thread(
                            chat.send_message,
                            genai.protos.Content(
                                parts=[
                                    genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=fn.name,
                                            response={"result": result},
                                        )
                                    )
                                ]
                            ),
                        )
                        break  # Process new response

                if not has_function_call:
                    break

    except KeyboardInterrupt:
        print("\nGoodbye!")


async def process_message(
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
    model = _create_gemini_model(tools, cfg)

    # Build history from conversation
    history = []
    if conversation:
        for msg in conversation:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=history)
    tools_used: list[str] = []
    response_text = ""

    # Track conversation
    conv = conversation.copy() if conversation else []
    conv.append({"role": "user", "content": user_message})

    # Send initial message
    response = await asyncio.to_thread(chat.send_message, user_message)

    # Process until no more function calls
    while True:
        has_function_call = False
        assistant_content = []

        for part in response.parts:
            if part.text:
                response_text += part.text
                assistant_content.append(part.text)
            elif part.function_call:
                has_function_call = True
                fn = part.function_call
                tools_used.append(fn.name)

                # Execute the tool
                result = await execute_tool(tools, fn.name, dict(fn.args))

                # Send function response back
                response = await asyncio.to_thread(
                    chat.send_message,
                    genai.protos.Content(
                        parts=[
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=fn.name,
                                    response={"result": result},
                                )
                            )
                        ]
                    ),
                )
                break  # Process new response

        if not has_function_call:
            break

    conv.append({"role": "assistant", "content": response_text})

    return ProcessResult(
        response=response_text,
        conversation=conv,
        tools_used=tools_used,
    )
