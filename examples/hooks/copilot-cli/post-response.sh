#!/usr/bin/env bash
# examples/hooks/copilot-cli/post-response.sh
# Copilot CLI post-response hook: captures user-approved observations.
# Only runs when the env var AIMEM_CAPTURE is set to a non-empty value.

set -euo pipefail
export AIMEM_CALLER_ROLE=hook

if [ -z "${AIMEM_CAPTURE:-}" ]; then
    exit 0
fi

TIMEOUT_CMD="timeout"
if ! command -v timeout &>/dev/null; then
    TIMEOUT_CMD="gtimeout"
fi

$TIMEOUT_CMD 1 aimem add \
    --type observation \
    --title "Captured from Copilot CLI session" \
    --body "${AIMEM_CAPTURE}" \
    --tag "copilot-cli" \
    --tag "auto" \
    2>/dev/null || true

exit 0
