"""Git repository operations for the aimem memory store.

Manages the ~/.ai-memory/ git repository: initialization, note CRUD,
git commit/sync, and directory structure.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from aimem.core.config import DEFAULT_MEMORY_DIR, AimemConfig
from aimem.core.note import MemoryType, Note, NoteMeta

logger = logging.getLogger(__name__)

DIRECTORY_STRUCTURE: dict[str, list[str]] = {
    "identity": [],
    "knowledge": ["languages", "frameworks", "tools", "domains", "projects"],
    "procedures": ["workflows", "commands", "patterns", "troubleshooting"],
    "journal": ["sessions", "decisions", "incidents", "learnings"],
    ".links": [],
    ".archive": [],
}


class MemoryRepository:
    """Manages the git-backed memory repository."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or DEFAULT_MEMORY_DIR
        self.config = AimemConfig.load(self.root)

    @property
    def is_initialized(self) -> bool:
        """Check if the memory repository exists and is a git repo."""
        return (self.root / ".git").is_dir()

    def init(self) -> Path:
        """Initialize a new memory repository with directory structure."""
        if self.is_initialized:
            logger.warning("Repository already initialized at %s", self.root)
            return self.root

        self.root.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        for dir_name, subdirs in DIRECTORY_STRUCTURE.items():
            dir_path = self.root / dir_name
            dir_path.mkdir(exist_ok=True)
            for subdir in subdirs:
                (dir_path / subdir).mkdir(exist_ok=True)

        # Create .hot buffer (gitignored)
        (self.root / ".hot").mkdir(exist_ok=True)

        # Create .machine directory (gitignored)
        (self.root / ".machine").mkdir(exist_ok=True)

        # Write .gitignore
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            ".machine/\n" "*.secret.md\n" "journal/private/\n" ".env\n" ".hot/\n",
            encoding="utf-8",
        )

        # Write default config
        self.config.save(self.root)

        # Initialize git repo
        self._git("init")
        self._git("checkout", "-b", "main")
        self._git("add", ".")
        self._git("commit", "-m", "Initialize aimem memory repository")

        logger.info("Initialized memory repository at %s", self.root)
        return self.root

    def list_notes(
        self,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        project: str | None = None,
    ) -> list[Note]:
        """List all notes, optionally filtered by type, tags, or project."""
        notes: list[Note] = []

        if memory_type:
            search_dir = self._type_dir(memory_type)
            if not search_dir.exists():
                return []
            md_files = list(search_dir.rglob("*.md"))
        else:
            md_files = []
            for type_dir_name in ["identity", "knowledge", "procedures", "journal"]:
                type_dir = self.root / type_dir_name
                if type_dir.exists():
                    md_files.extend(type_dir.rglob("*.md"))

        for md_file in sorted(md_files):
            try:
                note = Note.from_file(md_file)
                if tags and not set(tags).intersection(note.meta.tags):
                    continue
                if project and note.meta.project != project:
                    continue
                notes.append(note)
            except Exception as exc:
                logger.warning("Failed to parse %s: %s", md_file, exc)

        return notes

    def get_note(self, path: str) -> Note | None:
        """Get a specific note by relative path."""
        full_path = self.root / path
        if not full_path.exists():
            logger.warning("Note not found: %s", full_path)
            return None
        return Note.from_file(full_path)

    def add_note(
        self,
        memory_type: MemoryType,
        title: str,
        body: str,
        tags: list[str] | None = None,
        **kwargs: str,
    ) -> Note:
        """Create a new memory note and save it to the repository."""
        slug = title.lower().replace(" ", "-").replace("/", "-")
        type_dir = self._type_dir(memory_type)
        note_path = type_dir / f"{slug}.md"

        meta = NoteMeta(
            type=memory_type,
            tags=tags or [],
            **kwargs,
        )

        note = Note(path=note_path, meta=meta, title=title, body=body)
        note.save()

        logger.info("Added note: %s (%s)", note_path, memory_type.value)
        return note

    def remove_note(self, path: str) -> bool:
        """Soft-delete a note by moving it to .archive/."""
        full_path = self.root / path
        if not full_path.exists():
            logger.warning("Note not found for removal: %s", path)
            return False

        archive_path = self.root / ".archive" / path
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.rename(archive_path)

        logger.info("Archived note: %s -> %s", path, archive_path)
        return True

    def sync(self) -> bool:
        """Sync with remote: pull --rebase, then push."""
        try:
            self._git("pull", "--rebase")
            self._git("push")
            logger.info("Synced with remote")
            return True
        except subprocess.CalledProcessError as exc:
            logger.error("Sync failed: %s", exc)
            return False

    def commit(self, message: str, paths: list[str] | None = None) -> None:
        """Stage and commit changes."""
        if paths:
            for p in paths:
                self._git("add", p)
        else:
            self._git("add", ".")
        self._git("commit", "-m", message)
        logger.info("Committed: %s", message)

    def _type_dir(self, memory_type: MemoryType) -> Path:
        """Get the directory for a memory type."""
        dir_map = {
            MemoryType.IDENTITY: "identity",
            MemoryType.KNOWLEDGE: "knowledge",
            MemoryType.PROCEDURE: "procedures",
            MemoryType.JOURNAL: "journal",
        }
        return self.root / dir_map[memory_type]

    def _git(self, *args: str) -> str:
        """Run a git command in the repository."""
        result = subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
