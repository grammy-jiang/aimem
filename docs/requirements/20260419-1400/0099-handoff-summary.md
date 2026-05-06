# Handoff Summary for req-analyzer

> **NEXT AGENT**: Read this document FIRST before processing other artifacts.
>
> **HALT RULE**: If any artifact version in the table below does not match, STOP and report the inconsistency. Do not proceed with mismatched versions.

Spec-Version: 20260419-1400
Source: req-clarifier (refreshed 2026-05-06 against docs/design.md iter 2)
Document-Range: 0000-0099 (0009 added in iter-1 pass; 0010 added in iter-2 pass)

## Artifact Version Table (MUST BE CONSISTENT)

| File | Spec-Version | Status |
| ------ | -------------- | -------- |
| 0000-requirements-registry.md | 20260419-1400 | Generated |
| 0001-acceptance-criteria.md | 20260419-1400 | Generated |
| 0002-scenario-inventory.md | 20260419-1400 | Generated |
| 0003-roles-permissions.md | 20260419-1400 | Generated |
| 0004-data-dictionary.md | 20260419-1400 | Generated |
| 0005-nfr-targets.md | 20260419-1400 | Generated |
| 0006-traceability-skeleton.md | 20260419-1400 | Generated |
| 0007-traceability-audit.md | 20260419-1400 | Generated |
| 0008-red-team-findings.md | 20260419-1400 | Generated |
| 0009-design-iter-1-addendum.md | 20260419-1400 | Generated (iter-1 delta) |
| 0010-design-iter-2-addendum.md | 20260419-1400 | Generated (iter-2 delta) |
| 0099-handoff-summary.md | 20260419-1400 | Generated |

> All versions match. Artifacts are consistent. Iter-1 deltas live in 0009; original 0000-0008 are preserved verbatim and amendments are flagged in 0009.

## Artifact Paths (Downstream Contract)

**Output Directory**: docs/requirements/20260419-1400/

| File | Relative Path | Status |
| ------ | --------------- | -------- |
| 0000-requirements-registry.md | docs/requirements/20260419-1400/0000-requirements-registry.md | Written |
| 0001-acceptance-criteria.md | docs/requirements/20260419-1400/0001-acceptance-criteria.md | Written |
| 0002-scenario-inventory.md | docs/requirements/20260419-1400/0002-scenario-inventory.md | Written |
| 0003-roles-permissions.md | docs/requirements/20260419-1400/0003-roles-permissions.md | Written |
| 0004-data-dictionary.md | docs/requirements/20260419-1400/0004-data-dictionary.md | Written |
| 0005-nfr-targets.md | docs/requirements/20260419-1400/0005-nfr-targets.md | Written |
| 0006-traceability-skeleton.md | docs/requirements/20260419-1400/0006-traceability-skeleton.md | Written |
| 0007-traceability-audit.md | docs/requirements/20260419-1400/0007-traceability-audit.md | Written |
| 0008-red-team-findings.md | docs/requirements/20260419-1400/0008-red-team-findings.md | Written |
| 0009-design-iter-1-addendum.md | docs/requirements/20260419-1400/0009-design-iter-1-addendum.md | Written |
| 0010-design-iter-2-addendum.md | docs/requirements/20260419-1400/0010-design-iter-2-addendum.md | Written |
| 0099-handoff-summary.md | docs/requirements/20260419-1400/0099-handoff-summary.md | Written |

> **Note**: All paths are relative to the project root at /home/grammy-jiang/projects/aimem.

## Required Files for Downstream Agents

**For req-analyzer** (next agent in pipeline):

- **MUST READ FIRST**: 0099-handoff-summary.md
- **Required**: All files 0000-0008 listed above

> **Contract**: If ANY of the above files are missing, req-analyzer MUST HALT with FAIL.MISSING_UPSTREAM_ARTIFACT and return to req-clarifier.

## Project Overview

aimem is a git-backed persistent memory system for local AI coding agents (Claude Code, GitHub Copilot, Cursor, and future agents). It stores structured memory notes (YAML frontmatter + Markdown body) in a git repository with four memory types (identity, knowledge, procedure, journal), tiered context injection, hybrid BM25+embedding retrieval with pyramid expansion, type-aware forgetting policies, and defense-in-depth security against memory poisoning. The system exposes a CLI (Click-based) and an MCP server (FastMCP) that share a common core library, with agent-specific export adapters that generate configuration files from the unified memory store.

## Completeness Status

All 19 exit gates passed:

