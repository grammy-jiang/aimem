# aimem — Engineering Design

| Field | Value |
| --- | --- |
| Status | Draft for Phase 1 kickoff |
| Iteration | 2 (supersedes iter 1; adds MCP 2025-11-25 surface, configurable embeddings, agent-hooks integration) |
| Date | 2026-05-06 |
| Evidence basis | `memory-system/ai-memory-system-design.md` (research vault, iter 8, 54 papers, validator PASS / 1.00) |
| Harness | `local-agent-harness` stage **S2**, AI-readiness **15/25** |
| Hard constraints | `../GROUNDING.md` (HC1–HC6) |

> This document is the **engineering** design for `aimem`. It is intentionally
> shorter than the research report and deliberately omits literature
> evidence — for that, read the linked research report. This document
> answers: *what are we building, what are the engineering decisions, and
> in what order?*

## 1. Goals and Non-Goals

### 1.1 Goals

1. A **local, git-based** memory system for desktop AI coding agents:
   Claude Code, GitHub Copilot CLI, and Codex CLI.
2. **Three sharing layers** with strict, mechanically-enforced isolation:
   - **personal** — private to one developer (preferences, identity).
   - **project** — shared with everyone working on the same project.
   - **team** — shared organization-wide policies and procedures.
3. **Pluggable remotes**, with GitHub as the reference remote.
4. **Local-first**: every operation works offline; sync is asynchronous.
5. **Auditable**: every memory change is a signed git commit on a branch
   the user can inspect, revert, and review.
6. **Safe-by-default**: no plaintext secrets (HC1), no writes outside the
   working tree (HC2), no agent-driven destructive ops (HC3, HC4).

### 1.2 Non-Goals (v1)

- A cloud SaaS, multi-tenant API, or hosted control plane.
- Replacing existing IDE memory features; we *adapt* into them.
- Online RL training of the retrieval policy. Phase 1 ships **deterministic
  retrieval**; the offline-RL rail (E-2) is Phase 4.
- Cross-agent state synchronization beyond memory artifacts (no shared
  prompt history, no shared tool logs).

## 2. Architecture (one screen)

```mermaid
flowchart TD
    subgraph Agents
      A1[Claude Code]
      A2[Copilot CLI]
      A3[Codex CLI]
    end

    A1 -- MCP --> S[aimem MCP server]
    A2 -- MCP --> S
    A3 -- MCP --> S

    U[User] -- CLI --> C[aimem CLI]
    C --> Core
    S --> Core

    subgraph Core
      W[Write Gate]
      R[Retriever]
      L[Layer Resolver]
      X[Index]
    end

    Core --> Store

    subgraph Store [git submodules under ~/.ai-memory/]
      P[(personal)]
      PR[(projects/&lt;project&gt;)]
      T[(teams/&lt;team&gt;)]
    end

    P -. push/pull .-> GH1[GitHub: personal repo]
    PR -. push/pull .-> GH2[GitHub: project repo]
    T -. push/pull .-> GH3[GitHub: team repo]
```

The **CLI** and the **MCP server** are two front-ends over the same
`aimem.core` library. Storage is three independent git repos mounted as
submodules of a small parent index repo. Writes go through a write-gate
(content-classified, layer-checked, signed). Reads union the three layers
under an information-flow-control lattice.

