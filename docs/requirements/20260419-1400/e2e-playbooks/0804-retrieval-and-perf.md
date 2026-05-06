# Playbooks — Retrieval Fallback & Performance Gates

Spec-Version: 20260419-1400
Source: e2e-playbook-generator
Document-Range: 0800-0899

## PB-007 Hybrid retrieval falls back to BM25 when embedder unavailable

**Trace**: US-005 AC-4, R-011.

**Preconditions**: initialized AIMEM_DIR with bench_corpus seeded.

**Steps**:

1. Set `AIMEM_DISABLE_EMBED=1` (test hook) or point `embed.model` to a non-existent path.
2. Run `aimem query "test prompt" --json`.
3. Assert exit 0.
4. Assert one log line at `level=warning op=query reason=embed_unavailable`.
5. Assert results are returned (BM25-only ranking) rather than an error.

**Expected**: Graceful degradation; never silent failure.

## PB-008 Performance gate: query / add / MCP RTT under §10 budgets

**Trace**: US-005, US-007, US-012, R-046.

**Preconditions**: bench_corpus seeded; warm caches.

**Steps**:

1. Run `pytest tests/e2e/test_perf.py --benchmark-only`.
2. Collect p95 metrics:
   - `query_p95_ms`
   - `add_p95_ms`
   - `mcp_query_rtt_p95_ms`
   - `cold_start_ms`
3. Assert:
   - `query_p95_ms ≤ 150`
   - `add_p95_ms ≤ 200`
   - `mcp_query_rtt_p95_ms ≤ 200`
   - `cold_start_ms ≤ 1500`
4. Compare to baseline file `tests/e2e/perf_baseline.json`. Fail if any metric regresses by > 10 %.

**Expected**: Budgets met; no regression beyond tolerance.
