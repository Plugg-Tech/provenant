"""HTTP API for Tangible.

Run:  uvicorn tangible.api:app --reload
Verbs:
  notarize        (sandbox / simulated fulfillment)
  verify_identity (LIVE via Stripe Identity when STRIPE_API_KEY is set)

Endpoints:
  POST /v1/actions/notarize
  GET  /v1/actions/{action_id}
  POST /v1/verify
  POST /v1/proofs/{proof_id}/revoke
  GET  /v1/ledger/verify
  POST /v1/actions/verify-identity
  GET  /v1/identity/{action_id}
  POST /v1/webhooks/stripe
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .identity_service import IdentityService
from .models import ACTION_NOTARIZE, ActionRequest, Party
from .service import TangibleService

app = FastAPI(title="Provenant API", version="0.3.0")
service = TangibleService()
identity_service = IdentityService()


@app.get("/", response_class=HTMLResponse)
def home():
    mode = "LIVE (Stripe Identity)" if os.environ.get("STRIPE_API_KEY") else "sandbox"
    return (
        "<html><body style='font-family:system-ui;max-width:640px;margin:64px auto;'>"
        "<h1>Provenant</h1>"
        "<p>The physical-action API for agents. Identity verification is "
        f"<b>{mode}</b>; notarization runs in sandbox.</p>"
        "<p><a href='/docs'>API docs</a></p>"
        "</body></html>"
    )


@app.get("/healthz")
def healthz():
    return {"ok": True, "identity_live": bool(os.environ.get("STRIPE_API_KEY"))}


# ---------- notarization (sandbox) ----------
class PartyIn(BaseModel):
    name: str
    email: str
    role: str = "signer"
    force_identity_fail: bool = False


class NotarizeIn(BaseModel):
    document_name: str
    document_sha256: str
    jurisdiction: str
    parties: List[PartyIn]
    reference: Optional[str] = None
    idempotency_key: Optional[str] = None


class VerifyIn(BaseModel):
    proof: dict


@app.post("/v1/actions/notarize")
def notarize(body: NotarizeIn):
    req = ActionRequest(
        action_type=ACTION_NOTARIZE,
        document_name=body.document_name,
        document_sha256=body.document_sha256,
        parties=[Party(**p.model_dump()) for p in body.parties],
        jurisdiction=body.jurisdiction,
        reference=body.reference,
        idempotency_key=body.idempotency_key,
    )
    return asdict(service.notarize(req))


@app.get("/v1/actions/{action_id}")
def get_action(action_id: str):
    result = service.get_action(action_id)
    if result is None:
        raise HTTPException(status_code=404, detail="action not found")
    return asdict(result)


@app.post("/v1/verify")
def verify(body: VerifyIn):
    # Time the actual verification: it's offline (no network), so this number is
    # the real "verify a signed proof in <1ms" wedge claim, not the human session.
    start = time.perf_counter()
    ok, reason = service.verify(body.proof)
    took_ms = round((time.perf_counter() - start) * 1000, 3)
    return {"valid": ok, "reason": reason, "took_ms": took_ms}


@app.post("/verify")
def verify_alias(body: VerifyIn):
    """Unversioned alias for the demo's `curl …/verify` snippet (web/try.html)."""
    return verify(body)


@app.post("/v1/proofs/{proof_id}/revoke")
def revoke(proof_id: str):
    service.revoke(proof_id)
    return {"proof_id": proof_id, "revoked": True}


@app.get("/v1/ledger/verify")
def ledger_verify():
    ok, reason = service.ledger.verify_chain()
    return {"valid": ok, "reason": reason, "entries": len(service.ledger)}


# ---------- identity verification (LIVE via Stripe Identity) ----------
class VerifyIdentityIn(BaseModel):
    name: str
    email: str
    return_url: Optional[str] = None


@app.post("/v1/actions/verify-identity")
def verify_identity_start(body: VerifyIdentityIn):
    sess = identity_service.start(Party(name=body.name, email=body.email), body.return_url)
    return asdict(sess)


@app.get("/v1/identity/{action_id}")
def identity_status(action_id: str):
    sess = identity_service.finalize(action_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="identity session not found")
    return asdict(sess)


@app.post("/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if secret:
        try:
            import stripe

            event = stripe.Webhook.construct_event(
                payload, request.headers.get("stripe-signature"), secret
            )
        except Exception as exc:  # bad signature / parse
            raise HTTPException(status_code=400, detail=f"webhook verification failed: {exc}")
    else:
        event = json.loads(payload or b"{}")

    etype = event.get("type", "")
    if etype.startswith("identity.verification_session"):
        obj = event.get("data", {}).get("object", {})
        session_id = obj.get("id")
        if session_id:
            identity_service.handle_session_event(session_id)
    return {"received": True}
