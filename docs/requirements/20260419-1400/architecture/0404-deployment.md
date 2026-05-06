# Deployment

Spec-Version: 20260419-1400
Source: arch-designer
Document-Range: 0400-0499

## Distribution

- Built and published as a Python wheel via `uv build`.
- Installed by users via `uv tool install aimem` (preferred) or `pipx install aimem`.
- Single executable entry points:
  - `aimem` (Click CLI)
  - `aimem-mcp` (MCP stdio server)

## Bootstrap

1. `uv tool install aimem`.
2. `aimem init --path ~/.ai-memory` (US-001).
3. Optionally edit `~/.ai-memory/.aimem.yaml`.
4. Add aimem to your agent runtime:
   - Claude Code: `~/.config/claude/mcp.json` entry pointing to `aimem-mcp`.
   - Copilot CLI / Codex CLI: equivalent MCP block.

## Filesystem Layout

```text
~/.ai-memory/
  .aimem.yaml              # config
  .keys/ (0700)            # ed25519 fallback when keyring unavailable
  .privacy/budget.json     # Phase-2 DP ledger
  .index/
    fts.sqlite             # FTS5
    hnsw.bin               # vector index
  personal/                # git submodule
    preference/<ulid>.md
    procedure/<ulid>.md
    ...
  projects/<slug>/         # P2
  teams/<slug>/            # P2
.agent/logs/aimem.jsonl    # workspace-local logs (per-process cwd)
```

## Runtime Sandbox

- aimem reads/writes ONLY under `--path` or `AIMEM_DIR` (HC2).
- No outbound network in Phase 1 except git push (P2).
- MCP server has no networking; stdio only.

## CI/CD

- GitHub Actions: `verify.yml` (lint+type+tests), `governance.yml` (gitleaks + dependency scan + SAST).
- Release: tag → build wheel → upload to PyPI on signed tag.
- Branch protection on `main` requires both workflows green plus 1 reviewer.

## Operational Concerns

- **Backups**: user's responsibility (it's a git repo); document `git bundle` recipe in README.
- **Telemetry**: NONE. Logs are local-only.
- **Updates**: `uv tool upgrade aimem`; schema migrations handled by `aimem migrate`.

## Iter-2 Update (2026-05-06)

### Process model (per R-054)

- **No daemon.** Two distinct processes coexist:
  1. `aimem` CLI — short-lived; one process per command.
  2. `aimem-mcp` MCP server — long-lived for the duration of an agent session, but its handlers open / transact / close `aimem.core` per request.
- Both share the same `~/.ai-memory/` storage; serialization is via COMP-023 LockManager (`flock(2)` on `~/.ai-memory/.aimem.lock`).
- Hook callers (ROLE-005) invoke the CLI form only; they never spawn an MCP server.

### MCP protocol pin

- Server advertises `protocolVersion=2025-11-25` (preferred) and accepts `2025-06-18` with degraded features (no Elicitation, no Sampling, no Tasks). Other versions → explicit `error.kind=invariant`. Smoke test asserts `pyproject.toml` MCP pin matches `docs/design.md` §6 (G-23).

### Hook deployment

- Reference hook configs are *not* installed automatically. Users opt in by copying from `examples/hooks/{claude-code,copilot-cli,codex-cli}/` into the host's config location, per the host's docs. README documents the recipe.
- All reference configs set `AIMEM_CALLER_ROLE=hook` in the environment they hand to `aimem`. This is the sole signal COMP-001 uses to enable the deny-list.

### Embedding provider deployment

- Default install runs fully offline (`embed.provider=local`).
- Switching to `openai` / `http` requires the user to set the env var named in `embed.api_key_env`. aimem refuses to start if the env var is missing.
- A provider switch is a documented operator step: edit `~/.ai-memory/.aimem.yaml`, run `aimem doctor --reembed`, wait for warm-up.
