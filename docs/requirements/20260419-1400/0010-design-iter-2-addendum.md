# Design Iteration 2 Addendum (2026-05-06)

Spec-Version: 20260419-1400
Source: req-clarifier (iter-2 pass, user-confirmed)
Supersedes evidence basis: `docs/design.md` iter 1 → `docs/design.md` iter 2

## Purpose

This file captures the **delta** introduced by `docs/design.md` iter 2 on
top of iter 1 (`0009-design-iter-1-addendum.md`). It uses the same
Spec-Version. Existing R-IDs are preserved verbatim. New requirements
append starting at R-051. Modified requirements appear under
"Amendments to Existing R-IDs" and override the prior wording.

The iter-2 pass is driven by three user-confirmed inputs:

1. The four assumptions in `0099-handoff-summary.md` are confirmed,
   with assumptions 2 and 4 refined (see "Assumption Confirmations"
   below).
2. Bump MCP from `2025-06-18` to **`2025-11-25`** (current revision)
   and exercise the full client/server feature surface where it
   benefits aimem.
3. Add an **agent-hooks** integration story so Claude Code, GitHub
   Copilot CLI, and Codex CLI can drive aimem automatically.

## Assumption Confirmations (refines 0099 §"Assumptions Made")

| # | Original assumption | Confirmed status (iter 2) |
| --- | --- | --- |
| 1 | Git is always available on the host system. | **Confirmed.** Unchanged. |
| 2 | Embedding model is a local Python library. | **Refined.** Embedding provider is **configurable** (`local | openai | http`); **default is local** (`bge-small-en-v1.5`). Remote providers MUST source API keys from environment variables (HC1). See R-053. |
| 3 | Maximum repository scale ~10 000 notes. | **Confirmed.** Unchanged. |
| 4 | Single-user CLI process (no daemon). | **Refined.** The MCP server **may be long-running** for the duration of an agent session, but the `aimem.core` library it wraps is **per-request stateless**: every CLI invocation and every MCP tool call opens, transacts, and closes the on-disk repo. There is no persistent in-memory write buffer. See R-054. |

## Amendments to Existing R-IDs

| ReqID | Change | Source in design.md |
| ------- | -------- | --------------------- |
| R-010 | MCP protocol pin moved from `2025-06-18` to **`2025-11-25`**. Tool list extended with `memory_verify`. Tools advertise SEP-973 icons and human-readable `description`s. Tool input schemas use JSON Schema 2020-12. Input validation failures are returned as Tool Execution Errors per SEP-1303 (not protocol errors). The server emits structured JSON logs to stderr per PR #670. | §6 (rewritten) |
| R-011 | Embedding **provider** is configurable as `local | openai | http`; default remains`bge-small-en-v1.5` local. Remote providers fail-closed if unreachable (no silent fallback to local). API keys MUST come from `*_env` references, never literal values in config. | §7 |
| R-002 | Single-user invariant clarified: any pair of concurrent invocations (CLI×CLI, CLI×MCP, MCP×MCP) is serialized by `flock(2)` on `~/.ai-memory/.aimem.lock`; lock-acquisition timeout maps to `error.kind=conflict`. | §12 (new "Process model" section) |

## New Must-Have Requirements (R-051 → R-054)

