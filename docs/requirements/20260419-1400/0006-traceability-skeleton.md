# Traceability Skeleton

Spec-Version: 20260419-1400
Source: req-clarifier

> **Mirror**: This entity registry MUST exactly mirror the Entity Registry Summary in `0000-requirements-registry.md`.

## Entity Registry (Stable IDs)

### Personas

| ID | Name | Description |
| ---- | ------ | ------------- |
| P-001 | Solo Developer | Individual developer using one or more AI coding agents locally. Manages personal preferences, project knowledge, and session history. Moderate-to-high technical proficiency. |
| P-002 | Team Lead | Developer who maintains shared team conventions and reviews memory contributions via PRs. High technical proficiency. Concerned with consistency and onboarding. |

### Roles

| ID | Name | Description |
| ---- | ------ | ------------- |
| ROLE-001 | Repository Owner | Full control over the memory repository: all CRUD, config, prune, doctor, sync, export. |
| ROLE-002 | Team Contributor | Can propose memory additions via PR to team repos. Cannot directly push to main or prune. |
| ROLE-003 | Agent (MCP Client) | Automated consumer: can search, read, add (to hot buffer), and list notes via MCP tools. Cannot prune, configure, or directly commit. |

### Workflows

| ID | Name | Description | Primary Persona |
| ---- | ------ | ------------- | ----------------- |
| WF-001 | Repository Setup | Initialize memory repo, configure adapters, set token budgets, import existing configs. | P-001 |
| WF-002 | Note Lifecycle | Create, read, update, search, soft-delete, and evolve memory notes through CLI or MCP. | P-001 |
| WF-003 | Context Injection | Agent retrieves relevant memories during a coding session via MCP or exported config files. | P-001 |
| WF-004 | Export & Sync | Export memory to agent-specific formats, sync across machines via git remote. | P-001 |
| WF-005 | Memory Maintenance | Run doctor checks, prune stale notes, deduplicate, consolidate hot buffer, rebuild link graph. | P-001 |
| WF-006 | Team Sharing | Fork team repo, contribute memories via PR, review and merge team contributions. | P-002 |

### Integrations

| ID | Name | Type | Description |
| ---- | ------ | ------ | ------------- |
| INT-001 | Git | Local + Remote | Version control backend for storage, history, sharing, provenance, and atomic writes. |
| INT-002 | MCP Protocol | API | Model Context Protocol for direct agent-to-memory communication. |
| INT-003 | Embedding Model | Library | Local embedding model for semantic search and dedup (e.g., sentence-transformers). |

### Data Entities

| ID | Name | Description | Source |
| ---- | ------ | ------------- | -------- |
| E-001 | Note | Atomic memory unit: YAML frontmatter metadata + Markdown body, stored as a file in the git repository. | Core domain |
| E-002 | NoteMeta | YAML frontmatter fields for note metadata. | Core domain |
| E-003 | LinkGraph | Auto-generated `.links/graph.yaml` mapping note relationships. | Derived from E-001 |
| E-004 | AimemConfig | `.aimem.yaml` configuration file. | User-defined |
| E-005 | HotBufferEntry | Staged note in `.hot/` awaiting probation. | Transient (derived from E-001) |
| E-006 | SearchIndex | BM25 + embedding index for hybrid retrieval. | Derived from E-001 |

## Mapping Tables

### Requirements <-> Personas

| ReqID | P-001 (Solo Developer) | P-002 (Team Lead) |
| ------- | ------------------------ | ------------------- |
| R-001 | X | X |
| R-002 | X | X |
| R-003 | X | X |
| R-004 | X | X |
| R-005 | X | X |
| R-006 | X | X |
| R-007 | X | |
| R-008 | X | |
| R-009 | X | X |
| R-010 | X | |
| R-011 | X | X |
| R-012 | X | |
| R-013 | X | |
| R-014 | X | X |
| R-015 | X | X |
| R-016 | X | X |
| R-017 | X | |
| R-018 | X | |
| R-019 | X | X |
| R-020 | X | X |
| R-021 | X | X |
| R-022 | | X |
| R-023 | X | X |
| R-024 | X | |
| R-025 | X | |
| R-026 | X | X |
| R-027 | X | X |

