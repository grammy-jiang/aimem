# aimem — AI Agent Memory Manager

Git-based persistent memory for local AI coding agents.

A unified memory system that works across Claude Code, GitHub Copilot, Cursor,
and future AI agents. Stores structured memory notes (YAML frontmatter +
Markdown) in a git repository with tiered context injection, hybrid retrieval,
and type-aware forgetting policies.

## Features

- **4 memory types**: Identity, Knowledge, Procedure, Journal
- **Git-backed**: Full version history, branching, sharing via remotes
- **CLI + MCP server**: Manage memory via terminal or agent integration
- **Agent adapters**: Generate CLAUDE.md, copilot-instructions.md, .cursorrules
- **Hybrid retrieval**: BM25 + embedding search with pyramid expansion
- **Security**: Defense-in-depth against memory poisoning

## Quick Start

```bash
# Install
pipx install aimem

# Initialize memory repository
aimem init

# Add a memory note
aimem add identity "Python Preferences" \
  --tags python,formatting \
  --summary "Python 3.12+ with black, ruff, pytest"

# Search memories
aimem search "python formatting"

# Export to Claude Code
aimem export claude
```

## Design

Informed by 14 academic papers. See `docs/design.md` for the full design document.

## License

MIT
