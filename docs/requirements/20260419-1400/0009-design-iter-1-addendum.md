# Design Iteration 1 Addendum (2026-05-06)

Spec-Version: 20260419-1400
Source: req-clarifier (addendum pass)
Supersedes evidence basis: docs/design.2026-04-19.md → docs/design.md (iter 1)

## Purpose

This file captures the **delta** introduced by `docs/design.md` (iter 1, 2026-05-06) on top of the original 0000-0008 artifacts. It uses the same Spec-Version. Existing R-IDs (R-001..R-033) are preserved verbatim. New requirements append starting at R-034. Modified requirements are listed under "Amendments to existing R-IDs" and override the original wording.

## Amendments to Existing R-IDs

| ReqID | Change | Source in design.md |
| ------- | -------- | --------------------- |
| R-003 | Memory `type` set replaced with `{identity, preference, procedure, observation, knowledge}` (was `{identity, knowledge, procedure, journal}`). `journal` is renamed to `observation`; `preference` added; type-aware forgetting weights are now keyed on the new set. | §4 schema |
| R-004 | YAML frontmatter now MUST include `schema_version: 1`, `id: <ulid>`, `layer: personal\|project\|team`,`links.{causal,evolves,refines}`,`forgetting.{ttl_days,decay∈{none,exponential}}`,`provenance.{agent,session}`,`sig: <ed25519>`. Old fields retained where compatible. CI rejects records without`schema_version`. | §4 schema |
| R-005 | All commits MUST be ed25519-signed using the user's local key; signature verification is part of `aimem verify`. GPG/SSH wording in original superseded by ed25519 detached sigs at the record level (commit-level signing remains best-practice but not invariant). | §4, §8 |
| R-010 | MCP server **pinned** to protocol version `2025-06-18`, transport `stdio` only for v1 (WebSocket deferred). Tool list amended to: `memory_query, memory_add, memory_link, memory_tag, memory_layer_list, memory_layer_scope, memory_layer_promote, memory_sync, memory_inbox`. Resources: `memory://record/<id>`, `memory://layer/<layer>/<path>`, `memory://search?q=...`, `memory://inbox`. Server is one-shot per call; no in-memory write state across reconnects. | §6 |
| R-011 | Default embedding model is **`bge-small-en-v1.5`** (384-dim, MIT, CPU-runnable). Configurable via `~/.ai-memory/.aimem.yaml::embed.model`. Index = SQLite FTS5 (keyword) + flat HNSW (vectors). Index is **never** committed to git. | §7 |
| R-017 | Hot-buffer/dual-buffer consolidation is **Dropped for v1**; replaced by inbox quarantine (R-037) for sync, and by deterministic write-gate (R-040) for fresh writes. Phase-3 hardening may reintroduce a probation-style buffer if needed. | §12 roadmap |
| R-018 | Forgetting policy now reads `forgetting.{ttl_days, decay}` from frontmatter (per-record). The ABF-style aggregate scoring in 0000 remains as the *default* engine when `forgetting` is unset. `aimem prune` MUST NOT touch records in `personal/.inbox/` or those with active incoming `links.causal`. | §4, §7 |
| R-022 | Commit-author-only provenance is insufficient; provenance is now anchored at the record `sig` field. Team-layer trust is per **layer key set**, not per-commit GPG identity. | §8 |
| R-027 | Structured-logging fields fixed to: `ts, level, op, layer, record_id, latency_ms, agent, session, error.code, error.kind`. Logs land at `.agent/logs/aimem.jsonl`, daily-rotated, never committed. Error messages MUST NOT contain note bodies. | §11 |

## New Must-Have Requirements (R-034 → R-046)

