# E2E Playbooks — Index & Harness

Spec-Version: 20260419-1400
Source: e2e-playbook-generator
Document-Range: 0800-0899
App Type: CLI + MCP (no browser)

## Harness

E2E tests run as `pytest` cases under `tests/e2e/` using:

- A scratch `AIMEM_DIR` per test (`tmp_path`).
- Subprocess calls to `aimem` and `aimem-mcp` (built from this repo via `uv run`).
- A pytest fixture `mcp_client` that talks to `aimem-mcp` over stdio.
- A pytest fixture `bench_corpus` that seeds the bundled LongMemEval slice for perf playbooks.

Each playbook below specifies preconditions, steps, expected outcomes, and trace IDs. Playbooks are language-agnostic descriptions; their pytest implementation is part of US-001…US-016 delivery.

## Playbook Index

| ID | Title | File |
| ---- | ------- | ------ |
| PB-001 | Cold install → init → add → query | 0801 |
| PB-002 | Reject secret on add (write-gate) | 0801 |
| PB-003 | MCP round-trip query under budget | 0802 |
| PB-004 | Verify catches malformed signature | 0802 |
| PB-005 | Forget tombstones a record | 0803 |
| PB-006 | Migrate dry-run reports without writing | 0803 |
| PB-007 | Hybrid retrieval falls back to BM25 when embedder unavailable | 0804 |
| PB-008 | Performance gate: query / add / MCP RTT under §10 budgets | 0804 |

## Iter-2 Update (2026-05-06)

Nine iter-2 playbooks added covering R-051..R-054 plus amendments to R-002/R-010/R-011. All numbered PB-051..PB-059 to keep iter-1 IDs frozen.

| ID | Scenario | File |
| ---- | ---------- | ------ |
| PB-051 | MCP `2025-11-25` initialize handshake; `2025-06-18` degraded path; unknown version rejected | 0805-mcp-iter2.md |
| PB-052 | Roots-driven auto-scope: write tool resolves layer from Roots; missing Root → invariant | 0805-mcp-iter2.md |
| PB-053 | Elicitation gates `layer promote`; decline → auth, no fs change | 0805-mcp-iter2.md |
| PB-054 | Tasks: `memory_sync` returns Task handle; sync fallback when unsupported | 0805-mcp-iter2.md |
| PB-055 | Sampling restricted to evolve/compact/promote with `toolChoice="none"` (import-graph + runtime probe) | 0805-mcp-iter2.md |
| PB-056 | Hook capture/recall via `examples/hooks/` reference configs | 0806-hooks.md |
| PB-057 | Hook safety contract: deny `--layer team\|project`, deny destructive subcommands, 1 s wall clock | 0806-hooks.md |
| PB-058 | Embed provider switch (`local` → `openai`); generation rotation; old gen serves reads during warm-up; canary verify | 0807-embed-provider.md |
| PB-059 | `flock(2)` concurrency: two concurrent `aimem add` serialize; lock timeout → conflict | 0807-embed-provider.md |
