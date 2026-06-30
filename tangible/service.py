"""Orchestration: turn an ActionRequest into a signed, ledgered, verifiable proof.

Pipeline:
  0. idempotency check (return prior result for a repeated key)
  1. validate request (format, emails, dedupe, limits)
  2. identity-proof every signer (IAL2)         [simulated or Stripe]
  3. jurisdiction / RON eligibility routing
  4. perform the notarial act                    [simulated or PandaDoc]
  5. issue a cryptographically signed proof      [real]
  6. append to the tamper-evident ledger         [real]

Also supports revocation and registry-pinned verification.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Optional, Set, Tuple

from . import compliance, crypto, identity
from .keyring import KeyRing, default_keyring
from .ledger import Ledger
from .models import (
    STATUS_COMPLETED,
    STATUS_PENDING,
    STATUS_REJECTED,
    ActionRequest,
    ActionResult,
    Party,
    new_id,
    now_iso,
)
from .providers.notary_providers import default_notary_provider


def _party_dict(p: Party) -> dict:
    d = asdict(p)
    d.pop("force_identity_fail", None)  # never leak the simulation flag
    return d


def _request_dict(req: ActionRequest) -> dict:
    d = asdict(req)
    d["parties"] = [_party_dict(p) for p in req.parties]
    return d


class TangibleService:
    def __init__(self, keyring: Optional[KeyRing] = None, ledger: Optional[Ledger] = None,
                 notary_provider=None) -> None:
        self.keyring = keyring or default_keyring()
        self.ledger = ledger if ledger is not None else Ledger()
        self.notary_provider = notary_provider or default_notary_provider()
        self._actions: Dict[str, ActionResult] = {}
        self._idempotency: Dict[str, str] = {}  # idempotency_key -> action_id
        self._revoked: Set[str] = set()

    def notarize(self, req: ActionRequest, document_pdf: Optional[bytes] = None) -> ActionResult:
        # 0. idempotency
        if req.idempotency_key and req.idempotency_key in self._idempotency:
            return self._actions[self._idempotency[req.idempotency_key]]

        action_id = new_id("axn")
        created = now_iso()

        ok, reason = compliance.validate_request(req)
        if not ok:
            return self._reject(action_id, req, created, reason)

        id_results = [identity.verify_identity(p) for p in req.parties]
        failed = [r for r in id_results if not r.verified]
        if failed:
            who = ", ".join(r.party_email for r in failed)
            return self._reject(action_id, req, created, f"identity proofing failed for: {who}")

        eligible, ron_reason = compliance.check_ron_eligibility(req.jurisdiction)
        if not eligible:
            return self._reject(action_id, req, created, ron_reason)

        act_result = self.notary_provider.perform_notarization(
            document_name=req.document_name,
            jurisdiction=req.jurisdiction,
            signer_names=[p.name for p in req.parties],
            document_pdf=document_pdf,
        )

        notarial_act = act_result.get("notarial_act")
        notarial_act_dict = asdict(notarial_act) if notarial_act else {
            "act_id": new_id("act"),
            "notary_id": "pending",
            "notary_name": f"Notary via {self.notary_provider.name}",
            "commission_number": "pending",
            "commission_state": req.jurisdiction.upper(),
            "act_type": "pending (awaiting notary session)" if act_result.get("status") != "pending_upload" else "awaiting document upload",
            "performed_at": now_iso(),
            "journal_entry": act_result.get("message") or "Notarization session initiated — awaiting completion.",
        }

        content = {
            "proof_id": new_id("prf"),
            "action_type": req.action_type,
            "document_name": req.document_name,
            "document_sha256": req.document_sha256,
            "jurisdiction": req.jurisdiction.upper(),
            "parties": [_party_dict(p) for p in req.parties],
            "identity_verifications": [asdict(r) for r in id_results],
            "notarial_act": notarial_act_dict,
            "issued_at": now_iso(),
            "issuer": f"Provenant ({self.notary_provider.name})",
            "algorithm": "Ed25519",
            "notarization_status": act_result.get("status", "completed"),
        }

        if act_result.get("notarization_link"):
            content["notarization_link"] = act_result["notarization_link"]
        if act_result.get("request_id"):
            content["notarization_request_id"] = act_result["request_id"]

        proof = crypto.issue_proof(content, self.keyring)
        entry = self.ledger.append(proof)

        result_status = STATUS_COMPLETED if act_result.get("status") == "completed" else STATUS_PENDING
        result = ActionResult(
            action_id=action_id,
            status=result_status,
            request=_request_dict(req),
            proof=proof,
            ledger_entry=entry,
            created_at=created,
        )
        self._store(result, req)
        return result

    def _reject(self, action_id, req, created, reason) -> ActionResult:
        result = ActionResult(
            action_id=action_id,
            status=STATUS_REJECTED,
            request=_request_dict(req),
            rejection_reason=reason,
            created_at=created,
        )
        self._actions[action_id] = result
        return result

    def _store(self, result: ActionResult, req: ActionRequest) -> None:
        self._actions[result.action_id] = result
        if req.idempotency_key:
            self._idempotency[req.idempotency_key] = result.action_id

    def get_action(self, action_id: str) -> Optional[ActionResult]:
        return self._actions.get(action_id)

    def revoke(self, proof_id: str) -> None:
        self._revoked.add(proof_id)

    def is_revoked(self, proof_id: str) -> bool:
        return proof_id in self._revoked

    def verify(self, proof: dict) -> Tuple[bool, str]:
        ok, reason = crypto.verify_proof(proof, self.keyring)
        if not ok:
            return ok, reason
        if proof.get("proof_id") in self._revoked:
            return False, "proof has been revoked"
        return True, "valid"
