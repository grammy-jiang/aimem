# User Stories — MVP (Phase 1)

Spec-Version: 20260419-1400
Source: story-generator
Document-Range: 0200-0299
MVP basis: 0199 (16 Phase-1 R-IDs)

## Story Card Format

`US-XXX` (story id) → `R-NNN` (requirement) → `AC-XXX-Y` (acceptance criteria with TestLevel).

---

## US-001 — Initialize a personal memory repository

**As** a Solo Developer (P-001)
**I want** to run `aimem init` once on my laptop
**So that** I have a git-backed personal memory store that downstream tooling can use offline.

- **Traces**: R-001, R-005, R-024, R-034 (personal layer subset for Phase 1).
- **Workflow**: WF-001.
- **AC-US001-1** (Unit): `aimem init --path ~/.ai-memory` creates the parent index repo with `.aimem.yaml` and a `personal/` submodule pointing to a fresh git repo. Exit 0.
- **AC-US001-2** (Smoke): Re-running `aimem init` on an initialized path is idempotent: no duplicate submodules, exit 0, log line `op=init result=already-initialized`.
- **AC-US001-3** (Unit): `aimem init` refuses to write outside the path passed via `--path` or `AIMEM_DIR` (HC2).

## US-002 — Add a memory note

**As** a Solo Developer
**I want** `aimem add --type preference --title "..." -- "..."`
**So that** I can persist a note with valid v1 schema in my personal layer.

- **Traces**: R-002, R-004, R-038, R-039, R-040.
- **Workflow**: WF-002.
- **AC-US002-1** (Unit): A successful add writes one Markdown file under `personal/preference/<ulid>.md` with frontmatter containing `schema_version: 1`, `id`, `layer: personal`, `type: preference`, `created_at`, `updated_at`, `sig`.
- **AC-US002-2** (Unit): Add fails with `error.kind=invariant` and exit ≠0 if frontmatter would be missing `schema_version`.
- **AC-US002-3** (E2E): A note containing a known-pattern AWS access key is rejected at write with `error.kind=invariant`; no file is created (R-040).
- **AC-US002-4** (Smoke): The `sig` field verifies under the user's local ed25519 public key.

## US-003 — Read a note by ID

**As** a Solo Developer
**I want** `aimem get <ulid>` and `aimem show <ulid>`
**So that** I can inspect a note's content and frontmatter.

- **Traces**: R-002, R-004.
- **AC-US003-1** (Unit): `aimem get` returns the body to stdout; `aimem show --json` emits structured frontmatter+body JSON.
- **AC-US003-2** (Unit): Missing id returns `error.kind=not_found` and exit 4 (per R-045 mapping).
- **AC-US003-3** (Unit): `aimem show --include-tombstones <ulid>` returns the tombstone record when the note has been forgotten (forward link to R-044).

## US-004 — List and tag notes

**As** a Solo Developer
**I want** `aimem list` and `aimem tag`
**So that** I can browse and curate my notes.

- **Traces**: R-002, R-014.
- **AC-US004-1** (Unit): `aimem list --layer personal --type preference` returns all matching notes' `(id, title, updated_at)`.
- **AC-US004-2** (Unit): `aimem tag add <ulid> stack:python` updates frontmatter and produces a new commit with op=tag.
- **AC-US004-3** (Unit): `aimem tag rm` removes the tag idempotently.

## US-005 — Search across notes (hybrid)

**As** a Solo Developer
**I want** `aimem query "git rebase preferences"`
**So that** I get the top-K most relevant notes ranked by hybrid BM25+embedding scoring.

- **Traces**: R-011, R-021, R-046.
- **AC-US005-1** (Unit): Default K=5 (R-021); `--top-k` overrides up to 50.
- **AC-US005-2** (Smoke): On the bundled LongMemEval slice, `aimem query` reports P@5 ≥ 0.7 (release-blocking, R-046).
- **AC-US005-3** (Smoke): `aimem query` p95 ≤ 150 ms on warm bench fixture (R-046, design.md §10).
- **AC-US005-4** (Unit): With embedding model unavailable, query falls back to BM25-only and emits a `level=warning op=query reason=embed_unavailable` log line.

## US-006 — Verify the store

**As** a Solo Developer
**I want** `aimem verify`
**So that** I know my schema is valid, signatures verify, and there are no orphan links.

- **Traces**: R-006, R-038, R-039.
- **AC-US006-1** (Unit): `aimem verify` exits 0 on a clean store.
- **AC-US006-2** (Unit): A record with malformed `sig` makes `aimem verify` exit ≠0 with `error.kind=auth`.
- **AC-US006-3** (Unit): A record without `schema_version` makes `aimem verify` exit ≠0 with `error.kind=invariant`.

