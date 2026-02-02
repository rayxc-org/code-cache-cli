"""Pydantic models for Raysurfer API request and response types."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ── Request models ──────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    """Request body for POST /api/retrieve/search."""

    task: str
    top_k: int = 5
    min_verdict_score: float = 0.0
    prefer_complete: bool = True


class UploadFile(BaseModel):
    """A single file entry for the upload request."""

    path: str
    content: str


class UploadRequest(BaseModel):
    """Request body for POST /api/store/execution-result (single file)."""

    task: str
    file_written: UploadFile
    succeeded: bool = True
    auto_vote: bool = True


class VoteRequest(BaseModel):
    """Request body for POST /api/store/cache-usage."""

    code_block_id: str
    succeeded: bool
    task: str
    code_block_name: str = ""
    code_block_description: str = ""


class PatternsRequest(BaseModel):
    """Request body for POST /api/retrieve/task-patterns."""

    task: str
    code_block_id: str = ""
    min_thumbs_up: int = 1
    top_k: int = 5


class FewShotRequest(BaseModel):
    """Request body for POST /api/retrieve/few-shot-examples."""

    task: str
    k: int = 3


# ── Response models ─────────────────────────────────────────────────────────


class CodeBlock(BaseModel):
    """Metadata for a cached code block."""

    id: str = ""
    name: str = ""
    description: str = ""
    source: str = ""
    entrypoint: str = ""
    language: str = ""
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class SearchMatch(BaseModel):
    """A single match returned from a search query."""

    code_block: Optional[CodeBlock] = None
    combined_score: float = 0.0
    vector_score: float = 0.0
    verdict_score: float = 0.0
    thumbs_up: int = 0
    thumbs_down: int = 0
    filename: str = ""
    language: str = ""
    entrypoint: str = ""
    dependencies: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Response from POST /api/retrieve/search."""

    matches: List[SearchMatch] = Field(default_factory=list)
    total_found: int = 0
    cache_hit: bool = False
    search_namespaces: List[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """Response from POST /api/store/execution-result."""

    success: bool = False
    code_block_ids: List[str] = Field(default_factory=list)
    message: str = ""


class VoteResponse(BaseModel):
    """Response from POST /api/store/cache-usage."""

    success: bool = False
    message: str = ""


class PatternEntry(BaseModel):
    """A single pattern entry from task-patterns."""

    code_block: Optional[CodeBlock] = None
    thumbs_up: int = 0
    thumbs_down: int = 0
    combined_score: float = 0.0
    # Allow extra fields the API may return.
    model_config = {"extra": "allow"}


class PatternsResponse(BaseModel):
    """Response from POST /api/retrieve/task-patterns."""

    patterns: List[PatternEntry] = Field(default_factory=list)
    model_config = {"extra": "allow"}


class FewShotExample(BaseModel):
    """A single few-shot example."""

    task: str = ""
    code: str = ""
    model_config = {"extra": "allow"}


class FewShotResponse(BaseModel):
    """Response from POST /api/retrieve/few-shot-examples."""

    examples: List[FewShotExample] = Field(default_factory=list)
    model_config = {"extra": "allow"}
