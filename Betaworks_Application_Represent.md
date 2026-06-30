# Betaworks AI Camp — H2 2026: The New Agentic Economy
## Application Working Draft — "Represent" (working name)

*Priority deadline: **July 24, 2026** · Final deadline: July 31, 2026 · Camp runs Aug 31 – Nov 20, 2026 (in-person, NYC). Reviewed on a rolling basis — apply early.*

**How to use this doc.** Each **bold field heading** maps to a question on the betaworks form. Plain text is your drafted answer — edit to your voice. Lines marked **`▶ TO FILL`** are facts only you have. *Italic "Tip" lines* explain what the reader is looking for. The prototype plan, video scripts, and a pre-submit checklist are at the end.

---

## The company, in one screen

**What it is.** An agent-run firm that recovers revenue lost to payment disputes (chargebacks) for online sellers. An agent fleet ingests order, fulfillment, and customer-communication data, assembles evidence, and files representments across reason codes and processor formats. We sell *recovered dollars* — a cut of what we win back — not software seats.

**Why this wins the read.** Betaworks said this Camp judges the novelty of *how you build the company*, not the product surface — "a services firm that spends more on tokens than payroll." This is that, literally. It also lets you show recovered-dollar traction in an application, not just a demo.

**The actual bet.** Chargebacks are the beachhead — they fund the company and generate a proprietary outcome dataset. The bet is that as commerce shifts to agents transacting autonomously (ACP / AP2 / x402), disputes multiply at machine speed and the human-in-the-loop incumbents structurally can't follow. We become the dispute-and-trust layer for the agent economy.

**Honest risk.** The card-chargeback layer is crowded and well-funded — Chargeflow ($35M Series A, ~15k merchants), Justt ($100M+ raised), Chargebacks911. The answers below name them head-on and pivot to the agentic future they can't serve. Lean into that; don't pitch "a better Chargeflow."

---

## Application answers, field by field

### Company name
**Represent** (working name — swap if you have a brand you prefer).
*Tip: short, sayable, hints at the product — a chargeback rebuttal is literally a "representment." Alternatives: Rebut, Reclaim, Recoup.*

### Website
`▶ TO FILL` — Your landing page URL. A one-page site is fine for now: headline, the outcome-pricing promise, an email capture, a "connect Stripe" button.

### One-liner
"Agent-native dispute resolution — we recover the revenue online sellers lose to chargebacks, and we only get paid when you do."

*Alt (thesis-forward):* "We recover revenue lost to payment disputes today, and we're building dispute resolution for the agent economy of tomorrow."

### Describe your product
Online sellers lose billions to chargebacks — disputed card payments where the merchant must assemble evidence and rebut within a tight deadline or forfeit the money. Most lose simply because they can't gather the right evidence fast enough. Represent is an agent fleet that connects (read-only) to a merchant's Stripe / Shopify / PayPal data, reconstructs the order story, drafts a reason-code-specific rebuttal, and files it in the processor's required format — then tracks the outcome and learns from it. Because the operation is run by agents rather than analysts, our cost to fight a dispute is a fraction of an incumbent's, so we can profitably serve the long tail and price purely on success.

We start with e-commerce and subscription sellers (DTC brands, SaaS, digital goods) where dispute volume is high and margins are thin. It matters because disputes are a fast-growing tax on all commerce — ~337M disputes projected in 2026, up ~42% since 2023 — and the problem is about to change shape entirely as agents begin transacting on people's behalf.

### What stage are you at?
**Ideation / Product design** — building the prototype now. *(Select "Product design" if your prototype files a real test dispute end-to-end by submission; otherwise "Ideation.")*

### In one sentence, what is a truth about the future world that makes your company possible?
"Commerce is shifting from humans clicking 'buy' to agents transacting autonomously — and when machines transact at machine speed, disputes multiply past any human team's capacity, forcing dispute resolution to become agent-native too."

*Tip: this is the most important sentence in the application — it's their thesis question. It must name a second-order effect of an AI-native economy, not just "AI is good at writing."*

### Link to a live product or demo
`▶ TO FILL` — Prototype URL or a Loom of it running. See the prototype plan below; a rough proof-of-concept that ingests one real dispute and outputs a filing-ready rebuttal is enough.

### Share screenshots of your product
`▶ TO FILL` — 3–5 screenshots: (1) connect-account screen, (2) a dispute being ingested, (3) the auto-assembled evidence + drafted rebuttal, (4) an outcome/dashboard view. Mockups are acceptable if not live.