1. Requirement registry with stable IDs (R-001 through R-033; R-001 to R-027 Must-Have, R-028 to R-033 Nice-to-Have/Deferred)
2. All personas (P-001, P-002), workflows (WF-001 through WF-006), integrations (INT-001 through INT-003), and roles (ROLE-001 through ROLE-003) have stable IDs
3. Out-of-scope items documented (8 items: no GUI/web, no cloud, no mobile, no real-time collab, no non-text memories, no Cursor/Continue adapters in MVP, no alerting system, no LLM self-validation for security)
4. Acceptance criteria: all 27 Must-Have requirements have 3 or more ACs each with TestLevel tags
5. No requirements violate split rule (max 3 WF per requirement, max 7 AC, max 2 personas, max 2 integrations)
6. Scenario inventory with workflow-scoped IDs covering HP, NEG, EMPTY, FAIL across all 6 workflows
7. Role/permission matrix for ROLE-001, ROLE-002, ROLE-003 with 20 capabilities mapped
8. Data dictionary with E-001 through E-006 (Note, NoteMeta, LinkGraph, AimemConfig, HotBufferEntry, SearchIndex)
9. NFR targets with measurement methods (performance at 10K note scale, reliability with atomic writes, i18n with message catalogs, observability with JSONL logging)
10. Traceability skeleton with 5 mapping tables (Req-Persona, Req-Workflow, Req-Integration, Req-Role, Req-DataEntity)
11. Traceability audit completed: zero orphans across all entity types, zero split rule violations
12. Red-team findings documented: 20 findings across 6 categories (0 critical, 3 high, 12 medium, 5 low)
13. Open questions tagged to ReqIDs (none remaining)
14. Artifact versions consistent (20260419-1400 across all 10 files)
15. No synthetic/placeholder entities in final artifacts (all IDs are real project entities)
16. 0099 contains no fenced code blocks (plain markdown only)
17. No TEMPLATE WARNING markers in 0099
18. No literal placeholder patterns in 0099
19. No placeholders/template markers across 0000-0008

## Open Questions

*None identified during requirements clarification.*

## Assumptions Made

> Iter-2 update: all four assumptions have been **user-confirmed** on 2026-05-06; assumptions 2 and 4 were refined and now have dedicated requirements (R-053 and R-054 respectively in `0010-design-iter-2-addendum.md`).

| Assumption | Confirmed | Refinement (iter 2) | Impacted ReqIDs | Risk if Wrong | Source |
| ------------ | ----------- | --------------------- | ----------------- | --------------- | -------- |
| Git is always available on the host system | Yes | Unchanged | R-001, R-005, R-017 | High -- all storage operations depend on git | Design document specifies git-backed storage; INTFAIL-001 documents the failure mode |
| Embedding model is local | Yes | **Refined**: provider is configurable (`local \| openai \| http`); local is default. Remote providers MUST source API keys from env vars (HC1) and fail closed if unreachable. See R-053. | R-011, R-012, R-016, R-053 | Low -- explicitly pluggable now | User confirmation 2026-05-06 |
| Maximum repository scale ~10 000 notes | Yes | Unchanged | R-011, R-012, R-018 | Low -- if larger, index strategy and git performance need re-evaluation | User confirmed Round 4 + iter-2 confirmation |
| Single-user CLI process (no daemon) | Yes | **Refined**: MCP server may be long-running for an agent session, but the `aimem.core` library is per-request stateless (open/transact/close on every call). No daemon, no IPC beyond MCP stdio. Concurrency serialized by `flock(2)`. See R-054. | R-002, R-005, R-054 | Low | User confirmation 2026-05-06 |

## Key Personas Summary

**P-001 -- Solo Developer**: The primary user. An individual developer who uses one or more AI coding agents (Claude Code, Copilot) locally. They want their preferences, project knowledge, and session history to persist across sessions and machines. Moderate-to-high technical proficiency. Interacts via CLI and benefits from MCP server integration with their agents.

**P-002 -- Team Lead**: A developer who maintains shared team conventions in a team memory repository. Reviews memory contributions via git pull requests. Concerned with consistency across team members, onboarding new developers, and security of shared memory repos. High technical proficiency.

## Red-Team Summary

| Category | Critical | High | Medium | Low |
| ---------- | ---------- | ------ | -------- | ----- |
| Abuse Cases | 0 | 1 | 2 | 1 |
| Permission Escalation | 0 | 0 | 2 | 0 |
| Data Loss | 0 | 1 | 2 | 1 |
| Concurrency | 0 | 0 | 2 | 1 |
| Integration Failures | 0 | 1 | 2 | 1 |
| Resource Exhaustion | 0 | 0 | 2 | 1 |
| **Total** | **0** | **3** | **12** | **5** |

The primary security concern is memory poisoning via malicious contributions to shared team repos (ABUSE-001). The design document's defense-in-depth model (memory density reducing ASR from 62% to 6%, GPG-signed commits, pattern filtering, retrieval window limits) addresses this comprehensively. The three high-priority items (ABUSE-001, DATA-001, INTFAIL-001) all have clear, implementable mitigations. No critical issues were identified.

