# Playbooks — Bootstrap & Write-Gate

Spec-Version: 20260419-1400
Source: e2e-playbook-generator
Document-Range: 0800-0899

## PB-001 Cold install → init → add → query

**Trace**: US-001, US-002, US-005. Scenarios: SCN-WF001-HP-01, SCN-WF002-HP-01, SCN-WF003-HP-01.

**Preconditions**: clean `AIMEM_DIR=$tmp/.ai-memory`; aimem installed in test env.

**Steps**:

1. Run `aimem init --path "$AIMEM_DIR"`.
2. Assert exit 0; assert `$AIMEM_DIR/.aimem.yaml` exists; assert `$AIMEM_DIR/personal/.git` exists.
3. Run `aimem add --type preference --title "rebase pref" -- "Prefer rebase over merge for feature branches"`.
4. Capture stdout `id`. Assert exit 0; assert exactly one new file under `$AIMEM_DIR/personal/preference/`.
5. Run `aimem query "rebase or merge"` with `--top-k 5 --json`.
6. Assert the captured `id` appears in the result list.

**Expected**: All steps green; one structured log line per op.

## PB-002 Reject secret on add (write-gate)

**Trace**: US-002 AC-3, US-011, R-040, R-047. Scenario: SCN-WF002-NEG-04.

**Preconditions**: initialized AIMEM_DIR.

**Steps**:

1. Run `aimem add --type observation --title "creds" -- "AKIA1234567890ABCD12 secret=wJalrXUt..."`.
2. Assert exit ≠ 0; stderr (or json error) carries `error.kind=invariant`.
3. Assert no new file under `$AIMEM_DIR/personal/observation/`.
4. Stage a commit containing the same string in a fixture file; run `pre-commit run gitleaks --files <fixture>`. Assert non-zero exit.

**Expected**: Both the in-process write-gate and the gitleaks pre-commit reject the content.
