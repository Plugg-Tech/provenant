"""HTTP API tests. Skipped automatically if fastapi/httpx are not installed."""
import hashlib

import pytest


def _client():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from tangible.api import app

    return TestClient(app)


def _hash(data: bytes = b"api doc") -> str:
    return hashlib.sha256(data).hexdigest()


def _body(jurisdiction="TX"):
    return {
        "document_name": "API Doc",
        "document_sha256": _hash(),
        "jurisdiction": jurisdiction,
        "parties": [{"name": "Carol", "email": "carol@example.com"}],
    }


def test_api_notarize_then_verify():
    client = _client()
    resp = client.post("/v1/actions/notarize", json=_body())
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"

    verify = client.post("/v1/verify", json={"proof": data["proof"]})
    assert verify.json()["valid"] is True

    fetched = client.get(f"/v1/actions/{data['action_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["action_id"] == data["action_id"]


def test_api_rejects_ineligible_state():
    client = _client()
    data = client.post("/v1/actions/notarize", json=_body(jurisdiction="ZZ")).json()
    assert data["status"] == "rejected"


def test_api_unknown_action_404():
    client = _client()
    assert client.get("/v1/actions/does_not_exist").status_code == 404


def test_api_ledger_verify_and_revoke():
    client = _client()
    data = client.post("/v1/actions/notarize", json=_body()).json()
    proof_id = data["proof"]["proof_id"]

    ledger = client.get("/v1/ledger/verify").json()
    assert ledger["valid"] is True

    client.post(f"/v1/proofs/{proof_id}/revoke")
    after = client.post("/v1/verify", json={"proof": data["proof"]}).json()
    assert after["valid"] is False


def test_api_verify_identity_simulated():
    client = _client()
    resp = client.post("/v1/actions/verify-identity",
                       json={"name": "Dana", "email": "dana@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "verified"
    assert data["proof"] is not None
    verify = client.post("/v1/verify", json={"proof": data["proof"]})
    assert verify.json()["valid"] is True


def test_api_stripe_webhook_without_secret(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    client = _client()
    started = client.post("/v1/actions/verify-identity",
                          json={"name": "Dana", "email": "dana@example.com"}).json()
    event = {
        "type": "identity.verification_session.verified",
        "data": {"object": {"id": started["session_id"]}},
    }
    resp = client.post("/v1/webhooks/stripe", json=event)
    assert resp.json()["received"] is True


def test_api_pay_then_verify_receipt():
    client = _client()
    resp = client.post("/v1/actions/pay", json={
        "amount": 4200, "currency": "usd",
        "payment_method": "sim_ok", "idempotency_key": "api-pay-1",
    })
    assert resp.status_code == 200
    receipt = resp.json()
    assert receipt["signed"]["payment"]["amount"] == 4200
    # The receipt verifies via the same /v1/verify endpoint (Decision 8).
    verify = client.post("/v1/verify", json={"proof": receipt})
    assert verify.json()["valid"] is True

    fetched = client.get(f"/v1/receipts/{receipt['receipt_id']}")
    assert fetched.status_code == 200


def test_api_pay_decline_returns_code_message_hint():
    client = _client()
    resp = client.post("/v1/actions/pay", json={
        "amount": 100, "currency": "usd",
        "payment_method": "sim_decline", "idempotency_key": "api-decline-1",
    })
    assert resp.status_code == 402
    err = resp.json()["error"]
    assert err["code"] == "card_declined"
    assert err["message"] and err["hint"]
    assert err["retry_safe"] is False


def test_api_pay_mode_from_bearer_key():
    client = _client()
    resp = client.post("/v1/actions/pay",
                       headers={"Authorization": "Bearer pk_live_abc"},
                       json={"amount": 100, "currency": "usd",
                             "payment_method": "sim_ok", "idempotency_key": "api-live-1"})
    assert resp.json()["mode"] == "live"


def test_api_home_and_health():
    client = _client()
    assert client.get("/").status_code == 200
    assert client.get("/healthz").json()["ok"] is True
