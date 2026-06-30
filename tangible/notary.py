"""The notarial act.

SIMULATED. In production a commissioned notary (or the user's RON-platform
partner) performs and journals the act during an audio-visual session. Here we
synthesize a faithful act record so the rest of the pipeline — and the signed
proof — is exercised exactly as it would be in production.
"""
from __future__ import annotations

import random
from typing import List

from .models import NotarialAct, new_id, now_iso


def perform_notarial_act(
    document_name: str, jurisdiction: str, signer_names: List[str]
) -> NotarialAct:
    state = jurisdiction.upper()
    return NotarialAct(
        act_id=new_id("act"),
        notary_id="ntry_sim_0001",
        notary_name="Simulated Notary (Tangible sandbox)",
        commission_number=f"{state}-RON-{random.randint(100000, 999999)}",
        commission_state=state,
        act_type="acknowledgment (RON)",
        performed_at=now_iso(),
        journal_entry=(
            f"Acknowledgment taken for {', '.join(signer_names)} on "
            f"'{document_name}' via audio-visual remote online notarization."
        ),
    )
