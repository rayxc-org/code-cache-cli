"""Typer CLI application for the Raysurfer API."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from raysurfer_cli import __version__
from raysurfer_cli.client import RaysurferClient
from raysurfer_cli.types import (
    FewShotRequest,
    PatternsRequest,
    SearchRequest,
    UploadFile,
    UploadRequest,
    VoteRequest,
)

app = typer.Typer(
    name="raysurfer",
    help="Search, upload, vote, and browse cached code snippets from the Raysurfer API.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()
err_console = Console(stderr=True)


def _fatal(message: str) -> None:
    """Print an error message and exit with code 1."""
    err_console.print(f"[bold red]Error:[/bold red] {message}")
    raise typer.Exit(code=1)


def _get_client() -> RaysurferClient:
    """Create a RaysurferClient, exiting on missing API key."""
    try:
        return RaysurferClient()
    except RuntimeError as exc:
        _fatal(str(exc))
        raise  # unreachable, keeps mypy happy


# ── search ──────────────────────────────────────────────────────────────────


@app.command()
def search(
    task: str = typer.Argument(..., help="Task description to search for"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Maximum number of results"),
    min_score: float = typer.Option(
        0.0, "--min-score", "-m", help="Minimum verdict score threshold"
    ),
    prefer_complete: bool = typer.Option(
        True, "--prefer-complete/--no-prefer-complete", help="Prefer complete snippets"
    ),
    show_code: bool = typer.Option(
        False, "--show-code", "-c", help="Display source code for each match"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
) -> None:
    """Search for cached code snippets matching a task description."""
    with _get_client() as client:
        request = SearchRequest(
            task=task,
            top_k=top_k,
            min_verdict_score=min_score,
            prefer_complete=prefer_complete,
        )
        try:
            response = client.search(request)
        except Exception as exc:
            _fatal(f"Search failed: {exc}")
            return

    if json_output:
        console.print_json(response.model_dump_json())
        return

    # Summary line
    console.print(
        f"\n[bold]Found {response.total_found} result(s)[/bold]"
        f"  |  cache_hit={response.cache_hit}"
        f"  |  namespaces={response.search_namespaces}\n"
    )

    if not response.matches:
        console.print("[dim]No matches.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Name / ID", min_width=20)
    table.add_column("Language", width=10)
    table.add_column("Score", width=8, justify="right")
    table.add_column("Votes", width=12, justify="right")

    for idx, match in enumerate(response.matches, 1):
        cb = match.code_block
        name = (cb.name if cb and cb.name else match.filename) or "unnamed"
        block_id = (cb.id if cb else "") or ""
        lang = (cb.language if cb else "") or match.language or ""
        score = f"{match.combined_score:.2f}"
        votes = f"+{match.thumbs_up} / -{match.thumbs_down}"

        label = Text(name, style="bold")
        if block_id:
            label.append(f"\n{block_id}", style="dim")

        table.add_row(str(idx), label, lang, score, votes)

    console.print(table)

    if show_code:
        console.print()
        for idx, match in enumerate(response.matches, 1):
            cb = match.code_block
            source = cb.source if cb else ""
            if not source:
                continue
            lang = (cb.language if cb else "") or match.language or "text"
            title = (cb.name if cb else "") or match.filename or f"Match #{idx}"
            console.print(
                Panel(
                    Syntax(source, lang, theme="monokai", line_numbers=True),
                    title=f"[bold]{title}[/bold]",
                    border_style="green",
                )
            )


# ── upload ──────────────────────────────────────────────────────────────────


@app.command()
def upload(
    task: str = typer.Argument(..., help="Task description for the uploaded code"),
    files: List[Path] = typer.Option(
        ..., "--file", "-f", help="File path(s) to upload (can be repeated)"
    ),
    succeeded: bool = typer.Option(True, "--succeeded/--failed", help="Mark execution as succeeded or failed"),
    no_auto_vote: bool = typer.Option(False, "--no-auto-vote", help="Disable automatic upvote"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
) -> None:
    """Upload code files as a cached execution result."""
    files_written: List[UploadFile] = []
    for fp in files:
        if not fp.exists():
            _fatal(f"File not found: {fp}")
            return
        files_written.append(
            UploadFile(path=str(fp), content=fp.read_text(encoding="utf-8"))
        )

    with _get_client() as client:
        request = UploadRequest(
            task=task,
            files_written=files_written,
            succeeded=succeeded,
            auto_vote=not no_auto_vote,
        )
        try:
            response = client.upload(request)
        except Exception as exc:
            _fatal(f"Upload failed: {exc}")
            return

    if json_output:
        console.print_json(response.model_dump_json())
        return

    if response.success:
        console.print(f"[bold green]Uploaded successfully.[/bold green]  {response.message}")
        if response.code_block_ids:
            console.print(f"Code block IDs: {', '.join(response.code_block_ids)}")
    else:
        console.print(f"[bold red]Upload failed.[/bold red]  {response.message}")


# ── vote ────────────────────────────────────────────────────────────────────


@app.command()
def vote(
    code_block_id: str = typer.Argument(..., help="Code block ID to vote on"),
    up: bool = typer.Option(True, "--up/--down", help="Upvote (default) or downvote"),
    task: str = typer.Option("", "--task", "-t", help="Task description for context"),
    name: str = typer.Option("", "--name", "-n", help="Code block name"),
    description: str = typer.Option("", "--description", "-d", help="Code block description"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
) -> None:
    """Vote on a cached code block (upvote or downvote)."""
    with _get_client() as client:
        request = VoteRequest(
            code_block_id=code_block_id,
            succeeded=up,
            task=task,
            code_block_name=name,
            code_block_description=description,
        )
        try:
            response = client.vote(request)
        except Exception as exc:
            _fatal(f"Vote failed: {exc}")
            return

    if json_output:
        console.print_json(response.model_dump_json())
        return

    icon = "thumbs up" if up else "thumbs down"
    if response.success:
        console.print(
            f"[bold green]Voted {icon} on {code_block_id}.[/bold green]  {response.message}"
        )
    else:
        console.print(f"[bold red]Vote failed.[/bold red]  {response.message}")


# ── patterns ────────────────────────────────────────────────────────────────


@app.command()
def patterns(
    task: str = typer.Argument(..., help="Task description to find patterns for"),
    code_block_id: str = typer.Option("", "--id", help="Filter by code block ID"),
    min_thumbs_up: int = typer.Option(1, "--min-up", help="Minimum thumbs-up count"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Maximum number of results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
) -> None:
    """Get proven task patterns from the community registry."""
    with _get_client() as client:
        request = PatternsRequest(
            task=task,
            code_block_id=code_block_id,
            min_thumbs_up=min_thumbs_up,
            top_k=top_k,
        )
        try:
            response = client.patterns(request)
        except Exception as exc:
            _fatal(f"Patterns lookup failed: {exc}")
            return

    if json_output:
        console.print_json(response.model_dump_json())
        return

    if not response.patterns:
        console.print("[dim]No patterns found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Name / ID", min_width=20)
    table.add_column("Score", width=8, justify="right")
    table.add_column("Votes", width=12, justify="right")

    for idx, pat in enumerate(response.patterns, 1):
        cb = pat.code_block
        name = (cb.name if cb else "") or "unnamed"
        block_id = (cb.id if cb else "") or ""
        score = f"{pat.combined_score:.2f}"
        votes = f"+{pat.thumbs_up} / -{pat.thumbs_down}"

        label = Text(name, style="bold")
        if block_id:
            label.append(f"\n{block_id}", style="dim")

        table.add_row(str(idx), label, score, votes)

    console.print(table)


# ── examples ────────────────────────────────────────────────────────────────


@app.command()
def examples(
    task: str = typer.Argument(..., help="Task description to find examples for"),
    k: int = typer.Option(3, "--k", "-k", help="Number of examples"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
) -> None:
    """Get few-shot examples for a task."""
    with _get_client() as client:
        request = FewShotRequest(task=task, k=k)
        try:
            response = client.few_shot_examples(request)
        except Exception as exc:
            _fatal(f"Examples lookup failed: {exc}")
            return

    if json_output:
        console.print_json(response.model_dump_json())
        return

    if not response.examples:
        console.print("[dim]No examples found.[/dim]")
        return

    for idx, ex in enumerate(response.examples, 1):
        console.print(
            Panel(
                Syntax(ex.code or "(no code)", "python", theme="monokai", line_numbers=True),
                title=f"[bold]Example {idx}[/bold] - {ex.task or 'untitled'}",
                border_style="blue",
            )
        )


# ── version ─────────────────────────────────────────────────────────────────


@app.command()
def version(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
) -> None:
    """Print the raysurfer-code-caching-cli version."""
    if json_output:
        console.print_json(json.dumps({"version": __version__}))
    else:
        console.print(f"raysurfer-code-caching-cli [bold]{__version__}[/bold]")


# ── entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
