# The Merge Plan — Provenant + Represent

*Drafted 30 June 2026. Validation-first: every phase below has a kill criterion. Don't carry a phase forward on vibes.*

---

## 0. Scope decision (made now, not implied)

**Merging:** Provenant (proof layer) + Represent (dispute/recovery layer). Both are about the same primitive — a signed, verifiable claim about whether a real-world or financial action happened correctly — just on opposite ends of a transaction.

**Not merging: Handoff.** Shopify catalog ops is a different market, different customer, different motion ("done-for-you" services-as-software vs. "trust infrastructure for agents"). Forcing it into this story dilutes the pitch instead of sharpening it. Handoff stays on its own track, judged by its own test: 3+ paying customers from the brother's network in 2 weeks. If that test passes, it's a second company, not a third pillar of this one. If it fails, it's dead — independently of anything below.

**The merged thesis, one sentence:** *A signed proof when an agent-initiated action happens, and automated recovery when it goes wrong — the same cryptographic ledger on both ends.*

---

## 1. Validate before building anything new (target: 2 weeks)

Don't write code yet. The honest gap from the last conversation is that neither half has a real "yes" from a customer or integrator — both are demos. Close that gap first.

**Test A — proof side.** Talk to 3–5 teams actually integrating ACP, AP2, or x402 right now (not hypothetically — people shipping against these specs this quarter). Ask one question: is trust/verification of the counterparty or the action a wall they've hit, and would they pay to remove it. Separately, ask one existing notarization/KYC buyer persona (a lender, a title company, a marketplace) whether sub-second, API-callable verification is worth a premium over what they use today — no agent framing required for this one.

**Test B — dispute side.** Get one real merchant (or a realistic stand-in dataset) to let you file one real dispute end to end through the Represent pipeline. Ask if they'd pay success-fee pricing for it today.

**Kill criterion:** if neither test produces a real "yes" — a person who would act, not just one who found it interesting — stop here. Don't force a merged pitch onto two unvalidated halves. Fall back to whichever single thread (if any) got a real signal, and apply with that.

**Continue criterion:** at least one real "yes" on each side. You don't need volume yet, you need proof that the pain is real and someone would pay to remove it.

---

## 2. Technical integration — only after Phase 1 signal (target: 2–3 weeks)

Keep this narrow. The goal is one shared primitive wrapping two services, not a rewrite.

- **Unify the proof schema.** Extend Provenant's existing Ed25519 + hash-chained ledger format (`tangible/crypto.py`, `ledger.py`) so a dispute outcome (win/loss, evidence used, narrative filed) can be issued as a proof in the same envelope as an identity or notarization proof. Same `key_id`, `content_hash`, `signature` shape either way.
- **Add a dispute verb to Provenant's action API.** Represent's agent pipeline (intake → evidence → narrative → file → outcome) becomes an action type Provenant's `service.py` orchestrates, not a separate codebase living in its own repo with its own auth and ledger.
- **Ship one ambient/cheap proof flow as the proof-of-concept for the timing thesis.** Take the existing `verify-identity` path and push latency/cost down — this is the concrete evidence for "machine-speed trust," not a slide.
- **Explicitly out of scope for this phase:** the open verification protocol/registry, and underwriting. Both are real ideas but premature without transaction volume. Building them now would be solving for a category that doesn't exist yet instead of the wedge that might.

---

## 3. One pitch, one demo (target: align with Betaworks priority deadline, 24 July 2026 — roughly 3.5 weeks from today)

- Rewrite the one-liner and "truth about the future world" answer to cover both halves in one sentence (draft above; tighten after Phase 1 evidence is in hand).
- One demo, not two: an agent triggers a real-world action (identity check or notarization) *and* a payment dispute, and both come back as the same signed-proof object. The visual point is "same primitive, two situations," not "two products."
- Fill the `▶ TO FILL` fields in the Betaworks doc using whatever Phase 1 evidence actually came back — a named integrator conversation beats a hypothetical every time reviewers read it.
- Update `provenant/web/index.html` and `product.html` copy to the merged framing — but only after Phase 1, so the website isn't selling a thesis nobody's confirmed wants buying.

**Fallback:** if Phase 2 isn't finished by the deadline, apply with Phase 1 evidence and the *plan* for the merged demo rather than a half-built one. A validated narrow thesis beats a polished but unvalidated merged one.

---

## 4. Scale moves — gated behind real usage, not in this plan's timeline

Open proof schema/registry, ambient pricing at volume, underwriting on the outcome ledger. These are the "category-defining" answers from the last conversation. They stay parked until there's enough real transaction volume to justify them — revisit only after Phase 2 is live with actual usage, not demo traffic.

---

## Risks (tracked, not hidden)

- **Reads as unfocused.** Two businesses glued together by narrative rather than shared infrastructure is a known investor red flag. Mitigation: the one shared technical primitive (the proof envelope) has to be real in the demo, not just asserted in the pitch.
- **No signal in Phase 1.** Real possibility. Decide now that "don't merge" is an acceptable output of this plan, not a failure of it.
- **Engineering surfaces differ.** Represent's evidence-assembly and processor-specific filing logic is genuinely different from Provenant's identity/notary providers. Integrate at the proof-schema boundary, not by merging codebases — two services, one contract.
- **Timeline is tight.** ~3.5 weeks to the priority deadline covers validation *and* integration *and* application writing. If it doesn't fit, cut Phase 2 scope before cutting Phase 1 — an honest, evidence-backed narrow pitch beats a rushed merged demo.

---

## Owner / next action

Emmanuel — start Phase 1 outreach this week (both tracks in parallel; each takes a few conversations, not a build). Revisit this plan after the first 3–5 conversations land, before writing a line of integration code.
