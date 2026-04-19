"""Tests for the MemoryRepository."""

from __future__ import annotations

from pathlib import Path

import pytest

from aimem.core.note import MemoryType
from aimem.core.repository import MemoryRepository


@pytest.fixture
def repo(tmp_path: Path) -> MemoryRepository:
    """Create a fresh memory repository in a temp directory."""
    repo = MemoryRepository(root=tmp_path / ".ai-memory")
    repo.init()
    return repo


class TestMemoryRepository:
    def test_init_creates_structure(self, repo: MemoryRepository) -> None:
        assert repo.is_initialized
        assert (repo.root / "identity").is_dir()
        assert (repo.root / "knowledge").is_dir()
        assert (repo.root / "procedures").is_dir()
        assert (repo.root / "journal").is_dir()
        assert (repo.root / ".links").is_dir()
        assert (repo.root / ".archive").is_dir()
        assert (repo.root / ".hot").is_dir()
        assert (repo.root / ".gitignore").exists()
        assert (repo.root / ".aimem.yaml").exists()

    def test_add_and_get_note(self, repo: MemoryRepository) -> None:
        note = repo.add_note(
            memory_type=MemoryType.KNOWLEDGE,
            title="Python Tips",
            body="Use f-strings for formatting.",
            tags=["python", "tips"],
        )

        assert note.path.exists()
        assert note.meta.type == MemoryType.KNOWLEDGE

        loaded = repo.get_note(str(note.path.relative_to(repo.root)))
        assert loaded is not None
        assert loaded.title == "Python Tips"
        assert "f-strings" in loaded.body

    def test_list_notes_by_type(self, repo: MemoryRepository) -> None:
        repo.add_note(
            memory_type=MemoryType.IDENTITY,
            title="Profile",
            body="Senior developer",
            tags=["profile"],
        )
        repo.add_note(
            memory_type=MemoryType.KNOWLEDGE,
            title="Python",
            body="Python 3.12+",
            tags=["python"],
        )

        identity_notes = repo.list_notes(memory_type=MemoryType.IDENTITY)
        assert len(identity_notes) == 1
        assert identity_notes[0].title == "Profile"

        all_notes = repo.list_notes()
        assert len(all_notes) == 2

    def test_remove_note_archives(self, repo: MemoryRepository) -> None:
        note = repo.add_note(
            memory_type=MemoryType.JOURNAL,
            title="Test Session",
            body="Did some testing.",
            tags=["test"],
        )
        rel_path = str(note.path.relative_to(repo.root))

        result = repo.remove_note(rel_path)
        assert result is True
        assert not note.path.exists()
        assert (repo.root / ".archive" / rel_path).exists()

    def test_get_nonexistent_note_returns_none(self, repo: MemoryRepository) -> None:
        assert repo.get_note("does/not/exist.md") is None

    def test_remove_nonexistent_returns_false(self, repo: MemoryRepository) -> None:
        assert repo.remove_note("does/not/exist.md") is False
