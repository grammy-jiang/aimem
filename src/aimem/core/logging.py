"""Structured JSONL logging for aimem (R-027, design.md §11).

All application-level events are emitted as JSON lines to *stderr* so
that:
  - CLI users see them when ``--verbose`` is passed.
  - MCP hosts (per MCP 2025-11-25) pick them up from the server's
    stderr stream and forward to their own log sink.
  - A local copy lands in ``~/.agent/logs/aimem.jsonl`` for audit.

Usage::

    from aimem.core.logging import get_logger

    log = get_logger(__name__)
    log.info("op", op="add", layer="personal", record_id="01ARZ3...")
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict[str, Any] = {
            "ts": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
            ),
            "level": record.levelname.lower(),
            "logger": record.name,
        }

        # Pull structured kwargs stored by _StructuredLogger
        extra = getattr(record, "_structured", {})
        payload.update(extra)

        # The positional message (op description or fallback text)
        if record.getMessage():
            payload.setdefault("msg", record.getMessage())

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class _StructuredLogger:
    """Thin wrapper that accepts keyword arguments as structured fields."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _log(
        self, level: int, msg: str, **kwargs: Any
    ) -> None:
        extra = {"_structured": kwargs}
        self._logger.log(level, msg, extra=extra, stacklevel=3)

    def debug(self, msg: str = "", **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str = "", **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str = "", **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str = "", **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)


_configured = False


def configure(verbose: bool = False) -> None:
    """Install the JSON formatter on the root logger (call once at startup)."""
    global _configured
    if _configured:
        return
    _configured = True

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)


def get_logger(name: str) -> _StructuredLogger:
    """Return a structured logger for *name*."""
    return _StructuredLogger(logging.getLogger(name))
