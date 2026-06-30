"""Provenant SDK client.

A typed, minimal client for the Provenant API. Works with both synchronous
and async HTTP via httpx.

Usage:
    from provenant.sdk import ProvenantClient

    client = ProvenantClient("https://api.useprovenant.xyz", api_key="pk_live_xxx")

    # Identity verification
    session = client.verify_identity(name="Jordan", email="jordan@acme.com")
    if session.status == "verified":
        print(session.proof)

    # Notarization
    result = client.notarize(
        document_name="Promissory Note",
        document_sha256="7d784f...",
        jurisdiction="TX",
        parties=[{"name": "Jordan", "email": "jordan@acme.com"}],
    )

    # Verify a proof
    ok, reason = client.verify_proof(result.proof)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import httpx


@dataclass
class IdentitySession:
    """A started identity-verification session."""
    action_id: str
    session_id: str
    provider: str
    url: Optional[str]
    status: str
    party_email: str
    party_name: str
    created_at: str
    proof: Optional[dict] = None


@dataclass
class ActionResult:
    """The result of a notarization or other action."""
    action_id: str
    status: str
    request: dict
    proof: Optional[dict] = None
    ledger_entry: Optional[dict] = None
    rejection_reason: Optional[str] = None
    created_at: str = ""


class ProvenantClient:
    """Client for the Provenant physical-action API.

    Args:
        base_url: The API base URL (e.g. "https://api.useprovenant.xyz").
        api_key: Optional bearer API key for authenticated requests.
        timeout: Request timeout in seconds (default 30).
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000",
                 api_key: Optional[str] = None, timeout: float = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _post(self, path: str, body: dict) -> dict:
        resp = self._client.post(path, json=body)
        if resp.status_code == 401 or resp.status_code == 403:
            from .exceptions import AuthenticationError
            raise AuthenticationError("Invalid or missing API key", status_code=resp.status_code)
        if resp.status_code == 404:
            from .exceptions import NotFoundError
            raise NotFoundError(f"Not found: {path}", status_code=404)
        if resp.status_code >= 400:
            from .exceptions import ProvenantError
            raise ProvenantError(f"API error {resp.status_code}: {resp.text}",
                                 status_code=resp.status_code)
        return resp.json()

    def _get(self, path: str) -> dict:
        resp = self._client.get(path)
        if resp.status_code == 404:
            from .exceptions import NotFoundError
            raise NotFoundError(f"Not found: {path}", status_code=404)
        if resp.status_code >= 400:
            from .exceptions import ProvenantError
            raise ProvenantError(f"API error {resp.status_code}: {resp.text}",
                                 status_code=resp.status_code)
        return resp.json()

    # ---- Identity verification ----

    def verify_identity(self, name: str, email: str,
                        return_url: Optional[str] = None) -> IdentitySession:
        """Start an identity verification session.

        In sandbox mode (no Stripe key), returns verified immediately.
        In live mode, returns a pending session with a hosted URL.
        """
        body: dict[str, Any] = {"name": name, "email": email}
        if return_url:
            body["return_url"] = return_url
        data = self._post("/v1/actions/verify-identity", body)
        return IdentitySession(
            action_id=data["action_id"],
            session_id=data["session_id"],
            provider=data["provider"],
            url=data.get("url"),
            status=data["status"],
            party_email=data["party_email"],
            party_name=data["party_name"],
            created_at=data["created_at"],
            proof=data.get("proof"),
        )

    def get_identity_status(self, action_id: str) -> IdentitySession:
        """Poll the status of an identity verification session."""
        data = self._get(f"/v1/identity/{action_id}")
        return IdentitySession(
            action_id=data["action_id"],
            session_id=data["session_id"],
            provider=data["provider"],
            url=data.get("url"),
            status=data["status"],
            party_email=data["party_email"],
            party_name=data["party_name"],
            created_at=data["created_at"],
            proof=data.get("proof"),
        )

    # ---- Notarization ----

    def notarize(self, document_name: str, document_sha256: str,
                 jurisdiction: str, parties: List[dict],
                 reference: Optional[str] = None,
                 idempotency_key: Optional[str] = None) -> ActionResult:
        """Notarize a document.

        Args:
            document_name: Human-readable document name.
            document_sha256: SHA-256 hex digest of the document bytes.
            jurisdiction: 2-letter US state code (e.g. "TX").
            parties: List of dicts with keys: name, email, role.
            reference: Optional caller reference.
            idempotency_key: Optional retry-safe key.

        Returns:
            ActionResult with status "completed" and a signed proof,
            or "rejected" with a rejection_reason.
        """
        body: dict[str, Any] = {
            "document_name": document_name,
            "document_sha256": document_sha256,
            "jurisdiction": jurisdiction,
            "parties": parties,
        }
        if reference:
            body["reference"] = reference
        if idempotency_key:
            body["idempotency_key"] = idempotency_key
        data = self._post("/v1/actions/notarize", body)
        return ActionResult(
            action_id=data["action_id"],
            status=data["status"],
            request=data["request"],
            proof=data.get("proof"),
            ledger_entry=data.get("ledger_entry"),
            rejection_reason=data.get("rejection_reason"),
            created_at=data.get("created_at", ""),
        )

    # ---- Proof verification ----

    def verify_proof(self, proof: dict) -> Tuple[bool, str]:
        """Verify a signed proof. Returns (is_valid, reason)."""
        data = self._post("/v1/verify", {"proof": proof})
        return data["valid"], data["reason"]

    # ---- Revocation ----

    def revoke(self, proof_id: str) -> None:
        """Revoke a proof. Subsequent verifications will fail."""
        self._post(f"/v1/proofs/{proof_id}/revoke", {})

    # ---- Ledger ----

    def verify_ledger(self) -> dict:
        """Verify the tamper-evident ledger chain. Returns {valid, reason, entries}."""
        return self._get("/v1/ledger/verify")

    # ---- Health ----

    def health(self) -> dict:
        """Check API health. Returns {ok, identity_live}."""
        return self._get("/healthz")

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "ProvenantClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
