#!/usr/bin/env bash
# examples/hooks/codex-cli/pre-tool.sh
# Codex CLI pre-tool hook: fetches relevant context before each tool call.

set -euo pipefail
export AIMEM_CALLER_ROLE=hook

TIMEOUT_CMD="timeout"
if ! command -v timeout &>/dev/null; then
    TIMEOUT_CMD="gtimeout"
fi

TOOL_INPUT="${CODEX_TOOL_INPUT:-}"
if [ -z "$TOOL_INPUT" ]; then
    exit 0
fi

$TIMEOUT_CMD 1 aimem query --json "$(echo "$TOOL_INPUT" | head -c 200)" --top-k 3 2>/dev/null || true
exit 0
