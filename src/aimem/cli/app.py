"""aimem CLI — AI Agent Memory Manager.

Operator set informed by Autogenesis's 16-operator Context Manager API,
adapted for memory-specific operations.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from aimem.core.config import DEFAULT_MEMORY_DIR
from aimem.core.note import MemoryType
from aimem.core.repository import MemoryRepository

logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _get_repo(memory_dir: str | None) -> MemoryRepository:
    root = Path(memory_dir) if memory_dir else DEFAULT_MEMORY_DIR
    return MemoryRepository(root=root)


@click.group()
@click.option(
    "--memory-dir",
    envvar="AIMEM_DIR",
    default=None,
    help=f"Memory repository path (default: {DEFAULT_MEMORY_DIR})",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, memory_dir: str | None, verbose: bool) -> None:
    """aimem — AI Agent Memory Manager.

    Git-based persistent memory for local AI coding agents.
    """
    _setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["memory_dir"] = memory_dir


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize a new memory repository at ~/.ai-memory/."""
    repo = _get_repo(ctx.obj["memory_dir"])
    if repo.is_initialized:
        click.echo(f"Repository already exists at {repo.root}")
        sys.exit(1)

    path = repo.init()
    click.echo(f"Initialized memory repository at {path}")
    click.echo("Directory structure created:")
    click.echo("  identity/       — core persistent facts (Tier 1)")
    click.echo("  knowledge/      — domain facts, project conventions (Tier 2-3)")
    click.echo("  procedures/     — how-to recipes, workflows (Tier 2-3)")
    click.echo("  journal/        — episode logs, decisions (Tier 3)")


@cli.command()
@click.argument("memory_type", type=click.Choice([t.value for t in MemoryType]))
@click.argument("title")
@click.option("--body", "-b", default="", help="Note body content")
@click.option("--tags", "-t", multiple=True, help="Tags for the note")
@click.option("--summary", "-s", default="", help="One-line summary for retrieval")
@click.option("--project", "-p", default=None, help="Project scope")
@click.option("--commit/--no-commit", default=True, help="Auto-commit after adding")
@click.pass_context
def add(
    ctx: click.Context,
    memory_type: str,
    title: str,
    body: str,
    tags: tuple[str, ...],
    summary: str,
    project: str | None,
    commit: bool,
) -> None:
    """Create a new memory note."""
    repo = _get_repo(ctx.obj["memory_dir"])
    if not repo.is_initialized:
        click.echo("Error: repository not initialized. Run 'aimem init' first.")
        sys.exit(1)

    kwargs: dict[str, str] = {}
    if summary:
        kwargs["summary"] = summary
    if project:
        kwargs["project"] = project

    note = repo.add_note(
        memory_type=MemoryType(memory_type),
        title=title,
        body=body,
        tags=list(tags),
        **kwargs,
    )

    if commit:
        rel_path = note.path.relative_to(repo.root)
        repo.commit(f"Add {memory_type}: {title}", paths=[str(rel_path)])

    click.echo(f"Created: {note.path.relative_to(repo.root)}")


@cli.command()
@click.argument("path")
@click.pass_context
def get(ctx: click.Context, path: str) -> None:
    """Read a specific memory note by path."""
    repo = _get_repo(ctx.obj["memory_dir"])
    note = repo.get_note(path)
    if not note:
        click.echo(f"Note not found: {path}")
        sys.exit(1)

    click.echo(f"# {note.title}")
    click.echo(f"Type: {note.meta.type.value}")
    click.echo(f"Tags: {', '.join(note.meta.tags)}")
    click.echo(f"Confidence: {note.meta.confidence.value}")
    click.echo(f"Updated: {note.meta.updated}")
    if note.meta.summary:
        click.echo(f"Summary: {note.meta.summary}")
    click.echo("---")
    click.echo(note.body)


@cli.command("list")
@click.option(
    "--type",
    "memory_type",
    type=click.Choice([t.value for t in MemoryType]),
    default=None,
    help="Filter by memory type",
)
@click.option("--tags", "-t", multiple=True, help="Filter by tags")
@click.option("--project", "-p", default=None, help="Filter by project")
@click.pass_context
def list_notes(
    ctx: click.Context,
    memory_type: str | None,
    tags: tuple[str, ...],
    project: str | None,
) -> None:
    """List memory notes, optionally filtered."""
    repo = _get_repo(ctx.obj["memory_dir"])
    if not repo.is_initialized:
        click.echo("Error: repository not initialized. Run 'aimem init' first.")
        sys.exit(1)

    mt = MemoryType(memory_type) if memory_type else None
    notes = repo.list_notes(
        memory_type=mt,
        tags=list(tags) if tags else None,
        project=project,
    )

    if not notes:
        click.echo("No notes found.")
        return

    for note in notes:
        rel = note.path.relative_to(repo.root)
        tag_str = ", ".join(note.meta.tags[:3])
        click.echo(f"  {rel}  [{note.meta.type.value}]  ({tag_str})")

    click.echo(f"\n{len(notes)} note(s)")


@cli.command()
@click.argument("path")
@click.option("--commit/--no-commit", default=True, help="Auto-commit after removing")
@click.pass_context
def remove(ctx: click.Context, path: str, commit: bool) -> None:
    """Soft-delete a memory note (move to .archive/)."""
    repo = _get_repo(ctx.obj["memory_dir"])
    if repo.remove_note(path):
        if commit:
            repo.commit(f"Archive: {path}")
        click.echo(f"Archived: {path}")
    else:
        click.echo(f"Note not found: {path}")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show memory repository status."""
    repo = _get_repo(ctx.obj["memory_dir"])
    if not repo.is_initialized:
        click.echo("Not initialized. Run 'aimem init' first.")
        sys.exit(1)

    counts: dict[str, int] = {}
    for mt in MemoryType:
        notes = repo.list_notes(memory_type=mt)
        counts[mt.value] = len(notes)

    total = sum(counts.values())
    click.echo(f"Memory repository: {repo.root}")
    click.echo(f"Total notes: {total}")
    for type_name, count in counts.items():
        click.echo(f"  {type_name}: {count}")


@cli.command()
@click.pass_context
def sync(ctx: click.Context) -> None:
    """Sync with remote (git pull --rebase && git push)."""
    repo = _get_repo(ctx.obj["memory_dir"])
    if repo.sync():
        click.echo("Synced successfully.")
    else:
        click.echo("Sync failed. Check git status.")
        sys.exit(1)


@cli.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Check all notes for valid frontmatter."""
    repo = _get_repo(ctx.obj["memory_dir"])
    notes = repo.list_notes()
    errors = 0

    for note in notes:
        rel = note.path.relative_to(repo.root)
        if not note.meta.summary:
            click.echo(f"  WARN: {rel} — missing summary field")
        if not note.meta.tags:
            click.echo(f"  WARN: {rel} — no tags")

    click.echo(f"\nValidated {len(notes)} note(s), {errors} error(s)")
