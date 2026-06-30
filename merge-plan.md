# The Merge Plan — Provenant + Represent

*Drafted 30 June 2026. Updated with verified competitive intelligence 30 June 2026. Validation-first: every phase below has a kill criterion. Don't carry a phase forward on vibes.*

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

---

## Addendum — Verified Competitive Intelligence (30 June 2026)

A research report was reviewed and fact-checked against live sources. Here's what it changes, and what it doesn't.

### What's confirmed real

**ADRP / ATXN / VCAP** — Active IETF internet-drafts from SwarmSync.AI (Ben Stone), published April 2026. These are real, architecturally serious specifications covering: A2A transaction definition (ATXN), dispute resolution state machine (ADRP), verified commerce settlement (VCAP), and AP2 binding (VCAP-AP2). They explicitly define the "counter-attestation override pattern" — an immutable original proof superseded by an equally immutable ruling on the same append-only chain. This is the exact merged thesis, specified by a third party, published before you ship it. That's useful.

**AgentCourt** — Real, open-source, live at agentcourt.org. Policy-driven dispute resolution API: 7 policy templates, 39 deterministic rules, sub-500ms rulings, $0.05/dispute via x402 USDC on Base, MCP server and Python/JS SDKs available. It is a direct competitor to Represent's dispute pipeline, not just a market validator.

**CertNode** — Real. Reflex product does automated Stripe chargeback defense in under 60 seconds, $0.03/transaction captured, FRE 902(13)/(14) compliant, RFC 3161 timestamped. A direct competitor to Provenant's proof-issuance layer, specifically in the fiat/card chargeback context.

**Internet Court** (internetcourt.org) — Also real. AI agent agreements + AI jury verdicts. A third player.

### What the report overstates

**"IETF standards"** — Don't use this phrase. ADRP and ATXN are individual internet-drafts with no formal IETF process standing and no IETF endorsement. There is also a *competing* draft (`draft-kotecha-agentic-dispute-protocol-00`) from a different author, meaning the field hasn't converged yet. The accurate framing: "emerging specification" or "leading proposed standard." A sharp investor who checks will know the difference.

**"Adopt ADRP to avoid building a proprietary schema"** — Half right. Aligning the proof envelope with ADRP's ProofBundle/RulingBundle structure is the correct call architecturally, because it makes the output interoperable and gives you a spec to point to in the pitch. But the spec is young and competing, so frame it as "we implement the leading proposed standard" not "we are the commercial orchestrator of the IETF standard."

**x402/Base for the Betaworks demo** — The research report recommends anchoring proof signatures on-chain via x402. That's a real direction for Phase 4, but it adds non-trivial scope to a 3.5-week sprint when the existing stack is Ed25519 + internal ledger + Stripe. Show x402 compatibility as a design choice in the pitch deck; don't require it to demo the core loop.

### What this changes in the plan

**Phase 1 outreach — sharpen the questions.** When talking to ACP/AP2/x402 integrators, ask specifically: "If your agent triggers an irreversible on-chain payment and the counterparty doesn't deliver, how are you handling it today?" That maps directly to the proven AgentCourt pain and surfaces whether integrators are already using AgentCourt or looking for something else.

**Phase 2 schema — align with ADRP.** When extending `tangible/crypto.py` to cover dispute outcomes, structure the payload to be compatible with ADRP's ProofBundle/RulingBundle field names. This is a design decision, not extra engineering — you're building the same thing either way, just naming fields to match a published spec.

**The pitch "why us" answer now has a sharper target.** CertNode and AgentCourt together do most of the merged thesis — but they're siloed (not integrated), crypto-only with no fiat rails, and neither has compliance-grade identity (IAL2) or licensed notarization. The answer to "why not just use those" is: we cover fiat + crypto, we're the only one with compliance-grade identity and notarization baked into the same proof envelope, and the integration is the product — we're not two separate APIs you glue together yourself.

**Add these to the competitor section of the Betaworks application.** Naming AgentCourt and CertNode by name and explaining what they don't cover is more credible than ignoring them. Investors know they exist.
