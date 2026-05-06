# Requirements Analysis — MoSCoW Prioritization

Spec-Version: 20260419-1400
Source: req-analyzer
Document-Range: 0100-0199
Inputs: 0000, 0001, 0009 (iter-1 addendum), 0010 (iter-2 addendum)

## Framework

MoSCoW is applied per requirement, anchored on the iter-1 design's 5-phase roadmap (`docs/design.md` §12). MVP = Phase 1 only. Phase-2/3 items are Should-Have for the v1 program but Must-Have for those releases.

## Must-Have (MVP / Phase 1) — 14 items

These are blocking for the Phase-1 release (single user, personal layer only, deterministic retrieval).

| ReqID | Title | Phase | Priority Rank | Notes |
| ------- | ------- | ------- | --------------- | ------- |
| R-001 | Repository Initialization | 1 | P0 | Foundation |
| R-002 | Note CRUD Operations | 1 | P0 | Core data plane |
| R-003 | Memory Type System (amended) | 1 | P0 | Drives forgetting + retrieval |
| R-004 | YAML Frontmatter Schema (v1) | 1 | P0 | Includes schema_version, ULID, sig |
| R-005 | Git Integration | 1 | P0 | Atomic writes |
| R-006 | Frontmatter Validation | 1 | P0 | `aimem verify` per commit |
| R-009 | CLI Interface | 1 | P0 | Primary surface |
| R-010 | MCP Server (pinned 2025-06-18) | 1 | P0 | Agent surface |
| R-011 | Hybrid Search (BM25 + bge-small + FTS5/HNSW) | 1 | P0 | Retrieval baseline |
| R-027 | Structured Logging (fixed schema) | 1 | P0 | Observability invariant |
| R-038 | Schema Versioning & Migration | 1 | P0 | Forward-compat invariant |
| R-039 | Record-Level Signing | 1 | P0 | Tamper evidence |
| R-040 | Write-Gate Content Classifier | 1 | P0 | Red-class gate |
| R-045 | Stable Error Taxonomy | 1 | P0 | Contract for MCP clients |
| R-046 | Perf & Evaluation Gates (LongMemEval P@5≥0.7, latency §10) | 1 | P0 | Release blocker |
| R-047 | Gitleaks Pre-Commit | 1 | P0 | HC1 hardening |

## Should-Have (Phase 2 — Three Layers) — 9 items

| ReqID | Title | Phase | Priority Rank |
| ------- | ------- | ------- | --------------- |
| R-007 | Adapter — Claude | 1.5 | P1 |
| R-008 | Adapter — Copilot | 2 | P1 |
| R-013 | Tiered Context Injection | 2 | P1 |
| R-014 | Link System (causal/evolves/refines) | 2 | P1 |
| R-015 | Write-Path Pipeline | 2 | P1 |
| R-016 | Ingestion Dedup | 2 | P1 |
| R-018 | Forgetting Policy (per-record + ABF default) | 2 | P1 |
| R-019 | Memory Evolution | 2 | P1 |
| R-024 | Configuration System | 1 | P1 |

## Should-Have (Phase 2 cont.) — Three-Layer & Sync — 7 items

| ReqID | Title | Phase | Priority Rank |
| ------- | ------- | ------- | --------------- |
| R-034 | Three-Layer Sharing Model | 2 | P1 |
| R-035 | IFC Lattice Enforcement | 2 | P1 |
| R-036 | Layer Promote/Demote | 2 | P1 |
| R-037 | Inbox Quarantine | 2 | P1 |
| R-042 | Pluggable Remote (GitHub reference) | 2 | P1 |
| R-043 | Stale-Vector Handling | 2 | P1 |
| R-044 | Tombstones | 2 | P1 |

## Should-Have (Phase 3 — Sync Hardening) — 3 items

| ReqID | Title | Phase | Priority Rank |
| ------- | ------- | ------- | --------------- |
| R-022 | Provenance via record sig + per-layer key set | 3 | P1 |
| R-023 | `aimem doctor` health check | 3 | P1 |
| R-041 | DP on Cross-Layer Promote | 3 | P1 |

## Could-Have — 5 items

