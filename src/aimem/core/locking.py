"""flock(2) per-request file locking (R-054, design.md §12).

Every write operation acquires an exclusive lock on
``~/.ai-memory/.aimem.lock`` before touching the repo.  If the lock
cannot be acquired within ``lock.timeout_ms``, an ``error.kind=conflict``
is raised so callers can surface a useful error instead of silently
queueing or deadlocking.

Usage::

    with acquire_lock(memory_dir, timeout_ms=5000):
        record.to_file(path)
        repo.commit(...)
"""

from __future__ import annotations

import fcntl
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from aimem.core.error import ConflictError


@contextmanager
def acquire_lock(
    memory_dir: Path, *, timeout_ms: int = 5000
) -> Generator[None, None, None]:
    """Context manager that holds an exclusive flock for the duration.

    Raises ``ConflictError`` if the lock cannot be acquired within
    *timeout_ms* milliseconds.
    """
    lock_path = memory_dir / ".aimem.lock"
    lock_path.touch(exist_ok=True)

    deadline = time.monotonic() + timeout_ms / 1000.0
    fd = lock_path.open("w")
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    fd.close()
                    raise ConflictError(
                        "Could not acquire aimem lock within "
                        f"{timeout_ms} ms — another process holds it.",
                        detail=str(lock_path),
                    )
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        fd.close()
