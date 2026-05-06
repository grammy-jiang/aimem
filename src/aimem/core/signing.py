"""ed25519 signing for MemoryRecord (design.md §8, R-039).

Each record's ``sig`` field is a hex-encoded ed25519 detached signature
over ``record.canonical_bytes()``.

Keys are stored at:
  ``~/.ai-memory/.keys/signing.key``  — private key (mode 0600)
  ``~/.ai-memory/.keys/signing.pub``  — public key

If no key exists, ``ensure_key_pair()`` generates one automatically.
"""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from aimem.core.error import AuthError
from aimem.core.schema import MemoryRecord


def _key_dir(memory_dir: Path) -> Path:
    return memory_dir / ".keys"


def ensure_key_pair(memory_dir: Path) -> Path:
    """Generate an ed25519 key pair if one does not yet exist.

    Returns the path to the public-key file.
    """
    kdir = _key_dir(memory_dir)
    kdir.mkdir(parents=True, exist_ok=True)
    priv_path = kdir / "signing.key"
    pub_path = kdir / "signing.pub"

    if priv_path.exists() and pub_path.exists():
        return pub_path

    private_key = Ed25519PrivateKey.generate()
    priv_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    priv_path.chmod(0o600)

    pub_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return pub_path


def _load_private(memory_dir: Path) -> Ed25519PrivateKey:
    priv_path = _key_dir(memory_dir) / "signing.key"
    if not priv_path.exists():
        ensure_key_pair(memory_dir)
    key = serialization.load_pem_private_key(priv_path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise AuthError("Signing key is not an Ed25519 private key")
    return key


def _load_public(memory_dir: Path) -> Ed25519PublicKey:
    pub_path = _key_dir(memory_dir) / "signing.pub"
    if not pub_path.exists():
        ensure_key_pair(memory_dir)
    key = serialization.load_pem_public_key(pub_path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise AuthError("Public key is not an Ed25519 public key")
    return key


def sign_record(record: MemoryRecord, memory_dir: Path) -> MemoryRecord:
    """Return a copy of *record* with ``sig`` populated."""
    private_key = _load_private(memory_dir)
    payload = record.canonical_bytes()
    raw_sig = private_key.sign(payload)
    signed = record.model_copy(update={"sig": base64.b64encode(raw_sig).decode()})
    return signed


def verify_record(record: MemoryRecord, memory_dir: Path) -> None:
    """Raise AuthError if the record's sig does not verify."""
    if not record.sig:
        raise AuthError(f"Record {record.id} has no signature", detail="missing sig")

    public_key = _load_public(memory_dir)
    payload = record.canonical_bytes()
    try:
        raw_sig = base64.b64decode(record.sig)
        public_key.verify(raw_sig, payload)
    except (InvalidSignature, Exception) as exc:
        raise AuthError(
            f"Signature verification failed for record {record.id}",
            detail=str(exc),
        ) from exc
