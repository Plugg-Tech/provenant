"""Core data structures for Tangible actions and proofs."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

# ---- action types ----
ACTION_NOTARIZE = "notarize"

# ---- statuses ----
STATUS_COMPLETED = "completed"
STATUS_REJECTED = "rejected"
STATUS_PENDING = "pending"
STATUS_FAILED = "failed"


def now_iso() -> str:
    """UTC timestamp, ISO-8601."""
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


@dataclass
class Party:
    name: str
    email: str
    role: str = "signer"  # "signer" | "witness"
    # SIMULATION ONLY: force identity proofing to fail, to exercise the
    # rejection path in tests/demos. Stripped out of any issued proof.
    force_identity_fail: bool = False


@dataclass
class ActionRequest:
    action_type: str
    document_name: str
    document_sha256: str
    parties: List[Party]
    jurisdiction: str  # 2-letter US state code, e.g. "TX"
    reference: Optional[str] = None
    # Optional caller-supplied key: a retried request with the same key returns
    # the original result instead of notarizing again.
    idempotency_key: Optional[str] = None


@dataclass
class IdentityVerification:
    party_email: str
    method: str
    ial_level: str
    verified: bool
    reason: str
    verified_at: str


@dataclass
class NotarialAct:
    act_id: str
    notary_id: str
    notary_name: str
    commission_number: str
    commission_state: str
    act_type: str
    performed_at: str
    journal_entry: str


@dataclass
class ActionResult:
    action_id: str
    status: str
    request: dict
    proof: Optional[dict] = None
    ledger_entry: Optional[dict] = None
    rejection_reason: Optional[str] = None
    created_at: str = field(default_factory=now_iso)


@dataclass
class IdentitySession:
    """A real (or simulated) identity-verification session for the verify_identity verb."""
    action_id: str
    session_id: str
    provider: str
    url: Optional[str]          # hosted verification link to hand to the human
    status: str                 # pending | verified | failed
    party_email: str
    party_name: str
    created_at: str
    proof: Optional[dict] = None
