# FURPS+ Quality Assessment

Spec-Version: 20260419-1400
Source: req-analyzer
Document-Range: 0100-0199

## Functionality

| Capability | Coverage | ReqID(s) |
| ------------ | ---------- | ---------- |
| Memory CRUD | Complete | R-002, R-006 |
| Hybrid retrieval | Complete | R-011, R-021 |
| Three-layer model | Complete | R-034, R-035, R-036, R-037, R-042 |
| Schema migration | Complete | R-038 |
| Signing & trust | Complete | R-039, R-022 |
| Write gate / secrets | Complete | R-040, R-047 |
| DP on promote | Complete | R-041 |
| Stale-vector handling | Complete | R-043 |
| Tombstones / forgetting | Complete | R-044, R-018 |
| Adapters | Phase 1.5/2 | R-007, R-008 |
| MCP server | Complete (pinned) | R-010 |

## Usability

- CLI is sole human surface (R-009). MCP is the agent surface (R-010). i18n is Could-Have (R-026).
- Error messages MUST NOT leak note bodies (R-027 amended). Stable taxonomy (R-045) gives consumers a contract.

## Reliability

- Atomic git writes (R-005). Per-record ed25519 sigs (R-039) detect tamper. Tombstones cascade-aware (R-044). DP budget hard-stops on exhaustion (R-041).
- Graceful degradation: BM25-only fallback if embedding unavailable. Old index generation served read-only during re-embed (R-043).

## Performance (per `docs/design.md` §10, p95, warm)

| Op | Budget |
| ---- | -------- |
| `aimem query` (≤5 results, 3 layers) | 150 ms |
| `aimem add` | 200 ms |
| `aimem sync` (1 layer, no conflicts) | 2 s |
| MCP `memory_query` RTT | 200 ms |
| Cold start | 1.5 s |

## Supportability

- `aimem doctor` (R-023) consolidated health check.
- Structured JSONL logs at `.agent/logs/aimem.jsonl`, daily rotated, never committed (R-027).
- Schema migration framework with author-only `aimem migrate` and CI dry-run (R-038).
- Stable error taxonomy (R-045) makes triage contract-driven.

## "+" Constraints

- HC1–HC6 from `GROUNDING.md` are non-negotiable.
- HC1: gitleaks (R-047) + write-gate (R-040) + redacted error messages (R-027).
- HC2: writes only under repo working tree.
- HC3/HC4: agent never performs destructive ops directly; promote/demote always opens a PR (R-035, R-036).
- HC5: ed25519-signed records (R-039); per-layer known-key set (R-022).
- HC6: privacy budget tracked and enforced (R-041).

## Risk-Adjusted Posture

| Quality Attribute | Risk | Mitigation |
| ------------------- | ------ | ------------ |
| Cross-layer leakage | High | DP on promote (R-041) + IFC lattice (R-035) |
| Index drift after upgrade | Medium | Generations + warm-up (R-043) |
| Adversarial sync | Medium | Inbox quarantine + sig (R-037, R-039) |
| Schema lock-in | Low | Versioned migrations (R-038) |
| Adaptive jailbreak | Deferred | R-049 deferred to multi-tenant team release |

## Iter-2 Update (2026-05-06)

Incorporates `0010-design-iter-2-addendum.md` (R-002/R-010/R-011 amendments + R-051..R-054).

### Functionality additions

| Capability | Coverage | ReqID(s) |
| ------------ | ---------- | ---------- |
| Full MCP feature surface (Tools/Resources/Prompts + Roots/Elicitation/Sampling/Tasks/Logging) | Complete | R-051 |
| Agent-hooks integration (Claude Code / Copilot CLI / Codex CLI) | Complete (reference configs in `examples/hooks/`) | R-052 |
| Configurable embedding provider (`local` / `openai` / `http`) | Complete | R-053 |
| Per-request stateless backend (`flock(2)` concurrency) | Complete | R-002 (amended), R-054 |

### Usability

- Hooks deliver **automatic** memory capture/recall without human ceremony — a major usability win for the agent-driven workflow that motivates aimem.
- Elicitation (R-051) gives users human-readable consent prompts in the host UI for every write-down (promote/demote/inbox-approve/tombstone) instead of opaque CLI flags.
- Tool icons + `description` (SEP-973) improve discoverability inside MCP-aware hosts.

### Reliability

- Remote embedding fail-closed (R-053) prevents silent retrieval-quality collapse (EMBED-REMOTE-001).
- `flock(2)` (R-054) eliminates the race window between concurrent CLI/MCP writers; loser surfaces `error.kind=conflict`.
- Provider switch triggers index-generation rotation (R-053 → R-043) so retrieval keeps serving while the new generation warms.

### Performance additions

| Op | Budget |
| ---- | -------- |
| Hook invocation wall clock (p100) | ≤ 1 000 ms (self-terminating) — R-052 |
| `aimem add` with `embed.provider=openai` (warm endpoint) | ≤ 800 ms p95 — R-053 |
| `aimem sync` Task polling cadence | ≥ 250 ms between polls — R-051 |
| MCP `memory_query` RTT with Roots auto-scope | ≤ 200 ms p95 (unchanged) |

### Supportability

- Hook safety contract (R-052) makes hook misbehavior diagnosable from `.agent/logs/aimem.jsonl` alone.
- MCP version-negotiation surface (R-010 amended) gives loud failure on unknown versions and graceful degradation on `2025-06-18`.
- Sampling restricted to non-hot paths with `toolChoice: "none"` prevents recursive cost amplification (SAMPLING-001).

### "+" Constraint mapping (iter-2)

- **HC1**: R-053 enforces `api_key_env` (env-var only); R-052 hooks inherit the same write-gate (R-040) + gitleaks (R-047) path.
- **HC2**: R-052 explicitly opt-in; aimem MUST NOT auto-install hook configs.
- **HC3/HC4**: R-052 hooks cannot promote/demote/inbox-approve/tombstone — destructive ops remain human-driven through Elicitation (R-051).
- **HC4 (audit)**: R-054 keeps every write a complete git transaction observable from outside the running process.

### Risk-adjusted posture (iter-2 additions)

| Quality Attribute | Risk | Mitigation |
| ------------------- | ------ | ------------ |
| Hook-driven exfiltration | High | R-052 deny-list (no `team`/`project` writes; no promote) + ROLE-005 |
| Hook resource exhaustion | Medium | R-052 1 s wall clock + R-054 `flock` |
| MCP version drift | Medium | R-010 amended: explicit negotiation; unknown → fail loud |
| Remote embedding silent failure | Medium | R-053 fail-closed + canary in `aimem verify` |
| Recursive sampling cost | Medium | R-051 `toolChoice: "none"` on Sampling |
