# Complexity & Risk Assessment

Spec-Version: 20260419-1400
Source: req-analyzer
Document-Range: 0100-0199

## Complexity Score (1=trivial, 5=hard) per ReqID

| ReqID | Complexity | Drivers |
| ------- | ------------ | --------- |
| R-001 | 2 | Directory bootstrap + parent index repo + 3 submodules |
| R-002 | 2 | File I/O + path-by-id |
| R-004 | 3 | Pydantic v2 model with sig/migrations |
| R-005 | 2 | GitPython or shell-out; signed commits straightforward |
| R-010 | 3 | FastMCP server, stdio transport, 9 tools |
| R-011 | 4 | FTS5 + HNSW + bge-small embeddings; index lifecycle |
| R-034 | 4 | Submodule orchestration + per-layer remotes + IFC |
| R-035 | 4 | IFC lattice + score-margin tie policy |
| R-036 | 4 | PR opening + reversible state |
| R-037 | 3 | Inbox dir + sig verify gate |
| R-038 | 3 | Migrators + CI dry-run hook |
| R-039 | 3 | pynacl ed25519; canonical serialization |
| R-040 | 3 | Classifier rules + Red-data list |
| R-041 | 5 | DP accountant; Gaussian-mechanism noise on embeddings; budget ledger |
| R-043 | 4 | Index generations + tombstone-aware re-link |
| R-046 | 3 | Bench harness + LongMemEval slice |

## Top Risks

| ID | Risk | Likelihood | Impact | Mitigation |
| ---- | ------ | ----------- | -------- | ------------ |
| RSK-01 | DP-on-promote degrades retrieval utility on shared layers | M | H | Budget tuning per layer; A/B against no-DP baseline in eval suite |
| RSK-02 | bge-small recall insufficient on technical jargon | M | M | Pluggable model; offer `bge-large` as opt-in |
| RSK-03 | HNSW corruption after kill-9 mid-write | L | H | Index never committed; rebuild from records is cheap |
| RSK-04 | MCP `2025-06-18` spec drift | L | M | Pin in `pyproject.toml`; protocol-version test in smoke suite |
| RSK-05 | gitleaks false positives blocking legitimate writes | M | L | Configurable allowlist; clear error-kind=`invariant` |
| RSK-06 | Submodule UX confuses users | M | M | `aimem layer link` wraps git submodule add (R-042) |
| RSK-07 | DP budget exhaustion blocks team workflow unexpectedly | M | M | Doctor surfaces remaining budget; reset on quarter |
| RSK-08 | Schema v1→v2 migrator data loss | L | H | CI dry-run on every PR; author-only migrate command |
| RSK-09 | Adaptive jailbreak against retrieval | M (multi-tenant) | H | R-049 deferred to multi-tenant team release |
| RSK-10 | ed25519 keypair loss locks user out of own records | L | H | Doctor warns on missing key; recovery via re-signing on author-blessed import |

## Dependency Graph (Top-down)

R-001 → R-005 → R-034 → R-035 → R-036 → R-041
R-001 → R-002 → R-004 → R-038, R-039
R-002 → R-011 → R-043
R-002 → R-040 → R-047
R-009, R-010 share core lib R-002+R-011

No cycles detected.

## Iter-2 Update (2026-05-06)

Incorporates `0010-design-iter-2-addendum.md`.

### Complexity scores for new R-IDs

| ReqID | Complexity | Drivers |
| ------- | ------------ | --------- |
| R-051 | 4 | Wiring Roots auto-scope + Elicitation + Sampling + Tasks (experimental) across the FastMCP server; graceful degradation when client lacks a capability. |
| R-052 | 3 | Hook adapter package + per-agent reference configs + safety-contract enforcement at CLI parser layer + 1 s wall-clock guard. |
| R-053 | 3 | Provider abstraction with fail-closed remote calls + `api_key_env` resolver + index-generation rotation hook. |
| R-054 | 2 | `flock(2)` advisory lock + lock-timeout → `error.kind=conflict` mapping. |

Also re-baseline R-010 from 3 → **4** (now drives R-051's full feature surface) and R-002 stays at 2 (R-054 absorbs the concurrency complexity).

### Risks added

| ID | Risk | Likelihood | Impact | Mitigation |
| ---- | ------ | ----------- | -------- | ------------ |
| RSK-11 | Hook-driven exfiltration via project/team writes | M | H | R-052 hook safety contract + ROLE-005 deny-list; HOOK-001 finding |
| RSK-12 | Hook saturation (per-keystroke firing) starves aimem | M | M | R-052 1 s wall clock + R-054 `flock`; HOOK-002 finding |
| RSK-13 | Host advertises unsupported MCP version → silent degradation | L | M | R-010 amended: loud fail on unknown; MCP-VER-001 finding |
| RSK-14 | Remote embedding silently returns zero vectors | L | H | R-053 fail-closed + canary query in `aimem verify`; EMBED-REMOTE-001 finding |
| RSK-15 | Sampling recursion during `evolve` self-amplifies cost | L | M | R-051 `toolChoice: "none"`; never on hot read; SAMPLING-001 finding |

### Dependency graph additions

- R-010 → R-051 (full MCP surface depends on the protocol pin).
- R-051 → R-035, R-036, R-041 (Elicitation gates write-down on these).
- R-052 → R-040, R-045, R-009, R-010 (hook safety reuses write-gate, error taxonomy, CLI, MCP).
- R-053 → R-011, R-043 (provider switch triggers re-embed under new generation).
- R-054 → R-002, R-005 (concurrency layer over CRUD + git ops).

No cycles introduced.
