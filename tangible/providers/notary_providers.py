"""Notarization providers.

SimulatedNotaryProvider — deterministic, no network (default for tests/demo).
PandaDocNotaryProvider  — REAL notarization via PandaDoc Notary On-Demand API.
                          Requires a PandaDoc account with the Notary add-on.

`requests` is imported lazily so the package imports fine without it installed.
"""
from __future__ import annotations

import os
from typing import List, Optional

from ..models import NotarialAct, new_id, now_iso


class SimulatedNotaryProvider:
    """Simulated notary — used for tests, demos, and offline operation."""

    name = "simulated"

    def perform_notarization(
        self,
        document_name: str,
        jurisdiction: str,
        signer_names: List[str],
        **kwargs,
    ) -> dict:
        """Return a simulated notarial act record."""
        state = jurisdiction.upper()
        act = NotarialAct(
            act_id=new_id("act"),
            notary_id="ntry_sim_0001",
            notary_name="Simulated Notary (Tangible sandbox)",
            commission_number=f"{state}-RON-{new_id('')[:6]}",
            commission_state=state,
            act_type="acknowledgment (RON)",
            performed_at=now_iso(),
            journal_entry=(
                f"Acknowledgment taken for {', '.join(signer_names)} on "
                f"'{document_name}' via audio-visual remote online notarization."
            ),
        )
        return {
            "status": "completed",
            "notarial_act": act,
            "notarization_link": None,
            "provider": self.name,
        }