For the full mechanism inventory, see research report
[§3 Architecture Overview](../../Documents/Research/memory-system/ai-memory-system-design.md#3-architecture-overview).

## 3. Three-Layer Sharing Model

This is the headline feature. See research report
[§8.1 Three-Layer Sharing Model](../../Documents/Research/memory-system/ai-memory-system-design.md#81-three-layer-sharing-model)
for evidence. Engineering decisions:

### 3.1 On-disk layout

```text
~/.ai-memory/                # parent index repo (private, optional remote)
├── .aimem.yaml              # global config
├── personal/                # git submodule → personal remote
├── projects/
│   └── <project-slug>/      # git submodule → project remote (per project)
└── teams/
    └── <team-slug>/         # git submodule → team remote (per team)
```

Each layer is a **separate git repository** so that access control,
history, and remotes are independent. Submodules give us atomic
per-layer commits and lossless detach-in-place if the user drops a layer.

### 3.2 Information-flow-control lattice

`personal ⊑ project ⊑ team` (least → most public).

| Operation | Allowed without ceremony | Requires explicit promote PR |
| --- | --- | --- |
| Read `personal` from a `project` context | yes (read-up) | — |
| Read `project` from a `personal` context | yes | — |
| Write a `personal` note | yes | — |
| Write a `team` note | — | yes; signed; reviewed |
| Promote `personal` → `project` | — | `aimem layer promote` |
| Demote `team` → `project` | — | `aimem layer demote` |

Write-down (more-private → more-public) is **never silent**: it always
opens a maintainer-reviewed PR on the receiving remote.

### 3.3 Retrieval precedence

When the same logical note appears in multiple layers (e.g. a project
override of a team default), the **more private layer wins** with a
score margin `θ_tie = 0.05`. Below that margin, the union is returned
and the agent is told both exist.

## 4. MemoryRecord schema (v1)

```yaml
# every note ends with a YAML frontmatter; body is markdown
schema_version: 1            # MUST be present; CI rejects missing
id: <ulid>                   # ULID, monotonic per process
layer: personal | project | team
type: identity | preference | procedure | observation | knowledge
title: <string>
created_at: <RFC3339>
updated_at: <RFC3339>
tags: [<string>, ...]
links:
  causal:    [<id>, ...]
  evolves:   [<id>, ...]
  refines:   [<id>, ...]
forgetting:
  ttl_days: <int|null>
  decay:    none | exponential
provenance:
  agent:   <agent-name>
  session: <session-id>
sig: <ed25519-detached-sig over the canonical serialization>
```

**Schema versioning policy**:

- `schema_version` is an integer.
- Every breaking change bumps it by 1 and ships a migrator in
  `aimem/storage/migrations/v<N>_to_v<N+1>.py`.
- `aimem migrate` is **author-only**; CI runs the migrator dry-run on
  every PR and refuses merges that would silently downgrade.
- Old records are kept verbatim with their original `schema_version`;
  the retriever projects them up at read time.

## 5. CLI surface (v1)

`aimem` is the only entry point. Subcommands ship in this order:

| Phase | Commands |
| --- | --- |
| 1 | `init`, `add`, `query`, `show`, `tag`, `link`, `sync`, `status` |
| 1 | `layer init`, `layer link`, `layer list`, `layer scope` |
| 2 | `layer promote`, `layer demote`, `layer share`, `inbox` |
| 2 | `forget`, `tombstone`, `verify` |
| 3 | `evolve`, `compact`, `export`, `import` |
| 4 | `policy {train,roll,shadow}` (offline RL rail) |

All commands return structured JSON when `--json` is passed; that JSON
is the contract the MCP server marshals to/from.

## 6. MCP server

Single binary, one transport, pinned version. The server is allowed to be
long-running, but the `aimem.core` library it wraps is **per-request
stateless**: every tool call opens, transacts, and closes the on-disk
repo. There is no daemon, no in-memory write buffer across reconnects,
and no cached HNSW handle that survives a `memory_sync`.

- **Transport**: MCP `stdio` for v1. Streamable-HTTP transport is
  deferred to Phase 3.
- **Protocol version pin**: MCP **`2025-11-25`** (current revision).
  We bumped from `2025-06-18` to pick up: Implementation `description`
  field, icons metadata, JSON Schema 2020-12 default, stdio servers
  using `stderr` for logs, input-validation errors as Tool Execution
  Errors (not protocol errors), URL-mode and titled enum elicitation,
  experimental Tasks for durable requests.

### 6.1 Tools (server → client)

| Tool | Purpose | Notes |
| --- | --- | --- |
| `memory_query` | Hybrid search across the active layer set | Honors IFC precedence and `roots` scope. |
| `memory_add` | Add a record to a writable layer | Runs the write-gate classifier (R-040). |
| `memory_link` / `memory_tag` | Create `causal/evolves/refines` links and tags | — |
| `memory_layer_list` / `memory_layer_scope` | List layers; restrict the active set for this session | — |
| `memory_layer_promote` | Open a promote PR to a more-public layer | DP on cross-layer (R-041); requires user consent via Elicitation. |
| `memory_sync` | Pull/push one layer | Runs as a **Task** (see §6.5). |
| `memory_inbox` | List/approve quarantined incoming records | Approval requires user consent via Elicitation. |
| `memory_verify` | Run `aimem verify` and return a structured report | — |

All tools advertise SEP-973 icons and ship `description` fields
matching the CLI manpages. Tool input schemas use JSON Schema 2020-12.
Input validation failures are returned as Tool Execution Errors so the
calling model can self-correct, per SEP-1303.

### 6.2 Resources

- `memory://record/<id>` — single record (markdown + frontmatter).
- `memory://layer/<layer>/<path>` — raw layer file (debugging only).
- `memory://search?q=...` — saved-search resource template.
- `memory://inbox` — inbox listing.

Resources are **read-only** from the client's perspective; mutation is
exclusively via tools.

### 6.3 Prompts

Pre-baked workflow prompts the host can offer in its slash-command UI:

- `prompt:recall` — "Recall what I know about <topic>" (calls
  `memory_query`).
- `prompt:capture` — "Capture this as a <type> note in <layer>"
  (calls `memory_add` with type/layer pre-filled).
- `prompt:promote` — "Propose promoting note <id> to <target-layer>"
  (calls `memory_layer_promote`).
- `prompt:review-inbox` — "Walk me through pending inbox entries"
  (calls `memory_inbox` plus per-item Elicitation).

### 6.4 Client features the server uses

- **Roots** — at session start the host advertises filesystem roots
  (typically the open project). The server uses the first root that
  matches a known `projects/<slug>/.aimem-bind` file to **auto-scope**
  the active layer set; falls back to `personal` only if none match.
  This removes the need for the user to call `aimem layer scope`
  manually inside a project.
- **Elicitation** — required for every write-down operation
  (`memory_layer_promote`, `memory_inbox approve`, `memory_tombstone`).
  Uses titled single-select enums (SEP-1330) for the consent prompt and
  URL-mode elicitation (SEP-1036) to surface the diff/PR link in the
  host UI.
- **Sampling** — used **only** by `evolve`/`compact` and the
  DP-on-promote summarization step (R-041). The server requests a
  short summarization completion from the client's LLM with
  `toolChoice: "none"` so the model cannot recurse into our tools
  during summarization. Sampling is never invoked on a hot read path.
- **Logging** — structured JSON lines emitted to `stderr` per
  PR #670; the host forwards them to its own log sink. The same
  payload also lands in `.agent/logs/aimem.jsonl` (§11) so a CLI-only
  user has a complete trace.

### 6.5 Tasks (experimental, SEP-1686)

`memory_sync` is wrapped as a Task: the call returns a task handle
immediately, and the host polls for progress. This avoids long
request-response timeouts during a multi-MB pull. Polling endpoint and
deferred-result retrieval follow the 2025-11-25 spec verbatim. If the
host does not advertise Tasks capability, the server falls back to a
synchronous response with progress notifications.

### 6.6 What the server intentionally does NOT do

- It does **not** open background sync timers — sync is initiated by
  the user or by an agent hook (§15).
- It does **not** cache write state across tool calls.
- It does **not** invoke Sampling on the hot retrieval path; only on
  evolve/compact/promote-summarize.
- It does **not** claim Roots-watch capability — the active layer set
  is fixed at session-start and re-scoped only on a fresh
  `initialize`.

## 7. Storage and retrieval

- **Format**: one file per `MemoryRecord`, markdown body + YAML
  frontmatter, file path is content-addressed by `id`.
- **Index**: SQLite (FTS5) for keyword + a flat **HNSW** index for
  vectors. Index is **never committed** to git; it is rebuildable from
  the records.
- **Embeddings**: default model is **`bge-small-en-v1.5`** (384-dim,
  CPU-runnable, MIT-license), run **locally**. The provider is
  pluggable via `~/.ai-memory/.aimem.yaml::embed`:

  ```yaml
  embed:
    provider: local        # local | openai | http
    model: bge-small-en-v1.5
    # provider=openai|http additionally requires:
    # endpoint: https://...
    # api_key_env: OPENAI_API_KEY     # MUST resolve from env, never literal
    # dim: 1536
    # timeout_ms: 5000
  ```

  Remote providers (`openai`, `http`) MUST read the API key from an
  environment variable (HC1: no plaintext secrets at rest). When a
  remote provider is configured, the write path **fails closed** if
  the endpoint is unreachable — we do not silently fall back to local
  embeddings, because that would silently change the index distance
  metric. We do not require a GPU.
- **Stale-vector handling** (research A-3): tombstone deletes; HNSW
  re-link on scheduled compaction; embedding-model upgrade triggers a
  full re-embed under a new index generation, old generation served
  read-only until the new one is warm.

## 8. Security model

Layered on top of `GROUNDING.md` (HC1–HC6, never relaxed):

- **Secrets at write time**: gitleaks pre-commit hook on every layer
  blocks plaintext secrets (HC1).
- **Write gate**: every `aimem add` runs a content classifier; "red"
  data per `GROUNDING.md` data classification table is **rejected at
  write**, never quarantined.
- **Quarantine for sync**: incoming records from a remote land in
  `<layer>/.inbox/` and are **not retrievable** until `aimem inbox
  approve`. This is research E-3.
- **Signing**: every record is signed with the user's local ed25519
  key; sync verifies signatures against the layer's known-key set.
- **DP for cross-layer leakage** (research A-4): when a record is
  promoted from `personal` to `project`, only the **summary +
  embedding** cross the boundary, with Gaussian-mechanism noise; the
  raw text never crosses. Privacy budget tracked in
  `~/.ai-memory/.privacy/budget.json`.
- **Adaptive-attack robustness** (research A-2): HarmBench + PAIR + TAP
  red-team protocol is a **release blocker for multi-tenant team
  layers**. Single-user personal layer ships in Phase 1 without it.

## 9. Evaluation gates (release-blocking)

| Gate | What it measures | Blocks |
| --- | --- | --- |
| `aimem verify` | Schema validity, signature validity, no orphan links | every commit |
| LayerEval (research §15.4) | Cross-layer leakage rate, precedence correctness, cascade-delete purity | every release |
| LongMemEval slice | Retrieval P@5 ≥ 0.7 on bundled fixture | every release |
| RedTeam suite (A-2) | HarmBench + PAIR + TAP attack success rate ≤ 5 % | **multi-tenant team release only** |
| Latency budget | see §10 | every release |

## 10. Performance budget (per command, p95, on a 2024 laptop)

| Command | Budget |
| --- | --- |
| `aimem query` (≤ 5 results, all 3 layers, warm index) | 150 ms |
| `aimem add` (single record, no sync) | 200 ms |
| `aimem sync` (one layer, no conflicts) | 2 s |
| MCP `memory_query` round-trip | 200 ms |
| Cold-start (first command in a process) | 1.5 s |

These are **engineering targets**, not research claims. They drive the
choice of bge-small (cheap on CPU), SQLite FTS5 (no daemon), and HNSW
flat (no GPU).

## 11. Logging and error taxonomy

- **Logs**: structured JSON lines under `.agent/logs/aimem.jsonl`;
  rotated daily; never committed (see `.gitignore`).
- **Log fields**: `ts, level, op, layer, record_id, latency_ms,
  agent, session, error.code, error.kind`.
- **Error kinds** (stable contract for the MCP layer):

  | kind | meaning | retriable |
  | --- | --- | --- |
  | `config` | bad/missing `.aimem.yaml` field | no |
  | `auth` | signature, key, or remote-auth failure | no |
  | `conflict` | git merge conflict during sync | yes (after resolve) |
  | `quarantine` | inbox entry not yet approved | no |
  | `not_found` | record/layer/tag missing | no |
  | `invariant` | schema or IFC violation | no |
  | `transient` | I/O, network, or timeout | yes |

- **Redaction**: error messages MUST NOT contain note bodies; only IDs,
  paths relative to repo root, and error kinds.

## 12. Process model

`aimem` is **single-user, single-process per request**:

- The CLI process exits after each command.
- The MCP server may live for the duration of an agent session, but it
  holds no in-memory write state between tool calls; every call opens
  the layer repos, transacts, and closes them.
- There is **no daemon** and no IPC layer. Concurrency between two
  CLI invocations or between a CLI invocation and an MCP tool call is
  serialized by `flock(2)` on `~/.ai-memory/.aimem.lock` — a CLI
  invocation that cannot acquire the lock within `lock.timeout_ms`
  fails with `error.kind=conflict`.
- The index (FTS5 + HNSW) lives on disk; the MCP server may keep a
  read-only handle warm across calls, but it is invalidated and
  rebuilt on any write to the underlying layer.

This model is deliberately conservative: it preserves the property
that any write is a complete git transaction observable from outside
the running process, which is what makes `git log` a usable audit
surface (HC4).

## 13. Roadmap (mapped to research §18)

| Phase | Scope | Exit criteria |
| --- | --- | --- |
| 1 — Local single-layer | personal layer only, CLI, MCP, deterministic retrieval | `aimem verify` green; LongMemEval slice passes; idempotent harness |
| 2 — Three layers | project + team layers, IFC enforcement, inbox quarantine, write-gate classifier | LayerEval green; A-3 tombstone tests green |
| 3 — Sync hardening | conflict-resolution UX, signed sync, DP on promote | A-4 DP accountant in place; quarantine dogfooded |
| 4 — Policy upgrade | offline-RL retrieval policy (E-2) shadowed against deterministic baseline | divergence < 1 %, SR@1 strictly improves |
| 5 — Multi-tenant team release | A-2 red-team protocol numbers landed; key-rotation playbook; team onboarding doc | RedTeam ASR ≤ 5 % |

Phase boundaries are also `git tag`s.

## 14. Open engineering questions deferred past v1

- Default **evaluator LLM** for the `evolve`/`compact` step. Candidates:
  local Llama-3.1-8B-Instruct (offline-friendly) vs. user-provided API
  key. Decision: ship both, default to local; flag in
  `~/.ai-memory/.aimem.yaml::evolve.model`.
- Submodule **bootstrap UX**: today `git submodule add` requires the user
  to know each layer's remote URL. Phase 2 adds `aimem layer link <url>`
  that wraps `git submodule add` + initial sign-off.
- **CRDT engine** for OR-Set semantics (research A-5): hand-rolled in
  Phase 2; consider extracting to a separate crate/library in Phase 4 if
  reuse is needed.

## 15. Agent hooks integration

Most of `aimem`'s value comes from agents *automatically* writing and
recalling memory. Phase 1 ships a thin **hook adapter** layer so each
supported agent can call the CLI (preferred for write paths, since it
produces a deterministic git commit) or the MCP server (preferred for
read paths, since it is in-process to the agent).

### 15.1 Touchpoint matrix

| Agent event | aimem operation | Channel | Why |
| --- | --- | --- | --- |
| Session start | `memory_query` for identity + active project context | MCP | Pre-load context for the agent's system prompt. |
| User submits a prompt | `memory_query` (top-k=5) on the prompt | MCP | Just-in-time retrieval. |
| Tool use about to run | redact secrets in tool args via `aimem verify --classify` | CLI | Block HC1 violations before the tool runs. |
| Tool use finished | append `observation` note if the tool failed or made a meaningful change | CLI | Capture procedural memory. |
| Session end / Stop | `aimem evolve --since <session-id>` (Phase 3+) | CLI | Consolidate and de-duplicate. |
| Compact event | `memory_query` for the compacted topic to re-inject | MCP | Avoid losing context across compactions. |
| User-edited config | `aimem verify` on the personal layer | CLI | Catch schema drift early. |

### 15.2 Per-agent wiring (reference)

- **Claude Code** — `.claude/settings.json` `hooks` block. Map
  `SessionStart` → `aimem mcp serve` (already present), `PreToolUse`
  → `aimem verify --classify --json -`, `PostToolUse` →
  `aimem add --type observation --layer personal --json -`,
  `UserPromptSubmit` → MCP `memory_query`, `Stop` →
  `aimem evolve --since $CLAUDE_SESSION_ID`.
- **GitHub Copilot CLI** — uses the agent's `tools.json` plus its
  own `pre-prompt` and `post-response` shell hooks; same mapping as
  above, just reading `$COPILOT_SESSION_ID`.
- **Codex CLI** — uses `~/.codex/hooks/*.sh`; same shell-level
  contract.

### 15.3 Hook safety contract

Agent hooks are **untrusted callers** from `aimem`'s perspective.
They go through the same write gate, signing, and IFC checks as a
human invocation. Specifically:

- A hook MUST NOT pass `--layer team` or `--layer project` for
  writes; only `personal` and `<layer>/.inbox` are writable from
  hooks. Any other value is rejected at the CLI parser layer
  (`error.kind=auth`).
- A hook MUST NOT call `aimem layer promote`, `aimem layer demote`,
  `aimem inbox approve`, or `aimem tombstone`. These require human
  consent via MCP Elicitation or interactive CLI.
- Hook output budgets: a single hook invocation MUST NOT exceed 1 s
  wall clock; aimem self-terminates with `error.kind=transient` if
  budget is exceeded, so a slow hook never blocks the agent.
- Hook stdout is JSON-only; stderr is forwarded to
  `.agent/logs/aimem.jsonl`.

### 15.4 Examples shipped in `examples/hooks/`

- `claude-code/settings.json` — full reference settings file.
- `copilot-cli/pre-prompt.sh` and `post-response.sh`.
- `codex-cli/session-start.sh`, `pre-tool.sh`, `post-tool.sh`.

All examples are **opt-in**; the user copies them into their agent
config. We deliberately do not auto-install hooks, because that would
be a write outside the working tree (HC2).

## 16. References

- Research report (evidence basis):
  `~/Documents/Research/memory-system/ai-memory-system-design.md` (iter 8,
  PASS / 1.00).
- Hard constraints: `../GROUNDING.md`.
- Agent contract: `../AGENTS.md`.
- Snapshot of pre-iter-8 design (April 19): `./design.2026-04-19.md`.
