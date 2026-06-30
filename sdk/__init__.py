"""Provenant SDK — the physical-action API for agents.

Usage:
    from provenant.sdk import ProvenantClient

    client = ProvenantClient("https://api.useprovenant.xyz")
    result = client.verify_identity(name="Jordan", email="jordan@acme.com")
    print(result.proof)

CLI:
    python -m sdk.cli health
    python -m sdk.cli verify-identity --name "Jordan" --email "jordan@acme.com"
    python -m sdk.cli notarize --doc "Note" --hash <sha256> --state TX --signer "Jordan <jordan@acme.com>"
    python -m sdk.cli verify proof.json
    python -m sdk.cli revoke --proof-id prf_xxx
    python -m sdk.cli ledger
"""
from .client import ProvenantClient, Receipt
from .exceptions import (
    ActionRejectedError,
    AuthenticationError,
    ConfirmationRequired,
    NotFoundError,
    PaymentDeclined,
    PaymentError,
    ProofMintError,
    ProvenantError,
)

__all__ = [
    "ProvenantClient",
    "Receipt",
    "ProvenantError",
    "AuthenticationError",
    "ActionRejectedError",
    "NotFoundError",
    "PaymentError",
    "PaymentDeclined",
    "ProofMintError",
    "ConfirmationRequired",
]