| ReqID | Title | Description | Value/Rationale | Dependencies | Status |
| ------- | ------- | ------------- | ----------------- | -------------- | -------- |
| R-034 | Three-Layer Sharing Model | Storage is split into three independent git repos mounted as submodules under `~/.ai-memory/`: `personal/`, `projects/<slug>/`, `teams/<slug>/`. Each layer has its own remote, key set, and history. Parent index repo is private. | Headline feature; access control, history, and remotes are independent per layer. | R-001, R-005 | Active |
| R-035 | IFC Lattice Enforcement | Information-flow lattice `personal ⊑ project ⊑ team` enforced at retrieval and write time. Read-up is allowed silently; write-down (more-private → more-public) MUST go through an explicit promote PR — never silent. | Prevents accidental leakage of private notes into shared layers. | R-034 | Active |
| R-036 | Layer Promote/Demote | `aimem layer promote <id>` opens a maintainer-reviewed PR on the receiving remote. `aimem layer demote` mirrors the move toward more-private. Both operations record provenance and are reversible. | Operationalizes write-down with auditable controls. | R-034, R-035 | Active |
| R-037 | Inbox Quarantine | Incoming records from a remote land in `<layer>/.inbox/` and are NOT retrievable until `aimem inbox approve <id>`. Verification of `sig` against the layer's known-key set is a precondition for approval. | Prevents adversarial sync from polluting an active layer. | R-034, R-005 | Active |
| R-038 | Schema Versioning & Migration | `MemoryRecord.schema_version` is an integer. Breaking changes bump it by 1 and ship a migrator at `aimem/storage/migrations/v<N>_to_v<N+1>.py`. `aimem migrate` is author-only; CI dry-runs migrations on every PR and refuses silent downgrades. Old records keep their `schema_version`; the retriever projects them up at read time. | Forward-compatibility and reproducibility across versions. | R-004 | Active |
| R-039 | Record-Level Signing | Every record is signed with the user's local ed25519 key. `aimem verify` checks signature validity, schema validity, and orphan-link absence. Sync verifies signatures against each layer's known-key set. | Tamper-evidence at the record level; foundation for trusted promotion. | R-004, R-005 | Active |
| R-040 | Write-Gate Content Classifier | Every `aimem add` runs a content classifier; data classified "Red" per GROUNDING.md is **rejected at write**, never quarantined. Implementation is deterministic (rules + small classifier), not LLM-based. | Prevents red-class data from ever entering the store. | R-002, R-004 | Active |
| R-041 | DP on Cross-Layer Promote | When promoting `personal → project` (or any private → public step), only the **summary + embedding** cross the boundary, with Gaussian-mechanism noise (DP). Raw text never crosses. Privacy budget tracked at `~/.ai-memory/.privacy/budget.json`. | Bounds cross-layer information leakage by mechanism, not by trust. | R-035, R-036 | Active |
| R-042 | Pluggable Remote — GitHub Reference | Remote is pluggable per layer; GitHub is the v1 reference implementation. Layer linking via `aimem layer link <url>` wraps `git submodule add` plus initial sign-off. | Enables on-prem / GitLab / Gitea later without code changes. | R-034 | Active |
| R-043 | Stale-Vector Handling | Tombstoned deletes are recognized by the index; HNSW re-link runs on scheduled compaction; embedding-model upgrade triggers a full re-embed under a new index generation, with the old generation served read-only until the new one is warm. | Avoids silent retrieval drift after delete/upgrade (research A-3). | R-011, R-018 | Active |
| R-044 | Tombstones | `aimem forget` and `aimem tombstone` produce verifiable tombstone records. Purge is cascade-aware: dependent links are pruned; identity-layer never auto-purges. | Privacy-respecting deletion with audit trail. | R-018, R-039 | Active |
| R-045 | Stable Error Taxonomy | Errors expose one of: `config, auth, conflict, quarantine, not_found, invariant, transient`. `retriable` flag is part of the contract. The MCP layer marshals these unchanged to clients. | Stable contract for agent-side error handling. | R-010, R-027 | Active |
| R-046 | Performance & Evaluation Gates | Release-blocking gates: `aimem verify` per commit; LayerEval per release (cross-layer leakage, precedence correctness, cascade-delete purity); LongMemEval slice (P@5 ≥ 0.7); RedTeam suite (HarmBench+PAIR+TAP, ASR ≤ 5 %) is multi-tenant team release only. Latency budget per §10. | Mechanically-enforced quality bar. | R-011, R-034 | Active |
| R-047 | Secrets at Write Time | A `gitleaks` pre-commit hook on every layer blocks plaintext secrets at commit (HC1 hardening). | Defense-in-depth against credential leakage. | R-005, R-040 | Active |

## New Nice-to-Have / Deferred (R-048 → R-050)

| ReqID | Title | Description | Phase | Status |
| ------- | ------- | ------------- | ------- | -------- |
| R-048 | Offline-RL Retrieval Policy | Phase 4 (research E-2): replace deterministic retriever with shadow-tested offline-RL policy; ship only if divergence < 1 % and SR@1 strictly improves. | 4 | Deferred |
| R-049 | Adaptive Red-Team Protocol | HarmBench + PAIR + TAP attack-success-rate ≤ 5 % blocks **multi-tenant team** release only. Phase 1 personal-only ships without it. | 5 | Deferred |
| R-050 | CRDT OR-Set Engine | Hand-rolled in Phase 2; consider extracting to library in Phase 4 if reuse needed. | 2→4 | Proposed |

