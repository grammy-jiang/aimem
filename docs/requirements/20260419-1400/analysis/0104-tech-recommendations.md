# Technology & Architecture Recommendations

Spec-Version: 20260419-1400
Source: req-analyzer
Document-Range: 0100-0199

This is the analyzer's *recommendation* feeding `arch-designer` (Stage 6). Authoritative architecture lives at `docs/design.md` (iter 1); this document only summarizes for traceability.

## Application Type

**CLI library + MCP server** (Python). Not a web app, not a TUI.

- Two front-ends over `aimem.core`:
  - `aimem` (Click-based CLI) — primary human surface.
  - `aimem-mcp` (FastMCP, stdio) — agent surface.

## Recommended Stack

| Concern | Choice | Rationale |
| --------- | -------- | ----------- |
| Language | Python 3.12+ | per `CLAUDE.md` global preferences |
| Package mgmt | `uv` | per `CLAUDE.md` |
| CLI framework | Click | per existing `src/aimem/cli/` |
| MCP server | FastMCP | stdio transport pinned to MCP `2025-06-18` |
| Data model | Pydantic v2 | `MemoryRecord` v1 with `schema_version` |
| Storage | git submodules + Markdown+YAML files | per design §3.1 |
| Index | SQLite FTS5 (keyword) + flat HNSW (vectors), `hnswlib` | per design §7 |
| Embeddings | `bge-small-en-v1.5` via `sentence-transformers` | 384-dim, MIT, CPU |
| Crypto | `pynacl` (ed25519) | per design §8 |
| Secrets scan | `gitleaks` via `pre-commit` | HC1 hardening |
| DP | Gaussian mechanism on 384-dim float32, `numpy` + custom accountant | per design §8 |
| Tests | `pytest`, `tox`, `pytest-benchmark` | per `CLAUDE.md` |
| Lint/format | `isort` + `black` + `ruff` | per `CLAUDE.md` |
| Type check | `mypy` | per `CLAUDE.md` |

## Branching Decision for Skill Workflow

Per the orchestrator's app-type detection:

- No web frontend → **skip Stage 10a/11a (Web)**.
- No terminal-UI framework (Textual/Rich/curses) → **skip Stage 10b–17b (TUI)**.
- aimem ships only a Click CLI + FastMCP server. UI/TUI scaffolding is **Not Applicable** for this project.

Stage 8/9 (E2E playbooks) are still applicable: e2e tests will be CLI-and-MCP-driven scripts rather than browser-driven.

## Iter-2 Update (2026-05-06)

Incorporates `0010-design-iter-2-addendum.md`.

### Stack changes

| Concern | Choice | Rationale |
| --------- | -------- | ----------- |
| MCP server | FastMCP pinned to MCP **`2025-11-25`** (was `2025-06-18`) | R-010 amended; pin in `pyproject.toml` |
| MCP feature surface | Tools + Resources + Prompts (server) + Roots + Elicitation + Sampling + Tasks + Logging (client) | R-051 |
| Embedding provider abstraction | New `aimem.core.embed` package with `LocalProvider`, `OpenAIProvider`, `HTTPProvider`; selected by `embed.provider` config | R-053 |
| Concurrency | `flock(2)` advisory lock on `~/.ai-memory/.aimem.lock` (Windows shim via `msvcrt.locking`) | R-002 amended, R-054 |
| Hook adapters | New `src/aimem/hooks/` Python package + reference configs at `examples/hooks/{claude-code,copilot-cli,codex-cli}/` | R-052 |
| Tool input schemas | JSON Schema 2020-12 (per SEP-1613) | R-010 amended |

### Recommended package layout (additions)

```text
src/aimem/
  core/
    embed/                # NEW — R-053
      __init__.py
      base.py             # Provider Protocol
      local.py            # bge-small via sentence-transformers
      openai.py           # OpenAI embeddings API
      http.py             # generic HTTP/JSON endpoint
    locking.py            # NEW — R-054 (flock + Windows shim)
  hooks/                  # NEW — R-052
    __init__.py
    claude_code.py        # adapter helpers (env-var parsing, JSON I/O)
    copilot_cli.py
    codex_cli.py
    safety.py             # ROLE-005 deny-list enforcement at CLI parser
  mcp/
    server.py             # bumped to 2025-11-25; advertises icons/descriptions
    elicitation.py        # NEW — R-051 consent prompts
    sampling.py           # NEW — R-051 evolve/compact/promote summarize only
    tasks.py              # NEW — R-051 SEP-1686 wrapper for memory_sync

examples/hooks/           # NEW — R-052 reference configs (opt-in)
  claude-code/settings.json
  copilot-cli/{pre-prompt.sh,post-response.sh}
  codex-cli/{session-start.sh,pre-tool.sh,post-tool.sh}
```

### MCP version pinning policy

- `pyproject.toml`: pin `mcp` SDK at the version supporting `2025-11-25`.
- Server's `initialize` handler accepts `2025-11-25` (full features) and `2025-06-18` (degraded: no Tasks, no Elicitation, no Sampling). All other versions → explicit error per AC-R010-3.
- Smoke test asserts `pyproject.toml` MCP pin matches `docs/design.md` §6 pin (exit gate G-23).

### Hook adapter contract (CLI parser layer)

When `AIMEM_CALLER_ROLE=hook` is set in the environment (set automatically by all reference hook configs in `examples/hooks/`), the CLI parser:

- Rejects `--layer team` and `--layer project` for any write subcommand (`error.kind=auth`).
- Rejects subcommands `layer promote`, `layer demote`, `inbox approve`, `tombstone` outright (`error.kind=auth`).
- Wraps the subcommand in a 1 s wall-clock SIGTERM via `aimem.hooks.safety.with_budget()` (`error.kind=transient` on overrun).
- Forces `--json` output mode (hook stdout is JSON-only per R-052).
