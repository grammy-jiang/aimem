"""aimem MCP server — memory management tools for AI agents.

Exposes the same operations as the CLI via MCP protocol, enabling
direct agent integration without shell execution. The CLI and MCP
server share the same core library — no logic duplication.

MCP Tools (mapped from CLI commands):
  memory_search    — Hybrid BM25+embedding search with pyramid retrieval
  memory_get       — Read a specific memory note by path
  memory_add       — Create a new memory note (dedup + hot buffer)
  memory_update    — Update an existing memory note
  memory_remove    — Soft-delete a memory note
  memory_list      — List notes, optionally filtered by type/tag/project
  memory_link      — Create/remove links between notes
  memory_status    — Memory health summary
  memory_export    — Generate agent-specific config
  memory_consolidate — Promote hot buffer to long-term
  memory_doctor    — Run health checks, return issues
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from aimem.core.config import DEFAULT_MEMORY_DIR
from aimem.core.note import MemoryType
from aimem.core.repository import MemoryRepository

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "aimem",
    instructions=(
        "AI Agent Memory Manager. Use these tools to read, write, search, "
        "and manage persistent memory notes stored in a git repository. "
        "Memory types: identity (preferences), knowledge (facts), "
        "procedure (how-to), journal (episodes)."
    ),
)

_repo: MemoryRepository | None = None


def _get_repo() -> MemoryRepository:
    global _repo
    if _repo is None:
        _repo = MemoryRepository(root=DEFAULT_MEMORY_DIR)
    return _repo


@mcp.tool()
def memory_search(query: str, memory_type: str | None = None, limit: int = 5) -> str:
    """Search memory notes using keyword matching.

    Args:
        query: Search query string
        memory_type: Optional filter by type (identity/knowledge/procedure/journal)
        limit: Maximum results to return (default 5, for security)

    Returns:
        Matching notes with summaries for pyramid retrieval.
    """
    repo = _get_repo()
    mt = MemoryType(memory_type) if memory_type else None
    notes = repo.list_notes(memory_type=mt)

    # Basic keyword matching (Phase 2 will add BM25 + embedding)
    query_terms = set(query.lower().split())
    scored = []
    for note in notes:
        note_terms = set(note.meta.tags + note.title.lower().split())
        overlap = len(query_terms & note_terms)
        if overlap > 0:
            scored.append((overlap, note))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = scored[:limit]

    if not results:
        return "No matching notes found."

    lines = []
    for _score, note in results:
        rel = note.path.relative_to(repo.root)
        summary = note.meta.summary or note.title
        lines.append(f"[{rel}] ({note.meta.type.value}) {summary}")

    return "\n".join(lines)


@mcp.tool()
def memory_get(path: str) -> str:
    """Read a specific memory note by its relative path.

    Args:
        path: Relative path in the memory repo (e.g., 'identity/preferences.md')

    Returns:
        Full note content with metadata.
    """
    repo = _get_repo()
    note = repo.get_note(path)
    if not note:
        return f"Note not found: {path}"

    lines = [
        f"# {note.title}",
        f"Type: {note.meta.type.value}",
        f"Tags: {', '.join(note.meta.tags)}",
        f"Confidence: {note.meta.confidence.value}",
        f"Updated: {note.meta.updated}",
    ]
    if note.meta.summary:
        lines.append(f"Summary: {note.meta.summary}")
    lines.append("---")
    lines.append(note.body)
    return "\n".join(lines)


@mcp.tool()
def memory_add(
    memory_type: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    summary: str = "",
    project: str | None = None,
) -> str:
    """Create a new memory note in the repository.

    Args:
        memory_type: One of: identity, knowledge, procedure, journal
        title: Title for the memory note
        body: Content body in Markdown
        tags: List of tags for categorization and retrieval
        summary: One-line summary for pyramid retrieval
        project: Optional project scope

    Returns:
        Path of the created note.
    """
    repo = _get_repo()
    if not repo.is_initialized:
        return "Error: repository not initialized. Run 'aimem init' first."

    kwargs: dict[str, str] = {}
    if summary:
        kwargs["summary"] = summary
    if project:
        kwargs["project"] = project

    note = repo.add_note(
        memory_type=MemoryType(memory_type),
        title=title,
        body=body,
        tags=tags or [],
        **kwargs,
    )

    rel = note.path.relative_to(repo.root)
    repo.commit(f"Add {memory_type}: {title}", paths=[str(rel)])
    return f"Created: {rel}"


@mcp.tool()
def memory_remove(path: str) -> str:
    """Soft-delete a memory note by moving it to .archive/.

    Args:
        path: Relative path of the note to archive

    Returns:
        Confirmation message.
    """
    repo = _get_repo()
    if repo.remove_note(path):
        repo.commit(f"Archive: {path}")
        return f"Archived: {path}"
    return f"Note not found: {path}"


@mcp.tool()
def memory_list(
    memory_type: str | None = None,
    project: str | None = None,
) -> str:
    """List memory notes, optionally filtered by type or project.

    Args:
        memory_type: Optional filter (identity/knowledge/procedure/journal)
        project: Optional project name filter

    Returns:
        List of notes with paths and summaries.
    """
    repo = _get_repo()
    mt = MemoryType(memory_type) if memory_type else None
    notes = repo.list_notes(memory_type=mt, project=project)

    if not notes:
        return "No notes found."

    lines = []
    for note in notes:
        rel = note.path.relative_to(repo.root)
        summary = note.meta.summary or note.title
        lines.append(f"  {rel}  [{note.meta.type.value}]  {summary}")

    lines.append(f"\n{len(notes)} note(s)")
    return "\n".join(lines)


@mcp.tool()
def memory_status() -> str:
    """Show memory repository health summary.

    Returns:
        Note counts by type and repository status.
    """
    repo = _get_repo()
    if not repo.is_initialized:
        return "Not initialized. Run 'aimem init' first."

    counts: dict[str, int] = {}
    for mt in MemoryType:
        notes = repo.list_notes(memory_type=mt)
        counts[mt.value] = len(notes)

    total = sum(counts.values())
    lines = [f"Memory repository: {repo.root}", f"Total notes: {total}"]
    for type_name, count in counts.items():
        lines.append(f"  {type_name}: {count}")
    return "\n".join(lines)


def main() -> None:
    """Run the MCP server."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting aimem MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
