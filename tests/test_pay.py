"""Tests for the pay+proof verb (verifiable receipts).

Mirrors the existing test layout (tests/test_e2e.py) and covers the spec's
required scenarios: two-phase happy path, mint-failure void, decline, idempotency,
linked-action binding, and test/live mode stamping.
"""
import pytest

from tangible import crypto
from tangible.keyring import KeyRing
from tangible.ledger import Ledger
from tangible.pay_service import (
    ConfirmationRequired,
    PayService,
    PaymentDeclined,
    ProofMintError,
    reconstruct_proof,
)
from tangible.providers.rail_providers import (
    AUTHORIZED,
    CAPTURED,
    ChargeRequest,
    ChargeResult,
    SimulatedRail,
    get_rail_adapter,
)


class SpyRail:
    """A rail that records lifecycle calls so tests can assert capture/void."""

    name = "spy"

    def __init__(self, status=AUTHORIZED):
        self._status = status
        self.charges = 0
        self.captures = 0
        self.voids = 0

    def charge(self, req: ChargeRequest) -> ChargeResult:
        self.charges += 1
        return ChargeResult(rail=self.name, rail_ref="spy_ref", status=self._status)

    def capture(self, rail_ref: str) -> ChargeResult:
        self.captures += 1
        return ChargeResult(rail=self.name, rail_ref=rail_ref, status=CAPTURED)

    def void(self, rail_ref: str) -> None:
        self.voids += 1


def _svc(rail=None, ledger=None, **kw):
    return PayService(rail=rail or SimulatedRail(),
                      ledger=ledger if ledger is not None else Ledger(), **kw)


# ---------- two-phase happy path ----------
def test_happy_path_authorize_mint_capture_and_verify():
    rail = SpyRail()
    ledger = Ledger()
    svc = _svc(rail=rail, ledger=ledger)
    receipt = svc.pay(4200, "usd", "sim_ok", idempotency_key="t1")

    assert rail.charges == 1 and rail.captures == 1 and rail.voids == 0
    assert receipt["signed"]["payment"]["amount"] == 4200
    assert receipt["signed"]["payment"]["status"] == "captured"

    ok, reason = crypto.verify_proof(reconstruct_proof(receipt))
    assert ok, reason

    chain_ok, _ = ledger.verify_chain()
    assert chain_ok and len(ledger) == 1


def test_receipt_tamper_is_detected():
    svc = _svc()
    receipt = svc.pay(1000, "usd", "sim_ok", idempotency_key="t1")
    receipt["signed"]["payment"]["amount"] = 999999  # tamper after signing
    ok, _ = crypto.verify_proof(reconstruct_proof(receipt))
    assert not ok


# ---------- mint-failure path: auth voided, nothing captured ----------
def test_mint_failure_voids_auth_and_raises_retry_safe(monkeypatch):
    rail = SpyRail()
    svc = _svc(rail=rail)

    def boom(*a, **k):
        raise RuntimeError("signing exploded")

    monkeypatch.setattr(crypto, "issue_proof", boom)

    with pytest.raises(ProofMintError) as ei:
        svc.pay(4200, "usd", "sim_ok", idempotency_key="t1")

    assert ei.value.retry_safe is True
    assert ei.value.code == "proof_mint_failed"
    assert rail.captures == 0  # nothing captured
    assert rail.voids == 1     # auth voided


# ---------- decline path: no auth held ----------
def test_decline_raises_and_holds_nothing():
    rail = SpyRail(status="declined")
    svc = _svc(rail=rail)
    with pytest.raises(PaymentDeclined) as ei:
        svc.pay(4200, "usd", "sim_decline", idempotency_key="t1")
    assert ei.value.retry_safe is False
    assert ei.value.code == "card_declined"
    assert rail.captures == 0 and rail.voids == 0  # no hold to release


def test_simulated_rail_declines_on_decline_token():
    svc = _svc(rail=SimulatedRail())
    with pytest.raises(PaymentDeclined):
        svc.pay(100, "usd", "sim_decline", idempotency_key="t1")


def test_confirmation_required_is_rejected():
    rail = SpyRail(status="requires_confirmation")
    svc = _svc(rail=rail)
    with pytest.raises(ConfirmationRequired):
        svc.pay(100, "usd", "sim_confirm", idempotency_key="t1")
    assert rail.captures == 0


# ---------- idempotency: same key -> single charge, identical receipt ----------
def test_idempotency_returns_same_receipt_without_recharging():
    rail = SpyRail()
    svc = _svc(rail=rail)
    r1 = svc.pay(4200, "usd", "sim_ok", idempotency_key="dup")
    r2 = svc.pay(4200, "usd", "sim_ok", idempotency_key="dup")
    assert r1["receipt_id"] == r2["receipt_id"]
    assert rail.charges == 1 and rail.captures == 1


def test_missing_idempotency_key_is_rejected():
    svc = _svc()
    with pytest.raises(Exception):
        svc.pay(100, "usd", "sim_ok", idempotency_key="")


# ---------- linked-action binding (Decision 2) ----------
def test_action_ref_is_co_signed_and_present():
    resolver = lambda ref: {"kind": "notarize", "verified": True}
    svc = _svc(action_resolver=resolver)
    receipt = svc.pay(4200, "usd", "sim_ok", idempotency_key="t1",
                      action_ref="act_77c")
    action = receipt["signed"]["action"]
    assert action["action_ref"] == "act_77c"
    assert action["kind"] == "notarize" and action["verified"] is True
    # The bound action is inside the signed bytes.
    ok, _ = crypto.verify_proof(reconstruct_proof(receipt))
    assert ok


def test_payment_only_when_no_action_ref():
    svc = _svc()
    receipt = svc.pay(4200, "usd", "sim_ok", idempotency_key="t1")
    assert receipt["signed"]["action"] is None
    ok, _ = crypto.verify_proof(reconstruct_proof(receipt))
    assert ok


def test_unknown_action_ref_marked_unverified():
    svc = _svc(action_resolver=lambda ref: None)
    receipt = svc.pay(100, "usd", "sim_ok", idempotency_key="t1", action_ref="act_x")
    assert receipt["signed"]["action"]["action_ref"] == "act_x"
    assert receipt["signed"]["action"]["verified"] is False


# ---------- mode stamping (Decision 13) ----------
def test_mode_test_for_pk_test_key():
    svc = _svc()
    receipt = svc.pay(100, "usd", "sim_ok", idempotency_key="t1", api_key="pk_test_abc")
    assert receipt["mode"] == "test"


def test_mode_live_for_pk_live_key():
    svc = _svc()
    receipt = svc.pay(100, "usd", "sim_ok", idempotency_key="t1", api_key="pk_live_abc")
    assert receipt["mode"] == "live"


def test_mode_defaults_to_test_without_key():
    svc = _svc()
    receipt = svc.pay(100, "usd", "sim_ok", idempotency_key="t1")
    assert receipt["mode"] == "test"


# ---------- rail factory ----------
def test_get_rail_adapter_defaults_to_simulated(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    monkeypatch.delenv("PROVENANT_RAIL", raising=False)
    assert get_rail_adapter().name == "simulated"


# ---------- verification uses pinned key registry ----------
def test_receipt_from_untrusted_key_is_rejected():
    attacker = KeyRing(path=None)
    svc = PayService(rail=SimulatedRail(), keyring=attacker, ledger=Ledger())
    receipt = svc.pay(100, "usd", "sim_ok", idempotency_key="t1")
    ok, reason = crypto.verify_proof(reconstruct_proof(receipt))  # default registry
    assert not ok
    assert "untrusted" in reason
