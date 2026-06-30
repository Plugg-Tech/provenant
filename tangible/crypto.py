"""Cryptographic proof: Ed25519 signing with PINNED-KEY verification.

A proof is a JSON object of substantive claims plus derived fields:
  - key_id       : fingerprint of the signing key (part of the signed content)
  - content_hash : sha256 of the canonical (sorted, minified) claims
  - signature    : Ed25519 signature over those canonical bytes
  - public_key   : the signing key (for transparency ONLY; not trusted on verify)

Verification recomputes the canonical bytes, checks the hash, then verifies the
signature against the *trusted registry* key for `key_id` — never the embedded
public_key. Altering any signed field, or signing with an untrusted key, fails.
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional, Tuple

from cryptography.exceptions import InvalidSignature

from .keyring import KeyRing, default_keyring

# Derived fields that are NOT part of the signed content.
_EXCLUDED = {"signature", "public_key", "content_hash"}


def _canonical_bytes(content: dict) -> bytes:
    filtered = {k: v for k, v in content.items() if k not in _EXCLUDED}
    return json.dumps(filtered, sort_keys=True, separators=(",", ":")).encode("utf-8")


def issue_proof(content: dict, keyring: Optional[KeyRing] = None) -> dict:
    kr = keyring or default_keyring()
    key_id = kr.active_key_id()
    proof = dict(content)
    proof["key_id"] = key_id  # signed
    canonical = _canonical_bytes(proof)
    proof["content_hash"] = hashlib.sha256(canonical).hexdigest()
    proof["signature"] = kr.sign(key_id, canonical).hex()
    proof["public_key"] = kr.public_key_hex(key_id)  # transparency only
    return proof


def verify_proof(proof: dict, keyring: Optional[KeyRing] = None) -> Tuple[bool, str]:
    """Return (is_valid, reason). Verifies against the trusted registry key."""
    kr = keyring or default_keyring()
    try:
        canonical = _canonical_bytes(proof)
        if proof.get("content_hash") != hashlib.sha256(canonical).hexdigest():
            return False, "content_hash mismatch (proof claims were altered)"
        key_id = proof.get("key_id")
        pub = kr.trusted_public_key(key_id)
        if pub is None:
            return False, f"untrusted key_id '{key_id}' (not in trusted registry)"
        pub.verify(bytes.fromhex(proof["signature"]), canonical)
        return True, "valid"
    except InvalidSignature:
        return False, "invalid signature"
    except Exception as exc:  # malformed proof, bad hex, missing fields
        return False, f"verification error: {exc}"


def verify_document(proof: dict, document_bytes: bytes) -> Tuple[bool, str]:
    """Check that a proof is bound to a specific document's bytes."""
    actual = hashlib.sha256(document_bytes).hexdigest()
    if actual != proof.get("document_sha256"):
        return False, "document does not match the one in the proof"
    return True, "document matches proof"
