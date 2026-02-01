"""Tests for HackMD tools."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from hackmd_agent.tools import create_hackmd_tools


@pytest.fixture
def mock_client():
    """Create a mock HackMD client."""
    with patch("hackmd_agent.tools.HackMDClient") as MockClient:
        client = MockClient.return_value
        client.get_note_list = AsyncMock(
            return_value=[
                {"id": "note1", "title": "Test Note 1"},
                {"id": "note2", "title": "Test Note 2"},
            ]
        )
        client.get_note = AsyncMock(
            return_value={
                "id": "note1",
                "title": "Test Note",
                "content": "# Hello World",
            }
        )
        client.create_note = AsyncMock(
            return_value={
                "id": "new-note",
                "title": "New Note",
                "publishLink": "https://hackmd.io/new-note",
            }
        )
        client.update_note = AsyncMock(
            return_value={"id": "note1", "title": "Updated Note"}
        )
        client.delete_note = AsyncMock(return_value=None)
        yield client


def test_create_all_tools(mock_client):
    """Test that all required tools are created."""
    tools = create_hackmd_tools("test-token")
    tool_names = [t.name for t in tools]

    assert "hackmd_list_notes" in tool_names
    assert "hackmd_read_note" in tool_names
    assert "hackmd_create_note" in tool_names
    assert "hackmd_update_note" in tool_names
    assert "hackmd_delete_note" in tool_names
    assert "hackmd_search_notes" in tool_names


@pytest.mark.asyncio
async def test_list_notes(mock_client):
    """Test listing notes."""
    tools = create_hackmd_tools("test-token")
    tool = next(t for t in tools if t.name == "hackmd_list_notes")

    result = await tool.call({})
    parsed = json.loads(result)

    assert len(parsed) == 2
    assert parsed[0]["id"] == "note1"


@pytest.mark.asyncio
async def test_read_note(mock_client):
    """Test reading a note."""
    tools = create_hackmd_tools("test-token")
    tool = next(t for t in tools if t.name == "hackmd_read_note")

    result = await tool.call({"noteId": "note1"})
    parsed = json.loads(result)

    assert parsed["id"] == "note1"
    assert parsed["content"] == "# Hello World"


@pytest.mark.asyncio
async def test_read_note_missing_id(mock_client):
    """Test reading a note without ID."""
    tools = create_hackmd_tools("test-token")
    tool = next(t for t in tools if t.name == "hackmd_read_note")

    with pytest.raises(ValueError, match="noteId is required"):
        await tool.call({})


@pytest.mark.asyncio
async def test_create_note(mock_client):
    """Test creating a note."""
    tools = create_hackmd_tools("test-token")
    tool = next(t for t in tools if t.name == "hackmd_create_note")

    result = await tool.call({"title": "New Note", "content": "# Content"})
    parsed = json.loads(result)

    assert parsed["id"] == "new-note"


@pytest.mark.asyncio
async def test_delete_note(mock_client):
    """Test deleting a note."""
    tools = create_hackmd_tools("test-token")
    tool = next(t for t in tools if t.name == "hackmd_delete_note")

    result = await tool.call({"noteId": "note1"})
    parsed = json.loads(result)

    assert parsed["success"] is True


@pytest.mark.asyncio
async def test_search_notes(mock_client):
    """Test searching notes."""
    tools = create_hackmd_tools("test-token")
    tool = next(t for t in tools if t.name == "hackmd_search_notes")

    result = await tool.call({"keyword": "Note 1"})
    parsed = json.loads(result)

    assert len(parsed) == 1
    assert parsed[0]["title"] == "Test Note 1"
