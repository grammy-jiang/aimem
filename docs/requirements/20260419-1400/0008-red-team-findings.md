# Red-Team Findings - Failure Modes & Security Concerns

Spec-Version: 20260419-1400
Source: req-clarifier

## Abuse Cases

| ID | Attack Vector | Impacted ReqIDs | Mitigation Strategy | Priority |
| ---- | -------------- | ----------------- | --------------------- | ---------- |
| ABUSE-001 | Memory poisoning via malicious PR to team repo: attacker submits notes with subtle behavioral overrides or redirect instructions that pass human review | R-020, R-022, R-005 | Defense-in-depth: (1) memory density dilutes attacks (ASR 62%->6%), (2) GPG-signed commits for provenance, (3) pattern-based filtering on storage and retrieval, (4) retrieval window limit of 5 | High |
| ABUSE-002 | Progressive shortening attack: attacker submits a series of PRs that gradually compress malicious content to evade pattern filters | R-020, R-022 | PR review required for team repos; pattern filter is first layer only; memory density is primary defense | Medium |
| ABUSE-003 | Tag/metadata manipulation to hijack retrieval ranking: attacker crafts notes with popular tags to ensure poisoned content surfaces for common queries | R-011, R-015, R-020 | Dedup pipeline detects tag-overlap anomalies; retrieval window limits exposure; doctor detects suspicious tag patterns | Medium |
| ABUSE-004 | Hot buffer flooding: attacker (via compromised MCP client) rapidly adds thousands of notes to exhaust disk space or slow consolidation | R-017, R-010 | Rate limiting on MCP add operations; hot buffer size cap in config; consolidation quality checks reject noise | Low |

## Permission Escalation Risks

| ID | Risk Description | Impacted Roles (ROLE-XXX) | Impacted ReqIDs | Mitigation |
| ---- | ----------------- | --------------------------- | ----------------- | ------------ |
| PERM-001 | MCP agent bypasses hot buffer and commits directly to permanent storage | ROLE-003 | R-010, R-017 | MCP memory_add tool routes exclusively to hot buffer; direct git commit requires CLI access (ROLE-001 only) |
| PERM-002 | Team contributor pushes directly to main branch in team repo, bypassing PR review | ROLE-002 | R-022, R-005 | Git branch protection rules on team repos; aimem does not enforce this (relies on git hosting platform) |

## Data Loss / Corruption Scenarios

| ID | Scenario | Impacted Entities (E-XXX) | Impacted ReqIDs | Mitigation |
| ---- | ---------- | --------------------------- | ----------------- | ------------ |
| DATA-001 | Interrupted write leaves partial YAML frontmatter in a note file | E-001, E-002 | R-005, R-002 | Atomic writes: write to temp file, then rename; git commit only after successful write |
| DATA-002 | `aimem prune` accidentally removes a note that is actively referenced by links from other notes | E-001, E-003 | R-018, R-014 | Prune checks incoming links before archiving; notes with active incoming links from non-archived notes are never pruned |
| DATA-003 | Merge conflict during `aimem sync` corrupts a note's YAML frontmatter | E-001, E-002 | R-005, R-006 | Git rebase strategy; `aimem validate` after sync to detect corruption; user resolves conflicts manually |
| DATA-004 | Hot buffer notes lost during system crash (not git-tracked) | E-005 | R-017 | Accepted risk: hot buffer is explicitly gitignored and transient by design; notes can be re-added |

## Concurrency / Race Conditions

| ID | Scenario | Impacted Workflows (WF-XXX) | Impacted ReqIDs | Mitigation |
| ---- | ---------- | ---------------------------- | ----------------- | ------------ |
| RACE-001 | Two CLI processes run `aimem add` simultaneously, creating notes with conflicting git state | WF-002 | R-002, R-005 | Git handles concurrent commits via lock file (.git/index.lock); second process gets lock error and retries or fails gracefully |
| RACE-002 | `aimem consolidate` runs while `aimem prune` is archiving the same note | WF-005 | R-017, R-018 | File-level locking or sequential execution; consolidate checks note existence before promotion |
| RACE-003 | `aimem sync` runs during `aimem add --commit`, causing rebase conflict on uncommitted changes | WF-002, WF-004 | R-005 | Git lock file prevents concurrent git operations; second operation waits or fails with actionable error |

