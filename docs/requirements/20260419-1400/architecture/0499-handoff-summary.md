# Architecture Handoff for arch-validator

Spec-Version: 20260419-1400
Source: arch-designer
Document-Range: 0400-0499

> **NEXT AGENT**: arch-validator. Read this first.

## Outputs

| File | Purpose |
| ------ | --------- |
| 0400-overview.md | Top-level architecture and phase plan |
| 0401-technology-stack.md | Pinned tech choices |
| 0402-components.md | Component inventory + design.md entity mapping |
| 0403-data-flow.md | Add/Query/Verify/Forget flows + failure modes |
| 0404-deployment.md | Distribution + filesystem layout |
| 0405-security.md | Threat model + mitigations |
| 0406-nfr-mapping.md | Performance + reliability + HC mapping |
| 0499-handoff-summary.md | This file |

## App Type

CLI + MCP. UI scaffolding (Stages 10+) Not Applicable.

## Inputs Read

- docs/design.md (iter 1, authoritative)
- 0099, 0009, analysis/0199, analysis/audit-report.md, stories/0299, stories/0399.

## Status

- Architecture covers all 16 MVP stories.
- Forward-compat hooks for Phase 2 (LayerRepo, RemoteSyncer, privacy module).
- Ready for `arch-validator` review.

## Iter-2 Update (2026-05-06)

Driven by `0010-design-iter-2-addendum.md` and the stories iter-2 refresh (US-051..US-054).

### Iter-2 Inputs Verified

| File | Path |
| ------ | ------ |
| Stories iter-2 handoff | docs/requirements/20260419-1400/stories/0299-handoff-summary.md (§Iter-2 Update) |
| Story validator iter-2 | docs/requirements/20260419-1400/stories/0399-handoff-summary.md (APPROVED iter-2) |
| Iter-2 addendum | docs/requirements/20260419-1400/0010-design-iter-2-addendum.md |

### Iter-2 Outputs (additive)

| File | Change |
| ------ | -------- |
| 0400-overview.md | iter-2 overview of 4 architectural surfaces |
| 0401-technology-stack.md | MCP pin `2025-11-25`, embed-provider abstraction, `flock`+Windows shim, hook package |
| 0402-components.md | New COMP-021..COMP-024; CRUD + Index + MCP + CLI updates |
| 0403-data-flow.md | Roots / Elicitation / Sampling / Tasks / Hook / Embed-switch / Lock flows; iter-2 error-kind table |
| 0404-deployment.md | Process model (no daemon), MCP protocol pin negotiation, hook deployment, provider switch |
| 0405-security.md | Mitigations for HOOK-001/002, MCP-VER-001, EMBED-REMOTE-001, SAMPLING-001 |
| 0406-nfr-mapping.md | Iter-2 NFRs and HC1–HC6 enforcement table |

### Coverage (iter-2)

- Architecture covers all 20 MVP stories (16 prior + US-051..US-054).
- ROLE-005 (Hook Caller) integrated in COMP-001 deny-list and COMP-021 adapter.
- New entities E-013/E-014/E-015 traced to COMP-024/COMP-022/COMP-023.
- All HC1–HC6 enforcement preserved or strengthened (see 0406 iter-2 table).

### Status

Ready for `arch-validator` iter-2 review.
