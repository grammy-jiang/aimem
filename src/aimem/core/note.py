"""Memory note model — the atomic unit of the aimem system.

Each note is a YAML frontmatter + Markdown body file stored in a git repo.
Schema informed by A-MEM (Zettelkasten), MIRIX (type taxonomy), OMNIMEM
(summary field for pyramid retrieval), ABF (forgetting policy fields),
and EPOS-VLM (observation tracking).
"""

from __future__ import annotations

import datetime
import enum
import logging
from pathlib import Path
from typing import Any

import frontmatter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MemoryType(enum.StrEnum):
    """Four memory types simplified from MIRIX's six-type taxonomy."""

    IDENTITY = "identity"
    KNOWLEDGE = "knowledge"
    PROCEDURE = "procedure"
    JOURNAL = "journal"


class Confidence(enum.StrEnum):
    """Confidence level for a memory note."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NoteMeta(BaseModel):
    """YAML frontmatter metadata for a memory note."""

    # Required fields
    type: MemoryType
    tags: list[str] = Field(default_factory=list)
    updated: datetime.date = Field(default_factory=datetime.date.today)
    summary: str = ""

    # Optional fields
    confidence: Confidence = Confidence.MEDIUM
    links: list[str] = Field(default_factory=list)
    supersedes: str | None = None
    project: str | None = None
    agent: str = "all"
    machine: str | None = None
    date: datetime.date | None = None

    # Causal metadata (Memory Survey)
    caused_by: str | None = None
    causes: list[str] = Field(default_factory=list)

    # Observation tracking (EPOS-VLM)
    observation_count: int = 0
    first_observed: datetime.date | None = None
    last_observed: datetime.date | None = None

    # Forgetting policy inputs (ABF)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = 0


class Note(BaseModel):
    """A complete memory note with metadata and content."""

    path: Path
    meta: NoteMeta
    title: str = ""
    body: str = ""

    @classmethod
    def from_file(cls, path: Path) -> Note:
        """Load a note from a YAML frontmatter + Markdown file."""
        post = frontmatter.load(str(path))
        meta = NoteMeta.model_validate(post.metadata)

        content = post.content.strip()
        lines = content.split("\n", 1)
        title = lines[0].lstrip("# ").strip() if lines else ""
        body = lines[1].strip() if len(lines) > 1 else ""

        logger.debug("Loaded note from %s: type=%s", path, meta.type)
        return cls(path=path, meta=meta, title=title, body=body)

    def to_frontmatter_post(self) -> Any:
        """Convert note to a python-frontmatter Post object for writing."""
        metadata = self.meta.model_dump(
            exclude_none=True,
            exclude_defaults=False,
            mode="json",
        )
        content = f"# {self.title}\n\n{self.body}" if self.title else self.body
        return frontmatter.Post(content, **metadata)

    def save(self, path: Path | None = None) -> Path:
        """Write note to a YAML frontmatter + Markdown file."""
        target = path or self.path
        target.parent.mkdir(parents=True, exist_ok=True)

        post = self.to_frontmatter_post()
        target.write_text(frontmatter.dumps(post), encoding="utf-8")
        logger.info("Saved note to %s", target)
        return target
