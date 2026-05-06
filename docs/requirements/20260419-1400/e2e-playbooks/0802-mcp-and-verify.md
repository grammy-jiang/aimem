# Playbooks — MCP Round-Trip & Verification

Spec-Version: 20260419-1400
Source: e2e-playbook-generator
Document-Range: 0800-0899

## PB-003 MCP round-trip query under budget

**Trace**: US-007, R-010, R-046. Scenarios: SCN-WF003-HP-02.

**Preconditions**: initialized AIMEM_DIR with the bench_corpus seeded; `aimem-mcp` reachable over stdio.

**Steps**:

1. Connect MCP client; assert `serverInfo.protocolVersion == "2025-06-18"`.
2. Call `tools/list`. Assert presence of `memory_query, memory_add, memory_link, memory_tag, memory_layer_list, memory_layer_scope, memory_sync, memory_inbox` (P2 tools allowed to be present but no-op).
3. Issue 100 sequential `memory_query` calls with varied prompts.
4. Compute p95 wall-clock latency. Assert `p95 ≤ 200 ms`.
5. Inject one malformed payload (missing `q`). Assert error response carries `error.kind=invariant` and `retriable=false`.

**Expected**: Protocol pinned, tools advertised, latency budget met, error taxonomy correct.

## PB-004 Verify catches malformed signature

**Trace**: US-006, R-039.

**Preconditions**: initialized AIMEM_DIR with ≥1 record.

**Steps**:

1. Run `aimem verify`. Assert exit 0.
2. Mutate one record's `sig` field by flipping a byte (in-place edit).
3. Run `aimem verify`. Assert exit ≠ 0; assert structured output names the offending `record_id` and `error.kind=auth`.

**Expected**: Verifier rejects the tampered record without false positives elsewhere.
