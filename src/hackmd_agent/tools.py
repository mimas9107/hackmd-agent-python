"""HackMD tools for AI agents."""

import json
from typing import Any

from .hackmd_client import HackMDClient, RetryInfo
from .types import Tool


def create_hackmd_tools(api_token: str, base_url: str | None = None) -> list[Tool]:
    """
    Create HackMD tools for AI agents.
    Provides: list_notes, read_note, create_note, update_note, delete_note, search_notes
    """
    client = HackMDClient(api_token, base_url or "https://api.hackmd.io/v1")

    async def list_notes(_input: Any) -> str:
        """List all notes from HackMD."""
        retry_info = RetryInfo()
        notes = await client.get_note_list(retry_info=retry_info)
        return _build_response(notes, retry_info)

    async def read_note(input_data: Any) -> str:
        """Read a note by ID."""
        note_id = input_data.get("noteId") if isinstance(input_data, dict) else None
        if not note_id:
            raise ValueError("noteId is required")
        retry_info = RetryInfo()
        note = await client.get_note(note_id, retry_info=retry_info)
        return _build_response(note, retry_info)

    async def create_note(input_data: Any) -> str:
        """Create a new note."""
        if not isinstance(input_data, dict):
            raise ValueError("Invalid input")
        title = input_data.get("title")
        content = input_data.get("content")
        if not title or not content:
            raise ValueError("title and content are required")
        retry_info = RetryInfo()
        note = await client.create_note(
            title=title,
            content=content,
            read_permission=input_data.get("readPermission"),
            write_permission=input_data.get("writePermission"),
            retry_info=retry_info,
        )
        return _build_response(note, retry_info)

    async def update_note(input_data: Any) -> str:
        """Update an existing note."""
        if not isinstance(input_data, dict):
            raise ValueError("Invalid input")
        note_id = input_data.get("noteId")
        content = input_data.get("content")
        if not note_id or not content:
            raise ValueError("noteId and content are required")
        retry_info = RetryInfo()
        note = await client.update_note(
            note_id=note_id,
            content=content,
            read_permission=input_data.get("readPermission"),
            write_permission=input_data.get("writePermission"),
            retry_info=retry_info,
        )
        return _build_response(note, retry_info)

    async def delete_note(input_data: Any) -> str:
        """Delete a note."""
        note_id = input_data.get("noteId") if isinstance(input_data, dict) else None
        if not note_id:
            raise ValueError("noteId is required")
        retry_info = RetryInfo()
        await client.delete_note(note_id, retry_info=retry_info)
        return _build_response({"success": True, "message": "Note deleted"}, retry_info)

    async def search_notes(input_data: Any) -> str:
        """Search notes by title (and optionally content) with relevance ranking."""
        if not isinstance(input_data, dict):
            raise ValueError("Invalid input")
        keyword = input_data.get("keyword")
        if not keyword:
            raise ValueError("keyword is required")

        search_content = input_data.get("searchContent", False)
        fuzzy = input_data.get("fuzzy", False)
        limit = min(input_data.get("limit", 20), 100)

        def calculate_relevance(note: dict[str, Any]) -> tuple[int, int]:
            title = note.get("title", "").lower()
            keyword_lower = keyword.lower()
            if title == keyword_lower:
                return (100, len(title))
            if title.startswith(keyword_lower):
                return (90, len(title))
            if keyword_lower in title:
                return (70, len(title))
            words = keyword_lower.split()
            if any(w in title for w in words):
                return (60, len(title))
            return (0, len(title))

        def fuzzy_match(text: str) -> bool:
            text_lower = text.lower()
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                return True
            key_chars = set(keyword_lower.replace(" ", ""))
            text_chars = set(text_lower.replace(" ", ""))
            if not key_chars:
                return False
            return len(key_chars & text_chars) / len(key_chars) >= 0.6

        if search_content:
            notes, retry_info = await client.search_notes(keyword, search_content=True)
        else:
            retry_info = RetryInfo()
            notes = await client.get_note_list(retry_info=retry_info)

        keyword_lower = keyword.lower()

        if fuzzy:
            matched = [
                (note, calculate_relevance(note))
                for note in notes
                if fuzzy_match(note.get("title", ""))
            ]
        else:
            matched = [
                (note, calculate_relevance(note))
                for note in notes
                if keyword_lower in note.get("title", "").lower()
            ]

        matched.sort(key=lambda x: (-x[1][0], x[1][1]))
        return _build_response([note for note, _ in matched[:limit]], retry_info)

    def _build_response(data: Any, retry_info: RetryInfo) -> str:
        """Build JSON response with retry metadata for AI agent transparency."""
        result = {
            "data": data,
            "_meta": {
                "retry_info": {
                    "was_rate_limited": retry_info.attempted,
                    "total_attempts": retry_info.total_attempts,
                    "total_wait_seconds": round(retry_info.final_wait_total, 2),
                },
            },
        }
        return json.dumps(result, indent=2, ensure_ascii=False)

    return [
        Tool(
            name="hackmd_list_notes",
            description="List all notes from HackMD.",
            input_schema={"type": "object", "properties": {}},
            call=list_notes,
        ),
        Tool(
            name="hackmd_read_note",
            description="Read a note's full content by its ID.",
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
            description="Create a new note on HackMD.",
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
            description="Update an existing note's content.",
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
            description="Permanently delete a note by its ID.",
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
            description="Search notes by title with relevance ranking.",
            input_schema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The keyword to search for in note titles",
                    },
                    "searchContent": {
                        "type": "boolean",
                        "description": "Search within note content (slower)",
                    },
                    "fuzzy": {
                        "type": "boolean",
                        "description": "Enable fuzzy matching for typo tolerance",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default: 20)",
                    },
                },
                "required": ["keyword"],
            },
            call=search_notes,
        ),
    ]
