"""Identity-verification verb (verify_identity).

Real verification is asynchronous: an agent starts a session, hands the hosted
URL to the human, and the result arrives via polling or a webhook. On success we
issue the same kind of cryptographically signed, ledgered proof as notarization.
"""
from __future__ import annotations

from typing import Dict, Optional

from . import crypto
from .keyring import KeyRing, default_keyring
from .ledger import Ledger
from .models import IdentitySession, Party, new_id, now_iso
from .providers import default_identity_provider


class IdentityService:
    def __init__(self, provider=None, keyring: Optional[KeyRing] = None,
                 ledger: Optional[Ledger] = None) -> None:
        self.provider = provider or default_identity_provider()
        self.keyring = keyring or default_keyring()
        self.ledger = ledger if ledger is not None else Ledger()
        self._sessions: Dict[str, IdentitySession] = {}
        self._by_session: Dict[str, str] = {}

    def start(self, party: Party, return_url: Optional[str] = None) -> IdentitySession:
        res = self.provider.create_session(party, return_url)
        sess = IdentitySession(
            action_id=new_id("idv"),
            session_id=res["session_id"],
            provider=self.provider.name,
            url=res.get("url"),
            status=res["status"],
            party_email=party.email,
            party_name=party.name,
            created_at=now_iso(),
        )
        self._sessions[sess.action_id] = sess
        self._by_session[sess.session_id] = sess.action_id
        if sess.status == "verified":
            self._issue(sess)
        return sess

    def get(self, action_id: str) -> Optional[IdentitySession]:
        return self._sessions.get(action_id)

    def finalize(self, action_id: str) -> Optional[IdentitySession]:
        """Poll the provider and issue a proof if newly verified."""
        sess = self._sessions.get(action_id)
        if sess is None:
            return None
        if sess.status == "verified" and sess.proof:
            return sess
        res = self.provider.get_result(sess.session_id)
        sess.status = res["status"]
        if sess.status == "verified" and not sess.proof:
            self._issue(sess)
        return sess

    def handle_session_event(self, session_id: str) -> Optional[IdentitySession]:
        """Webhook entry point: resolve a provider session id and finalize it."""
        action_id = self._by_session.get(session_id)
        if action_id is None:
            return None
        return self.finalize(action_id)

    def verify(self, proof: dict):
        return crypto.verify_proof(proof, self.keyring)

    def _issue(self, sess: IdentitySession) -> None:
        content = {
            "proof_id": new_id("prf"),
            "action_type": "verify_identity",
            "subject_email": sess.party_email,
            "subject_name": sess.party_name,
            "provider": sess.provider,
            "session_id": sess.session_id,
            "ial_level": "IAL2",
            "verified": True,
            "issued_at": now_iso(),
            "issuer": "Tangible",
            "algorithm": "Ed25519",
        }
        proof = crypto.issue_proof(content, self.keyring)
        self.ledger.append(proof)
        sess.proof = proof
