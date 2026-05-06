# Acceptance Criteria

Spec-Version: 20260419-1400
Source: req-clarifier

## TestLevel Legend

| Tag | Meaning | When to Use |
|-----|---------|-------------|
| `[Unit]` | Unit test | Pure logic, no external dependencies |
| `[Integration]` | Integration test | Database, API, external service interaction |
| `[E2E]` | End-to-end test | Full user flow through UI |
| `[Manual]` | Manual verification | Visual, UX, or exploratory testing |

## R-001: Repository Initialization

- [ ] AC-R-001-01: `aimem init` creates `~/.ai-memory/` with `.git/` directory when no repository exists [Integration]
- [ ] AC-R-001-02: `aimem init` creates all standard subdirectories: identity/, knowledge/ (with languages/, frameworks/, tools/, domains/, projects/), procedures/ (with workflows/, commands/, patterns/, troubleshooting/), journal/ (with sessions/, decisions/, incidents/, learnings/), .links/, .archive/, .hot/, .machine/ [Integration]
- [ ] AC-R-001-03: `aimem init` writes default `.aimem.yaml` configuration file [Integration]
- [ ] AC-R-001-04: `aimem init` writes `.gitignore` excluding .machine/, *.secret.md, journal/private/, .env, .hot/ [Integration]
- [ ] AC-R-001-05: `aimem init` makes an initial git commit with message "Initialize aimem memory repository" [Integration]
- [ ] AC-R-001-06: `aimem init` on an existing repository exits with error and does not modify the repo [E2E]
- [ ] AC-R-001-07: `aimem init --memory-dir /custom/path` creates the repository at the specified path [Integration]

## R-002: Note CRUD Operations

- [ ] AC-R-002-01: `aimem add identity "Title" --body "content" --tags tag1,tag2 --summary "summary"` creates a file at identity/title.md with valid YAML frontmatter and Markdown body [Integration]
- [ ] AC-R-002-02: `aimem get identity/title.md` returns the note title, metadata, and body content [Integration]
- [ ] AC-R-002-03: `aimem list` returns all notes across all memory types with path, type, and tags [Integration]
- [ ] AC-R-002-04: `aimem list --type knowledge` returns only knowledge-type notes [Integration]
- [ ] AC-R-002-05: `aimem remove identity/title.md` moves the note to .archive/identity/title.md [Integration]
- [ ] AC-R-002-06: Note title is slugified for the filename (spaces to hyphens, lowercase, no special chars) [Unit]

## R-003: Memory Type System

- [ ] AC-R-003-01: MemoryType enum contains exactly four values: identity, knowledge, procedure, journal [Unit]
- [ ] AC-R-003-02: Each memory type maps to its correct directory (identity -> identity/, knowledge -> knowledge/, procedure -> procedures/, journal -> journal/) [Unit]
- [ ] AC-R-003-03: Type-specific forgetting weights are applied correctly: identity (alpha=0.0, gamma=0.9), journal (alpha=0.6, gamma=0.3), knowledge/procedure intermediate [Unit]

## R-004: YAML Frontmatter Schema

- [ ] AC-R-004-01: NoteMeta Pydantic model validates all required fields: type (MemoryType enum), tags (list[str]), updated (date), summary (str) [Unit]
- [ ] AC-R-004-02: NoteMeta accepts all optional fields: confidence, links, supersedes, project, agent, machine, date, caused_by, causes, observation_count, first_observed, last_observed, importance, access_count [Unit]
- [ ] AC-R-004-03: importance field is constrained to 0.0-1.0 range; values outside raise ValidationError [Unit]
- [ ] AC-R-004-04: Note.from_file() correctly parses a YAML frontmatter + Markdown file and populates all fields [Unit]
- [ ] AC-R-004-05: Note.save() writes valid YAML frontmatter + Markdown that round-trips through Note.from_file() [Unit]

## R-005: Git Integration

- [ ] AC-R-005-01: `aimem add` with --commit (default) creates a git commit with message "Add {type}: {title}" [Integration]
- [ ] AC-R-005-02: `aimem remove` with --commit (default) creates a git commit recording the archive action [Integration]
- [ ] AC-R-005-03: `aimem sync` runs `git pull --rebase` then `git push` and reports success or failure [Integration]
- [ ] AC-R-005-04: If a git commit fails (e.g., nothing to commit), the operation reports the error without corrupting state [Integration]
- [ ] AC-R-005-05: All note writes are atomic: either fully committed to git or rolled back with no partial file state [Integration]

## R-006: Frontmatter Validation

- [ ] AC-R-006-01: `aimem validate` reports notes missing the summary field as warnings [Integration]
- [ ] AC-R-006-02: `aimem validate` reports notes with no tags as warnings [Integration]
- [ ] AC-R-006-03: `aimem validate` returns a count of validated notes and errors [Integration]
- [ ] AC-R-006-04: Notes with invalid YAML frontmatter (malformed YAML, wrong types) are reported as errors [Unit]

