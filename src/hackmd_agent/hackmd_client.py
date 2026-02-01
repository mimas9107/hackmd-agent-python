"""HackMD API client for Python."""

import json
from typing import Any, Literal
import httpx


class HackMDClient:
    """Simple HackMD API client."""

    def __init__(
        self,
        api_token: str,
        base_url: str = "https://api.hackmd.io/v1",
    ) -> None:
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=self.headers,
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "HackMDClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def get_note_list(self) -> list[dict[str, Any]]:
        """Get all notes for the authenticated user."""
        response = await self._client.get("/notes")
        response.raise_for_status()
        return response.json()

    async def get_note(self, note_id: str) -> dict[str, Any]:
        """Get a specific note by ID."""
        response = await self._client.get(f"/notes/{note_id}")
        response.raise_for_status()
        return response.json()

    async def create_note(
        self,
        title: str,
        content: str,
        read_permission: Literal["owner", "signed_in", "guest"] | None = None,
        write_permission: Literal["owner", "signed_in", "guest"] | None = None,
    ) -> dict[str, Any]:
        """Create a new note."""
        data: dict[str, Any] = {"title": title, "content": content}
        if read_permission:
            data["readPermission"] = read_permission
        if write_permission:
            data["writePermission"] = write_permission

        response = await self._client.post("/notes", json=data)
        response.raise_for_status()
        return response.json()

    async def update_note(
        self,
        note_id: str,
        content: str,
        read_permission: Literal["owner", "signed_in", "guest"] | None = None,
        write_permission: Literal["owner", "signed_in", "guest"] | None = None,
    ) -> dict[str, Any]:
        """Update an existing note."""
        data: dict[str, Any] = {"content": content}
        if read_permission:
            data["readPermission"] = read_permission
        if write_permission:
            data["writePermission"] = write_permission

        response = await self._client.patch(f"/notes/{note_id}", json=data)
        response.raise_for_status()
        return response.json()

    async def delete_note(self, note_id: str) -> None:
        """Delete a note."""
        response = await self._client.delete(f"/notes/{note_id}")
        response.raise_for_status()
