"""Unit tests for aimem v1 schema (US-001 acceptance criteria)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from aimem.core.schema import (
    ForgettingPolicy,
    Layer,
    Links,
    MemoryRecord,
    MemoryType,
    Provenance,
)


def _make_record(**kwargs) -> MemoryRecord:
    defaults = dict(
        type=MemoryType.OBSERVATION,
        layer=Layer.PERSONAL,
        title="Test note",
        body="Hello world",
        tags=["test"],
        links=Links(),
        forgetting=ForgettingPolicy(),
        provenance=Provenance(agent="pytest"),
    )
    defaults.update(kwargs)
    return MemoryRecord(**defaults)


class TestMemoryRecordCreation:
    def test_creates_with_auto_ulid(self):
        rec = _make_record()
        assert rec.id, "id must not be empty"
        assert len(rec.id) == 26, "ULID should be 26 chars"

    def test_schema_version_is_one(self):
        rec = _make_record()
        assert rec.schema_version == 1

    def test_timestamps_present(self):
        rec = _make_record()
        assert rec.created_at
        assert rec.updated_at

    def test_all_memory_types(self):
        for mt in MemoryType:
            rec = _make_record(type=mt)
            assert rec.type == mt

    def test_all_layers(self):
        for layer in Layer:
            rec = _make_record(layer=layer)
            assert rec.layer == layer

    def test_empty_sig_by_default(self):
        rec = _make_record()
        assert rec.sig == ""


class TestMemoryRecordDiskIO:
    def test_round_trip(self, tmp_path: Path):
        rec = _make_record(title="Round trip", body="Some content")
        rec_path = tmp_path / "record.md"
        rec.to_file(rec_path)
        assert rec_path.exists()

        loaded = MemoryRecord.from_file(rec_path)
        assert loaded.id == rec.id
        assert loaded.title == rec.title
        assert loaded.body == rec.body

    def test_frontmatter_contains_id(self, tmp_path: Path):
        rec = _make_record(title="Frontmatter test")
        rec_path = tmp_path / "fm.md"
        rec.to_file(rec_path)
        content = rec_path.read_text()
        assert rec.id in content


class TestLinks:
    def test_default_empty_links(self):
        rec = _make_record()
        assert rec.links.causal == []
        assert rec.links.evolves == []
        assert rec.links.refines == []

    def test_links_are_set(self):
        links = Links(causal=["01ARZ3NDEKTSV4RRFFQ69G5FAV"])
        rec = _make_record(links=links)
        assert "01ARZ3NDEKTSV4RRFFQ69G5FAV" in rec.links.causal


class TestCanonicalBytes:
    def test_excludes_sig_and_body(self):
        rec = _make_record(body="should not appear")
        canonical = rec.canonical_bytes()
        data = json.loads(canonical)
        assert "sig" not in data
        assert "body" not in data

    def test_deterministic(self):
        rec = _make_record()
        assert rec.canonical_bytes() == rec.canonical_bytes()
