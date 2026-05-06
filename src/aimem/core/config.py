"""Configuration loader for aimem (R-024, design.md §7).

The config file is ``~/.ai-memory/.aimem.yaml`` (or wherever AIMEM_DIR
points).  All fields have sensible defaults so the file need not exist.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_DIR: Path = Path.home() / ".ai-memory"


class EmbedConfig(BaseModel):
    """Embedding provider configuration (R-053, design.md §7)."""

    provider: Literal["local", "openai", "http"] = "local"
    model: str = "bge-small-en-v1.5"
    endpoint: str = ""
    # MUST resolve from env; never stored as a literal value (HC1)
    api_key_env: str = ""
    dim: int = 384
    timeout_ms: int = 5000


class LockConfig(BaseModel):
    """flock(2) timeout settings (R-054)."""

    timeout_ms: int = 5000


class AimemConfig(BaseModel):
    """Root configuration object loaded from .aimem.yaml."""

    memory_dir: Path = DEFAULT_MEMORY_DIR
    embed: EmbedConfig = Field(default_factory=EmbedConfig)
    lock: LockConfig = Field(default_factory=LockConfig)
    retrieval_window: int = 5

    @classmethod
    def load(cls, memory_dir: Path | None = None) -> "AimemConfig":
        """Load config from *memory_dir*/.aimem.yaml, or return defaults."""
        root = memory_dir or DEFAULT_MEMORY_DIR
        config_path = root / ".aimem.yaml"
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            obj = cls.model_validate({**raw, "memory_dir": str(root)})
            logger.debug("Loaded config from %s", config_path)
            return obj
        logger.debug("No config at %s; using defaults", config_path)
        return cls(memory_dir=root)

    def save(self, memory_dir: Path | None = None) -> Path:
        """Write config to *memory_dir*/.aimem.yaml."""
        root = memory_dir or self.memory_dir
        config_path = root / ".aimem.yaml"
        data = self.model_dump(mode="json", exclude={"memory_dir"})
        config_path.write_text(
            yaml.dump(data, default_flow_style=False), encoding="utf-8"
        )
        return config_path
