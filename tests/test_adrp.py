"""Tests for the ADRP ProofBundle output adapter (crypto.to_adrp_bundle).

The adapter is a pure, read-only projection: it must produce the ProofBundle
shape *and* leave the signed proof verifiable, unchanged.
"""
import copy

from tangible import crypto
from tangible.identity_service import IdentityService
from tangible.ledger import Ledger
from tangible.models import Party
from tangible.providers.identity_providers import SimulatedIdentityProvider


def _identity_proof():
    svc = IdentityService(provider=SimulatedIdentityProvider(), ledger=Ledger())
    sess = svc.start(Party("Jane Okafor", "jane@acme.com"))
    assert sess.proof is not None
    return sess.proof


def test_bundle_has_proofbundle_shape():
    bundle = crypto.to_adrp_bundle(_identity_proof())

    assert bundle["proofType"] == "identity"
    assert bundle["subject"]["email"] == "jane@acme.com"
    assert bundle["subject"]["name"] == "Jane Okafor"
    assert bundle["claims"]["ial"] == "IAL2"
    assert bundle["claims"]["verified"] is True

    sig = bundle["signature"]
    assert set(sig) == {"keyId", "alg", "contentHash"}
    assert sig["alg"] == "Ed25519"
    assert sig["keyId"] and sig["contentHash"]


def test_bundle_signature_mirrors_signed_fields():
    proof = _identity_proof()
    bundle = crypto.to_adrp_bundle(proof)

    assert bundle["signature"]["keyId"] == proof["key_id"]
    assert bundle["signature"]["alg"] == proof["algorithm"]
    assert bundle["signature"]["contentHash"] == proof["content_hash"]


def test_adapter_is_read_only_and_proof_still_verifies():
    proof = _identity_proof()
    before = copy.deepcopy(proof)

    crypto.to_adrp_bundle(proof)

    # The adapter must not mutate the proof in any way...
    assert proof == before
    # ...and the original signed proof still verifies against the pinned key.
    ok, reason = crypto.verify_proof(proof)
    assert ok, reason


def test_unknown_action_type_falls_back_gracefully():
    bundle = crypto.to_adrp_bundle({"action_type": "witness"})
    assert bundle["proofType"] == "witness"
    assert bundle["subject"] == {}
    assert bundle["claims"] == {}
    assert bundle["signature"] == {"keyId": None, "alg": None, "contentHash": None}
