# Data Flow

Spec-Version: 20260419-1400
Source: arch-designer
Document-Range: 0400-0499

## Add Flow (CLI or MCP)

```text
Client → COMP-001/002 → COMP-004 (AddNote)
  → COMP-017 Config (load defaults)
  → COMP-016 WriteGate.classify(content) ──[Red?]── reject (error.kind=invariant)
  → COMP-012 MemoryRecord.build(content, meta)
  → COMP-015 Signer.sign(record) → record.sig
  → COMP-011 Repository.write(layer="personal", record)
       └── git commit (op=add, record.id)
  → COMP-013 Index.upsert(record)         (FTS5 + HNSW)
  → COMP-019 Log.emit(level=info, op=add, record_id, latency_ms)
```

## Query Flow

```text
Client → COMP-001/002 → COMP-005 (Query)
  → COMP-017 Config (top_k, weights)
  → COMP-013 Index.fts5_search(q) → cands_lex
  → COMP-014 Embedder.encode(q) → q_emb
  → COMP-013 Index.hnsw_search(q_emb) → cands_vec
  → COMP-005 hybrid_rank(cands_lex, cands_vec, layer_order)
  → return top-k with provenance.layer
  → COMP-019 Log.emit(op=query, latency_ms, k)
```

## Verify Flow

```text
COMP-006 → for each record in personal/:
  COMP-012 parse frontmatter
  COMP-015 verify sig
  validate links target ids exist (or are tombstones)
emit summary; exit 0 iff all pass.
```

## Forget Flow

```text
COMP-001 → COMP-007 Forget(record_id, cascade?)
  → check incoming causal links (block if any && !cascade)
  → COMP-011 write tombstone record (op=forget)
  → COMP-013 Index.delete(record_id)
  → COMP-019 Log.emit(op=forget, record_id, cascaded_n)
```

## MCP Round-Trip Budget

| Step | Budget |
| ------ | -------- |
| Stdio request decode | <5 ms |
| Service work | <140 ms |
| Stdio response encode | <5 ms |
| Total p95 | ≤ 200 ms (R-046, US-007 AC-2) |

## Failure Modes

| Stage | Failure | error.kind | retriable |
| ------- | --------- | ------------ | ----------- |
| Config load | malformed YAML | config | false |
| Signing | missing key | auth | false |
| Write-gate | red-class match | invariant | false |
| Repository write | git lock contention | transient | true |
| Repository write | submodule missing | config | false |
| Index upsert | hnsw rebuild needed | transient | true |
| Query | embedder unavailable | (warn, BM25 fallback) | n/a |
| Verify | sig mismatch | auth | false |
| Forget | causal links present | conflict | false |

## Iter-2 Update (2026-05-06)

### Roots auto-scope flow (R-051)

```text
MCP host  --[initialize, capabilities.roots]-->  aimem-mcp (COMP-007)
aimem-mcp --[roots/list]-->                       MCP host
MCP host  --[roots: file:///path/to/repo, ...]--> aimem-mcp
Write tool call:
  aimem-mcp resolves active layer from Roots via COMP-024.
  No resolvable Root → error.kind=invariant ("no resolvable layer from roots").
  Resolved → forwarded to COMP-002 (CRUD) under COMP-023 (LockManager).
```

### Elicitation consent flow (R-051, write-down)

```text
layer promote / demote / inbox approve / tombstone
  ↓
COMP-024.elicitation.create(prompt, schema)
  → host UI presents consent
  → user accepts → proceed under LockManager
  → user declines → error.kind=auth, no fs mutation, structured log to stderr
```

### Sampling flow (R-051, restricted)

```text
evolve / compact / DP-promote summarize
  ↓
COMP-024.sampling.create(prompt, toolChoice="none")
  → host LLM returns text only (no tool dispatch)
  → result stored as derived note via COMP-002 under LockManager
```

No other handler imports the sampling helper (asserted by an import-graph unit test).

### Tasks flow (R-051, `memory_sync`)

```text
client supports Tasks?
  yes → aimem-mcp returns Task handle, performs sync in background, polling cadence ≥ 250 ms
  no  → synchronous fallback (existing R-042 path)
```

### Hook capture / recall flow (R-052)

```text
host agent (Claude Code / Copilot CLI / Codex CLI)
  ↓ (configured hook)
shell exec: aimem add|query --json (env: AIMEM_CALLER_ROLE=hook)
  ↓
COMP-001 (CLI parser):
  if AIMEM_CALLER_ROLE=hook:
    deny --layer team|project, deny destructive subcommands  (AC-US052-1)
    force --json output                                       (AC-US052-4)
    wrap in 1 s wall-clock SIGTERM                            (AC-US052-2)
  ↓
COMP-002 (CRUD) under COMP-023 (LockManager) → git transaction → JSON to stdout
```

### Embed provider switch flow (R-053)

```text
user edits ~/.ai-memory/.aimem.yaml: embed.provider = openai
  ↓
aimem doctor --reembed:
  COMP-022 selects new provider, validates api_key_env
  COMP-006 starts new index generation
  Old generation continues serving reads until warm-up complete
  Switch atomic via index-generation pointer flip
```

### Concurrency / lock flow (R-054)

```text
any write:
  COMP-023.acquire(lock.timeout_ms=100)
    success → perform git transaction → release
    timeout → error.kind=conflict, retriable=true
No module-global retains repo / index handles across requests.
```

### Iter-2 error-kind mapping (additions)

| Operation | Failure | Kind | retriable |
| ----------- | --------- | ------ | ----------- |
| MCP initialize | unsupported protocolVersion | invariant | false |
| Roots resolve | no Root for write tool | invariant | false |
| Elicitation | user declines | auth | false |
| Hook write | `--layer team\|project` requested | auth | false |
| Hook destructive | promote/demote/inbox/tombstone requested | auth | false |
| Hook budget | wall clock > 1 s | transient | true |
| Embed remote | unreachable / timeout | transient | true |
| Embed config | missing api_key env var | invariant | false |
| Lock | timeout > `lock.timeout_ms` | conflict | true |
