"""Configuration loading for aimem.

Reads .aimem.yaml from the memory repository root.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_DIR = Path.home() / ".ai-memory"


class ContextBudget(BaseModel):
    """Token budget allocation for context injection."""

    total_max_tokens: int = 5000
    tier1_identity: int = 500
    tier2_project: int = 1500
    tier3_retrieval: int = 3000
    tier3_stage1_summaries: int = 500
    tier3_stage2_expansion: int = 2000
    tier3_stage3_links: int = 500
    retrieval_window: int = 5


class AdapterConfig(BaseModel):
    """Configuration for an agent adapter."""

    output: str
    include: list[str] = Field(default_factory=list)
    format: str = "markdown"
    max_tokens: int = 4000


class ConsolidationConfig(BaseModel):
    """Dual-buffer consolidation settings."""

    probation_hours: int = 24
    probation_sessions: int = 3
    dedup_jaccard_threshold: float = 0.8
    dedup_semantic_threshold: float = 0.9
    merge_semantic_threshold: float = 0.7


class ForgettingConfig(BaseModel):
    """Forgetting policy thresholds."""

    prune_bottom_percent: float = 0.10
    archive_max_multiplier: float = 2.0
    stale_months: int = 6
    archive_delete_months: int = 12


class AimemConfig(BaseModel):
    """Top-level aimem configuration."""

    memory_dir: Path = DEFAULT_MEMORY_DIR
    context_budget: ContextBudget = Field(default_factory=ContextBudget)
    consolidation: ConsolidationConfig = Field(default_factory=ConsolidationConfig)
    forgetting: ForgettingConfig = Field(default_factory=ForgettingConfig)
    adapters: dict[str, AdapterConfig] = Field(default_factory=dict)

    @classmethod
    def load(cls, memory_dir: Path | None = None) -> AimemConfig:
        """Load configuration from .aimem.yaml in the memory directory."""
        root = memory_dir or DEFAULT_MEMORY_DIR
        config_path = root / ".aimem.yaml"

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            logger.info("Loaded config from %s", config_path)
            config = cls.model_validate(data)
            config.memory_dir = root
            return config

        logger.info("No config found at %s, using defaults", config_path)
        return cls(memory_dir=root)

    def save(self, memory_dir: Path | None = None) -> Path:
        """Save configuration to .aimem.yaml."""
        root = memory_dir or self.memory_dir
        config_path = root / ".aimem.yaml"

        data = self.model_dump(exclude={"memory_dir"}, mode="json")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info("Saved config to %s", config_path)
        return config_path
