# Definition of Ready / Done

Spec-Version: 20260419-1400
Source: story-generator
Document-Range: 0200-0299

## Definition of Ready (DoR)

A user story is **Ready** when:

1. ID is stable (US-XXX), title is one sentence, role is from 0003.
2. Traces to ≥1 R-ID and ≥1 workflow.
3. Has ≥3 ACs, each with TestLevel ∈ {Unit, Smoke, E2E}.
4. Forward links to scenarios in 0002 are listed in 0202.
5. No "TBD" tokens.

## Definition of Done (DoD)

A user story is **Done** when:

1. All ACs pass at the stated TestLevel.
2. Code is type-checked (mypy clean) and passes ruff/black/isort.
3. Performance ACs (p95) verified under the §10 budget on the CI bench.
4. Logging ACs (R-027) verified — no body content in logs.
5. Security ACs verified — gitleaks clean; no Red-class data in fixtures.
6. PR includes the relevant 0007 traceability cell update.

## Story Splitting Rule

If any story exceeds **3 workflows OR 7 ACs OR 2 personas OR 2 integrations**, split it before development begins.
