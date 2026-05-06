# Business Data Dictionary

Spec-Version: 20260419-1400
Source: req-clarifier

## Entities

### E-001: Note

The atomic memory unit. A YAML frontmatter + Markdown body file stored in the git repository.

| Field | Type | Required | Constraints | Notes |
| ------- | ------ | ---------- | ------------- | ------- |
| path | Path | Yes | Must be within repo root; relative to memory_dir | Derived from type directory + slugified title |
| meta | NoteMeta (E-002) | Yes | Must validate against Pydantic model | YAML frontmatter section |
| title | string | Yes | Extracted from first `# Heading` line | Display name |
| body | string | No | UTF-8 encoded Markdown | Content after the title heading |

### E-002: NoteMeta

YAML frontmatter metadata for a memory note. Validated by Pydantic BaseModel.

| Field | Type | Required | Constraints | Notes |
| ------- | ------ | ---------- | ------------- | ------- |
| type | MemoryType enum | Yes | One of: identity, knowledge, procedure, journal | Determines directory and tier behavior |
| tags | list[str] | Yes (default: []) | Lowercase, no spaces within tags | Used for filtering and Jaccard dedup |
| updated | date | Yes (default: today) | ISO 8601 date (YYYY-MM-DD) | Auto-set on write |
| summary | string | Yes (default: "") | One-line, concise | Required for pyramid retrieval Stage 1 |
| confidence | Confidence enum | No (default: medium) | One of: high, medium, low | Observation-driven promotion |
| links | list[str] | No (default: []) | Valid relative paths within repo | Explicit connections (A-MEM) |
| supersedes | string | No | Valid relative path to predecessor note | Memory evolution tracking |
| project | string | No | Project identifier | Scopes note to project context (Tier 2) |
| agent | string | No (default: "all") | Agent identifier or "all" | Agent-specific memory filtering |
| machine | string | No | Hostname string | Machine-specific memory |
| date | date | No | ISO 8601 date (YYYY-MM-DD) | For journal entries: when the event occurred |
| caused_by | string | No | Valid relative path | Causal metadata upstream |
| causes | list[str] | No (default: []) | Valid relative paths | Causal metadata downstream |
| observation_count | int | No (default: 0) | >= 0 | Times this fact independently observed |
| first_observed | date | No | ISO 8601 date | When first encountered |
| last_observed | date | No | ISO 8601 date | When last independently confirmed |
| importance | float | No (default: 0.5) | 0.0 to 1.0 inclusive | Salience score for forgetting policy |
| access_count | int | No (default: 0) | >= 0 | Retrieval count (not admin reads) |

### E-003: LinkGraph

Auto-generated `.links/graph.yaml` mapping note relationships.

| Field | Type | Required | Constraints | Notes |
| ------- | ------ | ---------- | ------------- | ------- |
| nodes | dict[str, NodeEntry] | Yes | Keyed by relative note path | Top-level structure |
| nodes[path].outgoing | list[str] | Yes (default: []) | Valid relative paths | Notes this note links to |
| nodes[path].incoming | list[str] | Yes (default: []) | Valid relative paths | Notes that link to this note |
| nodes[path].causal_upstream | list[str] | No (default: []) | Valid relative paths | caused_by references |
| nodes[path].tags | list[str] | Yes (default: []) | Aggregated from note | For link-based search augmentation |

### E-004: AimemConfig

`.aimem.yaml` configuration file at repository root.