| ReqID | Title | Phase | Priority Rank |
| ------- | ------- | ------- | --------------- |
| R-020 | Injection Pattern Filtering | 2 | P2 |
| R-021 | Retrieval Window Limits (default 5) | 1 | P2 (lightweight) |
| R-025 | Import from Existing Configs | 2 | P2 |
| R-026 | Internationalized CLI | 3 | P2 |
| R-050 | CRDT OR-Set Engine | 2→4 | P2 |

## Won't-Have (this program / deferred)

| ReqID | Title | Phase | Priority Rank |
| ------- | ------- | ------- | --------------- |
| R-017 | Hot-Buffer Consolidation | — | Dropped (replaced by R-037 + R-040) |
| R-028 | Adapter — Cursor | post-v1 | W |
| R-029 | Export Watch Mode | post-v1 | W |
| R-030 | Screen-reader CLI | post-v1 | W |
| R-031 | Auto-Linking via Embedding | 4 | W (Deferred) |
| R-032 | Self-RAG Gating | 4 | W (Deferred) |
| R-033 | Causal Retrieval | 4 | W (Deferred) |
| R-048 | Offline-RL Retrieval Policy | 4 | W (Deferred) |
| R-049 | Adaptive Red-Team Protocol | 5 | W (Multi-tenant only) |

## MVP Scope (Phase 1) — 16 R-IDs

R-001, R-002, R-003, R-004, R-005, R-006, R-009, R-010, R-011, R-027, R-038, R-039, R-040, R-045, R-046, R-047 (+ R-021, R-024 carried in lightweight).

## Stop-Light Summary

- 16 Must-Have (MVP); 19 Should-Have (Phase 2/3); 5 Could-Have; 9 Won't/Deferred.
- 0 unknown priorities; 0 REQUIRES_CLARIFICATION items.

## Iter-2 Update (2026-05-06)

Driven by `0010-design-iter-2-addendum.md`. Existing rows above are preserved verbatim.

### Amendments to existing rows

| ReqID | Iter-2 change | Effect on priority |
| ------- | --------------- | -------------------- |
| R-002 | Concurrency clarified: `flock(2)` advisory lock; lock-timeout → `error.kind=conflict`. | Unchanged P0. |
| R-010 | MCP pin moved `2025-06-18` → `2025-11-25`; tools advertise SEP-973 icons + `description`; JSON Schema 2020-12; input-validation as Tool Execution Errors (SEP-1303); structured logs to stderr. | Unchanged P0. |
| R-011 | Embedding **provider** is configurable (`local | openai | http`); local default; remote fails closed. | Unchanged P0. |

### New Must-Have (MVP / Phase 1) — 4 items added

| ReqID | Title | Phase | Priority Rank | Notes |
| ------- | ------- | ------- | --------------- | ------- |
| R-051 | MCP feature surface (2025-11-25) | 1 | P0 | Tools+Resources+Prompts on the server side; Roots/Elicitation/Sampling/Tasks/Logging on the client side. Elicitation gates every write-down. Sampling restricted to `evolve`/`compact`/DP-promote with `toolChoice: "none"`. |
| R-052 | Agent-hooks integration | 1 | P0 | Reference hooks for Claude Code / Copilot CLI / Codex CLI; safety contract (no `team`/`project` writes, no promote/demote/inbox-approve/tombstone, ≤1 s wall clock); opt-in only (HC2). |
| R-053 | Configurable embedding provider | 1 | P0 | `embed.provider ∈ {local, openai, http}`; API keys via env vars only (HC1); fail-closed on unreachable; provider switch triggers index-generation rotation per R-043. |
| R-054 | Per-request stateless backend | 1 | P0 | MCP server may be long-running but core opens/transacts/closes per call; no daemon; `flock(2)` for concurrency. |

### Revised totals after iter-2

- **Must-Have (MVP)**: 16 + 4 = **20 R-IDs**.
- Should-Have / Could-Have / Won't unchanged in count.
- 0 unknown priorities; 0 REQUIRES_CLARIFICATION items.

### Iter-2 MVP scope (Phase 1) — 20 R-IDs

R-001, R-002, R-003, R-004, R-005, R-006, R-009, R-010, R-011, R-027, R-038, R-039, R-040, R-045, R-046, R-047, **R-051, R-052, R-053, R-054** (+ R-021, R-024 carried in lightweight).
