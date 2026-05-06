# Playbooks — MCP Feature Surface (Iter-2)

Spec-Version: 20260419-1400
Source: e2e-playbook-generator (iter-2)
Document-Range: 0800-0899
Traces: US-051, R-010 (amended), R-051, COMP-024.

These playbooks exercise the MCP `2025-11-25` feature surface added in iter-2. They are CLI/MCP-driven; no browser, no human UI. They run against a `FakeMCPHost` test fixture that emulates host capabilities.

---

## PB-051 — MCP version negotiation

**Goal**: Verify the server negotiates `2025-11-25` (preferred), falls back gracefully on `2025-06-18`, and rejects unknown versions.

### Steps

1. Start `aimem-mcp` over stdio under the test harness.
2. Send `initialize` with `protocolVersion=2025-11-25`. Assert response includes `capabilities.tools`, `capabilities.resources`, `capabilities.prompts`, and a non-empty server `instructions` string.
3. Restart server; send `initialize` with `protocolVersion=2025-06-18`. Assert response capabilities exclude Elicitation, Sampling, Tasks (degraded mode).
4. Restart server; send `initialize` with `protocolVersion=1999-01-01`. Assert MCP error response with payload mapping to `error.kind=invariant`, `retriable=false`.
5. Read `pyproject.toml` and assert the `mcp` SDK pin matches the version declared in `docs/design.md` §6 (gate G-23).

**Expected**: Strict three-way negotiation; pin matches doc.

---

## PB-052 — Roots auto-scope

**Goal**: When the host advertises Roots, write tools resolve the active layer from the Roots; missing Root → invariant.

### Steps

1. Start the server; complete `initialize` with `capabilities.roots = {listChanged: true}`.
2. Server requests `roots/list`; host responds with `["file:///tmp/aimem-test-repo"]`.
3. Call `memory_add` (write tool) with no explicit layer. Assert the recorded layer is the one resolved from the Root (`personal` for the user's home, `project` for a project Root, etc.).
4. Restart server; do not advertise Roots; call `memory_add` with no layer. Assert MCP error mapping to `error.kind=invariant` with message containing `"no resolvable layer from roots"`.

**Expected**: Write tools never invent a layer; missing Root fails loud.

---

## PB-053 — Elicitation gates `layer promote`

**Goal**: Destructive write-down (`promote`/`demote`/`inbox approve`/`tombstone`) requires Elicitation consent; decline = no fs change.

### Steps

1. Initialize with `capabilities.elicitation`.
2. Call `layer promote` for a draft note. Assert the server issued an `elicitation/create` request with a human-readable prompt and a structured schema.
3. Host responds with `decline`. Assert MCP error mapping to `error.kind=auth, retriable=false`.
4. `git -C ~/.ai-memory status --porcelain` returns empty.
5. Repeat with `accept`. Assert the promote completes and `git log` shows one new commit on the destination layer's submodule.

**Expected**: No mutation without explicit consent; consent path remains functional.

---

## PB-054 — Tasks for `memory_sync`

**Goal**: Long-running sync uses Tasks (SEP-1686) when supported; sync fallback otherwise.

### Steps

1. Initialize with `capabilities.tasks`. Call `memory_sync`. Assert the response is a Task handle, not the final result.
2. Poll the Task. Assert poll cadence ≥ 250 ms (measured client-side).
3. Once complete, assert the Task result matches the same payload as the synchronous fallback would produce.
4. Restart server; initialize without `capabilities.tasks`. Call `memory_sync`. Assert the response is the synchronous result (R-042 path).

**Expected**: Capability-driven dispatch; identical semantics across both paths.

---

## PB-055 — Sampling restricted to evolve / compact / DP-promote

**Goal**: Sampling is only invoked from `evolve`, `compact`, and DP-promote summarize handlers, all with `toolChoice="none"`. No other handler imports the sampling helper.

### Steps

1. Run the unit test that imports `aimem.mcp.sampling` and walks the import graph: assert exactly three callers (`evolve`, `compact`, `dp_promote_summarize`).
2. Start the server with a `FakeSampler` that records every call.
3. Run a hot read: 100× `memory_query`. Assert `FakeSampler` recorded zero calls.
4. Trigger `evolve` once. Assert one call to `FakeSampler` with `toolChoice="none"`.
5. Trigger `compact` once. Assert one call with `toolChoice="none"`.
6. Trigger `layer promote` with DP. Assert one summarize call with `toolChoice="none"` (only when summary is generated).

**Expected**: Sampling stays cold-path; cannot recurse; mitigates SAMPLING-001.

---

## Coverage map

| AC | Step |
| ---- | ------ |
| AC-US051-1 | PB-051 step 2 |
| AC-US051-2 | PB-052 |
| AC-US051-3 | PB-053 |
| AC-US051-4 | PB-054 |
| AC-US051-5 | PB-055 |
| AC-US051-6 | PB-051 (logging notification on `error.kind=invariant`) |
