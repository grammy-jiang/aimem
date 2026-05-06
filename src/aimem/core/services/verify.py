"""verify service — schema validation, signature check, orphan link detection (US-006).

``aimem verify`` exits 0 on a clean store.
``aimem verify --strict`` additionally checks all signatures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aimem.core import logging as _logging
from aimem.core.repository import LayerRepo
from aimem.core.schema import Layer, MemoryRecord
from aimem.core.signing import verify_record

log = _logging.get_logger(__name__)


@dataclass
class VerifyFinding:
    record_id: str
    kind: str  # "schema", "sig", "orphan_link"
    message: str


@dataclass
class VerifyReport:
    ok: bool
    findings: list[VerifyFinding] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "findings": [
                {"record_id": f.record_id, "kind": f.kind, "message": f.message}
                for f in self.findings
            ],
        }


def verify(
    *,
    memory_dir: Path,
    layer: Layer = Layer.PERSONAL,
    strict: bool = False,
) -> VerifyReport:
    """Run the verify suite and return a report.

    :param strict: also verify ed25519 signatures.
    """
    repo = LayerRepo(memory_dir)
    findings: list[VerifyFinding] = []

    try:
        records = repo.list_records(layer=layer)
    except Exception as exc:
        return VerifyReport(
            ok=False,
            findings=[VerifyFinding("*", "schema", f"Failed to list records: {exc}")],
        )

    # Build ID set for orphan detection
    id_set = {r.id for r in records}

    for rec in records:
        _check_schema(rec, findings)
        if strict:
            _check_sig(rec, memory_dir, findings)
        _check_links(rec, id_set, findings)

    ok = len(findings) == 0
    log.info(op="verify", layer=layer.value, ok=ok, findings=len(findings))
    return VerifyReport(ok=ok, findings=findings)


def _check_schema(rec: MemoryRecord, findings: list[VerifyFinding]) -> None:
    if rec.schema_version != 1:
        findings.append(
            VerifyFinding(rec.id, "schema", f"schema_version={rec.schema_version}, expected 1")
        )
    if not rec.id:
        findings.append(VerifyFinding(rec.id, "schema", "missing id field"))
    if not rec.title:
        findings.append(VerifyFinding(rec.id, "schema", "missing title field"))


def _check_sig(rec: MemoryRecord, memory_dir: Path, findings: list[VerifyFinding]) -> None:
    try:
        verify_record(rec, memory_dir)
    except Exception as exc:
        findings.append(VerifyFinding(rec.id, "sig", str(exc)))


def _check_links(rec: MemoryRecord, id_set: set[str], findings: list[VerifyFinding]) -> None:
    all_linked = (
        rec.links.causal + rec.links.evolves + rec.links.refines
    )
    for lid in all_linked:
        if lid not in id_set:
            findings.append(
                VerifyFinding(rec.id, "orphan_link", f"linked id {lid!r} not found in layer")
            )
