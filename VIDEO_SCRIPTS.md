# Betaworks Demo Video Scripts

Three videos, 2 minutes max each. Screen-record `demo_full.py` for Video 2.

---

## Video 1 — Founder background: who are you?

**Script (speak to camera):**

> I'm Emmanuel, an engineer who builds agent systems end-to-end.
>
> I kept hitting the same wall: my agents could run an entire workflow — draft a document, assemble a closing, onboard a contractor — then stall at one step. A signature that needed notarizing. An identity that needed verifying. No API could do it. The agent just... waited on a human.
>
> I realized the missing layer wasn't more intelligence. It was a way for agents to act in the physical world — and get back a result they could trust.
>
> So I started building Provenant.

**Close with:** "One endpoint for real-world actions. Signed proofs. Agent-native."

---

## Video 2 — Product demo: what are you building?

**Script (voiceover while screen-sharing `demo_full.py`):**

> Here's the problem. An AI agent runs a loan-closing workflow. It drafts the promissory note, assembles the packet, and then — it hits a wall. This signature must be notarized. The agent can't do that itself.
>
> So it calls Provenant — one API call: `provenant_notarize`. Behind the scenes, Provenant orchestrates identity proofing, jurisdiction routing, and the notarial act. It returns a cryptographically signed proof.
>
> Now watch what happens when we try to cheat. I alter one field in the proof — jurisdiction changes from TX to CA. Verification fails. Tamper detected.
>
> Here's a forged-key attack. Someone re-signs the proof with their own key. The pinned-registry verification rejects it — untrusted key.
>
> The ledger chain is valid. Every proof is appended to a hash chain. The head is anchored externally. Idempotency works — retry the same call, same proof, no double notarization. And revocation works — revoke a proof and it fails verification.
>
> All ten checks pass. The workflow proceeds safely.

**End on:** "One call, a signed proof, verifiable offline. That's the bridge between agents and the physical world."

---

## Video 3 — Which part of the thesis resonated most?

**Script (speak to camera):**

> The betaworks thesis has four lanes. Two hit me immediately.
>
> First: "marketplaces with non-human participants." Agents are going to need to transact, verify, notarize — and they can't click through a web app to do it. They need an API.
>
> Second: "AI breaking out of the computer into the physical world." The line that stuck with me: "there's a lot of money to be made in atoms." The binding constraint isn't intelligence anymore — it's action. A notarized signature. A verified identity. A witnessed signing.
>
> Provenant is the infrastructure layer for that. Notary is verb one. The same interface scales to witnessing, inspection, apostille — any real-world act an agent needs to perform.
>
> We want to be the API that lets agents act in the world. Provably.

---

## Recording checklist

- [ ] Record `python demo_full.py` in a clean terminal (dark background, large font)
- [ ] Keep the terminal visible for the full run — the PASS/FAIL summary is the money shot
- [ ] For Video 1: speak to camera, 90 seconds, natural pace
- [ ] For Video 2: voiceover on screen recording, sync narration with the demo output
- [ ] For Video 3: speak to camera, 90 seconds, reference the thesis lanes by name
- [ ] Upload to Loom or YouTube (unlisted), verify each opens in incognito
