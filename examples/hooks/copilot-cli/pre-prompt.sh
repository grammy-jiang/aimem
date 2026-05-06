#!/usr/bin/env bash
# examples/hooks/copilot-cli/pre-prompt.sh
# Copilot CLI pre-prompt hook: injects top-3 memories as context.
# Install: reference this script in your Copilot CLI extension config.
#
# SAFETY: runs as AIMEM_CALLER_ROLE=hook (untrusted layer) — write-downs rejected.
# WALL-CLOCK BOUND: aimem is expected to return in ≤1 s; script exits 0 on failure.

set -euo pipefail

# Wall-clock timeout guard (requires GNU timeout or gtimeout on macOS)
TIMEOUT_CMD="timeout"
if ! command -v timeout &>/dev/null; then
    TIMEOUT_CMD="gtimeout"
fi

export AIMEM_CALLER_ROLE=hook

RESULT=$(
    $TIMEOUT_CMD 1 aimem query --json "${COPILOT_PROMPT:-}" --top-k 3 2>/dev/null || echo "[]"
)

# Print as fenced block for the model to see
if [ "$RESULT" != "[]" ] && [ -n "$RESULT" ]; then
    echo "<!-- aimem memories -->"
    echo "$RESULT"
    echo "<!-- /aimem memories -->"
fi

exit 0
