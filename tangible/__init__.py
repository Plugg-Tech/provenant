"""Tangible — the physical-action API for agents (sandbox prototype).

Verb #1: notarization. An agent submits a typed action request; Tangible
orchestrates identity proofing, jurisdiction/compliance routing, and the
notarial act, then returns a cryptographically signed, verifiable proof.

WHAT IS REAL IN THIS PROTOTYPE:
  - The action API and orchestration pipeline.
  - The cryptographic proof: real Ed25519 signing, hashing, verification,
    and tamper detection (see tangible/crypto.py).
  - The agent -> tool -> proof -> verify loop (see agent_demo.py).

WHAT IS SIMULATED (and clearly labeled as such):
  - Identity proofing (would call an IAL2 IDV vendor).
  - The commissioned notary performing the act (would be a licensed human /
    RON-platform partner).
These require legal commissions and vendor contracts, not code.
"""

__version__ = "0.1.0"
