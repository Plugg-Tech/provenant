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
