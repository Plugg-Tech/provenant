"""Identity proofing.

SIMULATED. In production this calls an IAL2 identity-verification vendor
(credential analysis + knowledge-based auth / biometric liveness), as required
by Remote Online Notarization law. Here it is deterministic so tests and demos
are reproducible: it succeeds unless the party is flagged force_identity_fail.
"""
from __future__ import annotations

from .models import IdentityVerification, Party, now_iso


def verify_identity(party: Party) -> IdentityVerification:
    verified = not party.force_identity_fail
    return IdentityVerification(
        party_email=party.email,
        method="SIMULATED IAL2 (credential analysis + KBA)",
        ial_level="IAL2",
        verified=verified,
        reason="identity proofed" if verified else "identity proofing failed (KBA mismatch)",
        verified_at=now_iso(),
    )