## US-007 — MCP server exposes memory tools

**As** an AI coding agent (Claude Code / Copilot CLI / Codex CLI)
**I want** to connect to `aimem-mcp` over stdio (MCP `2025-06-18`)
**So that** I can query and add memory without invoking the shell.

- **Traces**: R-010, R-045.
- **AC-US007-1** (Smoke): Server announces protocol version `2025-06-18`; older protocol versions are rejected with `error.kind=config`.
- **AC-US007-2** (E2E): `memory_query` round-trip ≤ 200 ms p95 on warm bench (R-046).
- **AC-US007-3** (Unit): Errors emitted to MCP clients carry `error.kind` from {`config, auth, conflict, quarantine, not_found, invariant, transient`} and a boolean `retriable` flag (R-045).
- **AC-US007-4** (Smoke): `memory_query`, `memory_add`, `memory_link`, `memory_tag`, `memory_layer_list`, `memory_layer_scope`, `memory_layer_promote`, `memory_sync`, `memory_inbox` are all advertised in `tools/list`.

## US-008 — Structured logs

**As** a Solo Developer (or operator)
**I want** all aimem operations to emit structured JSONL logs
**So that** I can debug or audit without parsing free text.

- **Traces**: R-027.
- **AC-US008-1** (Unit): Every log line has fields `ts, level, op, layer, record_id, latency_ms, agent, session, error.code, error.kind` (some may be empty strings).
- **AC-US008-2** (Unit): No log message contains note body content (redaction invariant; R-027).
- **AC-US008-3** (Smoke): Logs land at `.agent/logs/aimem.jsonl`, daily-rotated; the file is in `.gitignore`.

## US-009 — Stable error taxonomy

**As** an MCP client author
**I want** errors to expose one of a fixed set of `error.kind` values
**So that** I can build retry / backoff / surface-to-user logic without parsing strings.

- **Traces**: R-045.
- **AC-US009-1** (Unit): Each MCP error response includes `error.kind` ∈ {config, auth, conflict, quarantine, not_found, invariant, transient}.
- **AC-US009-2** (Unit): `retriable` flag matches the table in design.md §11.

## US-010 — Schema migration framework

**As** a maintainer
**I want** `aimem migrate` and CI dry-run support
**So that** schema upgrades never silently drop data.

- **Traces**: R-038.
- **AC-US010-1** (Unit): `aimem migrate --dry-run` reports counts of records that would change, without writing.
- **AC-US010-2** (Smoke): CI fails a PR if a migrator would silently downgrade `schema_version`.
- **AC-US010-3** (Unit): `aimem migrate` is gated on author key; non-author keys exit with `error.kind=auth`.

## US-011 — Write-gate rejects red-class data

**As** a Solo Developer
**I want** `aimem add` to reject Red-class data at write time
**So that** secrets and PII never enter my memory store.

- **Traces**: R-040, R-047.
- **AC-US011-1** (E2E): Adding a note with an AWS access key is rejected with `error.kind=invariant`; no file is committed.
- **AC-US011-2** (Smoke): `pre-commit` runs `gitleaks` and blocks any staged commit containing a known secret pattern (R-047).
- **AC-US011-3** (Unit): The classifier is deterministic — same input yields same decision — and is not LLM-backed.

## US-012 — Performance budget enforced in CI

**As** a maintainer
**I want** the performance suite to run in CI on every PR
**So that** regressions to the §10 budgets are caught before merge.

- **Traces**: R-046.
- **AC-US012-1** (Smoke): CI reports `query_p95_ms ≤ 150`, `add_p95_ms ≤ 200`, `mcp_query_rtt_p95_ms ≤ 200`, `cold_start_ms ≤ 1500`.
- **AC-US012-2** (Smoke): Regression > 10 % on any of the above fails the PR.

## US-013 — Configuration file

**As** a Solo Developer
**I want** `~/.ai-memory/.aimem.yaml`
**So that** I can override embedding model, retrieval window, and forgetting parameters without code changes.

- **Traces**: R-024, R-011, R-021, R-018.
- **AC-US013-1** (Unit): Missing `.aimem.yaml` produces a `level=info op=config result=defaults` log line and uses defaults.
- **AC-US013-2** (Unit): Invalid YAML or unknown keys exit with `error.kind=config`.
- **AC-US013-3** (Unit): `embed.model` overrides default `bge-small-en-v1.5`.

## US-014 — Records have ULID + provenance

**As** an auditor
**I want** every record to carry a ULID and `provenance.{agent, session}`
**So that** I can trace authorship across agent sessions.