| Field | Type | Required | Constraints | Notes |
| ------- | ------ | ---------- | ------------- | ------- |
| memory_dir | Path | No (default: ~/.ai-memory) | Valid directory path | Override via CLI --memory-dir or AIMEM_DIR |
| context_budget | ContextBudget | No (defaults apply) | All values positive integers | Token allocation per tier |
| context_budget.total_max_tokens | int | No (default: 5000) | > 0 | Hard ceiling for context injection |
| context_budget.tier1_identity | int | No (default: 500) | > 0 | Identity note budget |
| context_budget.tier2_project | int | No (default: 1500) | > 0 | Project context budget |
| context_budget.tier3_retrieval | int | No (default: 3000) | > 0 | On-demand retrieval budget |
| context_budget.retrieval_window | int | No (default: 5) | > 0 | Max results per search (security) |
| consolidation | ConsolidationConfig | No (defaults apply) | See subfields | Hot buffer settings |
| consolidation.probation_hours | int | No (default: 24) | > 0 | Hours before promotion eligible |
| consolidation.probation_sessions | int | No (default: 3) | > 0 | Sessions before promotion eligible |
| consolidation.dedup_jaccard_threshold | float | No (default: 0.8) | 0.0 to 1.0 | Jaccard threshold for dedup trigger |
| consolidation.dedup_semantic_threshold | float | No (default: 0.9) | 0.0 to 1.0 | Semantic threshold for reject |
| consolidation.merge_semantic_threshold | float | No (default: 0.7) | 0.0 to 1.0 | Semantic threshold for merge |
| forgetting | ForgettingConfig | No (defaults apply) | See subfields | Pruning settings |
| forgetting.prune_bottom_percent | float | No (default: 0.10) | 0.0 to 1.0 | Bottom % to soft-demote |
| forgetting.stale_months | int | No (default: 6) | > 0 | Months before stale warning |
| forgetting.archive_delete_months | int | No (default: 12) | > 0 | Months in archive before hard delete |
| adapters | dict[str, AdapterConfig] | No (default: {}) | Keyed by agent name | Per-agent export configuration |

### E-005: HotBufferEntry

Staged note in `.hot/` directory awaiting probation before promotion.

| Field | Type | Required | Constraints | Notes |
| ------- | ------ | ---------- | ------------- | ------- |
| note | Note (E-001) | Yes | Valid Note instance | The staged memory note |
| staged_at | datetime | Yes | ISO 8601 with timezone | When the note entered hot buffer |
| session_count | int | Yes (default: 0) | >= 0 | Sessions since staging |
| quality_checks | dict | No | Pass/fail results | Dedup, consistency, importance |

### E-006: SearchIndex

BM25 + embedding index for hybrid retrieval.

| Field | Type | Required | Constraints | Notes |
| ------- | ------ | ---------- | ------------- | ------- |
| bm25_index | object | Yes | Built from all active note content + tags | Sparse retrieval component |
| embedding_index | object | Yes | Built from note summaries + bodies | Dense retrieval component |
| last_built | datetime | Yes | ISO 8601 | For stale index detection in doctor |
| note_count | int | Yes | >= 0 | Number of indexed notes |

## Data Ownership & Integration Sources

| Entity ID | Entity Name | Source of Truth | Integration | Related ReqIDs |
| ----------- | ------------- | ---------------- | ------------- | ---------------- |
| E-001 | Note | Git repository (filesystem + git history) | INT-001 (Git) | R-002, R-003, R-004, R-005 |
| E-002 | NoteMeta | YAML frontmatter in E-001 files | None (embedded in E-001) | R-004 |
| E-003 | LinkGraph | Auto-generated from E-001 links fields | None (derived) | R-014 |
| E-004 | AimemConfig | .aimem.yaml in repo root | INT-001 (Git) | R-024 |
| E-005 | HotBufferEntry | .hot/ directory (gitignored) | None (local only) | R-017 |
| E-006 | SearchIndex | Built from E-001 corpus | INT-003 (Embedding Model) | R-011, R-012 |

## Privacy & Retention

| Policy | Details | Related ReqIDs |
| -------- | --------- | ---------------- |
| Secrets exclusion | `.machine/`, `*.secret.md`, `journal/private/`, `.env` are gitignored and never committed | R-001, R-005 |
| Git history retention | All committed data retained permanently in git history; soft-deleted notes preserved in .archive/ | R-002, R-005 |
| Hot buffer retention | Transient; .hot/ is gitignored and entries are either promoted or discarded | R-017 |
| Archive retention | Archived notes retained for `archive_delete_months` (default 12) before hard deletion | R-018 |
| Machine-local data | `.machine/<hostname>/` contains machine-specific overrides and secrets; never shared | R-001 |
| JSONL log retention | Structured logs stored locally; retention managed by user/OS log rotation | R-027 |
| Note content privacy | All data stored locally; sharing only via explicit git remote configuration | R-005 |