### Do you have any interesting strategies for distribution or growth?
Yes — four:

- **Zero-friction pricing.** We charge only a share of recovered funds, so adoption has no downside for the merchant — a read-only connection and we go to work.
- **Distribute where disputes already surface.** Ship as a Shopify / Stripe app-store app so we meet merchants at the exact screen where the chargeback appears, with self-serve onboarding.
- **Land-and-expand.** Start with chargebacks, then expand to refund/return abuse, item-not-received claims, and marketplace A-to-z claims — same data, more recovered dollars per account.
- **Become the default dispute endpoint.** Partner with processors and 3PLs that see disputes, and position early to be the dispute endpoint that ACP / AP2 / x402 agentic transactions route to as that volume arrives.

### What's your technical stack?
Reasoning: a model router that picks the model by reason-code complexity (frontier models for novel/high-value narratives, cheaper models for routine codes). Orchestration: a staged agent graph — intake → evidence retrieval → narrative drafting → format-and-file → outcome tracking → learning loop — each stage an agent with a tight, testable contract. Integrations: Stripe, Shopify, PayPal, Adyen dispute APIs and their evidence formats (e.g., Visa Compelling Evidence 3.0, Mastercard). Infra: event-driven workers with a queue keyed to each dispute's filing deadline, so nothing expires. Data moat: every resolved case is written to a structured outcome dataset (reason code → evidence → narrative → win/loss) that continuously raises win rate — a compounding asset incumbents' closed pipelines don't share with the long tail.

The choice to attend to: the company is itself a "dark factory." Agents run operations; the founder writes specs and reviews edge cases. It was built largely with agentic coding tools, and we are designing on the emerging agent-payment rails (x402 / AP2) now, so we're native when agent-to-agent disputes become a category rather than retrofitting later.

