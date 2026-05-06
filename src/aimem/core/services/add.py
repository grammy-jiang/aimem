"""AddNote service — orchestrate write path (US-002, R-002, R-038, R-039, R-040).

Pipeline::

    validate schema  →  check_write (gate)  →  sign  →  flock  →  write  →  commit
"""

from __future__ import annotations

import datetime
from pathlib import Path

from aimem.core.config import AimemConfig
from aimem.core.error import InvariantError
from aimem.core.gate import check_write
from aimem.core import logging as _logging
from aimem.core.locking import acquire_lock
from aimem.core.repository import LayerRepo
from aimem.core.schema import (
    ForgettingPolicy,
    Layer,
    Links,
    MemoryRecord,
    MemoryType,
    Provenance,
    SCHEMA_VERSION,
)
from aimem.core.signing import sign_record

log = _logging.get_logger(__name__)


def add_note(
    *,
    memory_dir: Path,
    layer: Layer = Layer.PERSONAL,
    memory_type: MemoryType,
    title: str,
    body: str = "",
    tags: list[str] | None = None,
    links: Links | None = None,
    forgetting: ForgettingPolicy | None = None,
    agent: str = "cli",
    session: str = "",
) -> MemoryRecord:
    """Add a new memory record.

    Returns the final signed, committed record.
    Raises ``InvariantError`` on validation / gate failures.
    """
    if not title.strip():
        raise InvariantError("title must not be empty", detail="schema invariant")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = MemoryRecord(
        schema_version=SCHEMA_VERSION,
        layer=layer,
        type=memory_type,
        title=title,
        body=body,
        tags=tags or [],
        links=links or Links(),
        forgetting=forgetting or ForgettingPolicy(),
        provenance=Provenance(agent=agent, session=session),
        created_at=now,
        updated_at=now,
    )

    # 1. Write gate (secret scan + layer permission)
    check_write(record)

    # 2. Sign
    signed = sign_record(record, memory_dir)

    # 3. Acquire lock + write + commit
    cfg = AimemConfig.load(memory_dir)
    repo = LayerRepo(memory_dir)

    with acquire_lock(memory_dir, timeout_ms=cfg.lock.timeout_ms):
        path = repo.write(signed)

    log.info(op="add", record_id=signed.id, layer=layer.value, latency_ms=0)
    return signed.model_copy(update={"path": path})
