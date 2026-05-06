# Scenario Inventory

Spec-Version: 20260419-1400
Source: req-clarifier

---

## WF-001: Repository Setup

Related requirements: R-001, R-024, R-025

### Happy Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-001-R-001-HP | R-001 | User runs `aimem init` on a fresh system; repository is created at ~/.ai-memory/ with all directories, .gitignore, .aimem.yaml, and initial git commit. |
| SCN-WF-001-R-024-HP | R-024 | User edits .aimem.yaml to customize token budgets and adapter paths; config loads correctly on next command. |
| SCN-WF-001-R-025-HP | R-025 | User runs `aimem import claude ~/.claude/CLAUDE.md`; existing Markdown sections are parsed into typed memory notes. |

### Negative Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-001-R-001-NEG-01 | R-001 | User runs `aimem init` when repository already exists; CLI exits with error message, no modifications made. |
| SCN-WF-001-R-024-NEG-01 | R-024 | User provides malformed YAML in .aimem.yaml; config loader reports parse error and falls back to defaults. |
| SCN-WF-001-R-025-NEG-01 | R-025 | User imports a CLAUDE.md that contains sections duplicating existing notes; dedup pipeline flags them without overwriting. |

### Empty State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-001-R-001-EMPTY | R-001 | Fresh system with no ~/.ai-memory/; `aimem init` creates everything from scratch. |

### Failure State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-001-R-001-FAIL-01 | R-001 | Filesystem is read-only or path is inaccessible; `aimem init` fails with clear error message, no partial state left. |
| SCN-WF-001-R-001-FAIL-02 | R-001 | Git is not installed on the system; `aimem init` detects missing git and reports actionable error. |

---

## WF-002: Note Lifecycle

Related requirements: R-002, R-003, R-004, R-005, R-006, R-015, R-016, R-017, R-018, R-019

### Happy Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-002-R-002-HP | R-002 | User creates a note with `aimem add knowledge "Python Tips" --tags python --summary "Python best practices"`; note saved and committed. |
| SCN-WF-002-R-004-HP | R-004 | User creates a note with all optional frontmatter fields; all fields are persisted and readable via `aimem get`. |
| SCN-WF-002-R-015-HP | R-015 | User adds a note that passes filter, canonicalize, and dedup stages; note is accepted into hot buffer. |
| SCN-WF-002-R-017-HP | R-017 | User runs `aimem consolidate` after probation period; qualifying hot buffer notes are promoted to permanent storage with git commit. |
| SCN-WF-002-R-019-HP | R-019 | User runs `aimem evolve knowledge/old-note.md`; successor note created with supersedes field pointing to original. |

### Negative Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-002-R-002-NEG-01 | R-002 | User tries `aimem get nonexistent/path.md`; CLI reports "Note not found" and exits with non-zero code. |
| SCN-WF-002-R-004-NEG-01 | R-004 | User creates a note with importance=1.5 (out of range); Pydantic validation rejects with clear error. |
| SCN-WF-002-R-006-NEG-01 | R-006 | `aimem validate` finds notes with malformed YAML; each is reported as an error with file path. |
| SCN-WF-002-R-015-NEG-01 | R-015 | User adds a note containing "ignore previous instructions"; write-path filter rejects it with reason. |
| SCN-WF-002-R-016-NEG-01 | R-016 | User adds a note that is a near-duplicate (Jaccard > 0.8, semantic > 0.9); note is rejected with message identifying the existing duplicate. |

### Empty State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-002-R-002-EMPTY | R-002 | `aimem list` on an empty repository returns "No notes found." |

### Failure State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-002-R-005-FAIL-01 | R-005 | Git commit fails during `aimem add --commit`; note file is cleaned up, no partial state remains (atomic write). |
| SCN-WF-002-R-017-FAIL-01 | R-017 | Hot buffer note fails quality checks during consolidation; note is logged with rejection reason and discarded from .hot/. |

---

## WF-003: Context Injection

Related requirements: R-011, R-012, R-013, R-020, R-021

### Happy Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-003-R-011-HP | R-011 | Agent calls memory_search("python formatting"); hybrid search returns top-5 relevant notes ranked by BM25+embedding score. |
| SCN-WF-003-R-012-HP | R-012 | Pyramid retrieval returns summaries first (Stage 1), expands top results to full content (Stage 2), follows links (Stage 3), all within token budgets. |
| SCN-WF-003-R-013-HP | R-013 | Agent activates in project context; Tier 1 identity notes + Tier 2 project notes + Tier 3 search results injected within total 5000 token budget. |

