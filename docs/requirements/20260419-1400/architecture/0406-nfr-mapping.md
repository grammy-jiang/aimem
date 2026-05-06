# NFR Mapping

Spec-Version: 20260419-1400
Source: arch-designer
Document-Range: 0400-0499

## Performance (R-046, design.md §10)

| Metric | Budget (p95, warm) | Owner Component | Verifying AC |
| -------- | -------------------- | ----------------- | -------------- |
| Query latency | 150 ms | COMP-005, COMP-013 | AC-US005-3 |
| Add latency | 200 ms | COMP-004, COMP-013 | AC-US002 (perf bench in US-012) |
| MCP RTT | 200 ms | COMP-002 + service | AC-US007-2 |
| Cold start | 1500 ms | COMP-001/002 | AC-US012-1 |
| Sync (P2) | 2000 ms | COMP-009 | P2 |

Regression > 10 % fails CI (AC-US012-2).

## Quality / LongMemEval

| Metric | Threshold | Owner | AC |
| -------- | ----------- | ------- | ----- |
| P@5 on bundled slice | ≥ 0.7 | COMP-005 | AC-US005-2 |

## Reliability

| Concern | Approach |
| --------- | ---------- |
| Crash safety | Atomic writes via `os.replace`; index rebuild from store of record |
| Data integrity | `aimem verify` walks sigs and links |
| Idempotency | `init`, `tag add/rm`, MCP add with same canonical content + agent → no-op |

## Usability

- One-line install (`uv tool install aimem`).
- One command bootstrap (`aimem init`).
- Default config works without editing.

## Supportability

- JSONL logs with stable field set (R-027 / US-008).
- Stable error taxonomy (R-045 / US-009) for client tooling.
- `aimem verify` as a self-diagnostic.

## Security NFRs (also see 0405)

- gitleaks pre-commit blocks Red-class commits (R-047).
- Path confinement to AIMEM_DIR (HC2).
- No telemetry; no outbound calls in Phase 1.

## Constraints (HC1–HC6)

| HC | Architectural Enforcement |
| ---- | --------------------------- |
| HC1 deterministic write-gate | COMP-016, no LLM dependency |
| HC2 path confinement | COMP-011 realpath checks |
| HC3 stable error taxonomy | COMP-018 closed enum |
| HC4 schema versioned | COMP-012 + COMP-008 |
| HC5 signed records | COMP-015 mandatory at write |
| HC6 forward-compat for layers | COMP-011 LayerRepo abstraction |

## Iter-2 Update (2026-05-06)

### Iter-2 NFR additions

| NFR | Target | Owning component |
| ----- | -------- | ------------------ |
| Hook wall clock (p100) | ≤ 1 000 ms (SIGTERM-enforced) | COMP-021 (HookAdapter) |
| `aimem add` with remote embed (warm) | ≤ 800 ms p95 | COMP-022 (EmbedProvider) |
| Embed remote timeout default | 5 000 ms (`embed.timeout_ms`) | COMP-022 |
| MCP `memory_query` with Roots | ≤ 200 ms p95 (unchanged) | COMP-007 + COMP-024 |
| MCP `memory_sync` Task polling cadence | ≥ 250 ms | COMP-024.tasks |
| Lock acquisition timeout | 100 ms default (`lock.timeout_ms`) | COMP-023 (LockManager) |
| Concurrent writers, no daemon | 2+ writers serialize, no partial writes | COMP-023 + COMP-002 |
| Provider switch downtime | 0 (old generation serves reads during warm-up) | COMP-006 + COMP-022 |

### Iter-2 hard-constraint mapping (HC1–HC6)

| Constraint | Iter-2 enforcement |
| ------------ | -------------------- |
| HC1 no Red secrets | COMP-022 enforces `api_key_env` (no inline keys); COMP-001 hook deny-list prevents Red writes via hooks |
| HC2 host-policy scope | COMP-024 Roots auto-scope; COMP-001 hook deny-list of team/project writes; opt-in hook configs only |
| HC3 no implicit destructive | COMP-024 Elicitation gates promote/demote/inbox-approve/tombstone; COMP-001 denies these in hook mode entirely |
| HC4 auditability | COMP-023 ensures every write is a complete git transaction; no daemon, no shared in-memory state |
| HC5 signed records | unchanged; COMP-015 still mandatory at write |
| HC6 forward-compat for layers | unchanged; COMP-011 LayerRepo abstraction; COMP-022 EmbedProvider abstraction adds future provider extension |
