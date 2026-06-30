"""Identity-verification providers.

SimulatedIdentityProvider — deterministic, no network (default for tests/demo).
StripeIdentityProvider    — REAL Stripe Identity. Test mode (sk_test_...) runs the
                            full API without charges; live mode (sk_live_...) is
                            real IAL2 document verification.
PersonaIdentityProvider   — REAL identity verification via Persona. Supports
                            document verification + liveness checks. Free sandbox.

`stripe` and `httpx` are imported lazily so the package imports fine without them.
"""
from __future__ import annotations

import os
from typing import Optional

from ..models import Party, new_id


def _map_stripe(status: str) -> str:
    """Map a Stripe VerificationSession status to our vocabulary."""
    if status == "verified":
        return "verified"
    if status in ("canceled",):
        return "failed"
    return "pending"  # requires_input, processing


class SimulatedIdentityProvider:
    name = "simulated"

    def create_session(self, party: Party, return_url: Optional[str] = None) -> dict:
        verified = not getattr(party, "force_identity_fail", False)
        return {
            "session_id": new_id("ssn_sim"),
            "url": None,
            "status": "verified" if verified else "failed",
        }

    def get_result(self, session_id: str) -> dict:
        return {"status": "verified"}


class StripeIdentityProvider:
    name = "stripe"

    def __init__(self, api_key: str) -> None:
        import stripe  # lazy

        self._stripe = stripe
        stripe.api_key = api_key

    def create_session(self, party: Party, return_url: Optional[str] = None) -> dict:
        kwargs = {
            "type": "document",
            "metadata": {"email": party.email, "name": party.name},
        }
        if return_url:
            kwargs["return_url"] = return_url
        session = self._stripe.identity.VerificationSession.create(**kwargs)
        return {
            "session_id": session.id,
            "url": getattr(session, "url", None),
            "status": _map_stripe(session.status),
        }

    def get_result(self, session_id: str) -> dict:
        session = self._stripe.identity.VerificationSession.retrieve(session_id)
        return {"status": _map_stripe(session.status), "raw_status": session.status}


class PersonaIdentityProvider:
    """Identity verification via Persona.

    Flow:
      1. Create an inquiry (verification request) via API
      2. Persona returns a hosted verification URL
      3. The subject completes ID + liveness checks at the URL
      4. Poll or receive webhook when verification completes
      5. Retrieve the verification result

    Environment variables:
      PERSONA_API_KEY — your Persona API key (sandbox or live)

    Sandbox: sign up at https://withpersona.com, get a sandbox API key.
    Sandbox returns templated responses — no real documents needed.
    """

    name = "persona"

    def __init__(self, api_key: Optional[str] = None, template_id: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("PERSONA_API_KEY", "")
        self.template_id = template_id or os.environ.get("PERSONA_TEMPLATE_ID", "")
        self.base_url = "https://api.withpersona.com/api/v1"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Persona-Version": "2023-01-05",
            "Accept": "application/json",
        }

    def create_session(self, party: Party, return_url: Optional[str] = None) -> dict:
        """Create a Persona inquiry (identity verification session).

        Returns a dict with session_id, url, and status.
        Requires PERSONA_TEMPLATE_ID env var or template_id passed to __init__.
        """
        import httpx

        attrs: dict = {
            "reference-id": party.email,
            "fields": {
                "name-first": party.name.split(" ")[0],
                "name-last": party.name.split(" ", 1)[1] if " " in party.name else "",
                "email-address": party.email,
            },
        }
        if self.template_id:
            attrs["inquiry-template-id"] = self.template_id
        if return_url:
            attrs["redirect-uri"] = return_url

        body = {"data": {"attributes": attrs}}

        resp = httpx.post(
            f"{self.base_url}/inquiries",
            headers=self._headers(),
            json=body,
            timeout=30,
        )

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Persona inquiry creation failed ({resp.status_code}): {resp.text}"
            )

        data = resp.json()
        inquiry = data.get("data", {})
        inquiry_id = inquiry.get("id", "")
        status = inquiry.get("attributes", {}).get("status", "pending")

        # Build the hosted verification URL
        # Persona returns "created" or "pending" for new inquiries
        verification_url = None
        if status in ("pending", "created"):
            verification_url = f"https://app.withpersona.com/verify?inquiry-id={inquiry_id}"

        mapped_status = _map_persona_status(status)

        return {
            "session_id": inquiry_id,
            "url": verification_url,
            "status": mapped_status,
        }

    def get_result(self, session_id: str) -> dict:
        """Retrieve the status of a Persona inquiry."""
        import httpx

        resp = httpx.get(
            f"{self.base_url}/inquiries/{session_id}",
            headers=self._headers(),
            timeout=30,
        )

        if resp.status_code != 200:
            return {"status": "failed"}

        data = resp.json()
        inquiry = data.get("data", {})
        status = inquiry.get("attributes", {}).get("status", "pending")
        return {"status": _map_persona_status(status), "raw_status": status}


def _map_persona_status(status: str) -> str:
    """Map a Persona inquiry status to our vocabulary."""
    if status == "completed":
        return "verified"
    if status in ("failed", "declined"):
        return "failed"
    return "pending"  # pending, processing, awaiting_input


def default_identity_provider():
    """Select the identity provider by environment variable.

    TANGIBLE_IDENTITY_PROVIDER = auto | simulated | stripe | persona  (default: auto)
    STRIPE_API_KEY             = your Stripe API key
    PERSONA_API_KEY            = your Persona API key
    PERSONA_TEMPLATE_ID        = your Persona inquiry template ID (itmpl_xxx)
    """
    choice = os.environ.get("TANGIBLE_IDENTITY_PROVIDER", "auto").lower()
    stripe_key = os.environ.get("STRIPE_API_KEY")
    persona_key = os.environ.get("PERSONA_API_KEY")
    persona_template = os.environ.get("PERSONA_TEMPLATE_ID", "")

    if choice == "stripe" or (choice == "auto" and stripe_key):
        if not stripe_key:
            raise RuntimeError("STRIPE_API_KEY is required for the Stripe identity provider")
        return StripeIdentityProvider(stripe_key)

    if choice == "persona" or (choice == "auto" and persona_key):
        if not persona_key:
            raise RuntimeError("PERSONA_API_KEY is required for the Persona identity provider")
        return PersonaIdentityProvider(persona_key, template_id=persona_template)

    return SimulatedIdentityProvider()