### Negative Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-003-R-011-NEG-01 | R-011 | Agent searches with empty query string; search returns "No matching notes found" without error. |
| SCN-WF-003-R-020-NEG-01 | R-020 | A retrieved note contains injection patterns; pre-retrieval filter removes it from results before returning to agent. |
| SCN-WF-003-R-021-NEG-01 | R-021 | Search matches 50 notes but retrieval window is 5; only top 5 are returned. |

### Empty State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-003-R-011-EMPTY | R-011 | Search query has no matches in an empty or sparse repository; returns "No matching notes found." |

### Failure State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-003-R-011-FAIL-01 | R-011 | Embedding model is unavailable; search falls back to BM25-only with degraded ranking quality (graceful degradation). |

---

## WF-004: Export & Sync

Related requirements: R-007, R-008, R-005, R-026

### Happy Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-004-R-007-HP | R-007 | User runs `aimem export claude`; CLAUDE.md generated at configured path with filtered notes and auto-generation comment. |
| SCN-WF-004-R-008-HP | R-008 | User runs `aimem export copilot`; copilot-instructions.md generated with appropriate note selection. |
| SCN-WF-004-R-005-HP | R-005 | User runs `aimem sync`; local changes pushed to remote, remote changes rebased locally. |

### Negative Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-004-R-007-NEG-01 | R-007 | Export include patterns match no notes; generated file contains only the header comment and no content sections. |
| SCN-WF-004-R-005-NEG-01 | R-005 | `aimem sync` encounters a rebase conflict; sync reports failure with actionable message (resolve conflicts manually). |

### Empty State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-004-R-007-EMPTY | R-007 | Repository has no notes matching export patterns; export produces a minimal file with only the auto-generation header. |

### Failure State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-004-R-005-FAIL-01 | R-005 | No git remote configured; `aimem sync` reports "No remote configured" error. |
| SCN-WF-004-R-005-FAIL-02 | R-005 | Network is unavailable during sync; `aimem sync` reports network error without corrupting local state. |

---

## WF-005: Memory Maintenance

Related requirements: R-014, R-018, R-023, R-016, R-006

### Happy Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-005-R-023-HP | R-023 | User runs `aimem doctor`; comprehensive report shows broken links, stale notes, missing summaries, duplicates, stale index warnings. |
| SCN-WF-005-R-018-HP | R-018 | User runs `aimem prune`; bottom 10% of scored notes moved to .archive/ with git commit. Identity notes and linked notes are preserved. |
| SCN-WF-005-R-014-HP | R-014 | User runs `aimem graph`; .links/graph.yaml rebuilt with all outgoing, incoming, and causal links. |
| SCN-WF-005-R-016-HP | R-016 | User runs `aimem dedup --dry-run`; report shows potential duplicates with Jaccard and semantic scores without modifying notes. |

### Negative Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-005-R-018-NEG-01 | R-018 | `aimem prune` attempts to prune an identity note; operation skips it with log message explaining identity notes are never pruned. |
| SCN-WF-005-R-018-NEG-02 | R-018 | `aimem prune` attempts to prune a note with active incoming links; operation skips it with log message. |

### Empty State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-005-R-023-EMPTY | R-023 | `aimem doctor` on a healthy repository with no issues; reports "No issues found" with exit code 0. |

### Failure State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-005-R-014-FAIL-01 | R-014 | `aimem graph` encounters a note with links to files outside the repository; logs a warning, skips the invalid link, continues processing. |

---

## WF-006: Team Sharing

Related requirements: R-005, R-022

### Happy Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-006-R-005-HP | R-005 | Team lead merges a contributor's PR adding new knowledge notes; notes appear in team repo after merge. |
| SCN-WF-006-R-022-HP | R-022 | All commits in team repo are GPG-signed; `aimem doctor` confirms provenance chain. |

### Negative Path

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-006-R-022-NEG-01 | R-022 | Contributor pushes an unsigned commit; `aimem doctor` flags it as a provenance warning. |

### Empty State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-006-R-005-EMPTY | R-005 | Fresh team repo with only the initial commit; contributors can fork and start adding notes. |

### Failure State

| ID | ReqID | Description |
| ---- | ------- | ------------- |
| SCN-WF-006-R-005-FAIL-01 | R-005 | PR merge creates a conflict between contributor's note and existing note; git merge conflict reported, team lead resolves manually. |
