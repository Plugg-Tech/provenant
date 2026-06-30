"""Key registry with pinned-key verification.

SECURITY: a proof must be verified against a *trusted* public key, never the key
embedded in the proof itself (an attacker can embed their own). Each key has a
fingerprint-based key_id; proofs carry the key_id, and verification looks up the
trusted public key for that id in this registry. Unknown key_id -> rejected.

Keys persist to a JSON file so separate processes (e.g. the `tangible.verify`
CLI) share the same trusted registry. In production the *private* key would live
in an HSM/KMS, not on disk — this is a prototype.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Dict, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .models import now_iso

_RAW = serialization.Encoding.Raw
_PRIV_FMT = serialization.PrivateFormat.Raw
_PUB_FMT = serialization.PublicFormat.Raw


def _fingerprint(public_hex: str) -> str:
    return "k_" + hashlib.sha256(bytes.fromhex(public_hex)).hexdigest()[:16]


class KeyRing:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._keys: Dict[str, dict] = {}  # key_id -> {private_key?, public_key, created_at, status}
        self._active: Optional[str] = None
        if path and os.path.exists(path):
            self._load()
        else:
            self._create_active_key()
            self._save()

    # ---- internal ----
    def _create_active_key(self) -> str:
        priv = Ed25519PrivateKey.generate()
        priv_hex = priv.private_bytes(_RAW, _PRIV_FMT, serialization.NoEncryption()).hex()
        pub_hex = priv.public_key().public_bytes(_RAW, _PUB_FMT).hex()
        kid = _fingerprint(pub_hex)
        self._keys[kid] = {
            "private_key": priv_hex,
            "public_key": pub_hex,
            "created_at": now_iso(),
            "status": "active",
        }
        self._active = kid
        return kid

    def _load(self) -> None:
        with open(self.path) as f:
            data = json.load(f)
        self._keys = data["keys"]
        self._active = data["active"]

    def _save(self) -> None:
        if not self.path:
            return
        with open(self.path, "w") as f:
            json.dump({"active": self._active, "keys": self._keys}, f, indent=2)

    # ---- public ----
    def active_key_id(self) -> str:
        assert self._active is not None
        return self._active

    def sign(self, key_id: str, message: bytes) -> bytes:
        rec = self._keys[key_id]
        if "private_key" not in rec:
            raise ValueError(f"no private key for {key_id}")
        priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(rec["private_key"]))
        return priv.sign(message)

    def public_key_hex(self, key_id: str) -> str:
        return self._keys[key_id]["public_key"]

    def trusted_public_key(self, key_id: Optional[str]) -> Optional[Ed25519PublicKey]:
        rec = self._keys.get(key_id or "")
        if not rec:
            return None
        return Ed25519PublicKey.from_public_bytes(bytes.fromhex(rec["public_key"]))

    def rotate(self) -> str:
        """Create a new active key; old key stays trusted for verifying old proofs."""
        with self._lock:
            if self._active:
                self._keys[self._active]["status"] = "retired"
            kid = self._create_active_key()
            self._save()
            return kid

    def register_external(self, public_hex: str) -> str:
        """Trust a public key we did not generate (e.g. a partner issuer)."""
        kid = _fingerprint(public_hex)
        self._keys.setdefault(
            kid,
            {"public_key": public_hex, "created_at": now_iso(), "status": "external"},
        )
        self._save()
        return kid


_DEFAULT: Optional[KeyRing] = None
_DEFAULT_PATH = os.environ.get(
    "TANGIBLE_KEYRING",
    os.path.join(os.path.dirname(__file__), "..", "tangible_keyring.json"),
)


def default_keyring() -> KeyRing:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = KeyRing(_DEFAULT_PATH)
    return _DEFAULT