class PandaDocNotaryProvider:
    """Real notarization via PandaDoc Notary On-Demand.

    Flow:
      1. Upload a PDF document to PandaDoc
      2. Create a notarization request with invitees
      3. Signers receive a notarization link (video session with a commissioned notary)
      4. On completion, the notarized document is available

    Environment variables:
      PANDADOC_API_KEY — your PandaDoc API key (sandbox or live)
    """

    name = "pandadoc"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("PANDADOC_API_KEY", "")
        self.base_url = "https://api.pandadoc.com/public/v2"

    def _headers(self) -> dict:
        return {
            "Authorization": f"API-Key {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_document_from_pdf(self, pdf_bytes: bytes, name: str,
                                  recipients: Optional[List[dict]] = None) -> str:
        """Upload a PDF and return the document_id.

        Uses the multipart upload endpoint. Returns the PandaDoc document ID.
        """
        import json as _json
        import httpx

        data_payload: dict = {"name": name}
        if recipients:
            data_payload["recipients"] = recipients

        resp = httpx.post(
            "https://api.pandadoc.com/public/v1/documents?upload",
            headers={"Authorization": f"API-Key {self.api_key}"},
            files={"file": (f"{name}.pdf", pdf_bytes, "application/pdf")},
            data={"data": _json.dumps(data_payload)},
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"PandaDoc document upload failed ({resp.status_code}): {resp.text}"
            )
        return resp.json()["id"]

    def create_notarization_request(
        self,
        document_id: str,
        invitees: List[dict],
        message: Optional[str] = None,
    ) -> dict:
        """Create a notarization request for a document.

        Args:
            document_id: PandaDoc document ID (must be in draft status).
            invitees: List of dicts with keys: email, first_name, last_name.
            message: Optional message to signers.

        Returns:
            Dict with notarization_link, status, and request metadata.
        """
        import httpx

        body: dict = {
            "document_id": document_id,
            "invitation": {
                "invitees": invitees,
            },
        }
        if message:
            body["invitation"]["message"] = message

        resp = httpx.post(
            f"{self.base_url}/notary/notarization-requests",
            headers=self._headers(),
            json=body,
            timeout=30,
        )

        if resp.status_code == 403:
            error_detail = resp.text
            if "INACTIVE_ADDON" in error_detail:
                return {
                    "request_id": None,
                    "notarization_link": None,
                    "status": "addon_required",
                    "document_id": document_id,
                    "provider": self.name,
                    "error": (
                        "The PandaDoc Notary On-Demand add-on is not installed. "
                        "Install it at https://app.pandadoc.com/a/#/integrations "
                        "or contact PandaDoc support."
                    ),
                }
            raise RuntimeError(f"PandaDoc notarization request failed ({resp.status_code}): {resp.text}")

        resp.raise_for_status()
        data = resp.json()
        return {
            "request_id": data.get("id"),
            "notarization_link": data.get("notarization_link"),
            "status": data.get("status", "pending"),
            "document_id": document_id,
            "provider": self.name,
        }

    def perform_notarization(
        self,
        document_name: str,
        jurisdiction: str,
        signer_names: List[str],
        document_pdf: Optional[bytes] = None,
        signer_emails: Optional[List[str]] = None,
    ) -> dict:
        """Full notarization flow: upload doc -> create request -> return link.

        If document_pdf is provided, uploads it to PandaDoc and creates a
        notarization request. The signer receives a link to complete the
        notarization via video with a commissioned notary.

        If no PDF is provided, returns a pending status indicating the
        notarization requires document upload before it can proceed.

        Returns a dict with status, notarial_act (if completed), and
        notarization_link (for pending sessions).
        """
        if not self.api_key:
            raise RuntimeError(
                "PANDADOC_API_KEY is required for the PandaDoc notary provider. "
                "Get a free sandbox key at https://signup.pandadoc.com/"
            )

        emails = signer_emails or [f"{name.lower().replace(' ', '.')}@example.com"
                                    for name in signer_names]
        invitees = []
        for name, email in zip(signer_names, emails):
            parts = name.split(" ", 1)
            invitees.append({
                "email": email,
                "first_name": parts[0],
                "last_name": parts[1] if len(parts) > 1 else "",
            })

        if document_pdf:
            recipients = []
            for inv in invitees:
                recipients.append({
                    "email": inv["email"],
                    "first_name": inv["first_name"],
                    "last_name": inv["last_name"],
                    "role": "Signer",
                })
            doc_id = self.create_document_from_pdf(document_pdf, document_name, recipients)
            result = self.create_notarization_request(
                document_id=doc_id,
                invitees=invitees,
                message=f"Notarization requested for '{document_name}' — jurisdiction: {jurisdiction}",
            )

            nr_status = result.get("status", "pending")
            out = {
                "status": nr_status,
                "notarial_act": None,
                "notarization_link": result.get("notarization_link"),
                "request_id": result.get("request_id"),
                "document_id": doc_id,
                "provider": self.name,
                "jurisdiction": jurisdiction.upper(),
                "signers": signer_names,
            }
            if result.get("error"):
                out["message"] = result["error"]
            return out

        # No PDF provided — return pending status with instructions
        return {
            "status": "pending_upload",
            "notarial_act": None,
            "notarization_link": None,
            "request_id": None,
            "document_id": None,
            "provider": self.name,
            "jurisdiction": jurisdiction.upper(),
            "signers": signer_names,
            "message": (
                f"Notarization of '{document_name}' requires a PDF upload. "
                f"Upload the document bytes via the API or SDK to proceed. "
                f"Signers: {', '.join(signer_names)} ({', '.join(emails)})"
            ),
        }


def default_notary_provider():
    """Select the notary provider by environment variable.

    TANGIBLE_NOTARY_PROVIDER = auto | simulated | pandadoc (default: auto)
    PANDADOC_API_KEY          = your PandaDoc API key
    """
    choice = os.environ.get("TANGIBLE_NOTARY_PROVIDER", "auto").lower()
    key = os.environ.get("PANDADOC_API_KEY")

    if choice == "pandadoc" or (choice == "auto" and key):
        if not key:
            raise RuntimeError("PANDADOC_API_KEY is required for the PandaDoc notary provider")
        return PandaDocNotaryProvider(key)

    return SimulatedNotaryProvider()
