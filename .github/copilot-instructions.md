# Copilot Instructions — aimem

`aimem` is a git-backed persistent memory manager for local AI coding agents
(Claude Code, Copilot CLI, Codex CLI, Cursor). It stores structured notes
(YAML frontmatter + Markdown) in `~/.ai-memory/` and exposes them via a CLI
and an MCP server.

---

## Build, Test & Lint

**Package manager**: `uv`. All commands run inside the project venv.

```bash
# Install all deps (including dev)
uv sync --all-extras

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/unit/test_note.py

# Run a single test by name
uv run pytest tests/unit/test_note.py::TestNote::test_roundtrip

# Lint + format check
uv run ruff check src tests
uv run black --check src tests
uv run isort --check-only src tests

# Type check
uv run mypy src

# Pre-commit (runs gitleaks + file hygiene hooks)
uv run pre-commit run --all-files
```

Default pytest flags (set in `pyproject.toml`): `-xvs` — stops on first failure, verbose, no capture.

CI merge gates: `verify.yml` and `governance.yml` must both be green.

---

## Architecture

```
src/aimem/
  core/
    note.py        — Note + NoteMeta (Pydantic v2); the atomic data unit
    repository.py  — MemoryRepository; all git + CRUD operations
    config.py      — AimemConfig loaded from ~/.ai-memory/.aimem.yaml
  cli/
    app.py         — Click CLI (init, add, get, list, remove, status, sync, validate)
  adapters/
    claude.py      — Exports filtered notes as CLAUDE.md
  mcp/
    server.py      — FastMCP server; MCP tools are thin wrappers around MemoryRepository
```

The CLI and MCP server are **both thin layers** over the same `core/` library — no business logic lives in either layer.

### Memory Repository on Disk (`~/.ai-memory/`)

```
identity/                 — Tier 1 (always injected): user preferences, identity
knowledge/                — Tier 2-3: domain facts, languages, frameworks, tools, projects
  languages/ frameworks/ tools/ domains/ projects/
procedures/               — Tier 2-3: workflows, commands, patterns, troubleshooting
journal/                  — Tier 3: session logs, decisions, incidents, learnings
  sessions/ decisions/ incidents/ learnings/
.hot/                     — Gitignored write buffer; not yet promoted to long-term
.machine/                 — Gitignored machine-local state
.archive/                 — Soft-deleted notes (moved here, never hard-deleted)
.links/                   — Cross-note link stubs
.aimem.yaml               — Config (context budgets, consolidation, forgetting policy)
```

Note: the `MemoryType.PROCEDURE` enum value maps to the `procedures/` directory (plural), not `procedure/`.

---

## Key Conventions

### Note format

Every note is a file with YAML frontmatter followed by a Markdown `# Title` heading and body:

```markdown
---
type: knowledge
tags: [python, formatting]
updated: 2026-05-06
summary: One-line summary used for pyramid retrieval
confidence: high     # high / medium / low
importance: 0.8      # float 0.0–1.0 (forgetting policy input)
project: my-project  # optional scope
---
# Note Title

Body content in Markdown.
```

`summary` is the first-stage retrieval text (pyramid retrieval); always populate it.

### Note file naming

`add_note()` generates a slug from the title: `title.lower().replace(" ", "-").replace("/", "-")` + `.md`. There is no ULID in the filename.

### Soft-delete only

`remove_note()` moves the file to `.archive/<original-path>` — it never hard-deletes. The `.hot/` and `.machine/` dirs are gitignored.

### Pydantic v2 models

All data models use `pydantic.BaseModel`. Use `model_validate()` to construct from dicts and `model_dump(mode="json")` to serialize. `from __future__ import annotations` is present in every source file.

### Mypy strict mode

`mypy` is configured with `strict = true`. All public functions must have fully typed signatures.

### Config override

The memory directory can be overridden at runtime via the `AIMEM_DIR` environment variable (CLI reads it with `envvar="AIMEM_DIR"`).

### Agent overlay hierarchy

`GROUNDING.md` → `AGENTS.md` → `CLAUDE.md` / `.github/copilot-cli.md`. Lower layers may **specialize** but never relax constraints. HC1–HC6 in `GROUNDING.md` are absolute.

### Test isolation

Unit tests use the `tmp_path` pytest fixture for all file system operations. The `repo` fixture in `test_repository.py` creates a full initialized repo in a temp dir — follow this pattern for new repository tests.

### Ruff rule set

Active rule sets: `E, F, W, I, N, UP, B, A, SIM`. Line length: 88 (matches black).
