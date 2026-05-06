"""Write gate — content classifier and layer enforcer (R-040, design.md §8).

Every ``aimem add`` invocation (CLI or MCP) passes through this gate
before any file is written.  The gate:

1. Scans the title + body for known secret patterns (AWS keys, GH tokens,
   private keys, etc.) and raises ``InvariantError`` on a match.
2. Enforces layer write permissions for hook callers
   (``AIMEM_CALLER_ROLE=hook`` may only write to ``personal``).

Secrets are **rejected** (not quarantined) because writing them — even
to a gitignored area — risks accidental exposure.
"""

from __future__ import annotations

import os
import re

from aimem.core.error import AuthError, InvariantError
from aimem.core.schema import Layer, MemoryRecord

# ---------------------------------------------------------------------------
# Secret-pattern catalogue (gitleaks-style, conservative subset)
# ---------------------------------------------------------------------------
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    # AWS access key
    re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
    # AWS secret key (heuristic: 40-char base64-ish after context keyword)
    re.compile(r"aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*[A-Za-z0-9+/]{40}", re.IGNORECASE),
    # GitHub personal access token (classic)
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    # GitHub fine-grained PAT
    re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
    # GitHub OAuth token
    re.compile(r"gho_[A-Za-z0-9]{36}"),
    # GitHub Actions token
    re.compile(r"ghs_[A-Za-z0-9]{36}"),
    # Slack token
    re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}"),
    # Generic high-entropy password field
    re.compile(r"(?:password|passwd|secret|token|apikey|api_key)\s*[=:]\s*['\"]?[A-Za-z0-9+/=_\-]{20,}['\"]?", re.IGNORECASE),
    # Private key header
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
]


def _scan_secrets(text: str) -> str | None:
    """Return the first matched pattern name, or None if clean."""
    for pattern in _SECRET_PATTERNS:
        m = pattern.search(text)
        if m:
            return pattern.pattern[:60]
    return None


# ---------------------------------------------------------------------------
# Layer write-permission rules
# ---------------------------------------------------------------------------

# Hook callers (AIMEM_CALLER_ROLE=hook) may only write to personal layer
_HOOK_WRITABLE_LAYERS = {Layer.PERSONAL}


def check_write(record: MemoryRecord) -> None:
    """Gate a record before it is written.

    Raises ``InvariantError`` on secret detection or schema problems.
    Raises ``AuthError`` on layer permission violations.
    """
    full_text = f"{record.title}\n{record.body}"

    matched = _scan_secrets(full_text)
    if matched:
        raise InvariantError(
            "Record rejected by write gate: potential secret detected.",
            detail=f"Matched pattern: {matched!r}",
        )

    # Hook-caller layer restriction
    caller_role = os.environ.get("AIMEM_CALLER_ROLE", "")
    if caller_role == "hook" and record.layer not in _HOOK_WRITABLE_LAYERS:
        raise AuthError(
            f"Hook callers may not write to layer '{record.layer.value}'.",
            detail="Set AIMEM_CALLER_ROLE to a non-hook value or use personal layer.",
        )
