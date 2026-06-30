# Betaworks AI Camp — H2 2026: The New Agentic Economy
## Application Draft — Provenant  ·  useprovenant.xyz
### The physical-action API for agents — starting with notarization

*Priority deadline: **July 24, 2026** · Final deadline: July 31, 2026 · Camp runs Aug 31 – Nov 20, 2026 (in-person, NYC). Rolling review — apply early.*

*(This supersedes the earlier "Represent" draft — we moved off chargebacks because the market was crowded.)*

**How to use this doc.** Each **bold field heading** maps to a question on the betaworks form. Plain text is your drafted answer — edit to your voice. Lines marked **`▶ TO FILL`** are facts only you have. *Italic "Tip" lines* explain what the reader is after. Prototype plan, video scripts, and a pre-submit checklist are at the end.

---

## The company, in one screen

**What it is.** Provenant is a single API that lets an AI agent trigger, track, pay for, and receive cryptographic proof of a real-world action. Agents can do enormous amounts of digital work, but they hit a wall the moment a task requires a legally binding or physical act. Provenant is the bridge. **Verb #1 is notarization** (remote online notarization + mobile notaries), because it's a legally required step inside fast-automating workflows and its output is a clean, verifiable, signed artifact an agent can consume.

**Why notary is the wedge (not the whole company).** RON is legal in most states and is itself digital, so an agent can trigger *and fulfill* a notarization with no truck roll — which sidesteps the cold-start problem that kills physical marketplaces. It's the one real-world action a solo founder can both fulfill and defend (state-by-state RON compliance is the moat). From there you add verbs: identity verification → witnessing → inspection → apostille → dispatch.

**Why this wins the read.** It hits three betaworks lanes at once — marketplaces for non-human consumers, AI breaking out of the computer into the physical world, and AI-native organizations — and it sits *on top of* the now-commoditized agent payment rails (x402, AWS AgentCore Payments, Stripe) rather than competing with them.

**Honest risk.** Proof (formerly Notarize), DocuSign Notary, and Stavvy own human-facing RON. The entire bet is being **agent-API-first** — one endpoint, pay-per-action, no human UI — not another notary web app. Lean into that everywhere.

---

## Application answers, field by field

### Company name
**Provenant** — from *provenance* (proof of origin) + *covenant* (trust). Name locked; domain useprovenant.xyz.

### Website
https://useprovenant.xyz — live landing page is built (see web/index.html). Deploy it as a Render static site, or serve it at the API root, then put the URL here.

### One-liner
"Provenant is the API that lets AI agents get things done in the physical world — starting with legally valid notarization."

*Alt (more concrete):* "One endpoint for agents to dispatch, verify, and pay for real-world actions — beginning with notarization."

### Describe your product
Agents can now run whole document and back-office workflows, but they stall the instant a task requires a legally binding or physical act — a notarized signature, a verified identity, an in-person witness. Provenant exposes those acts as a single typed API: an agent submits an action request (type, documents, parties, jurisdiction), we orchestrate fulfillment, and we return a cryptographically signed proof object the agent can verify and store. We start with notarization via remote online notarization and a mobile-notary network, focused on agent-driven workflows in lending, title/real-estate, and legal — places where a notarized step is mandatory and the surrounding work is automating fast. It matters because as agents absorb the paperwork economy, the bottleneck shifts to the handful of steps that must touch the physical and legal world, and today there is no agent-native way to perform them.

