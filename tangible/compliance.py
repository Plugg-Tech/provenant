"""Request validation and jurisdiction / RON-eligibility routing.

The RON_ALLOWED_STATES set is illustrative for the prototype. In production,
this must track each state's notarization statutes continuously — and that
ongoing compliance work is a core part of the moat.
"""
from __future__ import annotations

import re
from typing import Tuple

from .models import ACTION_NOTARIZE, ActionRequest

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
MAX_PARTIES = 10
MAX_NAME_LEN = 256

# US states modeled as permitting Remote Online Notarization in this prototype.
RON_ALLOWED_STATES = {
    "AL", "AK", "AZ", "AR", "CO", "FL", "HI", "ID", "IL", "IN", "IA", "KS",
    "KY", "LA", "MD", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "SD", "TN", "TX", "UT",
    "VA", "WA", "WV", "WI", "WY",
}


def validate_request(req: ActionRequest) -> Tuple[bool, str]:
    if req.action_type != ACTION_NOTARIZE:
        return False, f"unsupported action_type '{req.action_type}'"
    if not req.document_name or len(req.document_name) > MAX_NAME_LEN:
        return False, "document_name missing or too long"
    if not req.document_sha256 or not _SHA256_RE.match(req.document_sha256):
        return False, "document_sha256 must be 64 hex characters"
    if not req.parties:
        return False, "no parties provided"
    if len(req.parties) > MAX_PARTIES:
        return False, f"too many parties (max {MAX_PARTIES})"
    seen = set()
    for p in req.parties:
        if not p.name:
            return False, "a party is missing a name"
        if not _EMAIL_RE.match(p.email or ""):
            return False, f"invalid email '{p.email}'"
        if p.email.lower() in seen:
            return False, f"duplicate party email '{p.email}'"
        seen.add(p.email.lower())
    return True, "ok"


def check_ron_eligibility(jurisdiction: str) -> Tuple[bool, str]:
    state = (jurisdiction or "").strip().upper()
    if not state:
        return False, "missing jurisdiction"
    if len(state) != 2:
        return False, f"jurisdiction '{jurisdiction}' is not a 2-letter US state code"
    if state in RON_ALLOWED_STATES:
        return True, f"{state} permits remote online notarization (RON)"
    return False, (
        f"{state} does not permit RON in this prototype's table; "
        f"route to a mobile notary"
    )