## Integration Failure Modes

| ID | Integration (INT-XXX) | Failure Mode | Impact | Fallback Strategy | Impacted ReqIDs |
| ---- | ---------------------- | -------------- | -------- | ------------------- | ----------------- |
| INTFAIL-001 | INT-001 (Git) | Git binary not found on system | All operations fail | `aimem init` checks for git availability and reports actionable error; document git as a hard dependency | R-001, R-005 |
| INTFAIL-002 | INT-001 (Git) | Git remote unreachable during sync | Sync fails; local operations unaffected | `aimem sync` reports network error; all other operations work offline | R-005 |
| INTFAIL-003 | INT-002 (MCP Protocol) | MCP server crashes or becomes unresponsive | Agent cannot access memories via MCP | Agent falls back to exported config files (CLAUDE.md, etc.); CLI remains operational | R-010 |
| INTFAIL-004 | INT-003 (Embedding Model) | Embedding model fails to load or is not installed | Semantic search and dedup unavailable | Search falls back to BM25-only; dedup falls back to Jaccard-only (tag overlap); log degradation warning | R-011, R-016 |

## Resource Exhaustion Risks

| ID | Resource | Exhaustion Scenario | Impact | Mitigation | Impacted ReqIDs |
| ---- | ---------- | --------------------- | -------- | ------------ | ----------------- |
| RESOURCE-001 | Disk space | Repository grows beyond 10,000 notes with large bodies; git history compounds disk usage | Filesystem full; writes fail | `aimem doctor` reports note budget vs. actual count; forgetting policy prunes bottom 10%; `aimem status` shows total notes | R-018, R-023 |
| RESOURCE-002 | Memory (RAM) | Search index for 10,000 notes with embeddings exceeds available RAM | Search crashes or OOM | Lazy index loading; configurable embedding dimensions; fallback to BM25-only if memory insufficient | R-011, R-012 |
| RESOURCE-003 | Git index performance | Very large number of files (>10,000) degrades git operations | Slow commits, slow status | Git sparse checkout for large repos; doctor warns at note count thresholds; forgetting policy keeps active set manageable | R-005, R-023 |

## Red-Team Summary

| Category | Issues Found | Critical | High | Medium | Low |
| ---------- | -------------- | ---------- | ------ | -------- | ----- |
| Abuse Cases | 4 | 0 | 1 | 2 | 1 |
| Permission Escalation | 2 | 0 | 0 | 2 | 0 |
| Data Loss | 4 | 0 | 1 | 2 | 1 |
| Concurrency | 3 | 0 | 0 | 2 | 1 |
| Integration Failures | 4 | 0 | 1 | 2 | 1 |
| Resource Exhaustion | 3 | 0 | 0 | 2 | 1 |
| **Total** | **20** | **0** | **3** | **12** | **5** |

Key findings:

- **No critical issues**: The defense-in-depth security model (memory density, git provenance, pattern filtering, retrieval window limits) provides strong protection against memory poisoning, which is the primary threat vector.
- **High priority items**: ABUSE-001 (memory poisoning via PR), DATA-001 (partial writes), INTFAIL-001 (missing git). All have clear mitigations.
- **Accepted risk**: DATA-004 (hot buffer loss on crash) is by-design; hot buffer is transient and gitignored.
- **Scale concerns**: The 10,000-note target is achievable but requires attention to index memory usage (RESOURCE-002) and git performance (RESOURCE-003). Forgetting policy and doctor warnings provide guardrails.