### What stage are you at?
**Beta/testflight** — a working prototype runs end-to-end; the `verify_identity` verb is live via Stripe Identity, notarization is in sandbox. *(Select "Beta/testflight" once it's deployed at useprovenant.xyz; "Product design" until then.)*

### In one sentence, what is a truth about the future world that makes your company possible?
"As agents automate the paperwork economy, the binding constraint becomes the legally required physical acts they can't perform themselves — so whoever gives agents a verifiable way to act in the physical world becomes critical infrastructure."

*Tip: this is their thesis question and the most important sentence in the application. It names a second-order effect of an AI-native economy (their lanes 3 and 4), not a feature.*

### Link to a live product or demo
`▶ TO FILL with your deployed URL` — the prototype is built and runs end-to-end. `verify_identity` is **live via Stripe Identity** (real verification → signed proof); notarization runs in sandbox. Deploy on Render (see SETUP_LIVE.md) and paste the URL, or link a Loom of `agent_demo.py`.

### Share screenshots of your product
`▶ TO FILL` — 3–5 frames: (1) the agent hitting the "physical step" wall, (2) the API/MCP tool call, (3) the orchestration/compliance routing, (4) the returned signed document + proof JSON. Mockups OK if not live.

### Do you have any interesting strategies for distribution or growth?
Yes — four:

- **Developer-led, API-first.** Land the AI builders already automating lending, title, and legal who hit the notarization wall. We're the drop-in step they'd otherwise have to build and get regulated themselves.
- **Ride the rails.** Integrate x402 / AWS AgentCore Payments so an agent with a wallet pays per action — we meet agents exactly where they already transact, and we're the thing they're paying *for*.
- **Compliance as the wedge.** Owning state-by-state RON compliance and identity proofing is the reason a builder picks Provenant over rolling their own — distribution and moat are the same thing.
- **Grow the verb list.** notarize → verify identity → witness → inspect → apostille → dispatch. Each new physical action is more API surface, more lock-in, and more of the agentic economy's bridge to the physical world.

### What's your technical stack?
A single "action" abstraction: the agent submits a typed request (action type, documents, parties, jurisdiction) and receives a signed, verifiable proof envelope. Orchestration is a staged agent graph — intake → identity proofing (KYC/IDV, NIST IAL2 as RON requires) → jurisdiction and compliance routing → notary matching and scheduling (RON session or mobile dispatch) → proof generation. Fulfillment runs through RON partner notaries / platform integrations plus a mobile-notary network for wet-ink. Payments are agent-native and pay-per-action via x402 / AgentCore / Stripe. Every completed action returns a cryptographically signed artifact and audit trail (notary journal, certificate, recording) that's tamper-evident and agent-consumable, exposed to agents as an MCP tool as well as REST.

The choice to attend to: we model real-world acts as **typed, verifiable actions with one uniform proof envelope**, so the same interface scales from notary to inspection to any dispatchable physical act. The company is run dark-factory style — agents handle scheduling and compliance routing; the founder writes specs and reviews edge cases.

### Who are your competitors and what makes you different?
Human-facing RON / e-notary incumbents: [Proof (formerly Notarize)](https://www.proof.com/), DocuSign Notary, [Stavvy](https://www.stavvy.com/), BlueNotary. They're built for a person clicking through a web app, sold to title companies and lenders. Provenant is **agent-API-first**: an agent calls one endpoint, pays per action, and gets back a verifiable result — no human UI, no seat licenses. Agent payment rails (Stripe, Coinbase x402, AWS AgentCore) are *not* competitors; we sit on top as the action the agent pays for. The broader bet — a general physical-action API for agents — has no direct competitor; the closest analogs are human-facing service marketplaces (Thumbtack and the like), which are not agent-native. We are not another notary platform; we're the interface agents use to act in the world, and notary is verb #1.

### What is another startup or founder that you admire? Tell us why.
`▶ TO FILL` — Personalize; they're testing your taste.

*Draft default (on-brand):* "Twilio / Jeff Lawson — they took a messy, regulated, physical-world system (telephony) and turned it into a few clean API calls, and a thousand products bloomed on top. That's exactly the move for physical-world actions: hide the regulatory and logistical mess behind one endpoint."

### Are you implementing any research we could familiarize ourselves with?
RON statutes and the MISMO RON standards; identity-proofing frameworks (NIST 800-63 / IAL2); the agent-payment stack — [Coinbase x402](https://www.openfort.io/blog/agentic-payments-landscape), [Google AP2](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol), and [AWS Bedrock AgentCore Payments](https://aws.amazon.com/blogs/machine-learning/agents-that-transact-introducing-amazon-bedrock-agentcore-payments-built-with-coinbase-and-stripe/); and MCP for exposing the action API as agent-callable tools.

### Inception date
`▶ TO FILL` — yyyy-mm-dd; when you started on this idea. If unsure, use the prototype start date.

### Prior funding
`▶ TO FILL` — Total raised and from whom. If bootstrapped: "None — self-funded to date" (fine at this stage).

### Origin story & bios
`▶ TO FILL` — Your real story + bio.
*Tip — a frame that fits: "I was building agents that could run a whole [lending / legal / ops] workflow, and they kept dead-ending at one step — a notarization, an identity check — that no API could do. I realized the missing layer wasn't more intelligence, it was a way for agents to act in the physical world, so I started building it." Then 2–3 sentences: what you've shipped, any fintech / proptech / legaltech / infra depth.*

### Why are you the team to solve this problem?
`▶ TO FILL` — Personalize.
*Tip — angle: "I'm an engineer who builds agent systems end-to-end, and I've felt this exact wall firsthand. The hard parts here are an API abstraction and a compliance maze — both things I can build solo and both things that compound into a moat. I run the company as a dark factory, so I'm living the betaworks thesis, not theorizing about it." Add any payments/identity/regulated-workflow experience — that's gold.*

### Team size
`▶ TO FILL` — Decimal, e.g. 1.0.

### Team location
`▶ TO FILL` — Your city; note if remote. Camp is in-person in NYC — if you're elsewhere, say you'll relocate for the program (they allow it).

### Team member 1 (Name / Email / LinkedIn)
`▶ TO FILL` — You. Email on file: ashikemlito@gmail.com. Add your LinkedIn.

### Team member 2 (optional)
`▶ TO FILL` — Only if you have a co-founder.

### How did you hear about Camp?
`▶ TO FILL` — Be specific (newsletter / a cohort founder / Twitter).

### Do you know anyone in the Betaworks network?
`▶ TO FILL` — Any name helps; leave blank rather than inventing.

### Primary phone number (SMS-capable)
`▶ TO FILL` — A number that can receive SMS.

---

## Prototype build plan (what to show)

A rough proof-of-concept is explicitly fine. The minimum convincing demo: **an agent calls one endpoint and completes a notarization, getting back a signed proof.** RON makes this fully demoable with no physical logistics.

**Smallest demo that lands**

- **The wall.** Show an agent (Claude/GPT) running a mock loan or legal-doc workflow that dead-ends at "this must be notarized."
- **One call.** The agent calls a Provenant MCP tool / REST endpoint: `notarize(document, parties, jurisdiction)`.
- **Orchestration.** Behind it: identity-proofing step (can stub), jurisdiction/compliance routing, and a RON session (sandbox or a single real pilot notary).
- **Proof back.** Return a signed PDF + a proof JSON (signer identity, notary commission, timestamp, audit trail) the agent verifies and continues with.

**Stack to move fast.** Expose the endpoint as both REST and an MCP tool; stub the RON session with a sandbox or one cooperating notary; generate a real signed-proof envelope so the *output* is genuine even if fulfillment is stubbed. One jurisdiction done convincingly beats fifty stubbed.

---

## The three required videos (2 min max each)

Three separate links (YT / Loom / Drive), 2-minute hard cap each. **Test every link in an incognito window — no access, no consideration.**

**Video 1 — Founder background: who are you?**

- Name + one line: engineer who builds agent systems end-to-end.
- 30-second path; any fintech / identity / regulated-workflow exposure.
- The moment you hit the "agents can't act in the physical world" wall.
- Close: "So I started building the layer that lets them."

**Video 2 — Product demo: what are you building and what problem are you solving?**

- One sentence: agents run whole workflows but dead-end at legally required physical acts.
- Screen-share: agent hits the wall → calls Provenant → gets back a signed notarization.
- Say the model: "One API call, pay-per-action, a verifiable proof comes back."
- End on the vision: notary is verb #1; the same interface scales to any physical action.

**Video 3 — Which part of the thesis resonated most?**

- Name the lanes: marketplaces for non-human consumers + AI breaking out of the computer into the physical world.
- "The line that hit me: 'AI systems will increasingly escape the domain of the virtual because there's a lot of money to be made in atoms.'"
- The bet: agents will dead-end at physical steps constantly; whoever gives them a verifiable way to act in the world becomes infrastructure — and we want to be it.

---

## Before you submit — checklist

- [x] Name locked (Provenant) + domain (useprovenant.xyz) + landing page built.
- [ ] Build the prototype (one jurisdiction, agent → API → signed proof) and capture screenshots.
- [ ] Line up one pilot notary or a RON sandbox for the demo.
- [ ] Record + upload the three videos; verify each opens in incognito.
- [ ] Fill every `▶ TO FILL` field (bio, dates, funding, phone, LinkedIn, location).
- [ ] Personalize the "founder you admire," origin story, and "why you" — don't ship defaults verbatim.
- [ ] Apply by the **July 24** priority deadline (rolling review — earlier is better).

*Source for thesis & deadlines: betaworks — "Apply to Betaworks' Fall '26 AI Camp: The New Agentic Economy."*
