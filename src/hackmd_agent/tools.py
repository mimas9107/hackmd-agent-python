"""HackMD tools for AI agents."""

import json
from typing import Any, Literal

from .types import Tool
from .hackmd_client import HackMDClient


def create_hackmd_tools(api_token: str, base_url: str | None = None) -> list[Tool]:
    """
    Create HackMD tools for AI agents.
    Provides: list_notes, read_note, create_note, update_note, delete_note, search_notes
    """
    client = HackMDClient(api_token, base_url or "https://api.hackmd.io/v1")

    async def list_notes(_input: Any) -> str:
        """List all notes from HackMD."""
        notes = await client.get_note_list()
        return json.dumps(notes, indent=2, ensure_ascii=False)

    async def read_note(input_data: Any) -> str:
        """Read a note by ID."""
        note_id = input_data.get("noteId") if isinstance(input_data, dict) else None
        if not note_id:
            raise ValueError("noteId is required")
        note = await client.get_note(note_id)
        return json.dumps(note, indent=2, ensure_ascii=False)

    async def create_note(input_data: Any) -> str:
        """Create a new note."""
        if not isinstance(input_data, dict):
            raise ValueError("Invalid input")
        title = input_data.get("title")
        content = input_data.get("content")
        if not title or not content:
            raise ValueError("title and content are required")
        note = await client.create_note(
            title=title,
            content=content,
            read_permission=input_data.get("readPermission"),
            write_permission=input_data.get("writePermission"),
        )
        return json.dumps(note, indent=2, ensure_ascii=False)

    async def update_note(input_data: Any) -> str:
        """Update an existing note."""
        if not isinstance(input_data, dict):
            raise ValueError("Invalid input")
        note_id = input_data.get("noteId")
        content = input_data.get("content")
        if not note_id or not content:
            raise ValueError("noteId and content are required")
        note = await client.update_note(
            note_id=note_id,
            content=content,
            read_permission=input_data.get("readPermission"),
            write_permission=input_data.get("writePermission"),
        )
        return json.dumps(note, indent=2, ensure_ascii=False)

    async def delete_note(input_data: Any) -> str:
        """Delete a note."""
        note_id = input_data.get("noteId") if isinstance(input_data, dict) else None
        if not note_id:
            raise ValueError("noteId is required")
        await client.delete_note(note_id)
        return json.dumps({"success": True, "message": "Note deleted"})

    async def search_notes(input_data: Any) -> str:
        """Search notes by title keyword."""
        keyword = input_data.get("keyword") if isinstance(input_data, dict) else None
        if not keyword:
            raise ValueError("keyword is required")
        notes = await client.get_note_list()
        filtered = [
            note
            for note in notes
            if note.get("title", "").lower().find(keyword.lower()) != -1
        ]
        return json.dumps(filtered, indent=2, ensure_ascii=False)

    return [
        Tool(
            name="hackmd_list_notes",
            description="List all notes from HackMD. Returns an array of note metadata including id, title, and timestamps.",
            input_schema={"type": "object", "properties": {}},
            call=list_notes,
        ),
        Tool(
            name="hackmd_read_note",
            description="Read a note's full content by its ID. Returns the note metadata and markdown content.",
            input_schema={
                "type": "object",
                "properties": {
                    "noteId": {
                        "type": "string",
                        "description": "The unique ID of the note to read",
                    },
                },
                "required": ["noteId"],
            },
            call=read_note,
        ),
        Tool(
            name="hackmd_create_note",
            description="Create a new note on HackMD. Returns the created note's metadata including its new ID and URL.",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the new note",
                    },
                    "content": {
                        "type": "string",
                        "description": "The markdown content of the note",
                    },
                    "readPermission": {
                        "type": "string",
                        "enum": ["owner", "signed_in", "guest"],
                        "description": "Who can read this note (default: owner)",
                    },
                    "writePermission": {
                        "type": "string",
                        "enum": ["owner", "signed_in", "guest"],
                        "description": "Who can write to this note (default: owner)",
                    },
                },
                "required": ["title", "content"],
            },
            call=create_note,
        ),
        Tool(
            name="hackmd_update_note",
            description="Update an existing note's content. Returns the updated note metadata.",
            input_schema={
                "type": "object",
                "properties": {
                    "noteId": {
                        "type": "string",
                        "description": "The unique ID of the note to update",
                    },
                    "content": {
                        "type": "string",
                        "description": "The new markdown content for the note",
                    },
                    "readPermission": {
                        "type": "string",
                        "enum": ["owner", "signed_in", "guest"],
                        "description": "Who can read this note",
                    },
                    "writePermission": {
                        "type": "string",
                        "enum": ["owner", "signed_in", "guest"],
                        "description": "Who can write to this note",
                    },
                },
                "required": ["noteId", "content"],
            },
            call=update_note,
        ),
        Tool(
            name="hackmd_delete_note",
            description="Permanently delete a note by its ID. This action cannot be undone.",
            input_schema={
                "type": "object",
                "properties": {
                    "noteId": {
                        "type": "string",
                        "description": "The unique ID of the note to delete",
                    },
                },
                "required": ["noteId"],
            },
            call=delete_note,
        ),
        Tool(
            name="hackmd_search_notes",
            description="Search notes by title keyword. Returns matching notes from your note list.",
            input_schema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The keyword to search for in note titles",
                    },
                },
                "required": ["keyword"],
            },
            call=search_notes,
        ),
    ]
