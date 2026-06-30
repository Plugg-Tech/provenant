"""Full demo: the agent-to-proof loop with all hardening checks.

Records a narrated trace suitable for the betaworks "product demo" video.
Shows: identity verification, notarization, proof verification, tamper
detection, forged-key rejection, ledger chain, external anchoring,
idempotency, and revocation.

Run:  python demo_full.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time

from tangible import crypto, mcp_tool, timestamp
from tangible.certificate import render_certificate_text
from tangible.identity_service import IdentityService
from tangible.keyring import KeyRing
from tangible.ledger import Ledger
from tangible.models import ACTION_NOTARIZE, ActionRequest, Party
from tangible.service import TangibleService


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _log(step: str, msg: str) -> None:
    print(f"  {step:<28} {msg}")


def _section(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def run() -> int:
    print()
    print("  PROVENANT — the physical-action API for agents")
    print("  Full demo: agent workflow -> signed proof -> verification")
    print()

    # =========================================================================
    # SECTION 1: Identity verification
    # =========================================================================
    _section("STEP 1: Identity verification")
    print()
    print("  An agent needs to confirm someone's identity before notarizing.")
    print("  It calls provenant_verify_identity — one API call, signed result.\n")

    id_svc = IdentityService()
    party = Party(name="Jordan Borrower", email="jordan@acme.com")
    _log("agent calls", "provenant_verify_identity(name='Jordan Borrower')")
    sess = id_svc.start(party)
    _log("status", sess.status)
    _log("provider", sess.provider)
    if sess.proof:
        ok, reason = crypto.verify_proof(sess.proof)
        _log("proof issued", f"proof_id={sess.proof['proof_id']}")
        _log("verify", f"valid={ok} ({reason})")

    # =========================================================================
    # SECTION 2: Notarization
    # =========================================================================
    _section("STEP 2: Notarization (the agent hits the physical-world wall)")
    print()
    print("  The agent drafts a document and reaches a step requiring")
    print("  a NOTARIZED signature. It cannot notarize itself.\n")

    document = b"PROMISSORY NOTE\nBorrower promises to pay USD 250,000 ... (mock).\n"
    doc_hash = _sha256(document)
    _log("draft document", f"assembled 'Promissory Note' (sha256 {doc_hash[:16]}...)")
    _log("workflow step", "next required step: NOTARIZED borrower signature")
    _log("decision", "calling provenant_notarize")

    args = {
        "document_name": "Promissory Note",
        "document_sha256": doc_hash,
        "jurisdiction": "TX",
        "parties": [{"name": "Jordan Borrower", "email": "jordan@acme.com", "role": "signer"}],
        "reference": "loan-4815162342",
    }
    _log("tool call", "provenant_notarize(jurisdiction=TX, signers=1)")
    result = mcp_tool.call_tool("tangible_notarize", args)

    if result["status"] != "completed":
        _log("REJECTED", str(result.get("rejection_reason")))
        return 1

    proof = result["proof"]
    _log("status", f"completed  proof_id={proof['proof_id']}  key_id={proof['key_id']}")

    # =========================================================================
    # SECTION 3: Proof verification
    # =========================================================================
    _section("STEP 3: Verify the proof (offline, no call back to Provenant)")
    print()

    ok, reason = crypto.verify_proof(proof)
    _log("signature", f"{ok}  ({reason})")

    bound, bound_reason = crypto.verify_document(proof, document)
    _log("doc binding", f"{bound}  ({bound_reason})")

    # =========================================================================
    # SECTION 4: Tamper detection
    # =========================================================================
    _section("STEP 4: Tamper detection")
    print()
    print("  Altering ANY signed field invalidates the proof.\n")

    tampered = json.loads(json.dumps(proof))
    tampered["jurisdiction"] = "CA"
    tampered_ok, _ = crypto.verify_proof(tampered)
    _log("altered proof", f"verifies = {tampered_ok}  (expected False)")

    # =========================================================================
    # SECTION 5: Forged-key attack
    # =========================================================================
    _section("STEP 5: Forged-key attack")
    print()
    print("  An attacker re-signs with their OWN key.")
    print("  Pinned-registry verification rejects it.\n")

    attacker = KeyRing(path=None)
    forged = crypto.issue_proof(
        {k: v for k, v in proof.items()
         if k not in ("key_id", "content_hash", "signature", "public_key")},
        attacker,
    )
    svc = mcp_tool.get_service()
    forged_ok, forged_reason = svc.verify(forged)
    _log("forged proof", f"verifies = {forged_ok}  ({forged_reason})")

    # =========================================================================
    # SECTION 6: Ledger chain
    # =========================================================================
    _section("STEP 6: Tamper-evident ledger")
    print()
    print("  Every proof is appended to a hash chain.")
    print("  Any insert, delete, or reorder breaks verification.\n")

    chain_ok, chain_reason = svc.ledger.verify_chain()
    _log("chain", f"{chain_ok}  ({chain_reason})")

    # =========================================================================
    # SECTION 7: External anchor
    # =========================================================================
    _section("STEP 7: External anchor (simulated TSA)")
    print()

    token = timestamp.anchor(svc.ledger.head())
    anchor_ok, _ = crypto.verify_proof(token)
    _log("anchor head", f"head={svc.ledger.head()[:16]}...  token valid={anchor_ok}")

    # =========================================================================
    # SECTION 8: Idempotency
    # =========================================================================
    _section("STEP 8: Idempotency")
    print()
    print("  A retried call with the same key does NOT notarize twice.\n")

    idem_args = dict(args, idempotency_key="idem-loan-demo")
    first = mcp_tool.call_tool("tangible_notarize", idem_args)
    second = mcp_tool.call_tool("tangible_notarize", idem_args)
    same = first["proof"]["proof_id"] == second["proof"]["proof_id"]
    _log("two calls", f"same proof_id = {same}  (no double notarization)")

    # =========================================================================
    # SECTION 9: Revocation
    # =========================================================================
    _section("STEP 9: Revocation")
    print()
    print("  A compromised proof can be revoked. Subsequent verification fails.\n")

    original_proof_id = proof["proof_id"]
    svc.revoke(original_proof_id)
    rev_ok, rev_reason = svc.verify(proof)
    _log("after revoke", f"verify = {rev_ok}  ({rev_reason})")

    # =========================================================================
    # SECTION 10: Summary
    # =========================================================================
    _section("SUMMARY")
    print()

    checks = [
        ("Identity verified", sess.status == "verified"),
        ("Notarization completed", result["status"] == "completed"),
        ("Signature valid", ok),
        ("Document bound", bound),
        ("Tamper detected", not tampered_ok),
        ("Forged key rejected", not forged_ok),
        ("Ledger chain valid", chain_ok),
        ("Anchor token valid", anchor_ok),
        ("Idempotency works", same),
        ("Revocation works", not rev_ok),
    ]

    all_pass = all(ok for _, ok in checks)
    for label, passed in checks:
        icon = "PASS" if passed else "FAIL"
        print(f"    [{icon}]  {label}")

    print()
    if all_pass:
        print("    All checks passed. The workflow can proceed safely.")
    else:
        print("    Some checks failed.")
        return 1

    # =========================================================================
    # Output artifacts
    # =========================================================================
    _section("ARTIFACTS")
    print()

    with open("sample_proof.json", "w") as f:
        json.dump(proof, f, indent=2)
    _log("wrote", "sample_proof.json")

    cert_text = render_certificate_text(proof)
    print()
    for line in cert_text.splitlines():
        print(f"    {line}")

    print()
    print(f"{'=' * 70}")
    print("  Done. Record this run for the betaworks demo video.")
    print(f"{'=' * 70}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
