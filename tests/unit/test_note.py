"""Tests for the Note model."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from aimem.core.note import Confidence, MemoryType, Note, NoteMeta


class TestNoteMeta:
    def test_defaults(self) -> None:
        meta = NoteMeta(type=MemoryType.KNOWLEDGE, tags=["python"])
        assert meta.type == MemoryType.KNOWLEDGE
        assert meta.confidence == Confidence.MEDIUM
        assert meta.agent == "all"
        assert meta.importance == 0.5
        assert meta.access_count == 0

    def test_identity_type(self) -> None:
        meta = NoteMeta(
            type=MemoryType.IDENTITY,
            tags=["profile"],
            summary="User profile",
            confidence=Confidence.HIGH,
        )
        assert meta.type == MemoryType.IDENTITY
        assert meta.summary == "User profile"

    def test_importance_bounds(self) -> None:
        with pytest.raises(ValueError):
            NoteMeta(type=MemoryType.KNOWLEDGE, tags=[], importance=1.5)
        with pytest.raises(ValueError):
            NoteMeta(type=MemoryType.KNOWLEDGE, tags=[], importance=-0.1)


class TestNote:
    def test_roundtrip(self, tmp_path: Path) -> None:
        """Test saving and loading a note produces identical content."""
        note_path = tmp_path / "test.md"
        meta = NoteMeta(
            type=MemoryType.PROCEDURE,
            tags=["git", "workflow"],
            summary="How to rebase",
            confidence=Confidence.HIGH,
        )
        original = Note(
            path=note_path,
            meta=meta,
            title="Git Rebase Workflow",
            body="1. Fetch upstream\n2. Rebase onto main\n3. Force push",
        )

        original.save()
        assert note_path.exists()

        loaded = Note.from_file(note_path)
        assert loaded.title == "Git Rebase Workflow"
        assert loaded.meta.type == MemoryType.PROCEDURE
        assert loaded.meta.tags == ["git", "workflow"]
        assert loaded.meta.summary == "How to rebase"
        assert "Fetch upstream" in loaded.body

    def test_from_file_with_all_fields(self, tmp_path: Path) -> None:
        """Test loading a note with all optional fields."""
        note_path = tmp_path / "full.md"
        note_path.write_text(
            "---\n"
            "type: journal\n"
            "tags: [debugging, python]\n"
            "updated: 2026-04-19\n"
            "summary: Fixed timeout bug\n"
            "confidence: high\n"
            "project: arxiv-pipeline\n"
            "date: 2026-04-19\n"
            "observation_count: 3\n"
            "importance: 0.8\n"
            "access_count: 5\n"
            "---\n"
            "# Fixed Timeout Bug\n"
            "\n"
            "Increased timeout from 30s to 60s.\n",
            encoding="utf-8",
        )

        note = Note.from_file(note_path)
        assert note.meta.type == MemoryType.JOURNAL
        assert note.meta.project == "arxiv-pipeline"
        assert note.meta.observation_count == 3
        assert note.meta.importance == 0.8
        assert note.meta.access_count == 5
        assert note.meta.date == datetime.date(2026, 4, 19)
