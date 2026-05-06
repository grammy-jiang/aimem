"""MCP server for aimem — protocol version 2025-11-25 (design.md §6).

Tools:      memory_query, memory_add, memory_link, memory_tag,
            memory_layer_list, memory_layer_scope, memory_sync,
            memory_inbox, memory_verify
Resources:  memory://record/<id>, memory://layer/<layer>/<path>
            memory://search?q=, memory://inbox
Prompts:    prompt:recall, prompt:capture
Transport:  stdio (Phase 1)
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import anyio
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from aimem.core import logging as _logging
from aimem.core.config import DEFAULT_MEMORY_DIR, AimemConfig
from aimem.core.error import AimemError
from aimem.core.repository import LayerRepo
from aimem.core.schema import Layer, MemoryType

log = _logging.get_logger(__name__)

# ---------------------------------------------------------------------------
# Build server
# ---------------------------------------------------------------------------

_MEMORY_DIR: Path = DEFAULT_MEMORY_DIR


def _repo() -> LayerRepo:
    return LayerRepo(_MEMORY_DIR)


def _tool_error(exc: Exception) -> list[types.TextContent]:
    kind = getattr(exc, "kind", "transient")
    msg = getattr(exc, "message", str(exc))
    return [types.TextContent(type="text", text=json.dumps({"error": {"kind": kind, "message": msg}}))]


def _ok(data: Any) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, default=str))]


def _build_server() -> Server:
    server: Server = Server(
        name="aimem",
        version="1.0.0",
        instructions=(
            "Local git-backed memory for AI coding agents. "
            "Use memory_add to persist facts, memory_query to recall them."
        ),
    )

    # ------------------------------------------------------------------
    # Tools list
    # ------------------------------------------------------------------

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="memory_query",
                description="Search memory using hybrid BM25 + embedding retrieval.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "q": {"type": "string", "description": "Query text"},
                        "top_k": {"type": "integer", "description": "Max results", "default": 10},
                        "layer": {"type": "string", "enum": [l.value for l in Layer], "default": "personal"},
                        "type": {"type": "string", "enum": [t.value for t in MemoryType]},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["q"],
                },
            ),
            types.Tool(
                name="memory_add",
                description="Add a new memory note. write-down requires elicitation in Phase 2.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": [t.value for t in MemoryType]},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "layer": {"type": "string", "enum": [l.value for l in Layer], "default": "personal"},
                    },
                    "required": ["type", "title"],
                },
            ),
            types.Tool(
                name="memory_link",
                description="Create a semantic link between two records.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "link_type": {"type": "string", "enum": ["causal", "evolves", "refines"], "default": "causal"},
                    },
                    "required": ["source", "target"],
                },
            ),
            types.Tool(
                name="memory_tag",
                description="Add or remove tags on a record.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "record_id": {"type": "string"},
                        "add": {"type": "array", "items": {"type": "string"}},
                        "remove": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["record_id"],
                },
            ),
            types.Tool(
                name="memory_layer_list",
                description="List available memory layers.",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="memory_layer_scope",
                description="Report current active layer (informational in Phase 1).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "layer": {"type": "string", "enum": [l.value for l in Layer]},
                    },
                    "required": ["layer"],
                },
            ),
            types.Tool(
                name="memory_sync",
                description="Sync a layer with its remote git repository.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "layer": {"type": "string", "enum": [l.value for l in Layer], "default": "personal"},
                    },
                },
            ),
            types.Tool(
                name="memory_verify",
                description="Verify schema, signatures, and link integrity of the memory store.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "strict": {"type": "boolean", "default": False},
                        "layer": {"type": "string", "enum": [l.value for l in Layer], "default": "personal"},
                    },
                },
            ),
        ]

    # ------------------------------------------------------------------
    # Tools call
    # ------------------------------------------------------------------

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:  # type: ignore[arg-type]
        try:
            if name == "memory_query":
                return await _tool_memory_query(arguments)
            elif name == "memory_add":
                return await _tool_memory_add(arguments)
            elif name == "memory_link":
                return await _tool_memory_link(arguments)
            elif name == "memory_tag":
                return await _tool_memory_tag(arguments)
            elif name == "memory_layer_list":
                return await _tool_layer_list(arguments)
            elif name == "memory_layer_scope":
                return await _tool_layer_scope(arguments)
            elif name == "memory_sync":
                return await _tool_memory_sync(arguments)
            elif name == "memory_verify":
                return await _tool_memory_verify(arguments)
            else:
                return _tool_error(ValueError(f"Unknown tool: {name}"))
        except AimemError as exc:
            log.warning(op=f"mcp.tool.{name}", error=exc.kind, message=exc.message)
            return _tool_error(exc)
        except Exception as exc:
            log.error(op=f"mcp.tool.{name}", error=str(exc))
            return _tool_error(exc)

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        resources: list[types.Resource] = []
        try:
            repo = _repo()
            records = repo.list_records()
            for rec in records[:50]:
                resources.append(
                    types.Resource(
                        uri=f"memory://record/{rec.id}",  # type: ignore[arg-type]
                        name=rec.title,
                        description=f"{rec.type.value} — {rec.layer.value}",
                        mimeType="text/markdown",
                    )
                )
        except Exception:
            pass
        return resources

    @server.read_resource()
    async def read_resource(uri: Any) -> str:
        uri_str = str(uri)
        try:
            if uri_str.startswith("memory://record/"):
                record_id = uri_str.removeprefix("memory://record/")
                repo = _repo()
                rec = repo.get(record_id)
                return rec.body or ""
            return ""
        except AimemError as exc:
            return json.dumps({"error": {"kind": exc.kind, "message": exc.message}})

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return [
            types.Prompt(
                name="recall",
                description="Recall relevant memories for a given task or question.",
                arguments=[
                    types.PromptArgument(name="topic", description="What to recall", required=True),
                ],
            ),
            types.Prompt(
                name="capture",
                description="Capture an observation or preference into memory.",
                arguments=[
                    types.PromptArgument(name="observation", description="What to capture", required=True),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        args = arguments or {}
        if name == "recall":
            topic = args.get("topic", "the current task")
            return types.GetPromptResult(
                description=f"Recall memories about: {topic}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Search my memory store for anything relevant to: {topic}\n\nUse memory_query to retrieve related records.",
                        ),
                    )
                ],
            )
        elif name == "capture":
            observation = args.get("observation", "")
            return types.GetPromptResult(
                description="Capture observation into memory",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Please capture the following into memory using memory_add:\n\n{observation}",
                        ),
                    )
                ],
            )
        raise ValueError(f"Unknown prompt: {name}")

    return server


# ------------------------------------------------------------------
# Tool implementations
# ------------------------------------------------------------------


async def _tool_memory_query(args: dict[str, Any]) -> list[types.TextContent]:
    from aimem.core.services.query import query as do_query

    results = do_query(
        memory_dir=_MEMORY_DIR,
        q=args["q"],
        top_k=args.get("top_k"),
        layer=Layer(args.get("layer", "personal")),
        memory_type=MemoryType(args["type"]) if args.get("type") else None,
        tags=args.get("tags"),
    )
    return _ok(
        [
            {
                "rank": r.rank,
                "score": r.score,
                "id": r.record.id,
                "title": r.record.title,
                "type": r.record.type.value,
                "tags": r.record.tags,
            }
            for r in results
        ]
    )


async def _tool_memory_add(args: dict[str, Any]) -> list[types.TextContent]:
    from aimem.core.services.add import add_note

    agent_id = os.environ.get("AIMEM_AGENT_ID", "mcp-client")
    session_id = os.environ.get("AIMEM_SESSION_ID", "")
    record = add_note(
        memory_dir=_MEMORY_DIR,
        layer=Layer(args.get("layer", "personal")),
        memory_type=MemoryType(args["type"]),
        title=args["title"],
        body=args.get("body", ""),
        tags=args.get("tags", []),
        agent=agent_id,
        session=session_id,
    )
    return _ok({"id": record.id, "type": record.type.value, "title": record.title})


async def _tool_memory_link(args: dict[str, Any]) -> list[types.TextContent]:
    repo = _repo()
    repo.link_records(args["source"], args["target"], args.get("link_type", "causal"))
    return _ok({"source": args["source"], "target": args["target"], "link_type": args.get("link_type", "causal")})


async def _tool_memory_tag(args: dict[str, Any]) -> list[types.TextContent]:
    repo = _repo()
    updated = repo.tag_record(args["record_id"], args.get("add", []), args.get("remove", []))
    return _ok({"id": args["record_id"], "tags": updated.tags})


async def _tool_layer_list(_args: dict[str, Any]) -> list[types.TextContent]:
    repo = _repo()
    layers = [
        {"layer": lyr.value, "path": str(repo.layer_path(lyr)), "exists": repo.layer_path(lyr).exists()}
        for lyr in Layer
    ]
    return _ok(layers)


async def _tool_layer_scope(args: dict[str, Any]) -> list[types.TextContent]:
    return _ok({"active_layer": args.get("layer", "personal")})


async def _tool_memory_sync(args: dict[str, Any]) -> list[types.TextContent]:
    repo = _repo()
    ok = repo.sync(Layer(args.get("layer", "personal")))
    return _ok({"result": "ok" if ok else "failed"})


async def _tool_memory_verify(args: dict[str, Any]) -> list[types.TextContent]:
    from aimem.core.services.verify import verify as do_verify

    report = do_verify(
        memory_dir=_MEMORY_DIR,
        layer=Layer(args.get("layer", "personal")),
        strict=bool(args.get("strict", False)),
    )
    return _ok(report.as_dict())


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------


def run_server(memory_dir: Path | None = None) -> None:
    global _MEMORY_DIR
    if memory_dir is not None:
        _MEMORY_DIR = memory_dir
    _logging.configure()

    server = _build_server()

    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            init_opts = server.create_initialization_options()
            await server.run(read_stream, write_stream, init_opts)

    asyncio.run(_run())


if __name__ == "__main__":
    run_server()
