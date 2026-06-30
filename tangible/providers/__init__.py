"""Fulfillment providers for Tangible verbs.

Selection is by environment variable so the same code runs simulated (no keys,
for tests/demo) or live (real provider, when keys are present):

  TANGIBLE_IDENTITY_PROVIDER = auto | simulated | stripe | persona  (default: auto)
  STRIPE_API_KEY             = sk_test_... or sk_live_...
  PERSONA_API_KEY            = persona_sandbox_... or persona_production_...

"auto" uses Stripe when STRIPE_API_KEY is set, Persona when PERSONA_API_KEY
is set, otherwise the simulated provider.
"""
from __future__ import annotations

from .identity_providers import (
    PersonaIdentityProvider,
    SimulatedIdentityProvider,
    StripeIdentityProvider,
    default_identity_provider,
)

__all__ = [
    "PersonaIdentityProvider",
    "SimulatedIdentityProvider",
    "StripeIdentityProvider",
    "default_identity_provider",
]