### Requirements <-> Workflows

| ReqID | WF-001 (Repository Setup) | WF-002 (Note Lifecycle) | WF-003 (Context Injection) | WF-004 (Export & Sync) | WF-005 (Memory Maintenance) | WF-006 (Team Sharing) |
| ------- | -------------------------- | ------------------------ | --------------------------- | ---------------------- | --------------------------- | --------------------- |
| R-001 | X | | | | | |
| R-002 | | X | | | | |
| R-003 | | X | X | | | |
| R-004 | | X | X | | | |
| R-005 | X | X | | X | | X |
| R-006 | | X | | | X | |
| R-007 | | | | X | | |
| R-008 | | | | X | | |
| R-009 | X | X | | X | X | |
| R-010 | | X | X | | | |
| R-011 | | | X | | | |
| R-012 | | | X | | | |
| R-013 | | | X | | | |
| R-014 | | X | | | X | |
| R-015 | | X | | | | |
| R-016 | | X | | | X | |
| R-017 | | X | | | X | |
| R-018 | | | | | X | |
| R-019 | | X | | | X | |
| R-020 | | X | X | | | |
| R-021 | | | X | | | |
| R-022 | | | | | X | X |
| R-023 | | | | | X | |
| R-024 | X | | | | | |
| R-025 | X | | | | | |
| R-026 | | X | | X | X | |
| R-027 | | X | X | X | X | |

### Requirements <-> Integrations

| ReqID | INT-001 (Git) | INT-002 (MCP Protocol) | INT-003 (Embedding Model) |
| ------- | --------------- | ---------------------- | -------------------------- |
| R-001 | X | | |
| R-002 | X | | |
| R-005 | X | | |
| R-006 | X | | |
| R-010 | | X | |
| R-011 | | | X |
| R-012 | | | X |
| R-016 | | | X |
| R-017 | X | | |
| R-022 | X | | |
| R-023 | X | | |

### Requirements <-> Roles

| ReqID | ROLE-001 (Repository Owner) | ROLE-002 (Team Contributor) | ROLE-003 (Agent/MCP Client) |
| ------- | --------------------------- | --------------------------- | --------------------------- |
| R-001 | X | | |
| R-002 | X | X | X |
| R-005 | X | X | |
| R-006 | X | X | |
| R-007 | X | X | X |
| R-008 | X | X | X |
| R-009 | X | X | |
| R-010 | | | X |
| R-011 | X | X | X |
| R-014 | X | X | |
| R-016 | X | X | |
| R-017 | X | | |
| R-018 | X | | |
| R-022 | X | X | |
| R-023 | X | X | X |
| R-024 | X | | |
| R-025 | X | | |

### Requirements <-> Data Entities

| ReqID | E-001 (Note) | E-002 (NoteMeta) | E-003 (LinkGraph) | E-004 (AimemConfig) | E-005 (HotBufferEntry) | E-006 (SearchIndex) |
| ------- | ------------- | ----------------- | ------------------ | -------------------- | ----------------------- | -------------------- |
| R-001 | | | | X | | |
| R-002 | X | X | | | | |
| R-003 | X | X | | | | |
| R-004 | | X | | | | |
| R-005 | X | | | | | |
| R-006 | | X | | | | |
| R-011 | X | X | | | | X |
| R-012 | X | X | X | X | | X |
| R-013 | X | X | | X | | |
| R-014 | X | X | X | | | |
| R-015 | X | X | | | | |
| R-016 | X | X | | X | | X |
| R-017 | X | | | X | X | |
| R-018 | X | X | | X | | |
| R-019 | X | X | X | | | |
| R-020 | X | | | X | | |
| R-023 | X | X | X | | | X |
| R-024 | | | | X | | |
