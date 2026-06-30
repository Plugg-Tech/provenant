"""Payment-rail adapters for the pay+proof verb.

A `RailAdapter` is the minimal seam that hides a money rail behind one normalized
verb (`charge`), so "rail-agnostic" is structurally true even with a single rail
today (Decision 1). The two-phase manual-capture lifecycle the pay flow needs
(authorize -> mint -> capture, Decision 4) is expressed *inside* each adapter via
the `capture()` / `void()` methods — it is not part of the minimal Protocol.

  SimulatedRail — deterministic, no keys (the no-keys default, Decision 11).
  StripeRail    — REAL Stripe via PaymentIntent with capture_method="manual"
                  (Decision 3). Test key (sk_test_...) runs the full API without
                  moving real money; live key (sk_live_...) moves real money.

Selection mirrors `identity_providers.default_identity_provider()`: an env-driven
`get_rail_adapter()` factory. `stripe` is imported lazily so the package imports
fine without it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

from ..models import new_id

# Normalized charge statuses returned by every adapter.
AUTHORIZED = "authorized"          # auth hold placed, awaiting capture
DECLINED = "declined"             # rail refused the charge; no hold
REQUIRES_CONFIRMATION = "requires_confirmation"  # needs interactive SCA/3DS
CAPTURED = "captured"            # funds captured


@dataclass
class ChargeRequest:
    """A normalized request to move money through a rail."""
    amount: int            # minor units (e.g. cents)
    currency: str          # ISO 4217, lowercase (e.g. "usd")
    payment_method: str    # rail-specific token (e.g. "pm_…" / "sim_ok")
    idempotency_key: str   # required; safe retries (Decision 12)


@dataclass
class ChargeResult:
    """A normalized result from a rail. `rail_ref` is the rail's own id for the
    money movement (e.g. a Stripe PaymentIntent id) used to capture/void later."""
    rail: str
    rail_ref: str
    status: str
    raw: dict = field(default_factory=dict)


@runtime_checkable
class RailAdapter(Protocol):
    """Minimal charge-only seam (Decision 1).

    A rail must expose `name` and `charge()`. The pay flow's manual-capture
    lifecycle (`capture`/`void`) is an adapter-internal detail, kept off the
    Protocol so a second rail is a drop-in with the smallest possible contract.
    """
    name: str

    def charge(self, req: ChargeRequest) -> ChargeResult:
        """Authorize (place an auth hold) — does NOT capture funds."""
        ...


class SimulatedRail:
    """No-keys, deterministic rail — the default so the first `pay()` returns a
    real signed receipt with no Stripe account (Decision 11).

    The `payment_method` string drives the outcome, mirroring the
    `force_identity_fail` simulation flag on `SimulatedIdentityProvider`:
      - contains "decline" -> declined
      - contains "confirm" -> requires_confirmation
      - anything else (e.g. "sim_ok") -> authorized
    """

    name = "simulated"

    def charge(self, req: ChargeRequest) -> ChargeResult:
        pm = (req.payment_method or "").lower()
        if "decline" in pm:
            status = DECLINED
        elif "confirm" in pm:
            status = REQUIRES_CONFIRMATION
        else:
            status = AUTHORIZED
        return ChargeResult(
            rail=self.name,
            rail_ref=new_id("sim_pi"),
            status=status,
            raw={"payment_method": req.payment_method},
        )

    def capture(self, rail_ref: str) -> ChargeResult:
        return ChargeResult(rail=self.name, rail_ref=rail_ref, status=CAPTURED)

    def void(self, rail_ref: str) -> None:
        # No external state to release in the simulator.
        return None


class StripeRail:
    """REAL Stripe rail via PaymentIntent with manual capture (Decisions 3 & 4).

    `charge()` creates and confirms a PaymentIntent with capture_method="manual",
    which places an authorization hold. `capture()` captures it; `void()` cancels
    it. Card declines and confirmation requirements are mapped to the normalized
    status vocabulary so the pay flow stays rail-agnostic.
    """

    name = "stripe"

    def __init__(self, api_key: str) -> None:
        import stripe  # lazy

        self._stripe = stripe
        stripe.api_key = api_key

    def charge(self, req: ChargeRequest) -> ChargeResult:
        try:
            intent = self._stripe.PaymentIntent.create(
                amount=req.amount,
                currency=req.currency,
                payment_method=req.payment_method,
                capture_method="manual",
                confirm=True,
                # No redirect-based confirmation: agents have no browser (D5).
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                idempotency_key=req.idempotency_key,
            )
        except self._stripe.error.CardError as exc:  # type: ignore[attr-defined]
            return ChargeResult(
                rail=self.name,
                rail_ref=getattr(getattr(exc, "error", None), "payment_intent", {}).get("id", "")
                if getattr(exc, "error", None) else "",
                status=DECLINED,
                raw={"error": str(exc)},
            )
        return ChargeResult(
            rail=self.name,
            rail_ref=intent.id,
            status=_map_stripe_status(intent.status),
            raw={"stripe_status": intent.status},
        )

    def capture(self, rail_ref: str) -> ChargeResult:
        intent = self._stripe.PaymentIntent.capture(rail_ref)
        return ChargeResult(
            rail=self.name,
            rail_ref=rail_ref,
            status=_map_stripe_status(intent.status),
            raw={"stripe_status": intent.status},
        )

    def void(self, rail_ref: str) -> None:
        if rail_ref:
            self._stripe.PaymentIntent.cancel(rail_ref)


def _map_stripe_status(status: str) -> str:
    """Map a Stripe PaymentIntent status onto our normalized vocabulary."""
    if status == "requires_capture":
        return AUTHORIZED
    if status == "succeeded":
        return CAPTURED
    if status in ("requires_action", "requires_confirmation", "requires_payment_method"):
        return REQUIRES_CONFIRMATION
    if status == "canceled":
        return DECLINED
    return REQUIRES_CONFIRMATION


def get_rail_adapter(choice: Optional[str] = None) -> RailAdapter:
    """Select the payment rail by environment, mirroring the identity factory.

    PROVENANT_RAIL = auto | simulated | stripe   (default: auto)
    STRIPE_API_KEY = sk_test_... or sk_live_...

    "auto" uses Stripe when STRIPE_API_KEY is set, otherwise the no-keys
    SimulatedRail (Decision 11).
    """
    choice = (choice or os.environ.get("PROVENANT_RAIL", "auto")).lower()
    stripe_key = os.environ.get("STRIPE_API_KEY")

    if choice == "stripe" or (choice == "auto" and stripe_key):
        if not stripe_key:
            raise RuntimeError("STRIPE_API_KEY is required for the Stripe rail")
        return StripeRail(stripe_key)

    return SimulatedRail()