- **Traces**: R-004, R-039.
- **AC-US014-1** (Unit): `id` field matches `^[0-9A-HJKMNP-TV-Z]{26}$` (Crockford-32 ULID).
- **AC-US014-2** (Unit): `provenance.agent` and `provenance.session` are non-empty when the writer is an MCP client; CLI writes use `agent=cli`.

## US-015 — Hybrid retrieval respects layer order (forward-compat for Phase 2)

**As** a Solo Developer (Phase-1) and Team Member (Phase-2)
**I want** retrieval to honor the IFC lattice (`personal ⊑ project ⊑ team`)
**So that** when overrides exist, the more-private layer wins by margin θ_tie=0.05.

- **Traces**: R-035 (forward-compat in Phase-1: `personal` only loaded; assertion-tested for >1 layer fixture).
- **AC-US015-1** (Unit): With a fixture containing the same logical note in `personal` and `team`, the personal candidate is returned when score margin ≥ 0.05.
- **AC-US015-2** (Unit): Below margin, both are returned with `provenance.layer` annotated; the response surface labels each.

## US-016 — Tombstone a record (forward-compat with Phase-2 forgetting)

**As** a Solo Developer
**I want** `aimem forget <ulid>`
**So that** the record stops appearing in queries while leaving an auditable tombstone.

- **Traces**: R-044.
- **AC-US016-1** (Unit): After `aimem forget`, the original ID returns `error.kind=not_found` from `aimem get`.
- **AC-US016-2** (Unit): `aimem show --include-tombstones <ulid>` returns the tombstone record with `op=forget` provenance.
- **AC-US016-3** (Unit): Records with active incoming `links.causal` are NOT tombstoned silently — the operator must pass `--cascade` and the cascade is recorded in the tombstone.

---

## Coverage Summary

- 16 MVP R-IDs → 16 user stories (1:1+, some R-IDs in multiple stories).
- All ACs carry TestLevel ∈ {Unit, Smoke, E2E}.
- All HC1–HC6 hard constraints have at least one AC enforcing them: HC1 via US-002 + US-011; HC2 via US-001-3; HC5 via US-002-4 + US-006-2; HC6 forward-compat via US-015 + (Phase-2 R-041 stories).

---

## Iter-2 Update (2026-05-06)

Four iter-2 stories added for the new Must-Have R-IDs. All previous stories US-001..US-016 are preserved verbatim.

### US-051 — Full MCP feature surface (Roots / Elicitation / Sampling / Tasks / Logging)

- **As an** AI coding agent (P-002)
- **I want** the aimem MCP server to negotiate the `2025-11-25` protocol with my host and offer Roots-based auto-scope, Elicitation-based consent for write-down, optional Sampling for `evolve`/`compact`/DP-promote summaries, Tasks for long-running `memory_sync`, and Logging notifications to stderr,
- **so that** I get an idiomatic, host-aware MCP experience without manual scope flags or opaque write-down approvals.
- **Traces**: R-010 (amended), R-051. ROLE-002 (agent caller). E-013 (LayerBindMarker). HC2 (host-policy respect), HC3 (no destructive without consent).

#### Acceptance Criteria

- AC-US051-1 (E2E): Initialize handshake with `protocolVersion=2025-11-25` returns server capabilities including `tools`, `resources`, `prompts`, and a server `instructions` block. Verified via the `aimem-mcp` smoke fixture in `tests/smoke/`.
- AC-US051-2 (Unit): When the client advertises Roots, every write tool resolves the active layer from Roots; if no Root resolves, the tool returns `error.kind=invariant` with message containing `"no resolvable layer from roots"` (no implicit fallback to `personal`).
- AC-US051-3 (E2E): A `layer promote` flow without prior consent triggers an `elicitation/create` request; declining the elicitation returns `error.kind=auth` and **no** filesystem mutation occurs (verified via `git status` clean).
- AC-US051-4 (Unit): `memory_sync` returns a Task handle when the client supports Tasks (SEP-1686); polling cadence ≥ 250 ms. Sync fallback exists when Tasks unsupported.
- AC-US051-5 (Unit): Sampling requests are issued only by `evolve` / `compact` / DP-promote summarize handlers, all with `toolChoice: "none"`. A unit test asserts no other handler imports the sampling helper.
- AC-US051-6 (Smoke): MCP logging notifications are emitted at minimum on `error.kind ∈ {invariant, auth}`; payload schema matches `0027` log schema.

---

### US-052 — Agent hooks integration (Claude Code / Copilot CLI / Codex CLI)

- **As an** AI coding agent invoked through a host's hook system (ROLE-005)
- **I want** to call `aimem add` / `aimem query` automatically before/after my prompts and tool calls,
- **so that** memory capture and recall happen with zero user ceremony, while a hard safety contract prevents the hook from causing destructive operations.
- **Traces**: R-052, R-040, R-045, R-009. ROLE-005 (Hook Caller). HC1 (no Red), HC2 (opt-in only), HC3 (no destructive ops).

