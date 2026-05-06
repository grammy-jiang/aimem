# Technology Stack

Spec-Version: 20260419-1400
Source: arch-designer
Document-Range: 0400-0499

## Runtime

| Concern | Choice | Rationale | Pin |
| --------- | -------- | ----------- | ----- |
| Language | Python | 0104 + design.md §2 | 3.12+ |
| Package manager | uv | CLAUDE.md global preference | latest |
| CLI | Click | Stable, ubiquitous, composable | ≥8.1 |
| MCP server | FastMCP | Stdio transport for `2025-06-18` | pinned per pyproject |
| Schema/data | Pydantic | v2 strict mode for MemoryRecord | ≥2.6 |
| Settings | pydantic-settings | YAML loader for `.aimem.yaml` | latest |
| Filesystem | pathlib + fsspec (only if needed) | Local-first | stdlib |
| Git | dulwich (preferred, pure-Python) OR `git` shell-out | Submodule support | TBD per US-001 spike |

## Storage & Index

| Concern | Choice | Rationale |
| --------- | -------- | ----------- |
| Note format | Markdown w/ YAML frontmatter | Human-readable, git-diffable |
| Lexical index | SQLite FTS5 | No service, fast, built-in |
| Vector index | hnswlib (flat HNSW) | CPU-only; ~10k notes scale |
| Embedding model | `bge-small-en-v1.5` (384-dim, CPU) | Quality/perf tradeoff per design.md |
| Embedding host | sentence-transformers | Local |

## Crypto / Security

| Concern | Choice |
| --------- | -------- |
| Signing | pynacl (ed25519) |
| Key storage | OS keyring (preferred) → fallback `~/.ai-memory/.keys/` 0600 |
| Secret scanning | gitleaks pre-commit |
| Write-gate classifier | Deterministic regex/AST patterns; no LLM (R-040) |

## Observability

| Concern | Choice |
| --------- | -------- |
| Logging | stdlib `logging` + JSONFormatter; rotated daily |
| Bench | pytest-benchmark for perf ACs (US-012) |
| Tracing | None in Phase 1 (logged correlation_id sufficient) |

## Quality Gates

| Tool | Purpose |
| ------ | --------- |
| pytest | Unit + smoke + e2e |
| tox | Python 3.12 / 3.13 matrix |
| black | Format |
| isort | Import order |
| ruff | Lint (formatting disabled) |
| mypy | Type check |
| gitleaks | Secret scan (pre-commit + CI) |

## Explicitly Rejected

- **Web frameworks**: out of scope; aimem is CLI+MCP only.
- **TUI frameworks**: out of scope.
- **External vector DBs (Qdrant, Weaviate)**: violate local-first; reconsider at >100k notes.
- **LLM-based write-gate / scoring at write time**: violates R-040 determinism.

## Forward-Compat Hooks (Phase 2/3)

- `LayerRepo` interface lets project/team submodules plug in without core changes.
- `RemoteSyncer` protocol (R-042) for pluggable git remotes.
- DP noise function isolated in `core/privacy.py` to swap mechanisms.

## Iter-2 Update (2026-05-06)

### Pin / version changes

| Concern | Iter-1 | Iter-2 | Rationale |
| --------- | -------- | -------- | ----------- |
| MCP protocol | `2025-06-18` | **`2025-11-25`** | R-010 amendment; required for Elicitation, Sampling, Tasks, server `instructions`, JSON Schema 2020-12, SEP-973 icons. Pinned in `pyproject.toml` (asserted by smoke test G-23). |
| MCP SDK | `mcp>=` (pinned at `2025-06-18`) | `mcp>=` matching `2025-11-25` | Same. |
| Tool input schemas | JSON Schema draft-07 | **JSON Schema 2020-12** (SEP-1613) | Aligns with current MCP spec. |
| Concurrency | implicit (single process) | **`flock(2)` advisory** + Windows `msvcrt.locking` shim | R-002 amended, R-054. |

### New stack additions

| Concern | Choice | Rationale |
| --------- | -------- | ----------- |
| Embedding provider abstraction | `aimem.core.embed.{base,local,openai,http}` | R-053; clean Protocol with `LocalProvider` (default), `OpenAIProvider`, `HTTPProvider` |
| Hook adapter package | `src/aimem/hooks/{claude_code,copilot_cli,codex_cli,safety}.py` | R-052; safety contract enforced at CLI parser layer via `AIMEM_CALLER_ROLE=hook` env var |
| Reference hook configs | `examples/hooks/{claude-code,copilot-cli,codex-cli}/` | Opt-in installation; HC2 |
| MCP feature surface | `aimem.mcp.{elicitation,sampling,tasks}.py` | R-051; Sampling restricted to evolve/compact/promote with `toolChoice="none"` |
| Lock manager | `aimem.core.locking.LockManager` | R-054; `lock.timeout_ms` (default 100 ms) → `error.kind=conflict` |

### Forward-compat hooks (additions)

- `EmbedProvider` Protocol decouples model implementation from index lifecycle (R-043 still owns generation rotation).
- `LockManager` is platform-agnostic; switching to a transactional store later requires no caller change.
- `HookAdapter` package isolates host-specific I/O conventions; adding a new host is a new submodule plus reference config.
