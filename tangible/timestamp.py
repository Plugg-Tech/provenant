"""Anchor a ledger head to an external time source.

SIMULATED. In production, submit the head hash to an RFC 3161 Time-Stamp
Authority or a public ledger so a third party can prove *when* the chain
existed, independent of Tangible. Here we locally sign (head_hash, time); the
returned token verifies with tangible.crypto.verify_proof.
"""
from __future__ import annotations

from typing import Optional

from . import crypto
from .keyring import KeyRing
from .models import now_iso


def anchor(head_hash: str, keyring: Optional[KeyRing] = None) -> dict:
    content = {
        "anchor_type": "LOCAL_SANDBOX (replace with RFC3161 TSA or public ledger)",
        "head_hash": head_hash,
        "anchored_at": now_iso(),
    }
    return crypto.issue_proof(content, keyring)
