"""Integration tests for LayerRepo (US-001, US-013, US-002 acceptance criteria)."""
from __future__ import annotations

from pathlib import Path

import pytest

from aimem.core.repository import LayerRepo
from aimem.core.schema import Layer, MemoryType, MemoryRecord, Provenance, Links, ForgettingPolicy
from aimem.core.error import NotFoundError


def _make_record(title: str = "Test note", **kwargs) -> MemoryRecord:
    defaults = dict(
        type=MemoryType.OBSERVATION,
        layer=Layer.PERSONAL,
        title=title,
        body="Test body",
        tags=["unit-test"],
        links=Links(),
        forgetting=ForgettingPolicy(),
        provenance=Provenance(agent="pytest"),
    )
    defaults.update(kwargs)
    return MemoryRecord(**defaults)


class TestLayerRepoInit:
    def test_init_creates_directory(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        assert not repo.is_initialized
        repo.init(tmp_path)
        assert repo.is_initialized

    def test_init_is_idempotent(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        repo.init(tmp_path)  # Should not raise
        assert repo.is_initialized


class TestLayerRepoWrite:
    def test_write_creates_file(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        rec = _make_record()
        repo.write(rec)
        path = repo.layer_path(Layer.PERSONAL) / rec.type.value / f"{rec.id}.md"
        assert path.exists()

    def test_write_is_readable(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        rec = _make_record(title="Writable record")
        repo.write(rec)
        loaded = repo.get(rec.id)
        assert loaded.title == "Writable record"

    def test_get_raises_not_found(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        with pytest.raises(NotFoundError):
            repo.get("NONEXISTENT00000000000000")


class TestLayerRepoList:
    def test_list_returns_written_records(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        for i in range(3):
            repo.write(_make_record(title=f"Note {i}"))
        records = repo.list_records()
        assert len(records) == 3

    def test_list_filters_by_type(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        repo.write(_make_record(type=MemoryType.OBSERVATION))
        repo.write(_make_record(type=MemoryType.KNOWLEDGE))
        obs = repo.list_records(memory_type=MemoryType.OBSERVATION)
        assert all(r.type == MemoryType.OBSERVATION for r in obs)

    def test_list_filters_by_tag(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        repo.write(_make_record(tags=["alpha"]))
        repo.write(_make_record(tags=["beta"]))
        result = repo.list_records(tags=["alpha"])
        assert len(result) == 1
        assert "alpha" in result[0].tags


class TestLayerRepoTag:
    def test_add_tag(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        rec = _make_record(tags=[])
        repo.write(rec)
        updated = repo.tag_record(rec.id, ["new-tag"], [])
        assert "new-tag" in updated.tags

    def test_remove_tag(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        rec = _make_record(tags=["old-tag"])
        repo.write(rec)
        updated = repo.tag_record(rec.id, [], ["old-tag"])
        assert "old-tag" not in updated.tags


class TestLayerRepoLink:
    def test_create_link(self, tmp_path: Path):
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        r1 = _make_record(title="Source")
        r2 = _make_record(title="Target")
        repo.write(r1)
        repo.write(r2)
        repo.link_records(r1.id, r2.id, "causal")
        updated = repo.get(r1.id)
        assert r2.id in updated.links.causal
