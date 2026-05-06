# Requirements Registry

Spec-Version: 20260419-1400
Source: req-clarifier

## Status Legend

| Status | Meaning |
|--------|---------|
| `Proposed` | Initial capture, not yet validated |
| `Active` | Confirmed in-scope for this release |
| `Deferred` | Confirmed but postponed to future release |
| `Dropped` | Explicitly removed (reason required) |

## Must-Have Requirements

| ReqID | Title | Description | Value/Rationale | Dependencies | Status |
|-------|-------|-------------|-----------------|--------------|--------|
| R-001 | Repository Initialization | `aimem init` creates a git-backed memory repository at a configurable path (default `~/.ai-memory/`) with the standard directory structure (identity/, knowledge/, procedures/, journal/, .hot/, .archive/, .machine/, .links/) and default `.aimem.yaml` config. | Provides the foundational storage layer; nothing works without an initialized repo. | None | Active |
| R-002 | Note CRUD Operations | Users can create (`aimem add`), read (`aimem get`), update (`aimem update`), list (`aimem list`), and soft-delete (`aimem remove`) memory notes. Notes use YAML frontmatter + Markdown body format. | Core data management capability; the fundamental interaction model. | R-001 | Active |
| R-003 | Memory Type System | Notes are classified into four types: identity, knowledge, procedure, journal. Each type maps to a directory and has type-specific behavior for tiering, forgetting policy weights, and context injection. | Differentiates memory by usage pattern (MIRIX-inspired), enabling type-aware retrieval and lifecycle management. | R-002 | Active |
| R-004 | YAML Frontmatter Schema | Every note has required fields (type, tags, updated, summary) and optional fields (confidence, links, supersedes, project, agent, machine, date, caused_by, causes, observation_count, first_observed, last_observed, importance, access_count). Validated by Pydantic models. | Structured metadata enables hybrid retrieval, pyramid expansion, forgetting policy scoring, and provenance tracking. | R-002 | Active |
| R-005 | Git Integration | All note writes are atomic git commits. Support for `aimem sync` (pull --rebase + push), GPG/SSH-signed commits, branch-based experimentation, and meaningful commit messages. All writes either fully commit or roll back. | Version history, sharing, provenance, and atomic data integrity. | R-001 | Active |
| R-006 | Frontmatter Validation | `aimem validate` checks all notes for valid frontmatter schema, required fields, and structural integrity. Pre-commit hook validates on every commit. | Prevents data corruption and ensures all notes are machine-parseable. | R-004 | Active |
| R-007 | Agent Export - Claude | `aimem export claude` generates a CLAUDE.md file from memory notes, filtered by configurable include patterns and respecting a token budget. | Enables Claude Code to consume structured memory without manual curation. | R-002, R-003 | Active |
| R-008 | Agent Export - Copilot | `aimem export copilot` generates `.github/copilot-instructions.md` from memory notes. | Extends memory system to GitHub Copilot users. | R-002, R-003 | Active |
| R-009 | CLI Interface | Click-based CLI with subcommands for all core, export, lifecycle, and health operations. Supports `--memory-dir` and `AIMEM_DIR` env var for repository path. Supports `--verbose` for debug logging. | Primary user interface for memory management. | R-001, R-002 | Active |
| R-010 | MCP Server | FastMCP-based server exposing 11 tools (memory_search, memory_get, memory_add, memory_update, memory_remove, memory_list, memory_link, memory_status, memory_export, memory_consolidate, memory_doctor) and 3 resources (memory://identity, memory://project/{name}, memory://search/{query}). Shares core library with CLI. | Enables direct agent integration without shell execution. | R-001, R-002 | Active |
| R-011 | Hybrid Search | `aimem search` performs BM25 + embedding search with set-union merging (OMNIMEM). Returns results within configurable retrieval window (default 5). | Accurate retrieval is the primary value proposition of the memory system. | R-002, R-004 | Active |
| R-012 | Pyramid Retrieval | Three-stage retrieval: Stage 1 scans summaries, Stage 2 expands top-K to full content, Stage 3 traverses links with distance decay. Respects per-tier token budgets from `.aimem.yaml`. | Maximizes retrieval accuracy within token constraints (OMNIMEM-inspired, Memori-validated). | R-011, R-004 | Active |
| R-013 | Tiered Context Injection | Three tiers: Tier 1 (identity/, always loaded, ~500 tokens), Tier 2 (project context, ~1500 tokens), Tier 3 (on-demand retrieval, ~3000 tokens). Configurable budgets. | Prevents context overflow while ensuring relevant memories are always available. | R-003, R-012 | Active |
| R-014 | Link System | Notes declare explicit connections via `links:` frontmatter. `aimem link` creates/removes links. `aimem graph` rebuilds `.links/graph.yaml` index. Support for causal links (caused_by, causes). | Enables knowledge graph traversal and contextual retrieval (A-MEM inspired). | R-004 | Active |
| R-015 | Write-Path Pipeline | Every memory write passes through: filter (reject noise/injection patterns) -> canonicalize (normalize tags, dates, format) -> dedup check (Jaccard + semantic). | Ensures data quality at ingestion time (Memory Survey + OMNIMEM). | R-002, R-004 | Active |
| R-016 | Ingestion Deduplication | Two-stage dedup: tag-based Jaccard similarity, then semantic comparison for high-overlap pairs. Actions: reject (true duplicate), merge (extend existing), accept (sufficiently different). Thresholds configurable. | Prevents knowledge fragmentation and note sprawl. | R-015 | Active |
| R-017 | Dual-Buffer Consolidation | New notes enter `.hot/` staging with configurable probation (default 24h or 3 sessions). `aimem consolidate` promotes qualified notes to permanent storage with git commit. | Prevents low-quality or ephemeral notes from polluting long-term memory. | R-015, R-005 | Active |
| R-018 | Forgetting Policy | Type-aware scoring using ABF formula: I(m,t) = alpha*R + beta*F + gamma*S with type-specific weights. `aimem prune` soft-demotes bottom 10% to `.archive/`. Never deletes identity/ notes or notes with active incoming links. | Prevents unbounded memory growth; keeps relevant notes surfaced. | R-003, R-004 | Active |
| R-019 | Memory Evolution | Support for `aimem evolve` (supersedes field), consolidation triggers (3+ journal entries on same topic -> knowledge note), confidence changes, observation counting. `aimem doctor` detects contradictions. | Memories must refine over time, not just accumulate (A-MEM principle). | R-002, R-014 | Active |
| R-020 | Security - Injection Pattern Filtering | Pre-retrieval and pre-storage scan for known injection patterns: redirect instructions, behavioral overrides, prompt injection markers. | First line of defense against memory poisoning (Memory Poisoning paper). | R-015 | Active |
| R-021 | Security - Retrieval Window Limits | Default retrieval window of 5 results (configurable). Smaller windows reduce probability of surfacing poisoned entries (ASR 6% at 5 vs 38% at 10). | Limits attack surface for memory poisoning. | R-011 | Active |
| R-022 | Security - Git Provenance | Require GPG/SSH-signed commits. Track commit author in metadata. PR reviews for team repos. Git blame provides audit trail. | Establishes trust chain for shared memory repositories. | R-005 | Active |
| R-023 | Health Check - Doctor | `aimem doctor` performs comprehensive health check: broken links, stale notes (6 months), duplicates, orphans, contradictions, missing summaries, budget check, confidence audit, forgetting score report, injection scan, unsigned commit detection, stale index warnings. | Ongoing maintenance and data integrity verification. | R-014, R-018, R-020 | Active |
| R-024 | Configuration System | `.aimem.yaml` in repo root configures: context budgets, adapter settings, consolidation thresholds, forgetting parameters. Loaded by Pydantic model with sensible defaults. | Enables user customization without code changes. | R-001 | Active |
| R-025 | Import from Existing Configs | `aimem import claude <path>` parses existing CLAUDE.md and creates structured notes. `aimem import copilot <path>` for copilot-instructions.md. | Migration path from current agent-specific configs to unified memory. | R-002, R-003 | Active |
| R-026 | Internationalized CLI | CLI messages use i18n message catalogs for user-facing strings. Note content supports any language/charset (UTF-8). | Enables non-English-speaking developers to use the tool natively. | R-009 | Active |
| R-027 | Structured Logging | JSONL structured logging using Python logging module with JSON formatter. Configurable verbosity (--verbose flag, AIMEM_LOG_LEVEL env var). | Enables programmatic log analysis and debugging. | R-009 | Active |

## Nice-to-Have Requirements

| ReqID | Title | Description | Value/Rationale | Dependencies | Status |
|-------|-------|-------------|-----------------|--------------|--------|
| R-028 | Agent Export - Cursor | `aimem export cursor` generates `.cursorrules` or `.cursor/rules/` files. | Extends to Cursor users. | R-002, R-003 | Proposed |
| R-029 | Export Watch Mode | `aimem export --watch --all` watches for memory changes and auto-regenerates agent configs. | Reduces manual export friction. | R-007, R-008 | Proposed |
| R-030 | Terminal Screen Reader Compatibility | CLI output should be compatible with terminal screen readers (no excessive ANSI codes, proper text structure). | Accessibility for visually impaired developers. | R-009 | Proposed |
| R-031 | Auto-Linking via Embedding Similarity | Automatically suggest or create links between notes based on embedding similarity (A-MEM style). | Reduces manual linking overhead. | R-014, R-011 | Deferred |
| R-032 | Self-RAG Gating | Expose `should_retrieve` hint in MCP protocol so agents can skip retrieval when unnecessary. | Reduces unnecessary retrieval overhead. | R-010, R-011 | Deferred |
| R-033 | Causal Retrieval | Follow causal chains (caused_by/causes) during retrieval for debugging scenarios. | Better context for incident investigation. | R-014, R-012 | Deferred |

## Out-of-Scope / Won't-Have (CRITICAL for preventing scope drift)

| Item | Reason for Exclusion | Related ReqIDs | Requested By |
|------|---------------------|----------------|--------------|
| GUI / Web Interface | CLI-only tool; agents interact via MCP, humans via terminal | R-009, R-010 | Stakeholder (Round 4) |
| Cloud Service / SaaS | Local-first architecture; sharing via git remotes only | R-005 | Stakeholder (Round 4) |
| Mobile Application | Desktop/server CLI tool only | R-009 | Stakeholder (Round 4) |
| Real-Time Collaboration | Git-based async collaboration via pull/push/PR | R-005 | Stakeholder (Round 4) |
| Non-Text Memories (Images/Audio) | Text-only (YAML frontmatter + Markdown); binary assets out of scope | R-004 | Stakeholder (Round 4) |
| Cursor/Continue.dev Adapters (MVP) | Deferred to Nice-to-Have; Claude and Copilot are MVP targets | R-028 | Stakeholder (Round 4) |
| Dedicated Alerting System | `aimem doctor` surfaces issues; no push notifications or monitoring integration | R-023 | Stakeholder (Round 4) |
| LLM Self-Validation for Security | LLMs cannot reliably detect injection (54/82 malicious entries scored 1.0 trust) | R-020 | Design doc (Section 9) |

## Entity Registry Summary (Canonical Source)

> **Contract**: This section is the authoritative source for Persona, Workflow, Integration, Role, and Data Entity IDs. Downstream agents (req-analyzer) MUST source these IDs from this file. The detailed traceability mappings in `0006-traceability-skeleton.md` reference these IDs but do not define them.

### Personas

| ID | Name | Description |
|----|------|-------------|
| P-001 | Solo Developer | Individual developer using one or more AI coding agents locally. Manages personal preferences, project knowledge, and session history. Moderate-to-high technical proficiency. |
| P-002 | Team Lead | Developer who maintains shared team conventions and reviews memory contributions via PRs. High technical proficiency. Concerned with consistency and onboarding. |

### Workflows

| ID | Name | Description | Primary Persona |
|----|------|-------------|-----------------|
| WF-001 | Repository Setup | Initialize memory repo, configure adapters, set token budgets, import existing configs. | P-001 |
| WF-002 | Note Lifecycle | Create, read, update, search, soft-delete, and evolve memory notes through CLI or MCP. | P-001 |
| WF-003 | Context Injection | Agent retrieves relevant memories during a coding session via MCP or exported config files. | P-001 |
| WF-004 | Export & Sync | Export memory to agent-specific formats, sync across machines via git remote. | P-001 |
| WF-005 | Memory Maintenance | Run doctor checks, prune stale notes, deduplicate, consolidate hot buffer, rebuild link graph. | P-001 |
| WF-006 | Team Sharing | Fork team repo, contribute memories via PR, review and merge team contributions. | P-002 |

### Integrations

| ID | Name | Type | Description |
|----|------|------|-------------|
| INT-001 | Git | Local + Remote | Version control backend for storage, history, sharing, provenance, and atomic writes. |
| INT-002 | MCP Protocol | API | Model Context Protocol for direct agent-to-memory communication. |
| INT-003 | Embedding Model | Library | Local embedding model for semantic search and dedup (e.g., sentence-transformers). |

### Roles

| ID | Name | Description |
|----|------|-------------|
| ROLE-001 | Repository Owner | Full control over the memory repository: all CRUD, config, prune, doctor, sync, export. |
| ROLE-002 | Team Contributor | Can propose memory additions via PR to team repos. Cannot directly push to main or prune. |
| ROLE-003 | Agent (MCP Client) | Automated consumer: can search, read, add (to hot buffer), and list notes via MCP tools. Cannot prune, configure, or directly commit. |

### Data Entities

| ID | Name | Description | Source |
|----|------|-------------|--------|
| E-001 | Note | Atomic memory unit: YAML frontmatter metadata + Markdown body, stored as a file in the git repository. | Core domain |
| E-002 | NoteMeta | YAML frontmatter fields: type, tags, updated, summary, confidence, links, supersedes, project, agent, machine, date, caused_by, causes, observation_count, first_observed, last_observed, importance, access_count. | Core domain |
| E-003 | LinkGraph | Auto-generated `.links/graph.yaml` mapping each note to outgoing, incoming, and causal links plus aggregated tags. | Derived from E-001 |
| E-004 | AimemConfig | `.aimem.yaml` configuration: context budgets, adapter settings, consolidation thresholds, forgetting parameters. | User-defined |
| E-005 | HotBufferEntry | Staged note in `.hot/` directory awaiting probation completion before promotion to permanent storage. | Transient (derived from E-001) |
| E-006 | SearchIndex | BM25 + embedding index built from all active notes for hybrid retrieval. | Derived from E-001 |
