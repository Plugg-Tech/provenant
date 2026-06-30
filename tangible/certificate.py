"""Render a human-readable notarial certificate from a proof.

Text rendering has no dependencies. PDF rendering is optional (requires
reportlab) and degrades gracefully if it is not installed.
"""
from __future__ import annotations


def render_certificate_text(proof: dict) -> str:
    act = proof["notarial_act"]
    lines = [
        "CERTIFICATE OF NOTARIAL ACT  (SANDBOX / SIMULATED)",
        "=" * 52,
        f"Proof ID:        {proof['proof_id']}",
        f"Document:        {proof['document_name']}",
        f"Document SHA256: {proof['document_sha256']}",
        f"Jurisdiction:    {proof['jurisdiction']}",
        f"Act:             {act['act_type']}",
        f"Notary:          {act['notary_name']}  (commission {act['commission_number']})",
        f"Performed at:    {act['performed_at']}",
        "",
        "Signers:",
    ]
    for p in proof["parties"]:
        lines.append(f"  - {p['name']} <{p['email']}> ({p['role']})")
    lines += [
        "",
        "Cryptographic proof:",
        f"  Algorithm:    {proof['algorithm']}",
        f"  Public key:   {proof['public_key']}",
        f"  Signature:    {proof['signature']}",
        f"  Content hash: {proof['content_hash']}",
        "",
        "Verify offline:  python -m tangible.verify <proof.json>",
    ]
    return "\n".join(lines)


def render_certificate_pdf(proof: dict, path: str) -> bool:
    """Write a one-page PDF certificate.

    Returns False (instead of raising) if reportlab is absent or the target file
    can't be written — e.g. it is currently open in a PDF viewer, which locks it
    on Windows. The PDF is a convenience artifact, never load-bearing.
    """
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except ImportError:
        return False

    try:
        c = canvas.Canvas(path, pagesize=LETTER)
        width, height = LETTER
        y = height - 72
        for line in render_certificate_text(proof).splitlines():
            c.setFont("Courier", 9)
            c.drawString(72, y, line[:110])
            y -= 13
            if y < 72:
                c.showPage()
                y = height - 72
        c.showPage()
        c.save()
        return True
    except OSError:
        return False