| ReqID | Title | Description | Value/Rationale | Dependencies | Status |
| ------- | ------- | ------------- | ----------------- | -------------- | -------- |
| R-051 | MCP feature surface (2025-11-25) | The MCP server MUST expose Tools, Resources, and Prompts; MUST consume client Roots, Elicitation, Sampling, and Logging; and MUST wrap `memory_sync` as an experimental Task (SEP-1686) with synchronous fallback when the client lacks Tasks capability. Roots auto-scope the active layer set via a `projects/<slug>/.aimem-bind` marker file. Elicitation gates every write-down operation (`memory_layer_promote`, `memory_inbox approve`, `memory_tombstone`). Sampling is used **only** by `evolve`/`compact` and the DP-on-promote summarization step, with `toolChoice: "none"`. | Aligns aimem with the current MCP revision and gives users HITL-grade consent on cross-layer flows. | R-010, R-035, R-041 | Active |
| R-052 | Agent-hooks integration | Ship reference hook configurations under `examples/hooks/` for Claude Code (`SessionStart, PreToolUse, PostToolUse, UserPromptSubmit, Stop, PreCompact`), GitHub Copilot CLI (`pre-prompt`, `post-response`), and Codex CLI (`session-start`, `pre-tool`, `post-tool`). Hooks invoke the CLI for writes (deterministic git commits) and MCP for reads. Hooks are **untrusted callers**: they MUST NOT write to `project` or `team` layers, MUST NOT call promote/demote/inbox-approve/tombstone, and are wall-clock-bounded (≤1 s; over-budget → `error.kind=transient`). All examples are opt-in; aimem MUST NOT auto-install them (HC2). | Makes memory capture automatic without surrendering safety invariants. | R-035, R-040, R-045, HC1, HC2 | Active |
| R-053 | Configurable embedding provider | `~/.ai-memory/.aimem.yaml::embed.provider ∈ {local, openai, http}`. Local is default. Remote providers require `endpoint`, `dim`, `timeout_ms`, and `api_key_env` (env var name, never a literal key — HC1). On a remote provider, the write path fails closed if the endpoint is unreachable (no silent fallback to local). Switching providers triggers a full re-embed under a new index generation per R-043. | Refines assumption 2; allows users with API budgets or higher-quality models to opt in without sacrificing local-first defaults. | R-011, R-043 | Active |
| R-054 | Per-request stateless backend | The `aimem.core` library MUST hold no write-side in-memory state between operations. CLI processes exit per command. The MCP server MAY live for an agent session but MUST open, transact, and close the on-disk repo on every tool call. A read-only index handle MAY be cached but MUST be invalidated on any underlying write. There is no daemon and no IPC layer beyond MCP stdio. | Refines assumption 4; preserves the property that every write is a complete git transaction observable from outside the running process (HC4 audit surface). | R-002, R-005 | Active |

## New Acceptance Criteria

| AC-ID | ReqID | Statement | TestLevel |
| ------- | ------- | ----------- | ----------- |
| AC-R010-3 | R-010 | `initialize` with the host advertising protocolVersion `2025-11-25` succeeds; advertising `2025-06-18` succeeds with feature degradation (no Tasks, no Elicitation); advertising an older or unknown version fails with a clear error. | Smoke |
| AC-R010-4 | R-010 | Each tool's `description` field is non-empty and matches the CLI manpage one-liner; each tool advertises an icon (SEP-973). | Unit |
| AC-R010-5 | R-010 | A tool input that fails JSON-Schema-2020-12 validation returns a Tool Execution Error (not a Protocol Error) with `error.kind=invariant`. | Unit |
| AC-R051-1 | R-051 | When the host advertises Roots and one root contains a `.aimem-bind` file naming a project slug, `memory_query` returns results scoped to `personal + projects/<slug>` and excludes other projects. | E2E |
| AC-R051-2 | R-051 | `memory_layer_promote` issues an Elicitation request before opening the PR; declining the elicitation aborts the promote with no remote-side mutation. | E2E |
| AC-R051-3 | R-051 | A Sampling request issued during `evolve` carries `toolChoice: "none"` and never recurses into aimem tools. | Unit |
| AC-R051-4 | R-051 | `memory_sync` returns a Task handle when the client advertises Tasks capability; otherwise returns synchronously with progress notifications. | Smoke |
| AC-R052-1 | R-052 | A hook invocation that passes `--layer team` for an `aimem add` is rejected at the CLI parser with `error.kind=auth`; no file is created. | Unit |
| AC-R052-2 | R-052 | A hook invocation that exceeds the 1 s wall-clock budget is terminated with `error.kind=transient` and emits a structured log line; the agent's tool call returns within budget. | Unit |
| AC-R052-3 | R-052 | The shipped Claude Code `examples/hooks/claude-code/settings.json` is consumed by Claude Code without warnings on a clean install. | Smoke |
| AC-R053-1 | R-053 | Setting `embed.provider: openai` without `api_key_env` fails `aimem verify` with `error.kind=config`. | Unit |
| AC-R053-2 | R-053 | Setting `embed.provider: http` and pointing at an unreachable endpoint causes `aimem add` to fail with `error.kind=transient` and produces no record. | E2E |
| AC-R053-3 | R-053 | Switching `embed.provider` from `local` to `openai` triggers a new index generation and serves the old one read-only until the new one is warm (per R-043). | E2E |
| AC-R054-1 | R-054 | Two overlapping `aimem add` invocations serialize via `flock(2)`; the loser returns `error.kind=conflict` after `lock.timeout_ms`. | Unit |
| AC-R054-2 | R-054 | After `memory_sync` is invoked through MCP, a subsequent `memory_query` reflects the synced records without an explicit reconnect. | Smoke |

## New Scenario Inventory Additions

