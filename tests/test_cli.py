"""Integration tests for the raysurfer CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest


def _run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run the raysurfer CLI as a subprocess and return the result."""
    merged_env = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, "-m", "raysurfer_cli.cli", *args],
        capture_output=True,
        text=True,
        env=merged_env,
        timeout=30,
    )


# ── version ─────────────────────────────────────────────────────────────────


class TestVersion:
    """Tests for the version subcommand."""

    def test_version_outputs_semver(self) -> None:
        """Version command prints a semver-style version string."""
        result = _run(["version"])
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_version_json(self) -> None:
        """Version command with --json returns valid JSON containing the version."""
        result = _run(["version", "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["version"] == "0.1.0"


# ── search (requires RAYSURFER_API_KEY) ────────────────────────────────────


@pytest.mark.skipif(
    not os.environ.get("RAYSURFER_API_KEY"),
    reason="RAYSURFER_API_KEY not set",
)
class TestSearchIntegration:
    """Live integration tests for the search subcommand."""

    def test_search_returns_results_or_empty(self) -> None:
        """Search does not error and returns structured output."""
        result = _run(["search", "Generate a quarterly revenue report"])
        assert result.returncode == 0
        assert "Found" in result.stdout or "result" in result.stdout.lower()

    def test_search_json(self) -> None:
        """Search with --json returns valid JSON."""
        result = _run(["search", "Generate a quarterly revenue report", "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "matches" in data
        assert "total_found" in data

    def test_search_show_code(self) -> None:
        """Search with --show-code does not error."""
        result = _run(["search", "hello world python", "--show-code"])
        assert result.returncode == 0


# ── missing key ─────────────────────────────────────────────────────────────


class TestMissingKey:
    """Tests verifying behaviour when the API key is absent."""

    def test_search_without_key_fails(self) -> None:
        """Search fails gracefully when RAYSURFER_API_KEY is unset."""
        env = {k: v for k, v in os.environ.items() if k != "RAYSURFER_API_KEY"}
        result = _run(["search", "test query"], env=env)
        assert result.returncode != 0
        assert "RAYSURFER_API_KEY" in result.stderr
