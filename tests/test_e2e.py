"""End-to-end, unit, and hardening tests for the Tangible prototype."""
import hashlib
import json

from tangible import crypto, mcp_tool, timestamp
from tangible.keyring import KeyRing
from tangible.ledger import Ledger
from tangible.models import ActionRequest, Party
from tangible.service import TangibleService


def _hash(data: bytes = b"hello document") -> str:
    return hashlib.sha256(data).hexdigest()


def _req(jurisdiction="TX", fail=False):
    return ActionRequest(
        action_type="notarize",
        document_name="Doc",
        document_sha256=_hash(),
        parties=[Party(name="Alice", email="alice@example.com", force_identity_fail=fail)],
        jurisdiction=jurisdiction,
    )


# ---------- core pipeline ----------
def test_full_pipeline_succeeds_and_proof_verifies():
    result = TangibleService().notarize(_req())
    assert result.status == "completed"
    ok, reason = crypto.verify_proof(result.proof)
    assert ok, reason


def test_proof_is_bound_to_document():
    result = TangibleService().notarize(_req())
    ok, _ = crypto.verify_document(result.proof, b"hello document")
    assert ok
    bad, _ = crypto.verify_document(result.proof, b"different bytes")
    assert not bad


def test_tampering_is_detected():
    result = TangibleService().notarize(_req())
    tampered = json.loads(json.dumps(result.proof))
    tampered["document_sha256"] = "deadbeef"
    ok, _ = crypto.verify_proof(tampered)
    assert not ok


def test_signature_swap_is_detected():
    result = TangibleService().notarize(_req())
    tampered = json.loads(json.dumps(result.proof))
    tampered["notarial_act"]["commission_state"] = "ZZ"
    ok, _ = crypto.verify_proof(tampered)
    assert not ok


def test_ron_ineligible_state_is_rejected():
    result = TangibleService().notarize(_req(jurisdiction="ZZ"))
    assert result.status == "rejected"
    assert "RON" in result.rejection_reason


def test_bad_jurisdiction_format_is_rejected():
    result = TangibleService().notarize(_req(jurisdiction="Texas"))
    assert result.status == "rejected"
    assert "state code" in result.rejection_reason


def test_identity_failure_blocks_notarization():
    result = TangibleService().notarize(_req(fail=True))
    assert result.status == "rejected"
    assert "identity" in result.rejection_reason
    assert result.proof is None


def test_simulation_flag_never_leaks_into_proof():
    result = TangibleService().notarize(_req())
    for party in result.proof["parties"]:
        assert "force_identity_fail" not in party


def test_get_action_round_trip():
    svc = TangibleService()
    result = svc.notarize(_req())
    assert svc.get_action(result.action_id).action_id == result.action_id
    assert svc.get_action("nope") is None


def test_mcp_tool_call_succeeds_and_verifies():
    args = {
        "document_name": "Doc",
        "document_sha256": _hash(),
        "jurisdiction": "NY",
        "parties": [{"name": "Bob", "email": "bob@example.com"}],
    }
    res = mcp_tool.call_tool("tangible_notarize", args)
    assert res["status"] == "completed"
    ok, _ = crypto.verify_proof(res["proof"])
    assert ok


def test_mcp_unknown_tool():
    assert "error" in mcp_tool.call_tool("nope", {})


# ---------- hardening: pinned-key verification ----------
def test_untrusted_key_is_rejected():
    attacker = KeyRing(path=None)
    forged = crypto.issue_proof({"proof_id": "prf_x", "document_sha256": _hash()}, attacker)
    ok, reason = crypto.verify_proof(forged)  # default registry doesn't know attacker
    assert not ok
    assert "untrusted" in reason


def test_embedded_public_key_is_ignored():
    result = TangibleService().notarize(_req())
    proof = json.loads(json.dumps(result.proof))
    proof["public_key"] = "00" * 32  # corrupt the transparency-only field
    ok, _ = crypto.verify_proof(proof)
    assert ok  # verification trusts the registry, not the embedded key


def test_key_rotation_keeps_old_proofs_valid(tmp_path):
    kr = KeyRing(path=str(tmp_path / "kr.json"))
    svc = TangibleService(keyring=kr, ledger=Ledger())
    r1 = svc.notarize(_req())
    kr.rotate()
    r2 = svc.notarize(_req())
    assert r1.proof["key_id"] != r2.proof["key_id"]
    assert crypto.verify_proof(r1.proof, kr)[0]
    assert crypto.verify_proof(r2.proof, kr)[0]


# ---------- hardening: ledger ----------
def test_ledger_chain_is_valid_after_appends():
    ledger = Ledger()
    svc = TangibleService(ledger=ledger)
    svc.notarize(_req())
    svc.notarize(_req())
    ok, _ = ledger.verify_chain()
    assert ok
    assert len(ledger) == 2


def test_ledger_detects_tampering():
    ledger = Ledger()
    svc = TangibleService(ledger=ledger)
    svc.notarize(_req())
    svc.notarize(_req())
    ledger._entries[0]["content_hash"] = "tampered"
    ok, _ = ledger.verify_chain()
    assert not ok


# ---------- hardening: idempotency, revocation ----------
def test_idempotency_returns_same_proof_without_relisting():
    ledger = Ledger()
    svc = TangibleService(ledger=ledger)
    req1 = _req()
    req1.idempotency_key = "k1"
    req2 = _req()
    req2.idempotency_key = "k1"
    r1 = svc.notarize(req1)
    r2 = svc.notarize(req2)
    assert r1.proof["proof_id"] == r2.proof["proof_id"]
    assert len(ledger) == 1


def test_revocation_blocks_verification():
    svc = TangibleService()
    result = svc.notarize(_req())
    assert svc.verify(result.proof)[0]
    svc.revoke(result.proof["proof_id"])
    ok, reason = svc.verify(result.proof)
    assert not ok
    assert "revoked" in reason


# ---------- hardening: input validation ----------
def test_invalid_email_rejected():
    req = _req()
    req.parties[0].email = "not-an-email"
    assert TangibleService().notarize(req).status == "rejected"


def test_duplicate_parties_rejected():
    req = ActionRequest("notarize", "Doc", _hash(),
                        [Party("A", "a@x.com"), Party("B", "a@x.com")], "TX")
    res = TangibleService().notarize(req)
    assert res.status == "rejected"
    assert "duplicate" in res.rejection_reason


def test_bad_sha_rejected():
    req = ActionRequest("notarize", "Doc", "xyz", [Party("A", "a@x.com")], "TX")
    res = TangibleService().notarize(req)
    assert res.status == "rejected"
    assert "hex" in res.rejection_reason


# ---------- hardening: external anchor ----------
def test_anchor_token_verifies():
    token = timestamp.anchor("ab" * 32)
    ok, _ = crypto.verify_proof(token)
    assert ok


# ---------- the full agent demo ----------
def test_agent_demo_runs_clean():
    import agent_demo

    assert agent_demo.run() == 0
