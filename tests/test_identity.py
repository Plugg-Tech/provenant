"""Tests for the verify_identity verb.

These run without network: the simulated provider is used by default, and the
Stripe provider is exercised against a fake `stripe` module injected via
monkeypatch (so we test our mapping/wiring, not Stripe itself).
"""
import sys
import types

import pytest

from tangible import crypto
from tangible.identity_service import IdentityService
from tangible.ledger import Ledger
from tangible.models import Party
from tangible.providers.identity_providers import (
    SimulatedIdentityProvider,
    StripeIdentityProvider,
    _map_stripe,
)


def _svc(ledger=None):
    return IdentityService(provider=SimulatedIdentityProvider(), ledger=ledger if ledger is not None else Ledger())


def test_identity_verification_issues_verifiable_proof():
    sess = _svc().start(Party("Dana", "dana@example.com"))
    assert sess.status == "verified"
    assert sess.proof is not None
    ok, reason = crypto.verify_proof(sess.proof)
    assert ok, reason
    assert sess.proof["action_type"] == "verify_identity"
    assert sess.proof["subject_email"] == "dana@example.com"


def test_identity_failure_yields_no_proof():
    sess = _svc().start(Party("Eve", "eve@example.com", force_identity_fail=True))
    assert sess.status == "failed"
    assert sess.proof is None


def test_identity_proof_is_ledgered():
    ledger = Ledger()
    _svc(ledger).start(Party("Dana", "dana@example.com"))
    ok, _ = ledger.verify_chain()
    assert ok
    assert len(ledger) == 1


def test_finalize_is_idempotent():
    svc = _svc()
    sess = svc.start(Party("Dana", "dana@example.com"))
    proof_id = sess.proof["proof_id"]
    again = svc.finalize(sess.action_id)
    assert again.proof["proof_id"] == proof_id  # not re-issued


def test_stripe_status_mapping():
    assert _map_stripe("verified") == "verified"
    assert _map_stripe("requires_input") == "pending"
    assert _map_stripe("processing") == "pending"
    assert _map_stripe("canceled") == "failed"


def test_stripe_provider_wiring_with_fake_client(monkeypatch):
    fake = types.ModuleType("stripe")

    class VerificationSession:
        @staticmethod
        def create(**kwargs):
            return types.SimpleNamespace(
                id="vs_123", url="https://verify.stripe.test/x", status="requires_input"
            )

        @staticmethod
        def retrieve(session_id):
            return types.SimpleNamespace(id=session_id, status="verified")

    fake.identity = types.SimpleNamespace(VerificationSession=VerificationSession)
    fake.api_key = None
    monkeypatch.setitem(sys.modules, "stripe", fake)

    provider = StripeIdentityProvider("sk_test_x")
    created = provider.create_session(Party("Dana", "dana@example.com"))
    assert created["session_id"] == "vs_123"
    assert created["status"] == "pending"
    assert created["url"].startswith("https://")

    result = provider.get_result("vs_123")
    assert result["status"] == "verified"


def test_full_identity_flow_with_pending_then_verified(monkeypatch):
    """Simulate the real async path: create -> pending -> later verified."""
    fake = types.ModuleType("stripe")
    state = {"status": "requires_input"}

    class VerificationSession:
        @staticmethod
        def create(**kwargs):
            return types.SimpleNamespace(id="vs_async", url="https://verify.stripe.test/y",
                                         status=state["status"])

        @staticmethod
        def retrieve(session_id):
            return types.SimpleNamespace(id=session_id, status=state["status"])

    fake.identity = types.SimpleNamespace(VerificationSession=VerificationSession)
    fake.api_key = None
    monkeypatch.setitem(sys.modules, "stripe", fake)

    svc = IdentityService(provider=StripeIdentityProvider("sk_test_x"), ledger=Ledger())
    sess = svc.start(Party("Dana", "dana@example.com"))
    assert sess.status == "pending"
    assert sess.proof is None

    state["status"] = "verified"  # human completes the session
    finalized = svc.finalize(sess.action_id)
    assert finalized.status == "verified"
    ok, _ = crypto.verify_proof(finalized.proof)
    assert ok