## R-007: Agent Export - Claude

- [ ] AC-R-007-01: `aimem export claude` generates a Markdown file at the configured output path (default ~/.claude/CLAUDE.md) [Integration]
- [ ] AC-R-007-02: Generated CLAUDE.md contains only notes matching the configured include patterns [Integration]
- [ ] AC-R-007-03: Generated file includes an auto-generation warning comment [Unit]

## R-008: Agent Export - Copilot

- [ ] AC-R-008-01: `aimem export copilot` generates `.github/copilot-instructions.md` at the configured output path [Integration]
- [ ] AC-R-008-02: Generated file contains only notes matching configured include patterns for Copilot [Integration]
- [ ] AC-R-008-03: Generated file respects the configured max_tokens budget [Unit]

## R-009: CLI Interface

- [ ] AC-R-009-01: `aimem --help` shows all available subcommands grouped by category (core, export, lifecycle, health) [E2E]
- [ ] AC-R-009-02: `--memory-dir /path` overrides the default repository location for all commands [E2E]
- [ ] AC-R-009-03: `AIMEM_DIR` environment variable is accepted as an alternative to --memory-dir [E2E]
- [ ] AC-R-009-04: `--verbose` flag enables DEBUG-level logging output [E2E]
- [ ] AC-R-009-05: All commands exit with code 0 on success and non-zero on error [Unit]

## R-010: MCP Server

- [ ] AC-R-010-01: MCP server starts and registers all 11 tools with correct names and schemas [Integration]
- [ ] AC-R-010-02: memory_search tool returns results within the configured retrieval window limit [Integration]
- [ ] AC-R-010-03: memory_add tool creates a note and returns the relative path [Integration]
- [ ] AC-R-010-04: MCP server shares the same core library as CLI (no duplicated business logic) [Unit]

## R-011: Hybrid Search

- [ ] AC-R-011-01: `aimem search "query"` returns notes ranked by combined BM25 + embedding scores [Integration]
- [ ] AC-R-011-02: Results are capped at the retrieval_window setting (default 5) [Unit]
- [ ] AC-R-011-03: Set-union merging combines BM25 and embedding result sets before ranking [Unit]
- [ ] AC-R-011-04: Search handles queries with no results gracefully, returning "No matching notes found" [Unit]

## R-012: Pyramid Retrieval

- [ ] AC-R-012-01: Stage 1 returns summaries only, within tier3_stage1_summaries token budget [Unit]
- [ ] AC-R-012-02: Stage 2 expands top-K summaries to full content, within tier3_stage2_expansion budget [Unit]
- [ ] AC-R-012-03: Stage 3 follows outgoing links with 0.5^hop distance decay, within tier3_stage3_links budget [Unit]
- [ ] AC-R-012-04: Rejection rule discards results where NOT keyword_match AND vector_max < 0.50 [Unit]

## R-013: Tiered Context Injection

- [ ] AC-R-013-01: Tier 1 always includes identity/ notes within the tier1_identity token budget [Unit]
- [ ] AC-R-013-02: Tier 2 includes project-scoped notes when a project is detected [Unit]
- [ ] AC-R-013-03: Total context does not exceed total_max_tokens (default 5000) [Unit]

## R-014: Link System

- [ ] AC-R-014-01: `aimem link src.md dst.md` adds dst.md to the links field of src.md frontmatter [Integration]
- [ ] AC-R-014-02: `aimem graph` regenerates .links/graph.yaml with outgoing, incoming, causal_upstream entries and aggregated tags [Integration]
- [ ] AC-R-014-03: Causal links (caused_by, causes) are tracked in frontmatter and reflected in graph.yaml [Unit]

## R-015: Write-Path Pipeline

- [ ] AC-R-015-01: Filter stage rejects notes containing known injection patterns (redirect, override, prompt injection markers) [Unit]
- [ ] AC-R-015-02: Canonicalize stage normalizes tag casing (lowercase) and date format (YYYY-MM-DD) [Unit]
- [ ] AC-R-015-03: Pipeline runs filter -> canonicalize -> dedup in sequence before storage [Integration]

## R-016: Ingestion Deduplication

- [ ] AC-R-016-01: Notes with tag Jaccard similarity > 0.8 AND semantic similarity > 0.9 are rejected as duplicates [Unit]
- [ ] AC-R-016-02: Notes with tag Jaccard > 0.8 AND 0.7 < semantic similarity <= 0.9 trigger merge with existing note [Unit]
- [ ] AC-R-016-03: Notes with tag Jaccard <= 0.8 are accepted regardless of semantic similarity [Unit]
- [ ] AC-R-016-04: `aimem dedup --dry-run` reports potential duplicates without modifying anything [Integration]

## R-017: Dual-Buffer Consolidation

