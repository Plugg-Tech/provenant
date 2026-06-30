"""Tamper-evident, append-only ledger of issued proofs (hash chain).

Each entry links to the previous via prev_hash, so any insertion, deletion,
reordering, or edit breaks verify_chain(). Optionally persists to a JSONL file.
The chain head can be anchored externally (see tangible/timestamp.py).
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import List, Optional, Tuple

from .models import now_iso

GENESIS = "0" * 64
_FIELDS = ("seq", "proof_id", "content_hash", "prev_hash", "appended_at")


def _hash_payload(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


class Ledger:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self._entries: List[dict] = []
        if path and os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._entries.append(json.loads(line))

    def append(self, proof: dict) -> dict:
        prev = self._entries[-1]["entry_hash"] if self._entries else GENESIS
        payload = {
            "seq": len(self._entries),
            "proof_id": proof.get("proof_id"),
            "content_hash": proof.get("content_hash"),
            "prev_hash": prev,
            "appended_at": now_iso(),
        }
        entry = {**payload, "entry_hash": _hash_payload(payload)}
        self._entries.append(entry)
        if self.path:
            with open(self.path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        return entry

    def verify_chain(self) -> Tuple[bool, str]:
        prev = GENESIS
        for i, e in enumerate(self._entries):
            if e.get("seq") != i:
                return False, f"seq mismatch at index {i}"
            if e.get("prev_hash") != prev:
                return False, f"broken link at seq {i}"
            payload = {k: e.get(k) for k in _FIELDS}
            if _hash_payload(payload) != e.get("entry_hash"):
                return False, f"entry hash mismatch at seq {i}"
            prev = e["entry_hash"]
        return True, f"chain valid ({len(self._entries)} entries)"

    def head(self) -> str:
        return self._entries[-1]["entry_hash"] if self._entries else GENESIS

    def entries(self) -> List[dict]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
