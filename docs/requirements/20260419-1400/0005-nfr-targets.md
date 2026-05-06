# Non-Functional Requirements

Spec-Version: 20260419-1400
Source: req-clarifier

## Performance

| Metric | Target | Measurement Method |
| -------- | -------- | ------------------- |
| Note CRUD operations | Best-effort; optimize based on real usage | Manual benchmarking with pytest-benchmark |
| Search latency (BM25 + embedding) | Best-effort; must remain interactive for up to 10,000 notes | Manual benchmarking with corpus of 10,000 notes |
| Index rebuild time | Best-effort; `aimem graph` and search index rebuild should complete in reasonable time for 10,000 notes | Manual benchmarking |
| Export generation | Best-effort; should complete within seconds for typical adapter configs | Manual testing |
| Scale ceiling | Must handle up to ~10,000 notes per repository without degradation | Automated scale test with synthetic corpus |

## Reliability

| Metric | Target | Measurement Method |
| -------- | -------- | ------------------- |
| Data integrity | All writes are atomic (fully committed to git or rolled back) | Integration tests with failure injection |
| Graceful degradation | If embedding model unavailable, search falls back to BM25-only | Integration test with mock unavailable model |
| Error reporting | All CLI commands exit with non-zero code on error, with actionable message | E2E test suite |
| Git state consistency | No partial file state after any interrupted operation | Integration tests with signal interruption |

## Accessibility

| Standard | Level | Compliance Method |
| ---------- | ------- | ------------------- |
| Terminal screen reader compatibility | Nice-to-have (not required) | Manual testing with terminal screen readers |
| CLI output structure | No excessive ANSI escape codes; clean text output | Code review |

## Internationalization

| Requirement | Details |
| ------------- | --------- |
| CLI messages | Internationalized using i18n message catalogs |
| Supported locales | English (primary) at launch; framework supports additional locales |
| Note content encoding | UTF-8; supports any language/charset including CJK, Cyrillic, RTL scripts |
| Date/Time formatting | ISO 8601 (YYYY-MM-DD) in frontmatter; locale-aware display in CLI output |
| Tag normalization | Lowercase ASCII-safe; Unicode tags preserved in content |

## Observability

### Dashboards & Metrics

| Metric/Dashboard | Audience | Purpose | Related ReqIDs |
| ------------------ | ---------- | --------- | ---------------- |
| `aimem status` output | Repository Owner (ROLE-001) | Note counts by type, repository health summary | R-002, R-009 |
| `aimem doctor` report | Repository Owner (ROLE-001) | Comprehensive health: broken links, stale notes, duplicates, injection patterns, stale index | R-023 |

### Alerts

| Alert | Condition | Severity | Response | Related ReqIDs |
| ------- | ----------- | ---------- | ---------- | ---------------- |
| Stale index warning | Search index last_built older than newest note's updated date | Warning | `aimem doctor` surfaces it; user rebuilds index | R-023 |
| Stale notes | Notes not accessed in > stale_months (default 6) | Info | `aimem doctor` lists them; user decides to prune or update | R-023, R-018 |
| Injection pattern detected | Note content matches known injection patterns | Warning | `aimem doctor` flags it; user reviews and removes | R-020, R-023 |
| Unsigned commits | Commits without GPG/SSH signature in team repo | Warning | `aimem doctor` reports; team lead investigates | R-022, R-023 |

### Logging Requirements

| Log Type | Retention | Purpose | Related ReqIDs |
| ---------- | ----------- | --------- | ---------------- |
| Structured JSONL logs | Local filesystem; user-managed rotation | Programmatic analysis, debugging, audit trail | R-027 |
| Git commit history | Permanent (git) | Data provenance, change tracking, blame | R-005 |
| Debug logs (--verbose) | Session only (stderr) | Interactive troubleshooting | R-027 |

### SLIs/SLOs (Service Level Indicators/Objectives)

| SLI | SLO Target | Measurement | Related ReqIDs |
| ----- | ------------ | ------------- | ---------------- |
| CLI command success rate | 100% for valid inputs (no crashes) | Automated test suite | R-009 |
| Data integrity (atomic writes) | 100% (zero partial commits) | Integration tests with failure injection | R-005 |
| Search recall at 10,000 notes | Best-effort; no formal target (optimize post-launch) | Benchmark with labeled test corpus | R-011 |
| Token efficiency per query | Target ~1,294 tokens (Memori benchmark) | Instrumented search path | R-012, R-013 |