- [ ] AC-R-017-01: `aimem add` writes new notes to .hot/ staging directory (not permanent storage) [Integration]
- [ ] AC-R-017-02: `aimem consolidate` promotes notes that have passed the probation period (default 24h or 3 sessions) to permanent storage with a git commit [Integration]
- [ ] AC-R-017-03: Notes that fail probation quality checks are logged with reason and discarded [Integration]

## R-018: Forgetting Policy

- [ ] AC-R-018-01: Forgetting score I(m,t) is computed correctly using the ABF formula with type-specific weights [Unit]
- [ ] AC-R-018-02: `aimem prune --dry-run` lists notes below threshold without modifying anything [Integration]
- [ ] AC-R-018-03: `aimem prune` moves bottom 10% of scored notes to .archive/ [Integration]
- [ ] AC-R-018-04: Identity notes are never pruned regardless of score [Unit]
- [ ] AC-R-018-05: Notes with active incoming links from non-archived notes are never pruned [Unit]

## R-019: Memory Evolution

- [ ] AC-R-019-01: `aimem evolve path/note.md` creates a successor note with `supersedes: path/note.md` in frontmatter [Integration]
- [ ] AC-R-019-02: `aimem doctor` detects contradictory notes (conflicting facts in same domain) and reports them [Integration]
- [ ] AC-R-019-03: Observation count increments when a fact is independently confirmed, and notes with observation_count > 5 are promoted to confidence: high [Unit]

## R-020: Security - Injection Pattern Filtering

- [ ] AC-R-020-01: Pre-storage filter rejects notes containing "ignore previous", "override", "System:", or redirect instructions [Unit]
- [ ] AC-R-020-02: Pre-retrieval filter scans results for injection patterns before returning to agent [Unit]
- [ ] AC-R-020-03: Blocked patterns are configurable in .aimem.yaml [Unit]

## R-021: Security - Retrieval Window Limits

- [ ] AC-R-021-01: Default retrieval_window is 5 in AimemConfig [Unit]
- [ ] AC-R-021-02: Search results never exceed the configured retrieval_window regardless of matches [Unit]
- [ ] AC-R-021-03: retrieval_window is configurable in .aimem.yaml context_budget section [Unit]

## R-022: Security - Git Provenance

- [ ] AC-R-022-01: `aimem doctor` detects and reports unsigned commits in the repository [Integration]
- [ ] AC-R-022-02: Configuration option exists to require GPG/SSH-signed commits [Unit]
- [ ] AC-R-022-03: Commit author is deterministic and verifiable via git blame [Integration]

## R-023: Health Check - Doctor

- [ ] AC-R-023-01: `aimem doctor` reports broken links (links pointing to non-existent files) [Integration]
- [ ] AC-R-023-02: `aimem doctor` reports stale notes (no access in configurable stale_months, default 6) [Integration]
- [ ] AC-R-023-03: `aimem doctor` reports notes missing the summary field [Integration]
- [ ] AC-R-023-04: `aimem doctor` reports stale index warnings when search index is outdated [Integration]
- [ ] AC-R-023-05: `aimem doctor` exit code is 0 when healthy, non-zero when issues found [E2E]

## R-024: Configuration System

- [ ] AC-R-024-01: AimemConfig.load() reads .aimem.yaml and returns a validated Pydantic model with all sections (context_budget, consolidation, forgetting, adapters) [Unit]
- [ ] AC-R-024-02: Missing .aimem.yaml returns sensible defaults (total_max_tokens=5000, retrieval_window=5, etc.) [Unit]
- [ ] AC-R-024-03: AimemConfig.save() writes valid YAML that round-trips through AimemConfig.load() [Unit]

## R-025: Import from Existing Configs

- [ ] AC-R-025-01: `aimem import claude ~/.claude/CLAUDE.md` parses Markdown sections and creates corresponding memory notes with correct types [Integration]
- [ ] AC-R-025-02: `aimem import copilot .github/copilot-instructions.md` creates notes from the instructions file [Integration]
- [ ] AC-R-025-03: Import does not overwrite existing notes; duplicates are flagged via the dedup pipeline [Integration]

## R-026: Internationalized CLI

- [ ] AC-R-026-01: All user-facing CLI messages are sourced from message catalogs (not hardcoded strings) [Unit]
- [ ] AC-R-026-02: Note content with non-ASCII characters (CJK, Cyrillic, emoji, etc.) is stored and retrieved correctly via UTF-8 encoding [Integration]
- [ ] AC-R-026-03: At least English locale is fully supported at launch [E2E]

## R-027: Structured Logging

- [ ] AC-R-027-01: Log output is JSONL formatted when not in verbose/debug mode [Unit]
- [ ] AC-R-027-02: --verbose flag switches to human-readable format with timestamps [E2E]
- [ ] AC-R-027-03: AIMEM_LOG_LEVEL environment variable controls logging verbosity (DEBUG, INFO, WARNING, ERROR) [Unit]