## Acceptance-Criteria Additions (excerpt; full set in 0001 amendments)

| AC-ID | ReqID | Statement | TestLevel |
| ------- | ------- | ----------- | ----------- |
| AC-R034-1 | R-034 | After `aimem init` with all three layers, `~/.ai-memory/{personal,projects/<slug>,teams/<slug>}` are independent git repos with distinct `.git/HEAD` and distinct configured remotes. | E2E |
| AC-R034-2 | R-034 | Detaching the team layer (`aimem layer detach team <slug>`) leaves personal and project layers fully functional; existing notes in detached layer remain on disk and unreachable from queries. | E2E |
| AC-R035-1 | R-035 | A `personal` query that semantically matches a `team` note must return the `personal` candidate when score margin ≥ θ_tie (0.05); otherwise both, with provenance labels. | Unit + E2E |
| AC-R035-2 | R-035 | A direct attempt to `aimem add --layer team` from a non-maintainer key is rejected with `error.kind=auth`. | Unit |
| AC-R036-1 | R-036 | `aimem layer promote <id>` produces a PR on the target remote and does NOT mutate the source layer until the PR merges. | E2E |
| AC-R037-1 | R-037 | Records pulled from a remote land under `<layer>/.inbox/`; `aimem query` does not return them. | E2E |
| AC-R037-2 | R-037 | `aimem inbox approve <id>` fails with `error.kind=auth` if the record's `sig` does not verify against the layer's known-key set. | Unit |
| AC-R038-1 | R-038 | A record without `schema_version` is rejected by `aimem verify` with `error.kind=invariant`. | Unit |
| AC-R038-2 | R-038 | CI dry-run of a v1→v2 migrator on a fixture corpus completes with no data loss and no schema regressions. | Smoke |
| AC-R039-1 | R-039 | A record with a malformed `sig` field fails `aimem verify` with `error.kind=auth`. | Unit |
| AC-R040-1 | R-040 | Writing a note containing a known-pattern Red secret (e.g. AWS access key) is rejected at write with `error.kind=invariant`; no file is created. | E2E |
| AC-R041-1 | R-041 | Promoting a `personal` record to `project` results in only `summary + embedding(noised)` being committed to the project remote; the raw body diff size on the project remote equals zero for body bytes. | E2E |
| AC-R041-2 | R-041 | Privacy budget at `~/.ai-memory/.privacy/budget.json` is debited on each promotion; budget exhaustion blocks further promotes with `error.kind=invariant`. | Unit |
| AC-R043-1 | R-043 | After embedding-model upgrade, queries served by the old generation continue to return non-empty results until the new generation is warm. | E2E |
| AC-R044-1 | R-044 | A tombstoned record's `id` returns `not_found` from `aimem get`; its tombstone record is still retrievable via `aimem show --include-tombstones`. | Unit |
| AC-R045-1 | R-045 | Each MCP error response exposes `error.kind` from the documented set; consumers can rely on `retriable` flag. | Smoke |
| AC-R046-1 | R-046 | LongMemEval slice on bundled fixture reports P@5 ≥ 0.7 in CI. | Smoke |
| AC-R046-2 | R-046 | `aimem query` p95 ≤ 150 ms on warm index in the bundled benchmark. | Smoke |
| AC-R047-1 | R-047 | A staged commit containing a known-pattern secret is blocked by the `gitleaks` pre-commit hook. | Smoke |

## New Scenario Inventory Additions

| Scenario ID | Workflow | Class | Description |
| ------------- | ---------- | ------- | ------------- |
| SCN-WF002-NEG-04 | WF-002 | NEG | Add a note that fails the write-gate classifier (Red secret). |
| SCN-WF004-HP-03 | WF-004 | HP | Promote `personal` note to `project` via PR; only summary+noised embedding committed remotely. |
| SCN-WF004-NEG-04 | WF-004 | NEG | Inbox approve fails because record sig does not verify. |
| SCN-WF004-FAIL-02 | WF-004 | FAIL | Privacy budget exhausted; promote rejected with `error.kind=invariant`. |
| SCN-WF005-HP-04 | WF-005 | HP | Embedding-model upgrade: old index serves reads while new index warms. |
| SCN-WF005-NEG-03 | WF-005 | NEG | Tombstone cascade: incoming-link counts decremented; orphans flagged by doctor. |
| SCN-WF006-HP-03 | WF-006 | HP | Team-layer maintainer reviews and merges promote PR; sigs verified. |
| SCN-WF006-NEG-02 | WF-006 | NEG | Promote PR by non-maintainer is rejected at the layer's CI gate. |