#### Acceptance Criteria

- AC-US052-1 (Unit): When `AIMEM_CALLER_ROLE=hook` is set, the CLI parser rejects `--layer team` and `--layer project` for *any* write subcommand with `error.kind=auth`; rejects `layer promote`, `layer demote`, `inbox approve`, `tombstone` outright.
- AC-US052-2 (Unit): Hook-mode invocations are wrapped in a 1 s wall-clock SIGTERM via `aimem.hooks.safety.with_budget()`. A test that sleeps 1 500 ms in a fake handler returns `error.kind=transient, retriable=true` and exits within 1 100 ms.
- AC-US052-3 (Smoke): Reference configs at `examples/hooks/{claude-code,copilot-cli,codex-cli}/` boot a fresh project, fire one capture and one recall round-trip end-to-end, and emit JSON-only stdout (no human-readable preamble).
- AC-US052-4 (Unit): Hook-mode forces `--json` output regardless of caller flags; a `--no-json` caller flag in hook mode is rejected with `error.kind=invariant`.
- AC-US052-5 (E2E): A hook config attempting `aimem layer promote` is denied at the parser layer **before** any git operation; `git status` confirms no working-tree change.

---

### US-053 — Configurable embedding provider with fail-closed remote

- **As a** workstation user (P-001)
- **I want** to configure aimem's embedding provider as `local`, `openai`, or `http` via `~/.ai-memory/.aimem.yaml`,
- **so that** I can trade local model size for hosted-model quality, while remote outages surface loudly instead of silently degrading retrieval.
- **Traces**: R-011 (amended), R-053, R-043. E-014 (EmbedProviderConfig). HC1 (api_key_env only).

#### Acceptance Criteria

- AC-US053-1 (Unit): `embed.provider ∈ {local, openai, http}`; absent or invalid value defaults to `local` with a WARN log line.
- AC-US053-2 (Unit): `openai` / `http` providers REQUIRE `api_key_env` (env-var name); missing env var aborts startup with `error.kind=invariant` mentioning the env var name (not its value).
- AC-US053-3 (Smoke): With `embed.provider=http` pointed at an unreachable URL, `aimem add` returns `error.kind=transient, retriable=true` within `embed.timeout_ms` (default 5 000 ms); the index is **not** updated with a zero vector.
- AC-US053-4 (E2E): Switching `embed.provider` from `local` to `openai` triggers `aimem doctor --reembed` to start a new index generation per R-043; old generation continues serving reads until warm-up completes.
- AC-US053-5 (Unit): A canary embedding query in `aimem verify` asserts the provider returns a non-zero vector with the configured dimensionality.

---

### US-054 — Per-request stateless backend with `flock(2)` concurrency

- **As a** maintainer (ROLE-003) reasoning about correctness
- **I want** the aimem core to open / transact / close per request, with concurrent CLI and MCP writers serialized by `flock(2)` on `~/.ai-memory/.aimem.lock`,
- **so that** there is no daemon to crash, no shared in-memory state, and concurrent writes are observably consistent through git history.
- **Traces**: R-002 (amended), R-054, R-005. E-015 (LockFile). HC4 (auditability).

#### Acceptance Criteria

- AC-US054-1 (Unit): A test that holds `flock(LOCK_EX)` on `.aimem.lock` for 200 ms causes a parallel `aimem add` to return `error.kind=conflict, retriable=true` after `lock.timeout_ms` (default 100 ms) without partial writes.
- AC-US054-2 (E2E): Two concurrent `aimem add` invocations from separate processes both succeed serially; final `git log` shows two distinct commits with no divergence or empty commit.
- AC-US054-3 (Unit): On Windows the `aimem.core.locking` shim selects `msvcrt.locking` and obeys the same `lock.timeout_ms`.
- AC-US054-4 (Unit): No long-lived module-global retains an open repo / index handle across requests (verified by a test that monkeypatches `__init__` and asserts re-entry per call).

---

### Iter-2 coverage summary

- 16 prior MVP R-IDs → 16 stories (unchanged).
- 4 new MVP R-IDs (R-051..R-054) → 4 new stories (US-051..US-054).
- ROLE-005 (Hook Caller) covered by US-052.
- HC1 reinforced by US-052 (hook deny-list) and US-053 (api_key_env).
- HC2 reinforced by US-051 (Roots) and US-052 (opt-in hooks).
- HC3 reinforced by US-051 (Elicitation gate) and US-052 (no destructive in hook mode).
- HC4 reinforced by US-054 (every write is a complete git transaction).