### Who are your competitors and what makes you different?
Incumbents: [Chargeflow](https://www.chargeflow.io/) ($35M Series A, ~15k merchants, success-priced), [Justt](https://justt.ai/) ($100M+ raised, enterprise), [Chargebacks911](https://chargebacks911.com/), plus Signifyd, Riskified, Verifi/Midigator. They sell SaaS or managed services to human ops teams, built on card-network reason codes.

Two differences: **(1) Cost structure** — our operation is agent-staffed, so our marginal cost per dispute is a fraction of an analyst-backed incumbent's. That lets us profitably serve the long tail they ignore and undercut them at scale. **(2) Direction** — they're optimized for the card-network, human-in-the-loop world. We're building for agentic commerce (ACP / AP2 / x402), where disputes today have no infrastructure and the incumbents' reason-code-plus-human model structurally can't follow. We're not a better chargeback tool; we're the dispute layer for a world where the buyer is an agent.

### What is another startup or founder that you admire? Tell us why.
`▶ TO FILL` — Personalize this; they're testing your taste, so pick someone you genuinely admire and say something non-obvious about why.

*Draft default (strong, on-thesis):* "Stripe — they turned the most unglamorous part of commerce, payment plumbing, into a developer-first product and compounded trust into a moat. I admire that they made boring infrastructure feel inevitable; Represent is trying to do the same for the dispute layer."

### Are you implementing any research we could familiarize ourselves with?
The agentic-commerce protocol stack: [Stripe/OpenAI ACP](https://docs.stripe.com/agentic-commerce/acp) (merchant checkout), [Google AP2](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol) (signed payment mandates), [Coinbase x402](https://www.openfort.io/blog/agentic-payments-landscape) (the HTTP 402 revival for machine payments), and [Google A2A](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) (agent-to-agent interop). Plus card-network dispute frameworks: Visa Compelling Evidence 3.0 / VCR and the Mastercard dispute rules, which define the evidence game we automate.

### Inception date
`▶ TO FILL` — yyyy-mm-dd; when you started on this idea. If unsure, use the date you began the prototype.

### Prior funding
`▶ TO FILL` — Total raised and from whom (funds / angels / grants). If bootstrapped: "None — self-funded to date," which is a fine answer at Ideation stage.

### Origin story & bios
`▶ TO FILL` — Your real story + team bios.
*Tip — a frame that fits you: "I kept seeing [trigger — a store I ran / a friend's DTC brand / a processor job] bleed money to disputes that were winnable but nobody had time to fight. The whole workflow was structured enough for agents to run end-to-end, so I built the company the way the work should be done — agents do the labor, I write the specs." Then 2–3 sentences of bio: what you've built, relevant domain or engineering depth.*

### Why are you the team to solve this problem?
`▶ TO FILL` — Personalize.
*Tip — angle: "I'm an engineer who builds agent systems, and I've run this company as a dark factory from day one — so I'm not theorizing about Betaworks' thesis, I'm living it. The dispute domain rewards exactly what agents are good at: structured evidence, deadline pressure, high-volume repetition. I can ship the whole loop myself and let the outcome data compound." Add any specific payments / e-commerce / fraud experience you have — that's gold here.*

### Team size
`▶ TO FILL` — Decimal, e.g. 1.0 (solo) or 1.5 (you + a part-time collaborator).

### Team location
`▶ TO FILL` — Your city; note if remote. Camp is in-person in NYC — if you're not there, state you're willing to relocate for the program (they explicitly allow this).

### Team member 1 (Name / Email / LinkedIn)
`▶ TO FILL` — You. Email on file: ashikemlito@gmail.com. Add your LinkedIn URL.

### Team member 2 (optional)
`▶ TO FILL` — Only if you have a co-founder.

### How did you hear about Camp?
`▶ TO FILL` — Be specific (newsletter / a previous cohort founder / Twitter). If a name, it doubles as a warm signal.

### Do you know anyone in the Betaworks network?
`▶ TO FILL` — Drop any name you can; a warm intro or reference materially helps. Leave blank rather than inventing one.

### Primary phone number (SMS-capable)
`▶ TO FILL` — A number that can receive SMS — they may text you about the application.

---

## Prototype build plan (what to show)

They explicitly accept a rough proof-of-concept. The minimum convincing demo: ingest one real (or realistic) dispute and produce a filing-ready rebuttal. Scope it to a weekend.

**Smallest demo that lands**

- **Connect / paste input.** A read-only Stripe test-mode connection, or a screen where you paste a dispute's details (reason code, amount, order ID).
- **Evidence assembly.** Pull order, fulfillment, and customer-comm records (mock data is fine) and have an agent select what's relevant to that reason code.
- **Rebuttal draft.** Generate a reason-code-specific representment narrative + an evidence checklist, formatted to what the processor expects.
- **Outcome view.** A simple dashboard: disputes in flight, deadline countdown, projected recovery. Even static, it tells the story.

**Stack to move fast.** Stripe test mode gives you real dispute objects and reason codes; an agent framework of your choice for the staged graph; a thin Next.js or single-page UI; deploy on Vercel. One reason code done convincingly beats ten done shallowly.

---

## The three required videos (2 min max each)

Strict 2-minute limit per video, three separate links (YT / Loom / Drive). **Test each in an incognito window — if they can't open it, they won't consider you.**

**Video 1 — Founder background: who are you?**

- Name + one line on what you build (engineer who ships agent systems).
- The 30-second version of your path — what you've built, any payments / e-commerce / fraud exposure.
- Why this problem found you (your origin trigger).
- Close: "So I built a company that runs the way I think all services companies will — agents do the work."

**Video 2 — Product demo: what are you building and what problem are you solving?**

- One sentence on the problem: sellers forfeit winnable disputes because no one has time to fight them.
- Screen-share the prototype: ingest a dispute → watch evidence assemble → show the drafted rebuttal.
- Say the pricing: "We only get paid when we recover — so there's no reason not to turn us on."
- End on the agent-native cost structure — why you can serve merchants incumbents can't.

**Video 3 — Which part of the thesis resonated most?**

- Name the lanes directly: AI-native organizations + marketplaces with non-human participants.
- "The line that hit me was 'a services firm that spends more on tokens than payroll.' That's the company."
- The bet: agentic commerce makes disputes explode at machine speed, the human-in-the-loop incumbents can't follow, so the dispute layer gets rebuilt agent-native — and we want to be it.

---

## Before you submit — checklist

- [ ] Lock the company name + register a domain / one-page site.
- [ ] Build the prototype (one reason code, end to end) and capture screenshots.
- [ ] Record + upload the three videos; verify each opens in incognito.
- [ ] Fill every `▶ TO FILL` field above (bio, dates, funding, phone, LinkedIn, location).
- [ ] Personalize the "founder you admire," origin story, and "why you" answers — don't ship the defaults verbatim.
- [ ] Apply by the **July 24** priority deadline (rolling review — earlier is better).

*Source for thesis & deadlines: betaworks — "Apply to Betaworks' Fall '26 AI Camp: The New Agentic Economy."*
