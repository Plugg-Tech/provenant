# Provenant — Instant Verification · Pricing Sheet

*One-pager for the warm-buyer validation call. Decisions 4 & 5 (plan `xzuWcxHctuSOrLkizGxKp`): bring a demo **and a real number** so the buyer gives a real reaction, not polite interest. The figures below are illustrative placeholders — replace with the buyer's actual bill (Decision 4) before the call.*

---

## The claim

**Verify a signed identity/action proof anywhere, offline, in under a millisecond.**
A Provenant proof re-verifies against a pinned key with **no callback** — the thing an incumbent KYC vendor structurally can't offer, because they re-run a check every time.

> What's priced here is **verification of an already-signed proof** (`crypto.verify_proof`), not the human identity session. That's the operation that's genuinely instant.

---

## Head-to-head

| | **Provenant** (verify a proof) | **Incumbent KYC** (re-run a check) |
|---|---|---|
| Latency | ~0.7 ms (offline, no network) | ~1–3 s (vendor round-trip) |
| Where it runs | Hosted **or** offline (pinned pubkey) | Vendor cloud only |
| Marginal cost | Compute-only (fractions of a cent) | ~$0.50–$2.50 / check (published rates) |
| Artifact | Signed, re-verifiable Ed25519 proof | A pass/fail result, not a portable artifact |
| Audit trail | Tamper-evident, hash-chained ledger | Vendor's dashboard |
| Standard | ADRP ProofBundle output (leading proposed standard) | Proprietary |

---

## Pricing (premium-vs-incumbent — illustrative)

| Plan | Price | For |
|---|---|---|
| **Verify** | **$0.10 / verification** | Re-verifying existing proofs at scale, offline-capable SDK included |
| **Issue + Verify** | **$0.75 / issued proof**, verification free | Issuing IAL2 identity proofs that anyone can re-verify forever |
| **Pilot** | **$2,500 / mo flat**, up to 50k verifications | Scoped 60-day pilot — the ask in this call |

**ROI framing (fill live):**
- Buyer's current per-check spend: `▶ $____ / check`
- Buyer's monthly check volume: `▶ ____ / mo`
- Current monthly spend: `▶ $____`
- Re-verifications that don't need a fresh check: `▶ ____%`
- **Redirectable spend with Provenant: `▶ $____ / mo`**

---

## The "premium" justification (when they push on price)

We are **not** the cheapest way to run a first-time KYC check — the incumbent stays in the issuance loop if you want it. We are the only way to get a **portable, offline-re-verifiable, audit-grade signed artifact** out of that check, so every downstream re-verification is instant and free of a vendor round-trip. You pay a premium once to never pay the per-check tax again on the same identity.

---

*Next step in the room: agree a scoped pilot at a stated price (Decision 6 — verbal commit within ~2 weeks, by ~14 July). Paperwork follows.*
