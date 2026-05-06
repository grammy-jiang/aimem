"""Unit tests for ed25519 signing (US-013 acceptance criteria)."""
from __future__ import annotations

from pathlib import Path

import pytest

from aimem.core.schema import Layer, MemoryRecord, MemoryType, Provenance, Links, ForgettingPolicy
from aimem.core.signing import ensure_key_pair, sign_record, verify_record
from aimem.core.error import AuthError


def _make_record() -> MemoryRecord:
    return MemoryRecord(
        type=MemoryType.KNOWLEDGE,
        layer=Layer.PERSONAL,
        title="Signed record",
        body="Important fact",
        tags=[],
        links=Links(),
        forgetting=ForgettingPolicy(),
        provenance=Provenance(agent="pytest"),
    )


class TestKeyGeneration:
    def test_creates_key_files(self, tmp_path: Path):
        pub = ensure_key_pair(tmp_path)
        priv = tmp_path / ".keys" / "signing.key"
        assert priv.exists()
        assert pub.exists()

    def test_idempotent(self, tmp_path: Path):
        pub1 = ensure_key_pair(tmp_path)
        pub2 = ensure_key_pair(tmp_path)
        assert pub1.read_bytes() == pub2.read_bytes()

    def test_private_key_mode(self, tmp_path: Path):
        ensure_key_pair(tmp_path)
        priv = tmp_path / ".keys" / "signing.key"
        import stat
        mode = priv.stat().st_mode & 0o777
        assert mode == 0o600, f"Expected 0600 got {oct(mode)}"


class TestSignAndVerify:
    def test_sign_sets_sig_field(self, tmp_path: Path):
        rec = _make_record()
        assert rec.sig == ""
        signed = sign_record(rec, tmp_path)
        assert signed.sig != ""
        assert len(signed.sig) > 10

    def test_verify_passes_on_valid_sig(self, tmp_path: Path):
        rec = _make_record()
        signed = sign_record(rec, tmp_path)
        verify_record(signed, tmp_path)  # Should not raise

    def test_verify_fails_on_tampered_title(self, tmp_path: Path):
        rec = _make_record()
        signed = sign_record(rec, tmp_path)
        tampered = signed.model_copy(update={"title": "hacked"})
        with pytest.raises(AuthError):
            verify_record(tampered, tmp_path)

    def test_verify_fails_on_missing_key(self, tmp_path: Path):
        rec = _make_record()
        signed = sign_record(rec, tmp_path)
        # Remove keys
        for f in (tmp_path / ".keys").iterdir():
            f.unlink()
        with pytest.raises(AuthError):
            verify_record(signed, tmp_path)
