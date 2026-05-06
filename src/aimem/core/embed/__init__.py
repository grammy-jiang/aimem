"""Pluggable embedding provider (R-053, design.md §7).

Providers: ``local`` (sentence-transformers), ``openai``, ``http``.

The default is ``local``.  Remote providers fail **closed**: if the
endpoint is unreachable, an error is raised rather than falling back to
a different provider (because that would silently change the distance
metric of the index).

When sentence-transformers is not installed, local provider degrades
gracefully to a BM25-only mode with a warning logged at first call.
"""

from __future__ import annotations

import hashlib
import os
from typing import Protocol

from aimem.core.config import EmbedConfig
from aimem.core.error import ConfigError, TransientError
from aimem.core import logging as _logging

log = _logging.get_logger(__name__)


class EmbedProvider(Protocol):
    """Contract for embedding providers."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...

    @property
    def dim(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...

    @property
    def available(self) -> bool:
        """True if the provider is ready to produce embeddings."""
        ...


class _LocalProvider:
    """sentence-transformers local provider (default)."""

    def __init__(self, model_name: str, dim: int) -> None:
        self._model_name = model_name
        self._dim = dim
        self._model: object | None = None
        self._available: bool | None = None

    def _load(self) -> None:
        if self._available is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

            self._model = SentenceTransformer(self._model_name)
            self._available = True
            log.info(op="embed_load", model=self._model_name, result="ok")
        except ImportError:
            self._available = False
            log.warning(
                op="embed_load",
                model=self._model_name,
                result="unavailable",
                reason="sentence_transformers not installed; BM25-only mode active",
            )

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._load()
        if not self._available or self._model is None:
            raise TransientError(
                "Local embedding model unavailable (sentence-transformers not installed).",
                detail="Install aimem[search] to enable dense retrieval.",
            )
        import numpy as np  # noqa: PLC0415

        result = self._model.encode(texts, convert_to_numpy=True)  # type: ignore[union-attr]
        if isinstance(result, np.ndarray):
            return result.tolist()
        return [list(r) for r in result]

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def available(self) -> bool:
        self._load()
        return bool(self._available)


class _OpenAIProvider:
    """OpenAI embeddings provider."""

    def __init__(self, cfg: EmbedConfig) -> None:
        self._cfg = cfg
        if not cfg.api_key_env:
            raise ConfigError(
                "embed.api_key_env must be set for openai provider (HC1)."
            )

    def _api_key(self) -> str:
        val = os.environ.get(self._cfg.api_key_env, "")
        if not val:
            raise ConfigError(
                f"Environment variable '{self._cfg.api_key_env}' is not set (HC1).",
                detail="Set the env var before starting aimem.",
            )
        return val

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            import openai  # type: ignore[import-untyped]  # noqa: PLC0415
        except ImportError as exc:
            raise TransientError(
                "openai package not installed.", detail="pip install openai"
            ) from exc

        client = openai.OpenAI(api_key=self._api_key())
        try:
            resp = client.embeddings.create(
                model=self._cfg.model,
                input=texts,
                timeout=self._cfg.timeout_ms / 1000,
            )
            return [item.embedding for item in resp.data]
        except Exception as exc:
            raise TransientError(
                "OpenAI embedding call failed (fail-closed per R-053).",
                detail=str(exc),
            ) from exc

    @property
    def dim(self) -> int:
        return self._cfg.dim

    @property
    def available(self) -> bool:
        try:
            self._api_key()
            return True
        except ConfigError:
            return False


class _HttpProvider:
    """Generic HTTP embedding provider."""

    def __init__(self, cfg: EmbedConfig) -> None:
        self._cfg = cfg
        if not cfg.endpoint:
            raise ConfigError("embed.endpoint must be set for http provider.")

    def _api_key(self) -> str | None:
        if not self._cfg.api_key_env:
            return None
        val = os.environ.get(self._cfg.api_key_env, "")
        if not val:
            raise ConfigError(
                f"Environment variable '{self._cfg.api_key_env}' is not set (HC1)."
            )
        return val

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            import urllib.request  # noqa: PLC0415
            import json  # noqa: PLC0415
        except ImportError as exc:
            raise TransientError("stdlib missing", detail=str(exc)) from exc

        key = self._api_key()
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        payload = json.dumps({"texts": texts}).encode()
        req = urllib.request.Request(
            self._cfg.endpoint, data=payload, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(
                req, timeout=self._cfg.timeout_ms / 1000
            ) as resp:
                data = json.loads(resp.read())
                return data["embeddings"]
        except Exception as exc:
            raise TransientError(
                "HTTP embedding provider call failed (fail-closed per R-053).",
                detail=str(exc),
            ) from exc

    @property
    def dim(self) -> int:
        return self._cfg.dim

    @property
    def available(self) -> bool:
        return bool(self._cfg.endpoint)


def make_provider(cfg: EmbedConfig) -> EmbedProvider:
    """Factory: return the correct provider for *cfg*."""
    if cfg.provider == "local":
        return _LocalProvider(cfg.model, cfg.dim)
    if cfg.provider == "openai":
        return _OpenAIProvider(cfg)
    if cfg.provider == "http":
        return _HttpProvider(cfg)
    raise ConfigError(f"Unknown embed provider: {cfg.provider!r}")


def fingerprint(cfg: EmbedConfig) -> str:
    """A short string that identifies the current embed configuration.

    Used to detect provider/model switches that require index rotation.
    """
    key = f"{cfg.provider}:{cfg.model}:{cfg.dim}:{cfg.endpoint}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]
