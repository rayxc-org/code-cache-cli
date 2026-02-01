"""Sync and async HTTP clients for the Raysurfer API."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from raysurfer_cli import __version__
from raysurfer_cli.types import (
    FewShotRequest,
    FewShotResponse,
    PatternsRequest,
    PatternsResponse,
    SearchRequest,
    SearchResponse,
    UploadRequest,
    UploadResponse,
    VoteRequest,
    VoteResponse,
)

DEFAULT_BASE_URL = "https://api.raysurfer.com"
USER_AGENT = f"raysurfer-code-caching-cli/{__version__}"
DEFAULT_TIMEOUT = 30.0


def _get_api_key() -> str:
    """Return the API key from the RAYSURFER_API_KEY environment variable or raise."""
    key = os.environ.get("RAYSURFER_API_KEY", "")
    if not key:
        raise RuntimeError(
            "RAYSURFER_API_KEY environment variable is not set. "
            "Set it to your Raysurfer API key before running commands."
        )
    return key


def _headers(api_key: str) -> Dict[str, str]:
    """Build common request headers."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }


# ── Synchronous client ─────────────────────────────────────────────────────


class RaysurferClient:
    """Synchronous client for the Raysurfer API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialise with optional explicit key, base URL, and timeout."""
        self.api_key = api_key or _get_api_key()
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=_headers(self.api_key),
            timeout=timeout,
        )

    # -- lifecycle -----------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP transport."""
        self._client.close()

    def __enter__(self) -> "RaysurferClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # -- endpoints -----------------------------------------------------------

    def search(self, request: SearchRequest) -> SearchResponse:
        """Search for cached code snippets matching a task description."""
        resp = self._client.post(
            "/api/retrieve/search",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return SearchResponse.model_validate(resp.json())

    def upload(self, request: UploadRequest) -> UploadResponse:
        """Upload code as a cached execution result."""
        resp = self._client.post(
            "/api/store/execution-result",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return UploadResponse.model_validate(resp.json())

    def vote(self, request: VoteRequest) -> VoteResponse:
        """Vote on a cached code block (thumbs up / thumbs down)."""
        resp = self._client.post(
            "/api/store/cache-usage",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return VoteResponse.model_validate(resp.json())

    def patterns(self, request: PatternsRequest) -> PatternsResponse:
        """Retrieve proven task patterns."""
        resp = self._client.post(
            "/api/retrieve/task-patterns",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return PatternsResponse.model_validate(resp.json())

    def few_shot_examples(self, request: FewShotRequest) -> FewShotResponse:
        """Retrieve few-shot examples for a task."""
        resp = self._client.post(
            "/api/retrieve/few-shot-examples",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return FewShotResponse.model_validate(resp.json())


# ── Asynchronous client ────────────────────────────────────────────────────


class AsyncRaysurferClient:
    """Asynchronous client for the Raysurfer API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialise with optional explicit key, base URL, and timeout."""
        self.api_key = api_key or _get_api_key()
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=_headers(self.api_key),
            timeout=timeout,
        )

    # -- lifecycle -----------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying async HTTP transport."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncRaysurferClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # -- endpoints -----------------------------------------------------------

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Search for cached code snippets matching a task description."""
        resp = await self._client.post(
            "/api/retrieve/search",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return SearchResponse.model_validate(resp.json())

    async def upload(self, request: UploadRequest) -> UploadResponse:
        """Upload code as a cached execution result."""
        resp = await self._client.post(
            "/api/store/execution-result",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return UploadResponse.model_validate(resp.json())

    async def vote(self, request: VoteRequest) -> VoteResponse:
        """Vote on a cached code block (thumbs up / thumbs down)."""
        resp = await self._client.post(
            "/api/store/cache-usage",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return VoteResponse.model_validate(resp.json())

    async def patterns(self, request: PatternsRequest) -> PatternsResponse:
        """Retrieve proven task patterns."""
        resp = await self._client.post(
            "/api/retrieve/task-patterns",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return PatternsResponse.model_validate(resp.json())

    async def few_shot_examples(self, request: FewShotRequest) -> FewShotResponse:
        """Retrieve few-shot examples for a task."""
        resp = await self._client.post(
            "/api/retrieve/few-shot-examples",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return FewShotResponse.model_validate(resp.json())
