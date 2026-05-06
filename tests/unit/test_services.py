"""Integration tests for add_note service + query (US-002, US-003 criteria)."""
from __future__ import annotations

from pathlib import Path

import pytest

from aimem.core.schema import Layer, MemoryType
from aimem.core.services.add import add_note
from aimem.core.services.query import query
from aimem.core.services.verify import verify


class TestAddNote:
    def test_add_note_creates_record(self, tmp_path: Path):
        from aimem.core.repository import LayerRepo
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)

        rec = add_note(
            memory_dir=tmp_path,
            layer=Layer.PERSONAL,
            memory_type=MemoryType.OBSERVATION,
            title="Test observation",
            body="The sky is blue",
            tags=["nature"],
            agent="pytest",
        )
        assert rec.id
        assert rec.title == "Test observation"
        assert "nature" in rec.tags

    def test_add_note_signs_record(self, tmp_path: Path):
        from aimem.core.repository import LayerRepo
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)

        rec = add_note(
            memory_dir=tmp_path,
            layer=Layer.PERSONAL,
            memory_type=MemoryType.KNOWLEDGE,
            title="Signed observation",
            body="Something important",
            agent="pytest",
        )
        assert rec.sig != "", "record should be signed"

    def test_add_note_rejects_secrets(self, tmp_path: Path):
        from aimem.core.repository import LayerRepo
        from aimem.core.error import InvariantError
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)

        with pytest.raises(InvariantError):
            add_note(
                memory_dir=tmp_path,
                layer=Layer.PERSONAL,
                memory_type=MemoryType.OBSERVATION,
                title="Leaks a token",
                body="My secret: AKIAIOSFODNN7EXAMPLE",
                agent="pytest",
            )


class TestQuery:
    def test_query_returns_results(self, tmp_path: Path):
        from aimem.core.repository import LayerRepo
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)

        add_note(memory_dir=tmp_path, layer=Layer.PERSONAL, memory_type=MemoryType.KNOWLEDGE,
                 title="Python typing module", body="Use TypeVar for generic types in Python.", agent="pytest")
        add_note(memory_dir=tmp_path, layer=Layer.PERSONAL, memory_type=MemoryType.KNOWLEDGE,
                 title="Git rebase workflow", body="Always rebase before pushing to main.", agent="pytest")

        results = query(memory_dir=tmp_path, q="Python generics", layer=Layer.PERSONAL)
        assert len(results) > 0
        top = results[0]
        assert "python" in top.record.title.lower() or "python" in (top.record.body or "").lower()

    def test_query_empty_store(self, tmp_path: Path):
        from aimem.core.repository import LayerRepo
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)

        results = query(memory_dir=tmp_path, q="anything", layer=Layer.PERSONAL)
        assert results == []


class TestVerify:
    def test_verify_clean_store(self, tmp_path: Path):
        from aimem.core.repository import LayerRepo
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)

        add_note(memory_dir=tmp_path, layer=Layer.PERSONAL, memory_type=MemoryType.OBSERVATION,
                 title="Clean record", body="Nothing suspicious.", agent="pytest")

        report = verify(memory_dir=tmp_path, layer=Layer.PERSONAL)
        assert report.ok

    def test_verify_empty_store(self, tmp_path: Path):
        from aimem.core.repository import LayerRepo
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        report = verify(memory_dir=tmp_path, layer=Layer.PERSONAL)
        assert report.ok

    def test_verify_strict_mode(self, tmp_path: Path):
        from aimem.core.repository import LayerRepo
        repo = LayerRepo(tmp_path)
        repo.init(tmp_path)
        add_note(memory_dir=tmp_path, layer=Layer.PERSONAL, memory_type=MemoryType.KNOWLEDGE,
                 title="Signed note", body="Verifiable.", agent="pytest")
        report = verify(memory_dir=tmp_path, layer=Layer.PERSONAL, strict=True)
        assert report.ok
