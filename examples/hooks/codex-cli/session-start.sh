#!/usr/bin/env bash
# examples/hooks/codex-cli/session-start.sh
# Codex CLI session-start hook: preloads top memories for the session.

set -euo pipefail
export AIMEM_CALLER_ROLE=hook

TIMEOUT_CMD="timeout"
if ! command -v timeout &>/dev/null; then
    TIMEOUT_CMD="gtimeout"
fi

$TIMEOUT_CMD 1 aimem query --json "project context and user preferences" --top-k 5 2>/dev/null || true
exit 0
