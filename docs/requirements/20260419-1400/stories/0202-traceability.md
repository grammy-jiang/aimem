# Story → Requirement → Scenario Traceability

Spec-Version: 20260419-1400
Source: story-generator
Document-Range: 0200-0299

## Story → Requirement (forward)

| Story | Requirements Covered |
| ------- | ---------------------- |
| US-001 | R-001, R-005, R-024, R-034 (forward-compat) |
| US-002 | R-002, R-004, R-038, R-039, R-040 |
| US-003 | R-002, R-004 |
| US-004 | R-002, R-014 |
| US-005 | R-011, R-021, R-046 |
| US-006 | R-006, R-038, R-039 |
| US-007 | R-010, R-045 |
| US-008 | R-027 |
| US-009 | R-045 |
| US-010 | R-038 |
| US-011 | R-040, R-047 |
| US-012 | R-046 |
| US-013 | R-024, R-011, R-018, R-021 |
| US-014 | R-004, R-039 |
| US-015 | R-035 (forward-compat) |
| US-016 | R-044 |

## Requirement → Story (reverse)

| ReqID | Story IDs | Coverage |
| ------- | ----------- | ---------- |
| R-001 | US-001 | Covered |
| R-002 | US-002, US-003, US-004 | Covered |
| R-003 | US-002 (type=preference test) | Covered (typed write) |
| R-004 | US-002, US-003, US-014 | Covered |
| R-005 | US-001 | Covered |
| R-006 | US-006 | Covered |
| R-009 | All US-* (CLI surface) | Covered implicitly |
| R-010 | US-007 | Covered |
| R-011 | US-005, US-013 | Covered |
| R-021 | US-005, US-013 | Covered |
| R-024 | US-013 | Covered |
| R-027 | US-008 | Covered |
| R-038 | US-006, US-010 | Covered |
| R-039 | US-002, US-006, US-014 | Covered |
| R-040 | US-002, US-011 | Covered |
| R-045 | US-007, US-009 | Covered |
| R-046 | US-005, US-012 | Covered |
| R-047 | US-011 | Covered |

## Iter-2 Update (2026-05-06)

### Story → Requirement (forward, iter-2 additions)

| Story | Requirements Covered |
| ------- | ---------------------- |
| US-051 | R-010 (amended), R-051 |
| US-052 | R-052, R-040, R-045, R-009 |
| US-053 | R-011 (amended), R-053, R-043 |
| US-054 | R-002 (amended), R-054, R-005 |

### Requirement → Story (reverse, iter-2 additions)

| ReqID | Story IDs | Coverage |
| ------- | ----------- | ---------- |
| R-002 (iter-2 amended) | US-002, US-054 | Covered |
| R-010 (iter-2 amended) | US-007, US-051 | Covered |
| R-011 (iter-2 amended) | US-005, US-013, US-053 | Covered |
| R-051 | US-051 | Covered |
| R-052 | US-052 | Covered |
| R-053 | US-053 | Covered |
| R-054 | US-054 | Covered |
| R-040 (hook deny-list path) | US-011, US-052 | Covered |

All 20 iter-2 MVP R-IDs covered by ≥1 story.

### Story → Scenario (iter-2 additions)

| Story | Scenarios |
| ------- | ----------- |
| US-051 | SCN-WF003-HP-02 (extended), SCN-WF051-HP-01 (Roots auto-scope), SCN-WF051-NEG-01 (Elicitation decline) |
| US-052 | SCN-WF052-HP-01 (hook capture), SCN-WF052-NEG-01 (hook denied promote), SCN-WF052-NEG-02 (hook timeout) |
| US-053 | SCN-WF053-HP-01 (provider switch), SCN-WF053-NEG-01 (remote unreachable) |
| US-054 | SCN-WF054-HP-01 (concurrent add serialized), SCN-WF054-NEG-01 (lock timeout) |

### Role coverage update

- ROLE-005 (Hook Caller) → US-052 (primary), US-051 (Elicitation gate is host-mediated, not hook-callable).

## Story → Scenario

| Story | Scenarios |
| ------- | ----------- |
| US-001 | SCN-WF001-HP-01, SCN-WF001-NEG-01 |
| US-002 | SCN-WF002-HP-01, SCN-WF002-NEG-01, SCN-WF002-NEG-04 |
| US-005 | SCN-WF003-HP-01, SCN-WF003-EMPTY-01 |
| US-007 | SCN-WF003-HP-02 (MCP path) |
| US-011 | SCN-WF002-NEG-04 |
| US-016 | SCN-WF005-NEG-03 |
