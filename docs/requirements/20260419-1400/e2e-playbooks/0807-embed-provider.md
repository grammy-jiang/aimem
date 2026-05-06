# Playbooks — Embedding Provider & Concurrency (Iter-2)

Spec-Version: 20260419-1400
Source: e2e-playbook-generator (iter-2)
Document-Range: 0800-0899
Traces: US-053 / R-053 / COMP-022; US-054 / R-054 / COMP-023.

---

## PB-058 — Embedding provider switch with index-generation rotation

**Goal**: Switching `embed.provider` from `local` to `openai` (or `http`) starts a new index generation; old generation continues serving reads during warm-up; remote failures fail closed and never poison the index.

### Steps

1. Boot a project with `embed.provider=local` and `aimem add` 100 fixture notes.
2. Run `aimem query` and capture P@5 baseline.
3. Edit `~/.ai-memory/.aimem.yaml`: set `embed.provider=openai`, `embed.api_key_env=OPENAI_API_KEY`. Set `OPENAI_API_KEY` to a working test key (or point `embed.provider=http` at the deterministic fake provider in `tests/e2e/fixtures/`).
4. Run `aimem doctor --reembed`. Assert it begins a new index generation per R-043 and exits 0.
5. While re-embed is in progress, run `aimem query`. Assert results come from the old generation (verified by a generation ID in the JSON response) and are non-empty.
6. Wait for warm-up to complete. Assert subsequent `aimem query` calls return the new generation ID.
7. Run `aimem verify`. Assert the canary embedding test passes (non-zero vector with expected dimensionality).
8. **Failure-mode sub-case**: set `embed.provider=http` to a URL that always returns 500. Run `aimem add`. Assert exit ≠ 0; `error.kind=transient, retriable=true`; the index file size and generation ID do not change (no zero-vector poison).
9. **Config-mode sub-case**: omit `embed.api_key_env`. Run `aimem-mcp` startup. Assert exit ≠ 0; `error.kind=invariant`; stderr names the missing env var name (not its value).

**Expected**: Provider switch is zero-downtime for reads; remote failures never silently degrade the index; configuration errors are loud at startup.

### Coverage map

| AC | Step |
| ---- | ------ |
| AC-US053-1 | PB-058 step 1, 9 (default fallback path) |
| AC-US053-2 | PB-058 step 9 |
| AC-US053-3 | PB-058 step 8 |
| AC-US053-4 | PB-058 steps 4–6 |
| AC-US053-5 | PB-058 step 7 |

| Red-team finding | Step |
| ------------------ | ------ |
| EMBED-REMOTE-001 (silent zero-vector) | PB-058 step 8 |

---

## PB-059 — `flock(2)` concurrency and per-request statelessness

**Goal**: Concurrent writers serialize; lock timeout maps to `error.kind=conflict`; no module-global retains a repo / index handle across requests.

### Steps

1. **Concurrent add (POSIX)**: Spawn two `aimem add` processes simultaneously. Assert both exit 0 (after serialization); `git log` on the personal layer shows two distinct commits with strictly increasing timestamps and no empty / merge commits.
2. **Lock contention**: From Python, open `~/.ai-memory/.aimem.lock` and hold `flock(LOCK_EX)` for 200 ms. In a parallel subprocess, run `aimem add ...` with default `lock.timeout_ms=100`. Assert the subprocess exits ≠ 0 within ~100–150 ms; JSON `error.kind=conflict, retriable=true`; `git status` clean.
3. Release the lock; rerun the same `aimem add`. Assert it succeeds.
4. **Windows shim** (run only on Windows runners): repeat steps 1–3. Assert `aimem.core.locking` selects `msvcrt.locking`; behavior matches POSIX.
5. **No module-global state**: A unit test monkeypatches `aimem.core.repository.__init__` to count instantiations; runs 5 sequential `aimem add` calls in a single Python process; asserts the counter incremented to 5 (no caching of repo / index handles across requests).

**Expected**: Writes serialize correctly under contention; loser surfaces a clean `conflict` error; Windows shim is behavior-equivalent; no shared in-memory state between requests.

### Coverage map

| AC | Step |
| ---- | ------ |
| AC-US054-1 | PB-059 step 2 |
| AC-US054-2 | PB-059 step 1 |
| AC-US054-3 | PB-059 step 4 |
| AC-US054-4 | PB-059 step 5 |
