"""Unit tests for write gate (US-014 / R-040 acceptance criteria)."""
from __future__ import annotations

import os

import pytest

from aimem.core.error import AuthError, InvariantError, AimemError
from aimem.core.gate import check_write
from aimem.core.schema import Layer, MemoryRecord, MemoryType, Provenance, Links, ForgettingPolicy


def _make_record(title: str = "Test", body: str = "") -> MemoryRecord:
    return MemoryRecord(
        type=MemoryType.OBSERVATION,
        layer=Layer.PERSONAL,
        title=title,
        body=body,
        tags=[],
        links=Links(),
        forgetting=ForgettingPolicy(),
        provenance=Provenance(agent="pytest"),
    )


class TestSecretDetection:
    def test_aws_key_rejected(self):
        rec = _make_record(body="AKIAIOSFODNN7EXAMPLE something something")
        with pytest.raises(InvariantError, match="secret"):
            check_write(rec)

    def test_github_token_rejected(self):
        rec = _make_record(body="ghp_1234567890abcdefghijklmnopqrstuvwxyz")
        with pytest.raises(InvariantError, match="secret"):
            check_write(rec)

    def test_private_key_header_rejected(self):
        rec = _make_record(body="-----BEGIN RSA PRIVATE KEY-----\nABC123\n-----END RSA PRIVATE KEY-----")
        with pytest.raises(InvariantError, match="secret"):
            check_write(rec)

    def test_clean_record_passes(self):
        rec = _make_record(body="This is a normal observation with no secrets.")
        check_write(rec)  # Should not raise


class TestHookLayerEnforcement:
    def test_hook_cannot_write_project_layer(self, monkeypatch):
        monkeypatch.setenv("AIMEM_CALLER_ROLE", "hook")
        rec = _make_record()
        rec = rec.model_copy(update={"layer": Layer.PROJECT})
        with pytest.raises(AuthError):
            check_write(rec)

    def test_hook_can_write_personal_layer(self, monkeypatch):
        monkeypatch.setenv("AIMEM_CALLER_ROLE", "hook")
        rec = _make_record()
        check_write(rec)  # personal layer is allowed for hooks

    def test_non_hook_can_write_project_layer(self, monkeypatch):
        monkeypatch.delenv("AIMEM_CALLER_ROLE", raising=False)
        rec = _make_record()
        rec = rec.model_copy(update={"layer": Layer.PROJECT})
        check_write(rec)  # Should not raise
