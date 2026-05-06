"""aimem CLI — AI Agent Memory Manager (design.md §5).

Phase-1 commands: init, add, show, list, tag, link, query, sync, status,
verify, layer (list/scope), serve (MCP).

All commands accept ``--json`` for machine-readable output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from aimem.core import logging as _logging
from aimem.core.config import DEFAULT_MEMORY_DIR, AimemConfig
from aimem.core.error import AimemError
from aimem.core.repository import LayerRepo
from aimem.core.schema import Layer, MemoryType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _out(data: Any, *, as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(data, default=str, indent=2))
    elif isinstance(data, str):
        click.echo(data)
    else:
        click.echo(str(data))


def _err(msg: str, *, as_json: bool, kind: str = "error") -> None:
    if as_json:
        click.echo(json.dumps({"error": {"kind": kind, "message": msg}}), err=True)
    else:
        click.echo(f"Error ({kind}): {msg}", err=True)


def _get_memory_dir(ctx: click.Context) -> Path:
    raw = ctx.obj.get("memory_dir")
    return Path(raw) if raw else DEFAULT_MEMORY_DIR


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group()
@click.option(
    "--memory-dir",
    envvar="AIMEM_DIR",
    default=None,
    help=f"Memory repository path (default: {DEFAULT_MEMORY_DIR})",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.option("--json", "as_json", is_flag=True, help="Emit structured JSON output")
@click.pass_context
def cli(ctx: click.Context, memory_dir: str | None, verbose: bool, as_json: bool) -> None:
    """aimem — git-backed persistent memory for local AI coding agents."""
    _logging.configure(verbose=verbose)
    ctx.ensure_object(dict)
    ctx.obj["memory_dir"] = memory_dir
    ctx.obj["as_json"] = as_json


# ---------------------------------------------------------------------------
# aimem init
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--path", "override_path", default=None, help="Init at this path instead of default")
@click.pass_context
def init(ctx: click.Context, override_path: str | None) -> None:
    """Initialize a new memory repository at ~/.ai-memory/."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = Path(override_path) if override_path else _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)

    if repo.is_initialized:
        msg = f"Already initialized at {memory_dir}"
        _out({"result": "already-initialized", "path": str(memory_dir)} if as_json else msg, as_json=as_json)
        return

    try:
        path = repo.init(memory_dir)
        _out(
            {"result": "ok", "path": str(path)} if as_json else f"Initialized memory repository at {path}",
            as_json=as_json,
        )
    except AimemError as exc:
        _err(exc.message, as_json=as_json, kind=exc.kind)
        sys.exit(1)


# ---------------------------------------------------------------------------
# aimem add
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--type", "memory_type", required=True, type=click.Choice([t.value for t in MemoryType]), help="Memory type")
@click.option("--title", required=True, help="Note title")
@click.option("--body", "-b", default="", help="Note body (Markdown)")
@click.option("--tag", "-t", multiple=True, help="Tag (repeatable)")
@click.option("--layer", "layer_str", default="personal", type=click.Choice([l.value for l in Layer]), help="Target layer")
@click.option("--agent", default="cli", help="Agent name for provenance")
@click.option("--session", default="", help="Session ID for provenance")
@click.pass_context
def add(
    ctx: click.Context,
    memory_type: str,
    title: str,
    body: str,
    tag: tuple[str, ...],
    layer_str: str,
    agent: str,
    session: str,
) -> None:
    """Add a new memory note."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)

    from aimem.core.services.add import add_note

    try:
        record = add_note(
            memory_dir=memory_dir,
            layer=Layer(layer_str),
            memory_type=MemoryType(memory_type),
            title=title,
            body=body,
            tags=list(tag),
            agent=agent,
            session=session,
        )
        _out(
            record.model_dump(mode="json", exclude={"body", "path"}) if as_json
            else f"Created: {record.id} ({record.type.value}: {record.title})",
            as_json=as_json,
        )
    except AimemError as exc:
        _err(exc.message, as_json=as_json, kind=exc.kind)
        sys.exit(1)


# ---------------------------------------------------------------------------
# aimem show
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("record_id")
@click.option("--layer", "layer_str", default="personal", type=click.Choice([l.value for l in Layer]))
@click.pass_context
def show(ctx: click.Context, record_id: str, layer_str: str) -> None:
    """Show a record by ID."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)

    from aimem.core.error import NotFoundError

    try:
        rec = repo.get(record_id, Layer(layer_str))
        if as_json:
            d = rec.model_dump(mode="json")
            d["body"] = rec.body
            _out(d, as_json=True)
        else:
            click.echo(f"ID:      {rec.id}")
            click.echo(f"Type:    {rec.type.value}")
            click.echo(f"Layer:   {rec.layer.value}")
            click.echo(f"Title:   {rec.title}")
            click.echo(f"Tags:    {', '.join(rec.tags)}")
            click.echo(f"Created: {rec.created_at}")
            click.echo(f"Updated: {rec.updated_at}")
            click.echo("---")
            click.echo(rec.body)
    except NotFoundError as exc:
        _err(exc.message, as_json=as_json, kind=exc.kind)
        sys.exit(4)
    except AimemError as exc:
        _err(exc.message, as_json=as_json, kind=exc.kind)
        sys.exit(1)


