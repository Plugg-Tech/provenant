# Validation Call Script — Instant Verification Wedge

*The call is the real end-to-end test (plan `xzuWcxHctuSOrLkizGxKp`). Pass condition: a **verbal pilot commit at a stated price by ~14 July** (Decision 6). This is the instrument that produces a real yes/no — demo + a real price (Decision 5) + asking for their actual bill (Decision 4).*

**Who:** one warm, already-known buyer whose budget currently goes to an incumbent KYC vendor (Persona / Onfido / Socure).
**Bring:** the live demo link (`web/try.html`), the pricing sheet, this script.

---

## 0 · Before the call (this week)

- Send the live demo link. One line: *"Built the thing we talked about — verify a signed identity proof offline in under a millisecond. 60-second play before we talk?"*
- Book 25 minutes.

## 1 · Frame (1 min)

> "You're paying your KYC vendor every time you need to confirm an identity. I want to show you a way to pay once, get a signed proof, and then re-verify it instantly forever — offline, no callback. Then I want to ask you what you actually spend, so the number I give you is real."

## 2 · Demo (5 min) — let them break it

1. Open the demo. Point at the **head-to-head race**: Provenant ~0.7 ms vs incumbent ~2.4 s.
2. **Hand them the keyboard.** "Change one character in the proof." → it flips to `content_hash mismatch` live. *(This is the moment — they feel the integrity guarantee, they don't just hear it.)*
3. Toggle **Summary → Raw JSON → ADRP Bundle**. "Same object, three views. The ADRP bundle is the leading proposed interop standard — your engineers can consume it without a Provenant SDK."
4. Show the **curl + 3-line SDK**. "Callable hosted, or fully offline against a pinned public key. Same result with or without the network."

## 3 · Ask for the bill (5 min) — the real test (Decision 4)

Ask directly; a buyer who knows these numbers has a budgeted, redirectable line item:

- **"What do you pay per check today?"**  `▶ $____`
- **"Roughly how many checks a month?"**  `▶ ____`
- **"What share of those are re-verifying someone you've already checked?"**  `▶ ____%`
- "If those re-verifications were instant and free, what does that change for you?"

> If they don't know their per-check spend, the pain isn't budgeted — note that; it's a softer signal.

## 4 · State the price + watch the reaction (5 min) — Decision 5

Put the pricing sheet on the table. Fill the ROI line with their numbers live:

> "At your volume, that's about `$____/mo` of per-check spend you'd redirect. A scoped 60-day pilot is `$2,500/mo` flat. Want to run it?"

**Then stop talking.** The reaction to a real number is the data.

## 5 · The ask (2 min) — the kill bar (Decision 6)

> "Can we agree, today, to a scoped pilot at that price — paperwork to follow?"

- **Verbal commit + agreed scope = the "real yes."** → Continue; capture scope in writing same day.
- "Interesting, let me think" / no number commitment = **not** a yes. → Log honestly.

---

## After the call

- **Real yes** → it's the headline Phase 1 evidence for the Betaworks application (Decision 14).
- **No real yes by ~14 July** → fall back to whichever thread got the strongest signal and apply honestly narrow; no signal anywhere → don't force a pitch this cycle (Decision 18).
