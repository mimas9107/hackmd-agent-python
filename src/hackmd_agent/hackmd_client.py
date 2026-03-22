"""HackMD API client for Python."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

import httpx


@dataclass
class RetryInfo:
    """Information about retry attempts."""

    attempted: bool = False
    total_attempts: int = 1
    last_wait_seconds: float = 0.0
    final_wait_total: float = 0.0


class HackMDClient:
    """HackMD API client with retry and rate limit handling."""

    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 1.0
    DEFAULT_MAX_DELAY = 32.0

    def __init__(
        self,
        api_token: str,
        base_url: str = "https://api.hackmd.io/v1",
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
    ) -> None:
        self.base_url = base_url
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
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

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        retry_info: RetryInfo | None = None,
        progress_callback: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with retry and exponential backoff.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            retry_info: Optional RetryInfo to track retry attempts
            progress_callback: Optional callback to report progress to AI agent
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Response object

        Raises:
            httpx.HTTPStatusError: After all retries exhausted
        """
        if retry_info is None:
            retry_info = RetryInfo()

        async def wait(seconds: float, reason: str = "") -> None:
            retry_info.last_wait_seconds = seconds
            retry_info.final_wait_total += seconds
            if progress_callback:
                progress_callback(f"Rate limited. Waiting {seconds:.1f}s... ({reason})")
            await asyncio.sleep(seconds)

        async def calc_delay(attempt: int, retry_after: float | None) -> float:
            if retry_after and retry_after > 0:
                return min(retry_after, self.max_delay)
            return min(self.base_delay * (2**attempt), self.max_delay)

        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(method, url, **kwargs)

                if response.status_code == 429:
                    retry_info.attempted = True
                    retry_after = response.headers.get("Retry-After")
                    retry_after_val: float | None = None
                    if retry_after:
                        try:
                            retry_after_val = float(retry_after)
                        except ValueError:
                            pass

                    if attempt < self.max_retries:
                        delay = await calc_delay(attempt, retry_after_val)
                        retry_info.total_attempts = attempt + 2
                        await wait(delay, f"attempt {attempt + 1}/{self.max_retries}")
                        continue
                    else:
                        response.raise_for_status()

                if response.status_code >= 500:
                    retry_info.attempted = True
                    if attempt < self.max_retries:
                        delay = await calc_delay(attempt, None)
                        retry_info.total_attempts = attempt + 2
                        await wait(
                            delay,
                            f"server error ({response.status_code}), "
                            f"attempt {attempt + 1}/{self.max_retries}",
                        )
                        continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code >= 400 and e.response.status_code < 500:
                    raise

            except httpx.RequestError as e:
                last_exception = e
                retry_info.attempted = True
                if attempt < self.max_retries:
                    delay = await calc_delay(attempt, None)
                    retry_info.total_attempts = attempt + 2
                    await wait(
                        delay,
                        f"connection error ({type(e).__name__}), "
                        f"attempt {attempt + 1}/{self.max_retries}",
                    )
                    continue

        if last_exception:
            raise last_exception
        raise httpx.HTTPStatusError(
            "Max retries exceeded",
            request=httpx.Request(method, url),
            response=httpx.Response(500),
        )

    async def get_note_list(
        self,
        retry_info: RetryInfo | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Get all notes for the authenticated user."""
        response = await self._request_with_retry(
            "GET",
            "/notes",
            retry_info=retry_info,
            progress_callback=progress_callback,
        )
        return response.json()

    async def get_note(
        self,
        note_id: str,
        retry_info: RetryInfo | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Get a specific note by ID."""
        response = await self._request_with_retry(
            "GET",
            f"/notes/{note_id}",
            retry_info=retry_info,
            progress_callback=progress_callback,
        )
        return response.json()

    async def create_note(
        self,
        title: str,
        content: str,
        read_permission: Literal["owner", "signed_in", "guest"] | None = None,
        write_permission: Literal["owner", "signed_in", "guest"] | None = None,
        retry_info: RetryInfo | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Create a new note."""
        data: dict[str, Any] = {"title": title, "content": content}
        if read_permission:
            data["readPermission"] = read_permission
        if write_permission:
            data["writePermission"] = write_permission

        response = await self._request_with_retry(
            "POST",
            "/notes",
            json=data,
            retry_info=retry_info,
            progress_callback=progress_callback,
        )
        return response.json()

    async def update_note(
        self,
        note_id: str,
        content: str,
        read_permission: Literal["owner", "signed_in", "guest"] | None = None,
        write_permission: Literal["owner", "signed_in", "guest"] | None = None,
        retry_info: RetryInfo | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Update an existing note."""
        data: dict[str, Any] = {"content": content}
        if read_permission:
            data["readPermission"] = read_permission
        if write_permission:
            data["writePermission"] = write_permission

        response = await self._request_with_retry(
            "PATCH",
            f"/notes/{note_id}",
            json=data,
            retry_info=retry_info,
            progress_callback=progress_callback,
        )
        return response.json()

    async def delete_note(
        self,
        note_id: str,
        retry_info: RetryInfo | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> None:
        """Delete a note."""
        await self._request_with_retry(
            "DELETE",
            f"/notes/{note_id}",
            retry_info=retry_info,
            progress_callback=progress_callback,
        )

    async def search_notes(
        self,
        keyword: str,
        search_content: bool = False,
        progress_callback: Callable[[str], None] | None = None,
    ) -> tuple[list[dict[str, Any]], RetryInfo]:
        """Search notes by title (and optionally content).

        Args:
            keyword: The keyword to search for.
            search_content: If True, also search within note content.
            progress_callback: Callback to report progress to AI agent.

        Returns:
            Tuple of (matching notes list, RetryInfo)
        """
        retry_info = RetryInfo()
        notes = await self.get_note_list(
            retry_info=retry_info,
            progress_callback=progress_callback,
        )
        keyword_lower = keyword.lower()

        if not search_content:
            filtered = [
                note
                for note in notes
                if note.get("title", "").lower().find(keyword_lower) != -1
            ]
            return filtered, retry_info

        filtered = []
        total = len(notes)
        for i, note in enumerate(notes):
            title_match = note.get("title", "").lower().find(keyword_lower) != -1
            if title_match:
                filtered.append(note)
                continue

            if progress_callback and i % 5 == 0:
                progress_callback(f"Searching content... {i + 1}/{total} notes checked")

            try:
                note_retry = RetryInfo()
                full_note = await self.get_note(
                    note.get("id", ""),
                    retry_info=note_retry,
                    progress_callback=progress_callback,
                )
                retry_info.final_wait_total += note_retry.final_wait_total
                if full_note.get("content", "").lower().find(keyword_lower) != -1:
                    filtered.append(note)
            except Exception:
                continue

        return filtered, retry_info
