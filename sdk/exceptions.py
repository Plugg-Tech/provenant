"""Provenant SDK exceptions."""
from __future__ import annotations


class ProvenantError(Exception):
    """Base exception for all Provenant SDK errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(ProvenantError):
    """Raised when the API key is missing or invalid (401/403)."""
    pass


class ActionRejectedError(ProvenantError):
    """Raised when an action is rejected (e.g. invalid jurisdiction, identity failure)."""

    def __init__(self, action_id: str, reason: str, response: dict | None = None):
        super().__init__(f"Action {action_id} rejected: {reason}", status_code=200, response=response)
        self.action_id = action_id
        self.reason = reason


class NotFoundError(ProvenantError):
    """Raised when an action or proof is not found (404)."""
    pass


class PaymentError(ProvenantError):
    """Base for pay() failures. Carries a stable machine `code`, a human-readable
    message, an actionable `hint`, and a `retry_safe` flag an agent can branch on
    (Decisions 9 & 14)."""

    def __init__(self, message: str, code: str = "pay_error", hint: str = "",
                 retry_safe: bool = False, status_code: int | None = None,
                 response: dict | None = None):
        super().__init__(message, status_code=status_code, response=response)
        self.code = code
        self.hint = hint
        self.retry_safe = retry_safe


class PaymentDeclined(PaymentError):
    """The rail declined the charge. No auth was held (retry_safe=False)."""
    pass


class ProofMintError(PaymentError):
    """Minting the proof failed; the auth was voided and nothing was captured, so
    it is safe to retry (retry_safe=True)."""
    pass


class ConfirmationRequired(PaymentError):
    """The payment needs interactive confirmation (SCA/3DS), which the
    synchronous pay flow does not handle (Decision 5)."""
    pass


# Map server error codes to the typed exception classes (Decision 14).
PAYMENT_EXCEPTIONS = {
    "card_declined": PaymentDeclined,
    "proof_mint_failed": ProofMintError,
    "confirmation_required": ConfirmationRequired,
}
