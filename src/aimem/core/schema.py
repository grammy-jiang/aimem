"""v1 MemoryRecord schema (design.md §4).

Every note on disk is a YAML frontmatter + Markdown body file.
The frontmatter is validated and round-tripped through this module.
"""

from __future__ import annotations

import datetime
import enum
import hashlib
import json
from pathlib import Path
from typing import Any

import frontmatter
from pydantic import BaseModel, Field, field_validator
from ulid import ULID

SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Enum types
# ---------------------------------------------------------------------------


class Layer(str, enum.Enum):
    PERSONAL = "personal"
    PROJECT = "project"
    TEAM = "team"


class MemoryType(str, enum.Enum):
    IDENTITY = "identity"
    PREFERENCE = "preference"
    PROCEDURE = "procedure"
    OBSERVATION = "observation"
    KNOWLEDGE = "knowledge"


class DecayPolicy(str, enum.Enum):
    NONE = "none"
    EXPONENTIAL = "exponential"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class Links(BaseModel):
    causal: list[str] = Field(default_factory=list)
    evolves: list[str] = Field(default_factory=list)
    refines: list[str] = Field(default_factory=list)


class ForgettingPolicy(BaseModel):
    ttl_days: int | None = None
    decay: DecayPolicy = DecayPolicy.NONE


class Provenance(BaseModel):
    agent: str = "unknown"
    session: str = ""


# ---------------------------------------------------------------------------
# Top-level schema
# ---------------------------------------------------------------------------


class MemoryRecord(BaseModel):
    """v1 MemoryRecord — the atomic unit stored on disk."""

    schema_version: int = SCHEMA_VERSION
    id: str = Field(default_factory=lambda: str(ULID()))
    layer: Layer = Layer.PERSONAL
    type: MemoryType
    title: str
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    tags: list[str] = Field(default_factory=list)
    links: Links = Field(default_factory=Links)
    forgetting: ForgettingPolicy = Field(default_factory=ForgettingPolicy)
    provenance: Provenance = Field(default_factory=Provenance)
    sig: str = ""  # ed25519 detached sig; empty until signed

    # Body stored separately (not part of frontmatter)
    body: str = Field(default="", exclude=True)

    # File path — not serialised to YAML
    path: Path | None = Field(default=None, exclude=True)

    @field_validator("schema_version")
    @classmethod
    def _check_version(cls, v: int) -> int:
        if v != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {SCHEMA_VERSION}, got {v}. "
                "Run `aimem migrate` to upgrade."
            )
        return v

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def canonical_bytes(self) -> bytes:
        """Deterministic bytes used as the signing payload.

        We serialise a dict with all frontmatter fields *except* sig,
        then JSON-encode it with sorted keys.
        """
        d = self.model_dump(
            exclude={"sig", "body", "path"},
            mode="json",
        )
        return json.dumps(d, sort_keys=True, ensure_ascii=False).encode()

    def content_hash(self) -> str:
        """SHA-256 of the canonical bytes (for quick change detection)."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    # ------------------------------------------------------------------
    # Disk I/O
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: Path) -> "MemoryRecord":
        """Load a MemoryRecord from a YAML-frontmatter Markdown file."""
        post = frontmatter.load(str(path))
        data: dict[str, Any] = dict(post.metadata)
        data["body"] = post.content.strip()
        data["path"] = path
        return cls.model_validate(data)

    def to_file(self, path: Path | None = None) -> Path:
        """Write this record to *path* (defaults to self.path)."""
        target = path or self.path
        if target is None:
            raise ValueError("No path specified for MemoryRecord.to_file()")
        target.parent.mkdir(parents=True, exist_ok=True)

        fm_data = self.model_dump(
            exclude={"body", "path"},
            mode="json",
            exclude_none=False,
        )
        post = frontmatter.Post(self.body, **fm_data)
        target.write_text(frontmatter.dumps(post), encoding="utf-8")
        return target
