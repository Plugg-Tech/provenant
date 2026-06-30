"""End-to-end demo: an AI agent that hits the physical-world wall and calls Tangible.

A mock LOAN-CLOSING agent runs a workflow, dead-ends at a step that requires a
NOTARIZED signature, calls the `tangible_notarize` tool, then exercises the
hardening: registry-pinned verification, document binding, tamper detection, a
forged-key attack (rejected), the tamper-evident ledger, external anchoring,
idempotency, and revocation.

In production the loop is driven by your LLM agent deciding to call the tool;
here it is scripted so it runs deterministically and offline. Record your screen
running this for the betaworks "product demo" video.

Run:  python agent_demo.py
"""
from __future__ import annotations

import hashlib
import json

from tangible import crypto, mcp_tool, timestamp
from tangible.certificate import render_certificate_pdf, render_certificate_text
from tangible.keyring import KeyRing


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _log(step: str, msg: str) -> None:
    print(f"[agent] {step:<22} | {msg}")


def run() -> int:
    print("=" * 72)
    print("MOCK LOAN-CLOSING AGENT  ->  powered by Tangible (sandbox)")
    print("=" * 72)
    service = mcp_tool.get_service()

    # 1. The agent assembles the closing document.
    document = b"PROMISSORY NOTE\nBorrower promises to pay USD 250,000 ... (mock).\n"
    doc_hash = _sha256(document)
    _log("draft document", f"assembled 'Promissory Note' (sha256 {doc_hash[:16]}...)")

    # 2. The agent reaches a step it cannot do on its own.
    _log("workflow step", "next required step: NOTARIZED borrower signature")
    _log("decision", "I cannot notarize this myself -> calling tangible_notarize")

    # 3. The agent calls the Tangible tool.
    args = {
        "document_name": "Promissory Note",
        "document_sha256": doc_hash,
        "jurisdiction": "TX",
        "parties": [{"name": "Jordan Borrower", "email": "jordan@example.com", "role": "signer"}],
        "reference": "loan-4815162342",
    }
    _log("tool call", "tangible_notarize(jurisdiction=TX, signers=1)")
    result = mcp_tool.call_tool("tangible_notarize", args)
    if result["status"] != "completed":
        _log("REJECTED", str(result.get("rejection_reason")))
        return 1
    proof = result["proof"]
    _log("tool result", f"status=completed  proof_id={proof['proof_id']}  key_id={proof['key_id']}")

    # 4. Registry-pinned signature verification.
    ok, reason = crypto.verify_proof(proof)
    _log("verify signature", f"{ok}  ({reason})")

    # 5. Document binding.
    bound, bound_reason = crypto.verify_document(proof, document)
    _log("verify doc binding", f"{bound}  ({bound_reason})")

    # 6. Tamper test: altering any signed field invalidates the proof.
    tampered = json.loads(json.dumps(proof))
    tampered["jurisdiction"] = "CA"
    tampered_ok, _ = crypto.verify_proof(tampered)
    _log("tamper check", f"altered proof verifies = {tampered_ok}  (expected False)")

    # 7. Forged-key attack: attacker re-signs with their OWN key and embeds their
    #    public key. Pinned-registry verification rejects it (untrusted key_id).
    attacker = KeyRing(path=None)
    forged = crypto.issue_proof({k: v for k, v in proof.items()
                                 if k not in ("key_id", "content_hash", "signature", "public_key")},
                                attacker)
    forged_ok, forged_reason = service.verify(forged)
    _log("forged-key attack", f"forged proof verifies = {forged_ok}  ({forged_reason})")

    # 8. Tamper-evident ledger.
    chain_ok, chain_reason = service.ledger.verify_chain()
    _log("ledger chain", f"{chain_ok}  ({chain_reason})")

    # 9. External anchor of the ledger head (simulated TSA).
    token = timestamp.anchor(service.ledger.head())
    anchor_ok, _ = crypto.verify_proof(token)
    _log("anchor head", f"anchored head {service.ledger.head()[:16]}...  token valid={anchor_ok}")

    # 10. Idempotency: a retried call with the same key does NOT notarize twice.
    idem_args = dict(args, idempotency_key="idem-loan-001")
    first = mcp_tool.call_tool("tangible_notarize", idem_args)
    second = mcp_tool.call_tool("tangible_notarize", idem_args)
    same = first["proof"]["proof_id"] == second["proof"]["proof_id"]
    _log("idempotency", f"two calls, same proof_id = {same}  (no double notarization)")

    # 11. Revocation.
    service.revoke(proof["proof_id"])
    rev_ok, rev_reason = service.verify(proof)
    _log("revocation", f"after revoke, verify = {rev_ok}  ({rev_reason})")

    checks = [ok, bound, not tampered_ok, not forged_ok, chain_ok, anchor_ok, same, not rev_ok]
    if not all(checks):
        _log("FAIL", "one or more hardening checks did not pass")
        return 1

    _log("workflow", "all checks passed; closing can proceed safely [done]")
    print("-" * 72)
    print(render_certificate_text(proof))
    print("-" * 72)

    with open("sample_proof.json", "w") as f:
        json.dump(proof, f, indent=2)
    _log("artifact", "wrote sample_proof.json (verify: python -m tangible.verify sample_proof.json)")
    if render_certificate_pdf(proof, "sample_certificate.pdf"):
        _log("artifact", "wrote sample_certificate.pdf")
    else:
        _log("artifact", "skipped PDF (reportlab missing, or sample_certificate.pdf is open/locked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
