# Security Architecture

Spec-Version: 20260419-1400
Source: arch-designer
Document-Range: 0400-0499

## Trust Model

- **Trusted**: the local user, their CLI, the MCP server, the local git repo.
- **Untrusted**: agent-supplied content (treat as data, never code), remote git mirrors (P2), external MCP clients.

## Threats and Mitigations

| ID | Threat | Mitigation | Component |
| ---- | -------- | ----------- | ----------- |
| T-1 | Secret leakage into memory | Deterministic write-gate (R-040); gitleaks pre-commit (R-047) | COMP-016 + CI |
| T-2 | Forged record on shared layer (P2) | ed25519 signing (R-039); KnownKeySet enforcement | COMP-015, E-012 |
| T-3 | Cross-layer leak via promote (P2) | DP-on-promote (R-041); inbox PR review (R-037) | COMP-020, COMP-010 |
| T-4 | Path traversal | `realpath` check confined to AIMEM_DIR (HC2) | COMP-011 |
| T-5 | Adversarial agent inputs | Content treated as data; never executed; no shell-out from add | COMP-004 |
| T-6 | Stale vectors after delete | Index reconciliation walk on `verify` (R-043) | COMP-013, COMP-006 |
| T-7 | Tombstone bypass | `forget` is the only deletion path; raw rm flagged by `verify` | COMP-007 |
| T-8 | Denial via huge note | Size cap in COMP-016 (configurable, default 256 KiB) | COMP-016 |

## Cryptography

- Ed25519 keypair generated on `init`; private key in OS keyring or `0600 ~/.ai-memory/.keys/`.
- Signature covers canonicalized frontmatter + body bytes; algorithm field on record.
- Key rotation: `aimem key rotate` issues new keypair, re-signs records owned by previous key, records the rotation in `KnownKeySet` (P2).

## Data Classification (per AGENTS.md overlay)

- Red: secrets, credentials, PII → blocked by write-gate.
- Amber: internal designs → personal/project layer only.
- Green: public/own preferences → any layer.

## Privacy (Phase 2 forward-compat)

- DP noise applied at promote on summary embedding only; raw text never crosses layer boundary unredacted.
- Privacy budget ledger at `~/.ai-memory/.privacy/budget.json`; exhaustion fails promotes with `error.kind=quarantine`.

## Audit

- All mutations are git commits with structured author/op metadata.
- `aimem verify` walks the store; CI runs it on PRs that touch fixtures.

## Iter-2 Update (2026-05-06)

Mitigations for the iter-2 red-team findings (HOOK-001, HOOK-002, MCP-VER-001, EMBED-REMOTE-001, SAMPLING-001).

### HOOK-001 — Hook-driven exfiltration

- Threat: a malicious or misconfigured hook causes `aimem` to write Red/Amber data into the team or project layer, escaping `personal` containment (HC1).
- Architectural mitigation:
  - COMP-001 (CLI parser) reads `AIMEM_CALLER_ROLE=hook` and rejects `--layer team|project` for any write subcommand and rejects `layer promote`, `layer demote`, `inbox approve`, `tombstone` outright (`error.kind=auth`).
  - The deny-list is applied **before** any git or index call. Verified by AC-US052-1 and AC-US052-5.
  - Reference hook configs at `examples/hooks/` set the env var; a hook author cannot bypass it without replacing the wrapper script.

### HOOK-002 — Hook resource exhaustion

- Threat: a hook firing per-keystroke or stuck on remote calls saturates the host.
- Architectural mitigation:
  - COMP-021 (HookAdapter) wraps every invocation in a 1 s wall-clock SIGTERM via `aimem.hooks.safety.with_budget()`. Verified by AC-US052-2.
  - COMP-023 (LockManager) bounds contention with `lock.timeout_ms` → `error.kind=conflict, retriable=true`.

### MCP-VER-001 — Silent MCP version drift

- Threat: a host advertises an unsupported MCP protocol version and the server proceeds anyway, producing undefined behavior.
- Architectural mitigation:
  - COMP-024 (MCPFeatureSurface) explicitly negotiates `2025-11-25` (full features) or `2025-06-18` (degraded). All other versions → `error.kind=invariant` at handshake. Verified by AC-US051-1.
  - Smoke test G-23 asserts the pin in `pyproject.toml` matches the documented pin.

### EMBED-REMOTE-001 — Remote embedding silent failure

- Threat: `openai` / `http` provider silently returns zero or constant vectors, collapsing retrieval quality.
- Architectural mitigation:
  - COMP-022 (EmbedProvider) fails closed: timeout / non-2xx / non-finite values → `error.kind=transient, retriable=true`. Index is **not** updated with degenerate vectors. Verified by AC-US053-3.
  - `aimem verify` runs a canary embedding and asserts non-zero vector with the configured dimensionality.
  - Provider switch goes through index-generation rotation (R-043); no in-place overwrite.

### SAMPLING-001 — Recursive sampling cost amplification

- Threat: a Sampling-enabled handler triggers further tool calls, which trigger more Sampling, recursing.
- Architectural mitigation:
  - Sampling handlers in COMP-024 set `toolChoice="none"`. The host LLM cannot dispatch tools from inside a Sampling response. Verified by AC-US051-5.
  - Sampling is restricted to `evolve`, `compact`, and DP-promote summarize — never on hot read paths. Asserted by an import-graph unit test.

### Cross-cutting

- ROLE-005 (Hook Caller) is added to the role matrix with deny-list semantics and is not granted access to any team/project write or destructive op.
- All iter-2 mitigations preserve the iter-1 properties: HC1 (no Red secrets), HC2 (host-policy scope), HC3 (no implicit destructive), HC4 (every mutation is a git commit).
