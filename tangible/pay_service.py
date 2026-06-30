"""pay+proof orchestration: charge a rail and mint a verifiable receipt.

The product invariant is **no captured payment ever lacks a valid proof**. We get
it with a two-phase flow (Decision 4):

  1. authorize  — place an auth hold on the rail (no money moves yet)
  2. mint       — sign the receipt over {payment, action} and append to the ledger
  3. capture    — capture funds ONLY if minting succeeded

On any failure between authorize and capture, the auth is **voided**, so money
never moves without a proof, and the tamper-evident ledger is never polluted with
rollback states.

The returned receipt is a nested envelope (Decision 8):

    {
      "receipt_id", "mode",
      "signed": { "payment": {...}, "action": {...} | null },
      "proof":  { "alg", "key_id", "content_hash", "sig", "public_key" },
      "ledger": { "seq", "prev_hash", "entry_hash", "appended_at" }
    }

`signed` is the exact byte range the Ed25519 signature covers; `crypto.py` and
`ledger.py` are reused unchanged. `reconstruct_proof()` rebuilds the flat proof
object the existing `crypto.verify_proof()` expects, so /v1/verify validates a
receipt with no new signing format.
"""
from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

from . import crypto
from .keyring import KeyRing, default_keyring
from .ledger import Ledger
from .models import new_id, now_iso
from .providers.rail_providers import (
    AUTHORIZED,
    DECLINED,
    REQUIRES_CONFIRMATION,
    ChargeRequest,
    RailAdapter,
    get_rail_adapter,
)

# ---- server-side typed failures (Decision 9 / 14) ----
# Each carries a stable machine `code`, a human `message`, an actionable `hint`,
# a `retry_safe` flag, and the HTTP status the API should return.


class PayError(Exception):
    code = "pay_error"
    http_status = 400
    retry_safe = False

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "retry_safe": self.retry_safe,
        }


class PaymentDeclined(PayError):
    code = "card_declined"
    http_status = 402
    retry_safe = False


class ProofMintError(PayError):
    code = "proof_mint_failed"
    http_status = 500
    retry_safe = True


class ConfirmationRequired(PayError):
    code = "confirmation_required"
    http_status = 402
    retry_safe = False


# An action resolver maps an action_ref to a small descriptor of the proven
# action it points at (kind + verified). Wired to the live notarize/identity
# stores by the API; defaults to an unverified descriptor when absent.
ActionResolver = Callable[[str], Optional[dict]]


def reconstruct_proof(receipt: dict) -> dict:
    """Rebuild the flat proof object that `crypto.verify_proof` expects from a
    nested receipt envelope. Pure inverse of how `mint` splits the proof."""
    p = receipt["proof"]
    flat = dict(receipt["signed"])  # payment, action
    flat["key_id"] = p["key_id"]
    flat["content_hash"] = p["content_hash"]
    flat["signature"] = p["sig"]
    flat["public_key"] = p["public_key"]
    return flat


def is_receipt(obj: dict) -> bool:
    """True if `obj` is a pay receipt envelope rather than a flat proof."""
    return isinstance(obj, dict) and "signed" in obj and "proof" in obj


def mode_for_key(api_key: Optional[str]) -> str:
    """Derive test/live from the key prefix (Decision 13). `pk_live_…` -> live;
    everything else (including no key) -> test."""
    return "live" if (api_key or "").startswith("pk_live") else "test"


