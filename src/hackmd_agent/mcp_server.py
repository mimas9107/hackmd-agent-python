"""MCP Server for HackMD Agent."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Literal

from fastmcp import FastMCP

from hackmd_agent.hackmd_client import HackMDClient, RetryInfo

# Initialize FastMCP
mcp = FastMCP("HackMD Agent")

# Global client and cache
_client: HackMDClient | None = None
_notes_cache: tuple[list[dict[str, Any]], float] | None = None
_CACHE_TTL_SECONDS = 60.0

# Store progress messages for the last request
_last_progress: list[str] = []


def _progress_callback(message: str) -> None:
    """Callback to track progress messages for AI agent transparency."""
    _last_progress.append(message)


def get_client() -> HackMDClient:
    """Get or create HackMDClient."""
    global _client
    if _client is None:
        token = os.environ.get("HACKMD_API_TOKEN")
        if not token:
            raise ValueError("HACKMD_API_TOKEN environment variable is required")
        _client = HackMDClient(token)
    return _client


async def get_cached_notes(
    retry_info: RetryInfo | None = None,
) -> list[dict[str, Any]]:
    """Get notes with simple in-memory caching."""
    global _notes_cache
    now = time.monotonic()
    if _notes_cache is None or (now - _notes_cache[1]) > _CACHE_TTL_SECONDS:
        client = get_client()
        notes = await client.get_note_list(
            retry_info=retry_info,
            progress_callback=_progress_callback,
        )
        _notes_cache = (notes, now)
        return notes
    return _notes_cache[0]


def _calculate_relevance(note: dict[str, Any], keyword: str) -> tuple[int, int]:
    """Calculate relevance score for ranking search results.

    Returns (score, title_length) where lower title_length = better tiebreaker.
    """
    title = note.get("title", "").lower()
    keyword_lower = keyword.lower()

    if title == keyword_lower:
        return (100, len(title))
    if title.startswith(keyword_lower):
        return (90, len(title))
    if title.startswith(keyword_lower.split()[0] + " "):
        return (80, len(title))
    if keyword_lower in title:
        return (70, len(title))

    words = keyword_lower.split()
    if any(w in title for w in words):
        return (60, len(title))

    return (0, len(title))


def _fuzzy_match(text: str, keyword: str, threshold: float = 0.6) -> bool:
    """Simple fuzzy matching using character overlap ratio."""
    text_lower = text.lower()
    keyword_lower = keyword.lower()

    if keyword_lower in text_lower:
        return True

    key_chars = set(keyword_lower.replace(" ", ""))
    text_chars = set(text_lower.replace(" ", ""))

    if not key_chars:
        return False

    overlap = len(key_chars & text_chars) / len(key_chars)
    return overlap >= threshold


def _invalidate_cache() -> None:
    """Invalidate the notes cache."""
    global _notes_cache
    _notes_cache = None


def _build_response(data: Any, retry_info: RetryInfo) -> str:
    """Build JSON response with retry metadata for AI agent transparency."""
    global _last_progress
    result = {
        "data": data,
        "_meta": {
            "retry_info": {
                "was_rate_limited": retry_info.attempted,
                "total_attempts": retry_info.total_attempts,
                "total_wait_seconds": round(retry_info.final_wait_total, 2),
            },
            "progress_messages": _last_progress.copy() if _last_progress else None,
        },
    }
    _last_progress = []
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def hackmd_list_notes() -> str:
    """
    List all notes from HackMD.
    Returns a JSON string containing an array of note metadata.
    """
    client = get_client()
    retry_info = RetryInfo()
    notes = await client.get_note_list(
        retry_info=retry_info,
        progress_callback=_progress_callback,
    )
    return _build_response(notes, retry_info)


@mcp.tool()
async def hackmd_read_note(note_id: str) -> str:
    """
    Read a note's full content by its ID.
    Returns a JSON string containing the note metadata and content.
    """
    client = get_client()
    retry_info = RetryInfo()
    note = await client.get_note(
        note_id,
        retry_info=retry_info,
        progress_callback=_progress_callback,
    )
    return _build_response(note, retry_info)


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
    client = get_client()
    retry_info = RetryInfo()
    note = await client.create_note(
        title=title,
        content=content,
        read_permission=read_permission,
        write_permission=write_permission,
        retry_info=retry_info,
        progress_callback=_progress_callback,
    )
    _invalidate_cache()
    return _build_response(note, retry_info)


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
    client = get_client()
    retry_info = RetryInfo()
    note = await client.update_note(
        note_id=note_id,
        content=content,
        read_permission=read_permission,
        write_permission=write_permission,
        retry_info=retry_info,
        progress_callback=_progress_callback,
    )
    _invalidate_cache()
    return _build_response(note, retry_info)


@mcp.tool()
async def hackmd_delete_note(note_id: str) -> str:
    """
    Permanently delete a note by its ID.
    """
    client = get_client()
    retry_info = RetryInfo()
    await client.delete_note(
        note_id,
        retry_info=retry_info,
        progress_callback=_progress_callback,
    )
    _invalidate_cache()
    return _build_response(
        {"success": True, "message": "Note deleted"},
        retry_info,
    )


@mcp.tool()
async def hackmd_search_notes(
    keyword: str,
    search_content: bool = False,
    fuzzy: bool = False,
    limit: int = 20,
) -> str:
    """
    Search notes by title (and optionally content) with relevance ranking.

    Args:
        keyword: The keyword to search for.
        search_content: If True, also search within note content (slower).
                       If False, only search titles (faster, uses cached list).
        fuzzy: If True, enable fuzzy matching for typo tolerance.
              If False, use exact substring matching.
        limit: Maximum number of results to return (default: 20).

    Returns:
        JSON string containing matching notes sorted by relevance.
    """
    client = get_client()
    retry_info = RetryInfo()

    if search_content:
        notes, retry_info = await client.search_notes(
            keyword,
            search_content=True,
            progress_callback=_progress_callback,
        )
    else:
        notes = await get_cached_notes(retry_info=retry_info)

    keyword_lower = keyword.lower()
    if fuzzy:
        matched = [
            (note, _calculate_relevance(note, keyword))
            for note in notes
            if _fuzzy_match(note.get("title", ""), keyword)
        ]
    else:
        matched = [
            (note, _calculate_relevance(note, keyword))
            for note in notes
            if keyword_lower in note.get("title", "").lower()
        ]

    matched.sort(key=lambda x: (-x[1][0], x[1][1]))
    return _build_response([note for note, _ in matched[:limit]], retry_info)


def main() -> None:
    """Entry point for the MCP server."""
    try:
        if not os.environ.get("HACKMD_API_TOKEN"):
            print(
                "Error: HACKMD_API_TOKEN environment variable is not set.",
                file=sys.stderr,
            )
            sys.exit(1)

        mcp.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
