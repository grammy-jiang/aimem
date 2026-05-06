# Components

Spec-Version: 20260419-1400
Source: arch-designer
Document-Range: 0400-0499

## Component IDs

| ID | Component | Module | Responsibility |
| ---- | ----------- | -------- | ---------------- |
| COMP-001 | CLI | `src/aimem/cli/app.py` | Click commands; map errors to exit codes (R-045). |
| COMP-002 | MCP Server | `src/aimem/mcp/server.py` | Expose tools; pin `2025-06-18`. |
| COMP-003 | Adapters | `src/aimem/adapters/` | Claude Code, Copilot CLI, Codex CLI shims. |
| COMP-004 | Service: AddNote | `src/aimem/services/add.py` | Validate → write-gate → sign → write → index. |
| COMP-005 | Service: Query | `src/aimem/services/query.py` | Hybrid retrieval; layer ordering (P2 IFC). |
| COMP-006 | Service: Verify | `src/aimem/services/verify.py` | Sig + schema + link integrity walk. |
| COMP-007 | Service: Forget | `src/aimem/services/forget.py` | Tombstone + cascade (R-044). |
| COMP-008 | Service: Migrate | `src/aimem/services/migrate.py` | Dry-run schema migrations (R-038). |
| COMP-009 | Service: Sync (P2) | `src/aimem/services/sync.py` | Pluggable remote (R-042). |
| COMP-010 | Service: Promote (P2) | `src/aimem/services/promote.py` | DP-on-promote + inbox PR (R-036, R-041). |
| COMP-011 | Repository | `src/aimem/core/repository.py` | LayerRepo abstraction; submodule glue. |
| COMP-012 | MemoryRecord | `src/aimem/core/note.py` | Pydantic v2 model + frontmatter codec. |
| COMP-013 | Index | `src/aimem/core/index.py` | FTS5 + hnswlib wrappers. |
| COMP-014 | Embedder | `src/aimem/core/embed.py` | sentence-transformers wrapper; lazy-loaded. |
| COMP-015 | Signer | `src/aimem/core/sig.py` | ed25519 sign/verify; key resolution. |
| COMP-016 | WriteGate | `src/aimem/core/write_gate.py` | Deterministic Red-class detector. |
| COMP-017 | Config | `src/aimem/core/config.py` | YAML + env loader. |
| COMP-018 | Errors | `src/aimem/core/errors.py` | Error taxonomy + exit-code map. |
| COMP-019 | Logging | `src/aimem/core/log.py` | JSONL formatter; redaction. |
| COMP-020 | Privacy (P2) | `src/aimem/core/privacy.py` | DP noise; budget ledger. |

## Mapping to docs/design.md Entities

| Design Entity | Component(s) |
| --------------- | -------------- |
| E-001 MemoryRecord | COMP-012 |
| E-002 KeyPair | COMP-015 |
| E-003 RetrievalQuery / Result | COMP-005, COMP-013 |
| E-004 SyncReport | COMP-009 |
| E-007 LayerRepo | COMP-011 |
| E-008 InboxEntry | COMP-010 (P2) |
| E-009 Tombstone | COMP-007 |
| E-010 PromotePR | COMP-010 (P2) |
| E-011 PrivacyBudget | COMP-020 (P2) |
| E-012 KnownKeySet | COMP-015 |

## Phase-1 Boundary

In scope: COMP-001..COMP-008, COMP-011..COMP-019.
Out of scope (Phase 2): COMP-009, COMP-010, COMP-020.

## Iter-2 Update (2026-05-06)

### New components (in scope for Phase 1 iter-2)

| ID | Name | Purpose | Owns | Traces |
| ---- | ------ | --------- | ------ | -------- |
| COMP-021 | HookAdapter | Hook-callable wrappers for `add` / `query` per host (Claude Code, Copilot CLI, Codex CLI). Pure I/O shaping; safety enforcement is in COMP-001 (CLI parser) gated on `AIMEM_CALLER_ROLE=hook`. | `src/aimem/hooks/` | R-052; ROLE-005 |
| COMP-022 | EmbedProvider | Provider abstraction with `LocalProvider` (default), `OpenAIProvider`, `HTTPProvider`. Selected by `embed.provider` config. Remote providers fail closed (`error.kind=transient`). Provider switch triggers COMP-006 (Index lifecycle) generation rotation. | `src/aimem/core/embed/` | R-011 (amended), R-053; E-014 |
| COMP-023 | LockManager | `flock(2)` (POSIX) / `msvcrt.locking` (Windows) advisory lock on `~/.ai-memory/.aimem.lock` with `lock.timeout_ms`. Wraps every write transaction. | `src/aimem/core/locking.py` | R-002 (amended), R-054; E-015 |
| COMP-024 | MCPFeatureSurface | Roots auto-scope, Elicitation consent, Sampling helpers (`evolve` / `compact` / DP-promote summarize, `toolChoice="none"`), Tasks (SEP-1686) wrapper for `memory_sync`, Logging notifications. | `src/aimem/mcp/{elicitation,sampling,tasks}.py` and bumps to `server.py` | R-010 (amended), R-051; E-013 |

### Component dependency updates

- COMP-001 (CLI parser) gains a deny-list pass triggered by `AIMEM_CALLER_ROLE=hook` (parses env var → rejects `--layer team|project` and destructive subcommands per AC-US052-1).
- COMP-002 (CRUD) becomes a *consumer* of COMP-023 (LockManager). Every write opens-transacts-closes through the lock.
- COMP-006 (Index lifecycle) becomes a consumer of COMP-022 (EmbedProvider). Provider switch is announced via an event that COMP-006 turns into a generation rotation.
- COMP-007 (MCP server) becomes a consumer of COMP-024 (MCPFeatureSurface) for negotiation and capability gating.
- COMP-021 is *not* a consumer of any layer-write path beyond `personal`; this is enforced upstream at COMP-001.

### Updated scope summary

In scope (Phase 1 iter-2): COMP-001..COMP-008, COMP-011..COMP-019, **COMP-021..COMP-024**.