## Iter-1 Delta Summary (2026-05-06)

The engineering design was rewritten as iter 1 (`docs/design.md`, supersedes `docs/design.2026-04-19.md`). Material additions captured in `0009-design-iter-1-addendum.md`:

- Three-layer sharing model with IFC lattice (R-034, R-035) and per-layer git submodules under `~/.ai-memory/`.
- Layer promote/demote (R-036), inbox quarantine (R-037), and DP-on-promote (R-041).
- MemoryRecord v1 schema with `schema_version`, ULID, ed25519 signing, forgetting policy, provenance (amends R-004; new R-038, R-039).
- MCP server pinned to `2025-06-18` over stdio with revised tool list (amends R-010).
- Default embedding `bge-small-en-v1.5` + SQLite FTS5 + flat HNSW; index never committed (amends R-011).
- Stale-vector handling and tombstones (R-043, R-044).
- Stable error taxonomy (R-045) and gitleaks pre-commit (R-047).
- Performance budgets §10 and evaluation gates §11/§12 promoted to NFRs (R-046).
- Hot-buffer (R-017) **dropped** for v1; replaced by R-037 + R-040.
- New red-team findings: LEAK-001, ADAPT-001, STALE-001, INBOX-001, DP-BUDGET-001.
- New role ROLE-004 (Team Layer Maintainer); new entities E-007..E-012; E-005 dropped.

All 19 original exit gates remain green; two additional gates (G-20, G-21) introduced and passing.

## Iter-2 Delta Summary (2026-05-06)

The engineering design was rewritten as iter 2 (`docs/design.md`, supersedes iter 1). Material additions captured in `0010-design-iter-2-addendum.md`:

- **MCP version bump** from `2025-06-18` to **`2025-11-25`** (amends R-010). Tools advertise SEP-973 icons and human-readable `description`s; tool input schemas use JSON Schema 2020-12; input-validation failures are returned as Tool Execution Errors (SEP-1303); structured JSON logs go to stderr (PR #670).
- **Full MCP feature surface (R-051)**: server uses Tools + Resources + Prompts; consumes client Roots (auto-scope active layer set via `.aimem-bind`), Elicitation (gates every write-down: promote/demote/inbox-approve/tombstone), Sampling (only for `evolve`/`compact` and DP-on-promote summarization, with `toolChoice: "none"`), and Logging. `memory_sync` is wrapped as an experimental Task (SEP-1686) with synchronous fallback.
- **Agent-hooks integration (R-052)**: reference hook configurations under `examples/hooks/` for Claude Code (`SessionStart`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `PreCompact`), GitHub Copilot CLI, and Codex CLI. Hooks are untrusted callers: cannot write to `project`/`team` layers, cannot promote/demote/inbox-approve/tombstone, wall-clock-bounded ≤1 s, opt-in install (HC2).
- **Configurable embedding provider (R-053)**: `embed.provider ∈ {local, openai, http}`; default local; remote providers fail closed; API keys from env vars only (HC1); provider switch triggers index-generation rotation (R-043).
- **Per-request stateless backend (R-054)**: MCP server may be long-running but the core library opens/transacts/closes on every call; no daemon; `flock(2)` serializes concurrent invocations (`error.kind=conflict` on timeout).
- **New red-team findings**: HOOK-001 (hook exfiltration), HOOK-002 (hook resource exhaustion), MCP-VER-001 (silent version degradation), EMBED-REMOTE-001 (remote embedding silent failure), SAMPLING-001 (recursive sampling).
- **New role**: ROLE-005 (Agent Hook Caller) with explicit deny-list.
- **New entities**: E-013 (LayerBindMarker), E-014 (EmbedProviderConfig), E-015 (LockFile).
- **New scenarios**: 8 across WF-001..WF-006 covering hooks, Tasks, Elicitation decline, remote-embed failure, provider switch, and hook denial of promote.

All 21 prior exit gates remain green; two new gates (G-22, G-23) introduced and passing:

- G-22: every R-051..R-054 has ≥1 AC with TestLevel; every new red-team finding maps to a mitigating ReqID.
- G-23: MCP version pin matches between `pyproject.toml` and `docs/design.md` (`2025-11-25`).

## Next Steps for req-analyzer

1. **Verify artifact versions match** (halt if mismatch) -- all files should show 20260419-1400
2. Validate requirement priorities using MoSCoW framework (27 Must-Have, 6 Nice-to-Have/Deferred)
3. Assess technical complexity and dependencies, particularly for hybrid search (R-011, R-012) and write-path pipeline (R-015, R-016, R-017)
4. Identify potential risks and mitigation strategies, referencing the 20 red-team findings in 0008
5. Review the 4 assumptions for risk assessment, especially the embedding model assumption
6. Evaluate the phased implementation roadmap from the design document (Sections 18.1 through 18.4) against the requirements registry
