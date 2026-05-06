# Traceability Audit - Orphans & Gaps Report

Spec-Version: 20260419-1400
Source: req-clarifier

## Orphan Requirements (ReqID with no mappings)

No orphan requirements identified.

## Orphan Workflows (Workflow with no ReqIDs)

No orphan workflows identified.

## Orphan Personas (Persona with no ReqIDs)

No orphan personas identified.

## Orphan Roles (Role with no permission mappings or ReqIDs)

No orphan roles identified.

## Scenario Coverage Gaps

No scenario coverage gaps identified. All Must-Have requirements that map to workflows have scenario coverage in each mapped workflow.

## Integration Coverage Gaps

No integration coverage gaps identified. All integrations are properly mapped.

## Data Entity Coverage Gaps

### Orphan Data Entities (Defined but not referenced by any ReqID)

All data entities (E-XXX) are referenced by at least one requirement.

### Missing Data Entities (Referenced by ReqID but not defined)

All referenced entities have E-XXX IDs in the data dictionary.

## Audit Summary

| Check | Status | Orphan Count |
| ------- | -------- | -------------- |
| All R-XXX have >= 1 P-XXX mapping | Pass | 0 |
| All R-XXX have >= 1 WF-XXX mapping | Pass | 0 |
| All WF-XXX map to >= 1 R-XXX | Pass | 0 |
| All P-XXX map to >= 1 R-XXX | Pass | 0 |
| All ROLE-XXX used in permission matrix | Pass | 0 |
| All ROLE-XXX map to >= 1 R-XXX | Pass | 0 |
| All INT-XXX map to >= 1 R-XXX | Pass | 0 |
| All E-XXX entities referenced by >= 1 R-XXX | Pass | 0 |
| All R-XXX-referenced entities have E-XXX IDs | Pass | 0 |
| All R-XXX have scenario coverage in each mapped WF-XXX | Pass | 0 |
| No R-XXX violates split rule (>3 WF, >7 AC, >2 P, >2 INT) | Pass | 0 |