class PayService:
    def __init__(self, rail: Optional[RailAdapter] = None,
                 keyring: Optional[KeyRing] = None,
                 ledger: Optional[Ledger] = None,
                 action_resolver: Optional[ActionResolver] = None) -> None:
        self.rail = rail or get_rail_adapter()
        self.keyring = keyring or default_keyring()
        self.ledger = ledger if ledger is not None else Ledger()
        self.action_resolver = action_resolver
        self._receipts: Dict[str, dict] = {}          # receipt_id -> receipt
        self._idempotency: Dict[str, str] = {}        # idempotency_key -> receipt_id

    def pay(self, amount: int, currency: str, payment_method: str,
            idempotency_key: str, action_ref: Optional[str] = None,
            api_key: Optional[str] = None, payer: Optional[str] = None) -> dict:
        """Charge and return a verifiable receipt. Two-phase: authorize -> mint
        -> capture, voiding the auth on any failure (Decision 4)."""
        if not idempotency_key:
            raise PayError(
                "idempotency_key is required",
                hint="Supply a stable idempotency_key so retries don't double-charge.",
            )

        # Idempotent replay: return the original receipt, never a second charge.
        if idempotency_key in self._idempotency:
            return self._receipts[self._idempotency[idempotency_key]]

        mode = mode_for_key(api_key)
        req = ChargeRequest(
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
        )

        # 1. authorize (auth hold; no money moves yet)
        auth = self.rail.charge(req)
        if auth.status == DECLINED:
            raise PaymentDeclined(
                "The card was declined.",
                hint="No auth was held; safe to retry with a new payment_method.",
            )
        if auth.status == REQUIRES_CONFIRMATION:
            # Confirmation-free only for the MVP (Decision 5); nothing was held.
            self.rail.void(auth.rail_ref)
            raise ConfirmationRequired(
                "This payment requires interactive confirmation (SCA/3DS).",
                hint="Use a confirmation-free payment_method for the synchronous pay flow.",
            )
        if auth.status != AUTHORIZED:  # defensive
            self.rail.void(auth.rail_ref)
            raise PaymentDeclined(
                f"Unexpected rail status: {auth.status}",
                hint="No funds were captured; safe to retry.",
            )

        receipt_id = new_id("rcpt")
        payment_block = {
            "amount": amount,
            "currency": currency,
            "rail": auth.rail,
            "rail_ref": auth.rail_ref,
            "status": "captured",
            "payer": payer or "agent",
        }
        action_block = self._resolve_action(action_ref)

        # 2. mint: sign {payment, action} and append to the ledger. Any failure
        #    here voids the auth so no captured payment ever lacks a proof.
        try:
            signed = {"payment": payment_block, "action": action_block}
            full = crypto.issue_proof(signed, self.keyring)
            entry = self.ledger.append({
                "proof_id": receipt_id,
                "content_hash": full["content_hash"],
            })
        except Exception as exc:
            self.rail.void(auth.rail_ref)
            raise ProofMintError(
                f"Failed to mint proof: {exc}",
                hint="The authorization was voided; nothing was captured — safe to retry.",
            )

        # 3. capture (only after a valid proof exists)
        try:
            self.rail.capture(auth.rail_ref)
        except Exception as exc:
            self.rail.void(auth.rail_ref)
            raise PaymentDeclined(
                f"Capture failed: {exc}",
                hint="The authorization was voided; nothing was captured — safe to retry.",
            )

        receipt = {
            "receipt_id": receipt_id,
            "mode": mode,
            "signed": signed,
            "proof": {
                "alg": "ed25519",
                "key_id": full["key_id"],
                "content_hash": full["content_hash"],
                "sig": full["signature"],
                "public_key": full["public_key"],
            },
            "ledger": {
                "seq": entry["seq"],
                "prev_hash": entry["prev_hash"],
                "entry_hash": entry["entry_hash"],
                "appended_at": entry["appended_at"],
            },
            "created_at": now_iso(),
        }

        self._receipts[receipt_id] = receipt
        self._idempotency[idempotency_key] = receipt_id
        return receipt

    def _resolve_action(self, action_ref: Optional[str]) -> Optional[dict]:
        """Build the bound-action block (Decision 2). Falls back to payment-only
        (None) when no action_ref is given."""
        if not action_ref:
            return None
        if self.action_resolver is not None:
            resolved = self.action_resolver(action_ref)
            if resolved:
                resolved.setdefault("action_ref", action_ref)
                return resolved
        return {"action_ref": action_ref, "kind": "unknown", "verified": False}

    def get_receipt(self, receipt_id: str) -> Optional[dict]:
        return self._receipts.get(receipt_id)

    def verify_receipt(self, receipt: dict) -> Tuple[bool, str]:
        """Validate a receipt by reconstructing the flat proof and reusing the
        existing pinned-key verification."""
        return crypto.verify_proof(reconstruct_proof(receipt), self.keyring)