# ---------------------------------------------------------------------------
# aimem list
# ---------------------------------------------------------------------------


@cli.command("list")
@click.option("--type", "memory_type", default=None, type=click.Choice([t.value for t in MemoryType]))
@click.option("--layer", "layer_str", default="personal", type=click.Choice([l.value for l in Layer]))
@click.option("--tag", "-t", multiple=True, help="Filter by tag (repeatable)")
@click.pass_context
def list_notes(ctx: click.Context, memory_type: str | None, layer_str: str, tag: tuple[str, ...]) -> None:
    """List memory records."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)
    mt = MemoryType(memory_type) if memory_type else None
    records = repo.list_records(layer=Layer(layer_str), memory_type=mt, tags=list(tag) if tag else None)

    if as_json:
        _out([{"id": r.id, "type": r.type.value, "title": r.title, "updated_at": r.updated_at, "tags": r.tags} for r in records], as_json=True)
    else:
        if not records:
            click.echo("No records found.")
            return
        for r in records:
            tag_str = ", ".join(r.tags[:3])
            click.echo(f"  {r.id}  [{r.type.value}]  {r.title}  ({tag_str})")
        click.echo(f"\n{len(records)} record(s)")


# ---------------------------------------------------------------------------
# aimem tag
# ---------------------------------------------------------------------------


@cli.group()
def tag() -> None:
    """Manage record tags."""


@tag.command("add")
@click.argument("record_id")
@click.argument("tags", nargs=-1, required=True)
@click.option("--layer", "layer_str", default="personal", type=click.Choice([l.value for l in Layer]))
@click.pass_context
def tag_add(ctx: click.Context, record_id: str, tags: tuple[str, ...], layer_str: str) -> None:
    """Add tags to a record."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)
    try:
        updated = repo.tag_record(record_id, list(tags), [])
        _out({"id": record_id, "tags": updated.tags} if as_json else f"Tags updated: {updated.tags}", as_json=as_json)
    except AimemError as exc:
        _err(exc.message, as_json=as_json, kind=exc.kind)
        sys.exit(1)


@tag.command("rm")
@click.argument("record_id")
@click.argument("tags", nargs=-1, required=True)
@click.option("--layer", "layer_str", default="personal", type=click.Choice([l.value for l in Layer]))
@click.pass_context
def tag_rm(ctx: click.Context, record_id: str, tags: tuple[str, ...], layer_str: str) -> None:
    """Remove tags from a record."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)
    try:
        updated = repo.tag_record(record_id, [], list(tags))
        _out({"id": record_id, "tags": updated.tags} if as_json else f"Tags updated: {updated.tags}", as_json=as_json)
    except AimemError as exc:
        _err(exc.message, as_json=as_json, kind=exc.kind)
        sys.exit(1)


# ---------------------------------------------------------------------------
# aimem link
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("source_id")
@click.argument("target_id")
@click.option("--type", "link_type", default="causal", type=click.Choice(["causal", "evolves", "refines"]))
@click.pass_context
def link(ctx: click.Context, source_id: str, target_id: str, link_type: str) -> None:
    """Create a link between two records."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)
    try:
        repo.link_records(source_id, target_id, link_type)
        _out(
            {"source": source_id, "target": target_id, "link_type": link_type} if as_json
            else f"Linked {source_id} --{link_type}--> {target_id}",
            as_json=as_json,
        )
    except AimemError as exc:
        _err(exc.message, as_json=as_json, kind=exc.kind)
        sys.exit(1)


