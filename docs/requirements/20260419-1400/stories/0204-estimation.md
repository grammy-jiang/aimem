# Estimation Notes

Spec-Version: 20260419-1400
Source: story-generator
Document-Range: 0200-0299

Effort scale: T-shirt — XS (≤0.5d), S (1d), M (2-3d), L (4-7d), XL (>1w).

| Story | Effort | Confidence | Notes |
| ------- | -------- | ------------ | ------- |
| US-001 init | S | High | Submodule glue + .aimem.yaml seed. |
| US-002 add | M | High | Schema, sig, write-gate; bulk of MemoryRecord plumbing. |
| US-003 get/show | XS | High | Trivial after US-002. |
| US-004 list/tag | S | High | FTS-backed listing; tag mutations. |
| US-005 query | L | Medium | Hybrid retrieval, hnswlib + BM25 + bench harness. |
| US-006 verify | S | High | Walk store, validate sig + frontmatter. |
| US-007 mcp | M | Medium | FastMCP wiring + protocol pin. |
| US-008 logs | XS | High | Structured JSONL writer. |
| US-009 errors | XS | High | Error class + mapping table. |
| US-010 migrate | S | Medium | Dry-run path; needs CI hook. |
| US-011 write-gate | S | High | Deterministic regex/AST-based scanner. |
| US-012 perf CI | S | Medium | pytest-benchmark + thresholds. |
| US-013 config | XS | High | Pydantic-settings load. |
| US-014 ulid+prov | XS | High | ULID lib + frontmatter fields. |
| US-015 IFC retrieval | S | Medium | Forward-compat assertions; no >1 layer in Phase-1. |
| US-016 forget | S | Medium | Tombstone semantics + cascade. |

Total: ~ 4-6 person-weeks for Phase 1.

## Iter-2 Update (2026-05-06)

| Story | Effort (story points) | Notes |
| ------- | ------------------------ | ------- |
| US-051 | 8 | Wires Roots/Elicitation/Sampling/Tasks/Logging across FastMCP; high test surface. |
| US-052 | 5 | Hook adapter package + parser-layer deny-list + 1 s budget guard + 3 reference configs. |
| US-053 | 5 | Provider abstraction + fail-closed remote + canary verify; depends on US-005. |
| US-054 | 3 | `flock(2)` + Windows shim + lock-timeout error mapping. |

Iter-2 increment total: **21 points** (~ 1.5 person-weeks) on top of iter-1's MVP estimate.
