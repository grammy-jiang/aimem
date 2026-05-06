# Playbooks — Forget & Migrate

Spec-Version: 20260419-1400
Source: e2e-playbook-generator
Document-Range: 0800-0899

## PB-005 Forget tombstones a record

**Trace**: US-016, R-044. Scenarios: SCN-WF005-NEG-03.

**Preconditions**: initialized AIMEM_DIR; one note A; one note B with `links.causal -> A`.

**Steps**:

1. Run `aimem forget <A.id>` (no `--cascade`). Assert exit ≠ 0 with `error.kind=conflict` (incoming causal link).
2. Run `aimem forget <A.id> --cascade`. Assert exit 0.
3. Run `aimem get <A.id>`. Assert `error.kind=not_found`.
4. Run `aimem show --include-tombstones <A.id>`. Assert returns tombstone with `op=forget` and lists `cascaded_ids` containing `<B.id>` (or B is also tombstoned, per cascade policy).
5. Run `aimem query "<A's title>"`. Assert A is absent from results.

**Expected**: Forget is gated, auditable, and removes the record from active retrieval.

## PB-006 Migrate dry-run reports without writing

**Trace**: US-010, R-038.

**Preconditions**: initialized AIMEM_DIR; ≥1 record at current schema_version=1; a fake migrator targeting v2 registered for the test.

**Steps**:

1. Snapshot HEAD commit of `personal/`.
2. Run `aimem migrate --to 2 --dry-run`. Assert exit 0; stdout reports `would_change=N` for some N>0.
3. Assert `git status` clean and HEAD unchanged.
4. Run `aimem migrate --to 2`. Assert exit 0; new commits authored; all records now `schema_version=2`.
5. Attempt `aimem migrate --to 1` (downgrade). Assert exit ≠ 0; `error.kind=invariant`.

**Expected**: Dry-run is read-only; real migrate forward only; downgrade blocked.
