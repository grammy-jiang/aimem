"""Stable error taxonomy for aimem (R-045).

Every AimemError carries an ``error.kind`` string that is part of the
public contract between the CLI, the MCP server, and any MCP client.
"""

from __future__ import annotations


class AimemError(Exception):
    """Base for all aimem errors.  Always carries a ``kind`` tag."""

    kind: str = "unknown"

    def __init__(self, message: str, *, detail: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def as_dict(self) -> dict[str, str]:
        d: dict[str, str] = {"kind": self.kind, "message": self.message}
        if self.detail:
            d["detail"] = self.detail
        return d


class ConfigError(AimemError):
    """Bad or missing .aimem.yaml field.  Not retriable."""

    kind = "config"


class AuthError(AimemError):
    """Signature, key, or remote-auth failure.  Not retriable."""

    kind = "auth"


class ConflictError(AimemError):
    """Git merge conflict during sync, or flock timeout.  Retriable after resolve."""

    kind = "conflict"


class QuarantineError(AimemError):
    """Inbox entry not yet approved.  Not retriable."""

    kind = "quarantine"


class NotFoundError(AimemError):
    """Record, layer, or tag missing.  Not retriable."""

    kind = "not_found"


class InvariantError(AimemError):
    """Schema or IFC violation.  Not retriable."""

    kind = "invariant"


class TransientError(AimemError):
    """I/O, network, or timeout.  Retriable."""

    kind = "transient"
