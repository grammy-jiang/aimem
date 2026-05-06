# E2E Playbook Handoff for e2e-playbook-validator

Spec-Version: 20260419-1400
Source: e2e-playbook-generator
Document-Range: 0800-0899

> **NEXT AGENT**: e2e-playbook-validator. Read this first.

## Outputs

| File | Purpose |
| ------ | --------- |
| 0800-index.md | Harness + playbook index |
| 0801-bootstrap.md | PB-001 cold path; PB-002 write-gate |
| 0802-mcp-and-verify.md | PB-003 MCP RTT; PB-004 verify sig |
| 0803-forget-migrate.md | PB-005 tombstone; PB-006 migrate dry-run |
| 0804-retrieval-and-perf.md | PB-007 BM25 fallback; PB-008 perf gates |
| 0899-handoff-summary.md | This file |

## App Type

CLI + MCP (no browser). All playbooks are subprocess + MCP-stdio.

## Coverage

8 playbooks cover the 16 MVP stories' E2E surface:

- US-001 → PB-001
- US-002 → PB-001, PB-002
- US-003 → PB-001 (lookup by id implicit)
- US-004 → covered at unit level (no E2E playbook needed)
- US-005 → PB-001, PB-007, PB-008
- US-006 → PB-004
- US-007 → PB-003, PB-008
- US-008 → exercised inside every playbook (log assertions)
- US-009 → PB-002, PB-005, PB-006 (error.kind assertions)
- US-010 → PB-006
- US-011 → PB-002
- US-012 → PB-008
- US-013 → exercised by harness (`AIMEM_DIR`, `.aimem.yaml`)
- US-014 → asserted in PB-001 (id format)
- US-015 → unit-only in Phase 1 (forward-compat)
- US-016 → PB-005

## Status

Ready for `e2e-playbook-validator`.

## Iter-2 Update (2026-05-06)

Driven by `0010-design-iter-2-addendum.md` and the architecture iter-2 refresh.

### Iter-2 Inputs Verified

| File | Path |
| ------ | ------ |
| Architecture iter-2 handoff | docs/requirements/20260419-1400/architecture/0499-handoff-summary.md |
| Architecture validator iter-2 | docs/requirements/20260419-1400/architecture/0599-handoff-summary.md |
| Iter-2 addendum | docs/requirements/20260419-1400/0010-design-iter-2-addendum.md |

### Iter-2 Outputs (additive)

| File | Change |
| ------ | -------- |
| 0800-index.md | Iter-2 index PB-051..PB-059 |
| 0805-mcp-iter2.md | NEW — PB-051..PB-055 (MCP feature surface) |
| 0806-hooks.md | NEW — PB-056..PB-057 (hooks integration + safety contract) |
| 0807-embed-provider.md | NEW — PB-058..PB-059 (provider switch + flock concurrency) |

### Coverage (iter-2)

- 4 new MVP stories (US-051..US-054) each → ≥1 playbook.
- All iter-2 ACs (AC-US051-1..6, AC-US052-1..5, AC-US053-1..5, AC-US054-1..4) mapped to a step in PB-051..PB-059.
- All HC1–HC4 reinforcements (per 0200 iter-2 coverage summary) verified by ≥1 step.
- All red-team mitigations (HOOK-001/002, MCP-VER-001, EMBED-REMOTE-001, SAMPLING-001) exercised.

### Status (iter-2)

Ready for `e2e-playbook-validator` iter-2 review.
