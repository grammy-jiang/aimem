# Roles & Permissions Matrix

Spec-Version: 20260419-1400
Source: req-clarifier

## Roles

| Role ID | Role Name | Description |
|---------|-----------|-------------|
| ROLE-001 | Repository Owner | Full control over the memory repository. Manages configuration, performs maintenance, and has all CRUD and lifecycle capabilities. Typically the solo developer or team lead. |
| ROLE-002 | Team Contributor | Can propose memory additions to team repositories via pull requests. Cannot directly push to main, prune, or modify configuration. |
| ROLE-003 | Agent (MCP Client) | Automated consumer that interacts via MCP protocol. Can search, read, add (to hot buffer), and list notes. Cannot prune, configure, doctor, or directly commit to permanent storage. |

## Permission Matrix

| Capability | ROLE-001 (Repository Owner) | ROLE-002 (Team Contributor) | ROLE-003 (Agent/MCP Client) | Related Reqs |
|------------|---------------------------|---------------------------|---------------------------|--------------|
| `aimem init` | Yes | No | No | R-001 |
| `aimem add` (direct commit) | Yes | Via PR only | Hot buffer only | R-002, R-017 |
| `aimem get` | Yes | Yes (own fork) | Yes | R-002 |
| `aimem list` | Yes | Yes (own fork) | Yes | R-002 |
| `aimem update` | Yes | Via PR only | No | R-002 |
| `aimem remove` | Yes | Via PR only | No | R-002 |
| `aimem search` | Yes | Yes (own fork) | Yes | R-011 |
| `aimem link` | Yes | Via PR only | No | R-014 |
| `aimem graph` | Yes | Yes (own fork) | No | R-014 |
| `aimem consolidate` | Yes | No | No | R-017 |
| `aimem prune` | Yes | No | No | R-018 |
| `aimem evolve` | Yes | Via PR only | No | R-019 |
| `aimem dedup` | Yes | Yes (own fork) | No | R-016 |
| `aimem validate` | Yes | Yes (own fork) | No | R-006 |
| `aimem doctor` | Yes | Yes (own fork) | Yes (read-only) | R-023 |
| `aimem export` | Yes | Yes (own fork) | Yes | R-007, R-008 |
| `aimem import` | Yes | No | No | R-025 |
| `aimem sync` | Yes | Yes (own fork) | No | R-005 |
| `aimem status` | Yes | Yes (own fork) | Yes | R-002 |
| Edit .aimem.yaml | Yes | No | No | R-024 |

## Audit & Logging Requirements

### Auditable Actions

| Action | Must Log | Retention | Related ReqIDs | Compliance Driver |
|--------|----------|-----------|----------------|-------------------|
| Note creation | Yes | Git history (permanent) | R-002, R-005 | Data provenance |
| Note update | Yes | Git history (permanent) | R-002, R-005 | Change tracking |
| Note removal (archive) | Yes | Git history (permanent) | R-002, R-005 | Data provenance |
| Note pruning | Yes | Git history + JSONL log | R-018, R-027 | Audit trail for automated deletions |
| Consolidation (hot -> permanent) | Yes | Git history + JSONL log | R-017, R-027 | Lifecycle tracking |
| Config changes | Yes | Git history (permanent) | R-024, R-005 | Change tracking |
| Sync operations | Yes | JSONL log | R-005, R-027 | Troubleshooting |
| Doctor findings | Yes | JSONL log | R-023, R-027 | Health monitoring |
| Security filter rejections | Yes | JSONL log | R-020, R-027 | Security audit |
| Export generation | Yes | JSONL log | R-007, R-008, R-027 | Operational tracking |

### Audit Log Contents

| Field | Required | Description |
|-------|----------|-------------|
| Timestamp | Yes | ISO 8601 format with timezone |
| Actor | Yes | User ID (from git config) or "mcp-agent" for automated actions |
| Action | Yes | What was done (add, update, remove, prune, consolidate, etc.) |
| Target | Yes | What was affected (note path or entity) |
| Result | Yes | Success/Failure |
| IP Address | No | Not applicable (local-first CLI tool) |
| Previous Value | Conditional | For updates: tracked via git diff |
| New Value | Conditional | For updates: tracked via git diff |

### Access to Audit Logs

| Role ID | Role Name | Can View | Can Export | Can Delete |
|---------|-----------|----------|------------|------------|
| ROLE-001 | Repository Owner | Yes (git log, JSONL logs) | Yes | No (immutable git history) |
| ROLE-002 | Team Contributor | Yes (own fork git log) | Yes (own fork) | No |
| ROLE-003 | Agent (MCP Client) | Yes (memory_status only) | No | No |

> **Note**: Audit logs are immutable. Git history cannot be deleted without force-push (which branch protection prevents on team repos). JSONL logs are append-only files.
> **Note**: Use ROLE-XXX IDs for traceability. All roles in this table are defined in the Roles table above.