| Scenario ID | Workflow | Class | Description |
| ------------- | ---------- | ------- | ------------- |
| SCN-WF001-HP-04 | WF-001 | HP | Claude Code `SessionStart` hook calls `memory_query` over MCP and pre-injects identity context. |
| SCN-WF002-HP-05 | WF-002 | HP | Claude Code `PostToolUse` hook captures a failed tool invocation as an `observation` note in `personal`. |
| SCN-WF002-NEG-05 | WF-002 | NEG | Hook attempts `aimem add --layer team`; CLI rejects with `error.kind=auth`. |
| SCN-WF002-FAIL-03 | WF-002 | FAIL | Remote embedding endpoint times out; `aimem add` fails closed with `error.kind=transient`. |
| SCN-WF003-HP-04 | WF-003 | HP | `memory_sync` returns a Task handle; host polls until completion. |
| SCN-WF004-NEG-05 | WF-004 | NEG | User declines Elicitation prompt for `memory_layer_promote`; promote is aborted with no remote mutation. |
| SCN-WF005-HP-05 | WF-005 | HP | Switching `embed.provider` from `local` to `openai` triggers index-generation rotation. |
| SCN-WF006-NEG-03 | WF-006 | NEG | Hook attempts to call `memory_layer_promote`; rejected with `error.kind=auth` (hooks cannot promote). |

## Roles / Permissions Updates

| ID | Name | Update |
| ---- | ------ | -------- |
| ROLE-005 | Agent Hook Caller | New synthetic role representing an unattended hook invocation. Capabilities: `query (read-up only)`, `add (personal layer only)`, `verify`. Explicitly **denied**: promote, demote, inbox-approve, tombstone, layer-team writes, layer-project writes. Mapped to `error.kind=auth` on any denied capability. |

## Data-Entity Updates

| ID | Name | Note |
| ---- | ------ | ------ |
| E-013 | LayerBindMarker | `projects/<slug>/.aimem-bind` file consumed by Roots auto-scope (R-051). Contains the layer slug and an optional version pin. |
| E-014 | EmbedProviderConfig | Subtree under `embed:` in `~/.ai-memory/.aimem.yaml`. Fields per R-053. |
| E-015 | LockFile | `~/.ai-memory/.aimem.lock`; advisory file lock used by R-054. |

## NFR Updates

| Metric | Target | Source |
| -------- | -------- | -------- |
| Hook invocation wall clock (p100) | ≤ 1 000 ms (self-terminating) | R-052 §15.3 |
| MCP `memory_query` round-trip with Roots auto-scope | ≤ 200 ms p95 | §10 (unchanged); confirmed under R-051 |
| `aimem add` with `embed.provider=openai` (warm endpoint) | ≤ 800 ms p95 | New: budget for remote embedding |
| `aimem sync` Task polling cadence | ≥ 250 ms between polls | R-051 |

## New Red-Team Findings

| Finding ID | Severity | Category | Description | Mitigation |
| ------------ | ---------- | ---------- | ------------- | ------------ |
| HOOK-001 | High | Abuse / Permission Escalation | A compromised agent uses a hook to silently exfiltrate private notes by writing them into the project layer. | R-052 hook safety contract: hooks cannot target `project`/`team`; promote/demote/tombstone explicitly denied at CLI parser. |
| HOOK-002 | Medium | Resource Exhaustion | A misconfigured hook fires per-keystroke and saturates aimem. | R-052 1 s wall-clock budget + `flock` serialization (R-054); structured logs surface the offender. |
| MCP-VER-001 | Medium | Integration Failure | Host advertises an MCP version we no longer support, causing silent feature degradation. | R-010 amended: explicit version negotiation; older versions degrade gracefully; unknown versions fail loudly. |
| EMBED-REMOTE-001 | Medium | Data Loss | Remote embedding endpoint silently returns zero-vectors; retrieval quality collapses without warning. | R-053: fail-closed on unreachable/erroring endpoint; new-generation index rotation on provider switch; canary query in `aimem verify`. |
| SAMPLING-001 | Medium | Recursion | A Sampling request issued during `evolve` recurses into `memory_query` and self-amplifies cost. | R-051: Sampling carries `toolChoice: "none"`; never invoked on hot read path. |

## Exit Gates Re-evaluated

All 21 prior exit gates remain green. Two new gates introduced by iter 2:

1. Every R-051..R-054 requirement has at least one AC with a TestLevel
    tag, and each new red-team finding maps to a mitigating ReqID.
2. The MCP version pin in `pyproject.toml` and in `docs/design.md`
    matches (`2025-11-25`).

Both pass.