## Roles / Permissions Updates

| ID | Name | Description |
| ---- | ------ | ------------- |
| ROLE-004 | Team Layer Maintainer | Holds a key in the team layer's known-key set. Can review/merge promote PRs; rotate keys; approve inbox entries on the team layer. Distinct from ROLE-001 (which is per-layer when the user owns that layer). |

## Data-Entity Updates

| ID | Name | Note |
| ---- | ------ | ------ |
| E-002 | NoteMeta | Replaced by `MemoryRecordV1` per §4 schema; `E-002` symbol now refers to the v1 schema. |
| E-005 | HotBufferEntry | **Dropped** (R-017 dropped). |
| E-007 | LayerRepo | One of three independent git repos under `~/.ai-memory/{personal, projects/<slug>, teams/<slug>}`. Has its own remote, history, and known-key set. |
| E-008 | InboxEntry | Quarantined incoming record under `<layer>/.inbox/`; not retrievable until approved. |
| E-009 | Tombstone | Verifiable deletion record; cascade-aware. |
| E-010 | PromotePR | Cross-layer promote artifact; carries summary + noised embedding only. |
| E-011 | PrivacyBudget | JSON ledger at `~/.ai-memory/.privacy/budget.json` tracking DP epsilon spent per layer pair. |
| E-012 | KnownKeySet | Per-layer set of accepted ed25519 public keys for sig verification. |

## NFR Updates (replaces 0005 §Performance)

| Metric | Target (p95, warm) | Source |
| -------- | --------------------- | -------- |
| `aimem query` (≤ 5 results, all 3 layers) | 150 ms | §10 |
| `aimem add` (single record, no sync) | 200 ms | §10 |
| `aimem sync` (one layer, no conflicts) | 2 s | §10 |
| MCP `memory_query` round-trip | 200 ms | §10 |
| Cold start (first command in a process) | 1.5 s | §10 |

## New Red-Team Findings

| Finding ID | Severity | Category | Description | Mitigation |
| ------------ | ---------- | ---------- | ------------- | ------------ |
| LEAK-001 | High | Cross-Layer Leakage | Naive promote leaks raw private text into a shared layer. | R-041 DP-on-promote: only summary+noised embedding crosses; raw body never. |
| ADAPT-001 | Medium | Adaptive Attack | HarmBench/PAIR/TAP-style adaptive jailbreak against memory retrieval. | R-049 deferred to multi-tenant team release; not Phase-1 blocker for personal layer. |
| STALE-001 | Medium | Data Loss | Stale vectors after delete or embedding upgrade serve incorrect retrieval. | R-043 generations + tombstone-aware re-link. |
| INBOX-001 | Medium | Abuse | Hostile sync injects malicious notes that are immediately retrievable. | R-037 inbox quarantine + sig verification gate. |
| DP-BUDGET-001 | Low | Privacy | Unbounded promotes exhaust differential-privacy budget without operator awareness. | R-041 budget ledger + hard stop on exhaustion (`error.kind=invariant`). |

## Assumptions Carried Forward / Refined

| Assumption | Risk if wrong |
| ------------ | --------------- |
| `bge-small-en-v1.5` is acceptable as default; users with GPU can swap. | Low — pluggable. |
| `ed25519` (libsodium) is available on all target platforms. | Low — Python `pynacl` covers Linux/macOS/Windows. |
| Single human reviewer is sufficient on team-layer promote PRs in Phase 2. | Medium — escalate to 2-of-N if abuse observed. |
| MCP `2025-06-18` will not break in Phase-1 timebox. | Low — pinned in `pyproject.toml`. |

## Exit Gates Re-evaluated

All 19 original exit gates remain green. Two additional gates introduced by iter 1:

1. Every requirement amended or added in this addendum has at least one AC with a TestLevel tag.
2. New red-team findings are mapped to a mitigating ReqID (no orphan finding).

Both pass.
