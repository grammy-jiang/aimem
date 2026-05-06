# Architecture Overview

Spec-Version: 20260419-1400
Source: arch-designer
Document-Range: 0400-0499
Authoritative reference: docs/design.md (iter 1, 2026-05-06)

## Purpose

`aimem` is a local-first, git-backed personal/project/team memory store with a CLI surface and an MCP server. Phase 1 ships the `personal` layer plus all primitives (schema, sig, write-gate, retrieval, MCP) needed for Phase 2 to introduce the team layer without redesign.

## Top-Level Architecture

```text
┌──────────────────────────────────────────────────────┐
│                  Clients                             │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   │
│  │ aimem CLI  │   │ MCP client │   │ Adapters   │   │
│  │ (Click)    │   │ (Claude /  │   │ (Claude    │   │
│  │            │   │  Copilot)  │   │  Code)     │   │
│  └─────┬──────┘   └──────┬─────┘   └─────┬──────┘   │
└────────┼─────────────────┼────────────────┼─────────┘
         │                 │                │
┌────────▼─────────────────▼────────────────▼─────────┐
│                Application Layer                     │
│  ┌────────────────────────────────────────────────┐ │
│  │ Service: AddNote / Query / Verify / Forget /   │ │
│  │          ListLayer / Sync / Promote (P2)       │ │
│  └────────────┬───────────────────────────────────┘ │
└───────────────┼──────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────┐
│                  Core Layer                          │
│  ┌────────────────────────────────────────────────┐ │
│  │ Repository (LayerRepo)  Index (FTS5+HNSW)      │ │
│  │ MemoryRecord schema     Sig (ed25519)          │ │
│  │ WriteGate (deterministic) ConfigLoader         │ │
│  │ ErrorTaxonomy           Logging                │ │
│  └────────────┬───────────────────────────────────┘ │
└───────────────┼──────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────┐
│                 Storage Layer                        │
│  ~/.ai-memory/                                       │
│   ├── .aimem.yaml                                    │
│   ├── personal/   (git submodule, Phase 1)           │
│   ├── projects/<slug>/  (P2)                         │
│   └── teams/<slug>/     (P2)                         │
│  + SQLite index, hnswlib index (rebuildable)         │
└──────────────────────────────────────────────────────┘
```

## Layer Responsibilities

- **Clients** translate user / agent intent to service calls.
- **Application** orchestrates services, enforces error taxonomy, emits structured logs.
- **Core** owns the schema, retrieval, signing, write-gate, and config — pure functions where possible.
- **Storage** is git + SQLite + hnswlib, organized as submodules under `~/.ai-memory/`.

## Phase Plan

- **Phase 1 (MVP)**: personal layer, hybrid retrieval, MCP server, write-gate, signing, perf gates.
- **Phase 2**: project + team layers, IFC retrieval ordering, promote/demote with PR + DP-on-promote, inbox quarantine, sync.
- **Phase 3**: forgetting/decay scheduler, adaptive red-team, evaluator harness.

## Cross-References

- Components: 0402.
- Tech stack: 0401.
- Data flow: 0403.
- Deployment: 0404.
- Security: 0405.
- NFR mapping: 0406.

## Iter-2 Update (2026-05-06)

Driven by `0010-design-iter-2-addendum.md`. Adds three architectural surfaces and one cross-cutting concurrency primitive:

1. **Full MCP feature surface** (R-051): Roots, Elicitation, Sampling, Tasks, Logging are first-class capabilities; `aimem-mcp` server pin moves to `2025-11-25`. Tools advertise SEP-973 icons + `description` and use JSON Schema 2020-12.
2. **Agent hook adapters** (R-052): a new top-level package `src/aimem/hooks/` plus reference configs at `examples/hooks/{claude-code,copilot-cli,codex-cli}/`. Hook callers (ROLE-005) are constrained at the CLI parser layer by an `AIMEM_CALLER_ROLE=hook` deny-list.
3. **Configurable embedding provider** (R-053): a Provider abstraction in `src/aimem/core/embed/` with `LocalProvider`, `OpenAIProvider`, `HTTPProvider`. Remote providers fail closed; provider switch triggers index-generation rotation per R-043.
4. **Per-request stateless backend** (R-054): no daemon. `aimem.core.locking` provides `flock(2)` (POSIX) / `msvcrt.locking` (Windows) advisory locking on `~/.ai-memory/.aimem.lock` with `lock.timeout_ms` (default 100 ms).

Downstream sections updated:

- 0401: pin `mcp` SDK at `2025-11-25`; add embed-provider abstraction; add `flock`/Windows shim; add hook package + reference configs.
- 0402: new components COMP-021 (HookAdapter), COMP-022 (EmbedProvider abstraction), COMP-023 (LockManager), COMP-024 (MCP feature surface: Elicitation/Sampling/Tasks).
- 0403: new flows for Roots auto-scope, Elicitation consent, Tasks polling, hook capture/recall.
- 0404: deployment topology stays single-process; document MCP server lifecycle as long-running but core as per-request stateless.
- 0405: mitigations for HOOK-001/002, MCP-VER-001, EMBED-REMOTE-001, SAMPLING-001.
- 0406: NFRs added for hook 1 s wall-clock, embed timeout, lock timeout, Tasks polling cadence.
