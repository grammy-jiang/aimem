# Playbooks — Agent Hooks Integration (Iter-2)

Spec-Version: 20260419-1400
Source: e2e-playbook-generator (iter-2)
Document-Range: 0800-0899
Traces: US-052, R-052, ROLE-005, COMP-021, COMP-001 deny-list.

These playbooks exercise the agent-hooks integration (Claude Code, Copilot CLI, Codex CLI) and the safety contract enforced at the CLI parser layer.

---

## PB-056 — Hook capture / recall round-trip

**Goal**: Reference hook configs at `examples/hooks/` capture and recall a memory in a fresh project.

### Steps

1. Create a clean tmp project; run `aimem init`.
2. Copy the reference hook config for the target host:
   - Claude Code: `examples/hooks/claude-code/settings.json` → host config dir.
   - Copilot CLI: `examples/hooks/copilot-cli/{pre-prompt.sh,post-response.sh}` → executable, on PATH.
   - Codex CLI: `examples/hooks/codex-cli/{session-start.sh,pre-tool.sh,post-tool.sh}` → executable, on PATH.
3. Drive the host with a scripted "user said: remember that X = 42" prompt.
4. Assert the hook executed `aimem add ... --json` (env `AIMEM_CALLER_ROLE=hook`); stdout was a single JSON object with `record_id` set.
5. Drive the host again with "what is X?" prompt. Assert the hook executed `aimem query ... --json` and returned a result containing the prior record.
6. Assert no human-readable preamble appears on stdout in either invocation (JSON-only).

**Expected**: One capture round-trip + one recall round-trip per host, with JSON-only stdout, no manual user step beyond the simulated prompts.

---

## PB-057 — Hook safety contract

**Goal**: A hook cannot escape `personal` containment, cannot perform destructive ops, and cannot run longer than 1 s.

### Sub-cases

### PB-057.a — Deny `--layer team` / `--layer project`

1. Set `AIMEM_CALLER_ROLE=hook` in the env.
2. Run `aimem add --layer team --type observation --content "..."`. Assert exit ≠ 0; stderr/JSON `error.kind=auth`; `git status` clean.
3. Repeat with `--layer project`. Assert same behavior.
4. Run `aimem add --layer personal --type observation --content "..."` in hook mode. Assert success.

### PB-057.b — Deny destructive subcommands

1. Set `AIMEM_CALLER_ROLE=hook`.
2. Run each of: `aimem layer promote ...`, `aimem layer demote ...`, `aimem inbox approve ...`, `aimem tombstone ...`. Assert each returns `error.kind=auth`, exits ≠ 0, and produces no fs mutation.
3. Unset `AIMEM_CALLER_ROLE`. Run the same commands; assert they execute normally (with their own R-001..R-047 gates intact).

### PB-057.c — 1 s wall-clock budget

1. Patch the hook adapter test fixture to run a handler that sleeps 1 500 ms.
2. In hook mode, invoke that fixture. Assert exit code maps to `error.kind=transient, retriable=true`. Assert the process tree is gone within 1 100 ms (measured by parent).
3. Patch a handler that sleeps 100 ms. Assert success; total wall clock < 800 ms typical.

### PB-057.d — Force `--json`

1. In hook mode, call `aimem query ...` without `--json`. Assert output is JSON anyway.
2. In hook mode, pass `--no-json`. Assert exit ≠ 0 with `error.kind=invariant`.

**Expected**: All deny-list paths exit cleanly with `error.kind=auth`; budget overruns map to `transient`; JSON mode is forced.

---

## Coverage map

| AC | Step |
| ---- | ------ |
| AC-US052-1 | PB-057.a + PB-057.b |
| AC-US052-2 | PB-057.c |
| AC-US052-3 | PB-056 |
| AC-US052-4 | PB-057.d |
| AC-US052-5 | PB-057.b (`layer promote` denial precedes any git op) |

| Red-team finding | Step |
| ------------------ | ------ |
| HOOK-001 (exfiltration) | PB-057.a + PB-057.b |
| HOOK-002 (resource exhaustion) | PB-057.c |
