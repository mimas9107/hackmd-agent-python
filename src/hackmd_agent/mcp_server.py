"""MCP Server for HackMD Agent."""

import os
import sys
from typing import Literal

from fastmcp import FastMCP
from .hackmd_client import HackMDClient

# Initialize FastMCP
mcp = FastMCP("HackMD Agent")

# Global client - lazy initialized
_client: HackMDClient | None = None


def get_client() -> HackMDClient:
    """Get or create HackMDClient."""
    global _client
    if _client is None:
        token = os.environ.get("HACKMD_API_TOKEN")
        if not token:
            raise ValueError("HACKMD_API_TOKEN environment variable is required")
        _client = HackMDClient(token)
    return _client


@mcp.tool()
async def hackmd_list_notes() -> str:
    """
    List all notes from HackMD.
    Returns a JSON string containing an array of note metadata.
    """
    import json
    client = get_client()
    notes = await client.get_note_list()
    return json.dumps(notes, indent=2, ensure_ascii=False)


@mcp.tool()
async def hackmd_read_note(note_id: str) -> str:
    """
    Read a note's full content by its ID.
    Returns a JSON string containing the note metadata and content.
    """
    import json
    client = get_client()
    note = await client.get_note(note_id)
    return json.dumps(note, indent=2, ensure_ascii=False)


@mcp.tool()
async def hackmd_create_note(
    title: str,
    content: str,
    read_permission: Literal["owner", "signed_in", "guest"] = "owner",
    write_permission: Literal["owner", "signed_in", "guest"] = "owner",
) -> str:
    """
    Create a new note on HackMD.
    
    Args:
        title: The title of the new note.
        content: The markdown content of the note.
        read_permission: Who can read this note (default: owner).
        write_permission: Who can write to this note (default: owner).
        
    Returns:
        JSON string containing the created note's metadata.
    """
    import json
    client = get_client()
    note = await client.create_note(
        title=title,
        content=content,
        read_permission=read_permission,
        write_permission=write_permission,
    )
    return json.dumps(note, indent=2, ensure_ascii=False)


@mcp.tool()
async def hackmd_update_note(
    note_id: str,
    content: str,
    read_permission: Literal["owner", "signed_in", "guest"] | None = None,
    write_permission: Literal["owner", "signed_in", "guest"] | None = None,
) -> str:
    """
    Update an existing note's content.
    
    Args:
        note_id: The unique ID of the note to update.
        content: The new markdown content for the note.
        read_permission: Optional update to read permission.
        write_permission: Optional update to write permission.
        
    Returns:
        JSON string containing the updated note metadata.
    """
    import json
    client = get_client()
    note = await client.update_note(
        note_id=note_id,
        content=content,
        read_permission=read_permission,
        write_permission=write_permission,
    )
    return json.dumps(note, indent=2, ensure_ascii=False)


@mcp.tool()
async def hackmd_delete_note(note_id: str) -> str:
    """
    Permanently delete a note by its ID.
    """
    import json
    client = get_client()
    await client.delete_note(note_id)
    return json.dumps({"success": True, "message": "Note deleted"})


@mcp.tool()
async def hackmd_search_notes(keyword: str) -> str:
    """
    Search notes by title keyword.
    Returns matching notes as JSON string.
    """
    import json
    client = get_client()
    notes = await client.get_note_list()
    filtered = [
        note
        for note in notes
        if note.get("title", "").lower().find(keyword.lower()) != -1
    ]
    return json.dumps(filtered, indent=2, ensure_ascii=False)


def main():
    """Entry point for the MCP server."""
    try:
        # Check environment early
        if not os.environ.get("HACKMD_API_TOKEN"):
             print("Error: HACKMD_API_TOKEN environment variable is not set.", file=sys.stderr)
             sys.exit(1)
             
        mcp.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
