# Assumptions Log

Spec-Version: 20260419-1400
Source: req-analyzer
Document-Range: 0100-0199

| # | Assumption | Impacted ReqIDs | Risk if wrong | Source |
| --- | ------------ | ----------------- | --------------- | -------- |
| 1 | Git ≥ 2.40 with submodules available on host | R-001, R-005, R-034 | High — storage layer breaks | design.md §3.1 |
| 2 | `pynacl` (libsodium) installable on Linux/macOS/Windows | R-039 | Medium — fall back to PyCA `cryptography` | design.md §8 |
| 3 | `bge-small-en-v1.5` runs at ≤ 50ms per embed on a 2024 laptop CPU | R-011, §10 budgets | Medium — switch to ONNX or pluggable | design.md §7 |
| 4 | SQLite FTS5 available in stdlib `sqlite3` (Python 3.12+) | R-011 | Low — sqlite3 ships FTS5 by default | design.md §7 |
| 5 | MCP `2025-06-18` is stable through Phase-1 timebox | R-010 | Low — pin in pyproject | design.md §6 |
| 6 | One human reviewer is sufficient for promote PRs in Phase 2 | R-036, ROLE-004 | Medium — escalate to 2-of-N if abuse observed | design.md §3.2 |
| 7 | bge-small-en-v1.5 384-dim Gaussian DP gives acceptable utility at ε≤2 per promote | R-041 | High — utility loss; adjust ε or per-vector clipping | design.md §8 |
| 8 | Users' team-layer remotes are GitHub repos in v1 | R-042 | Low — remote interface is pluggable | design.md §1 |
| 9 | ULID monotonicity is per-process, not global | R-004 | Low — collisions vanishingly improbable | design.md §4 |
| 10 | gitleaks pre-commit hook can be installed via `pre-commit` framework | R-047 | Low — alternative manual hook | design.md §8 |

## Open Questions

None blocking. Two decisions deferred per design.md §13:

- DQ-01: Default evaluator LLM for `evolve`/`compact`. Ship both local + API; default local. *Not Phase-1 critical.*
- DQ-02: CRDT engine for OR-Set semantics (R-050). *Phase 2.*

## Iter-2 Update (2026-05-06) — user-confirmed assumptions

The four high-level assumptions from `0099-handoff-summary.md` were USER-CONFIRMED on 2026-05-06. Two were refined and now have dedicated requirements:

| # | Original | Status | Refinement | New ReqID |
| --- | ---------- | -------- | ------------ | ----------- |
| 1 | Git always available | Confirmed | none | — |
| 2 | Embedding model is a local Python library | **Refined** | Provider is configurable (`local` / `openai` / `http`); local default; remote fails closed; API keys via env vars only (HC1). | **R-053** |
| 3 | ≄10 000 notes scale | Confirmed | none | — |
| 4 | Single-user CLI process, no daemon | **Refined** | MCP server may be long-running for an agent session, but `aimem.core` is per-request stateless (open/transact/close); `flock(2)` serializes concurrency. | **R-054** |

### New iter-2 assumptions

| # | Assumption | Impacted ReqIDs | Risk if wrong | Source |
| --- | ------------ | ----------------- | --------------- | -------- |
| 11 | MCP `2025-11-25` SDKs (Python `mcp>=` matching version) are available at Phase-1 timebox | R-010, R-051 | Low — fall back to `2025-06-18` with feature degradation | design.md §6 |
| 12 | Host clients (Claude Code, Copilot CLI, Codex CLI) advertise Roots capability often enough to make auto-scope useful | R-051 | Medium — fall back to manual `aimem layer scope` if Roots absent | design.md §6.4 |
| 13 | Tasks (SEP-1686) is acceptable as experimental in Phase 1; sync fallback covers clients that lack it | R-051 | Low — sync fallback already specified | design.md §6.5 |
| 14 | Linux/macOS/Windows all support `flock(2)` semantics (Windows via `msvcrt.locking` shim) | R-054 | Low — cross-platform shim is small | design.md §12 |
| 15 | Remote embedding endpoints are reachable within `embed.timeout_ms` (default 5 000 ms) on a typical workstation | R-053 | Medium — user can raise timeout per `~/.ai-memory/.aimem.yaml` | design.md §7 |
| 16 | Reference hook configs at `examples/hooks/` work on a clean install of each target agent | R-052 | Medium — covered by AC-R052-3 smoke test | design.md §15 |
