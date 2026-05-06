# Story Dependency Graph

Spec-Version: 20260419-1400
Source: story-generator
Document-Range: 0200-0299

## Sequence

```text
US-001 (init)
  └── US-013 (config)
        └── US-002 (add)
              ├── US-006 (verify)
              ├── US-008 (logs)
              ├── US-014 (ulid+provenance)
              ├── US-011 (write gate)
              └── US-003 (get/show)
                    └── US-004 (list/tag)
                          └── US-005 (query)
                                ├── US-009 (error taxonomy)
                                ├── US-012 (perf CI)
                                └── US-007 (mcp server)
US-010 (migrate)            ─ depends on US-002 schema
US-015 (IFC retrieval)      ─ depends on US-005
US-016 (tombstone/forget)   ─ depends on US-002 + US-006
```

## Critical Path for MVP

US-001 → US-013 → US-002 → US-005 → US-007 → US-012.

## Iter-2 Update (2026-05-06)

### Iter-2 story dependencies

- **US-054** (`flock` + per-request stateless) is a foundational dependency for **US-051** and **US-052** and amends US-002 / US-003 (CRUD) — schedule it first.
- **US-053** (configurable embedding provider) extends **US-005** (hybrid search) and **US-013** (config). Schedule after US-005, parallel with US-051.
- **US-051** (full MCP surface) extends **US-007** (MCP). Schedule after US-007.
- **US-052** (hooks) depends on **US-051** (MCP server feature parity) for the structured-logging consumer and on **US-009** (CLI parser) for the `AIMEM_CALLER_ROLE=hook` deny-list. Schedule last among iter-2.

### Updated critical path (iter-2)

`US-001 → US-002 → US-054 → US-005 → US-007 → US-051 → US-053 → US-052 → US-006 → US-012`

(Other stories continue their original parallel placement.)