# ---------------------------------------------------------------------------
# aimem query
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("query_text")
@click.option("--top-k", default=None, type=int, help="Max results (default: retrieval_window from config)")
@click.option("--layer", "layer_str", default="personal", type=click.Choice([l.value for l in Layer]))
@click.option("--type", "memory_type", default=None, type=click.Choice([t.value for t in MemoryType]))
@click.option("--tag", "-t", multiple=True)
@click.pass_context
def query(
    ctx: click.Context,
    query_text: str,
    top_k: int | None,
    layer_str: str,
    memory_type: str | None,
    tag: tuple[str, ...],
) -> None:
    """Search memory notes (hybrid BM25 + embedding)."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)

    from aimem.core.services.query import query as do_query

    try:
        results = do_query(
            memory_dir=memory_dir,
            q=query_text,
            top_k=top_k,
            layer=Layer(layer_str),
            memory_type=MemoryType(memory_type) if memory_type else None,
            tags=list(tag) if tag else None,
        )
        if as_json:
            _out(
                [{"rank": r.rank, "score": r.score, "id": r.record.id, "title": r.record.title, "type": r.record.type.value, "tags": r.record.tags} for r in results],
                as_json=True,
            )
        else:
            if not results:
                click.echo("No results found.")
                return
            for r in results:
                click.echo(f"  [{r.rank}] {r.score:.3f}  {r.record.id}  {r.record.title}")
    except AimemError as exc:
        _err(exc.message, as_json=as_json, kind=exc.kind)
        sys.exit(1)


# ---------------------------------------------------------------------------
# aimem verify
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--strict", is_flag=True, help="Also verify ed25519 signatures")
@click.option("--layer", "layer_str", default="personal", type=click.Choice([l.value for l in Layer]))
@click.pass_context
def verify(ctx: click.Context, strict: bool, layer_str: str) -> None:
    """Verify schema, signatures, and link integrity."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)

    from aimem.core.services.verify import verify as do_verify

    report = do_verify(memory_dir=memory_dir, layer=Layer(layer_str), strict=strict)
    if as_json:
        _out(report.as_dict(), as_json=True)
    else:
        if report.ok:
            click.echo("Verify: OK")
        else:
            click.echo(f"Verify: FAIL ({len(report.findings)} finding(s))")
            for f in report.findings:
                click.echo(f"  [{f.kind}] {f.record_id}: {f.message}")
    if not report.ok:
        sys.exit(1)


# ---------------------------------------------------------------------------
# aimem status
# ---------------------------------------------------------------------------


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show memory repository status."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)

    if not repo.is_initialized:
        _err("Not initialized. Run 'aimem init' first.", as_json=as_json, kind="config")
        sys.exit(1)

    counts: dict[str, int] = {}
    for mt in MemoryType:
        counts[mt.value] = len(repo.list_records(memory_type=mt))
    total = sum(counts.values())

    if as_json:
        _out({"path": str(memory_dir), "total": total, "by_type": counts}, as_json=True)
    else:
        click.echo(f"Memory repository: {memory_dir}")
        click.echo(f"Total records: {total}")
        for type_name, count in counts.items():
            click.echo(f"  {type_name}: {count}")


# ---------------------------------------------------------------------------
# aimem sync
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--layer", "layer_str", default="personal", type=click.Choice([l.value for l in Layer]))
@click.pass_context
def sync(ctx: click.Context, layer_str: str) -> None:
    """Sync a layer with its remote (git pull --rebase && git push)."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)
    ok = repo.sync(Layer(layer_str))
    if ok:
        _out({"result": "ok", "layer": layer_str} if as_json else "Synced successfully.", as_json=as_json)
    else:
        _err("Sync failed. Check git status.", as_json=as_json, kind="transient")
        sys.exit(1)


# ---------------------------------------------------------------------------
# aimem layer (sub-group)
# ---------------------------------------------------------------------------


@cli.group()
def layer() -> None:
    """Manage memory layers."""


@layer.command("list")
@click.pass_context
def layer_list(ctx: click.Context) -> None:
    """List available layers."""
    as_json: bool = ctx.obj["as_json"]
    memory_dir = _get_memory_dir(ctx)
    repo = LayerRepo(memory_dir)
    layers = []
    for lyr in Layer:
        lpath = repo.layer_path(lyr)
        layers.append({"layer": lyr.value, "path": str(lpath), "exists": lpath.exists()})
    if as_json:
        _out(layers, as_json=True)
    else:
        for info in layers:
            status_str = "active" if info["exists"] else "not initialized"
            click.echo(f"  {info['layer']:<12} {info['path']}  [{status_str}]")


@layer.command("scope")
@click.argument("layer_name", type=click.Choice([l.value for l in Layer]))
@click.pass_context
def layer_scope(ctx: click.Context, layer_name: str) -> None:
    """Set the active layer for this session (informational — Phase 1)."""
    as_json: bool = ctx.obj["as_json"]
    _out(
        {"active_layer": layer_name} if as_json else f"Active layer: {layer_name} (session scope)",
        as_json=as_json,
    )


# ---------------------------------------------------------------------------
# aimem serve (MCP server)
# ---------------------------------------------------------------------------


@cli.command()
@click.pass_context
def serve(ctx: click.Context) -> None:
    """Start the MCP server (stdio transport)."""
    memory_dir = _get_memory_dir(ctx)
    from aimem.mcp.server import run_server

    run_server(memory_dir=memory_dir)
