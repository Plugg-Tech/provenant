# Going Live — Identity Verification + Notary

This makes both verbs **genuinely real**:
- **Identity verification** → Stripe Identity or Persona (IAL2 document verification)
- **Notarization** → PandaDoc Notary On-Demand (video session with a commissioned notary)

Pick one identity provider: **Stripe** (simplest) or **Persona** (more flexible, free sandbox).
Plus **PandaDoc** for notarization (free sandbox, paid plan for live).

Total time: ~45–60 minutes.

---

## Part 1: Identity verification (pick one)

### Option A: Stripe Identity (simplest)

#### 1.1 Create a Stripe account (5 min)

1. Sign up at https://dashboard.stripe.com (no charges in test mode).
2. Toggle **Test mode** ON (top-right).
3. Developers → API keys → copy your **Secret key** (`sk_test_...`).
4. Enable Identity: https://dashboard.stripe.com/identity (turn it on; test mode is free).

#### 1.2 Run locally with Stripe (5 min)

```powershell
cd C:\Gopher\provenant
.venv\Scripts\activate

$env:STRIPE_API_KEY = "sk_test_xxx"
uvicorn tangible.api:app --reload
```

Verify it's live:

```powershell
curl http://127.0.0.1:8000/healthz
# → {"ok":true,"identity_live":true}
```

Start a real verification:

```powershell
curl -X POST http://127.0.0.1:8000/v1/actions/verify-identity `
  -H "Content-Type: application/json" `
  -d '{"name":"Your Name","email":"you@example.com"}'
```

The response includes a real **`url`** — open it in a browser and complete Stripe's hosted verification. In test mode, use Stripe's test document images: https://docs.stripe.com/identity/verification-sessions#test-mode

Then poll for the result:

```powershell
curl http://127.0.0.1:8000/v1/identity/<action_id>
```

When `status` is `verified`, the response contains a signed `proof`.

### 1.3 Webhook (optional, 5 min)

For production, webhooks are better than polling:

1. Stripe → Developers → Webhooks → **Add endpoint**: `https://<your-domain>/v1/webhooks/stripe`
2. Subscribe to `identity.verification_session.verified` and `.requires_input`.
3. Copy the signing secret (`whsec_...`):

```powershell
$env:STRIPE_WEBHOOK_SECRET = "whsec_xxx"
```

### Option B: Persona (more flexible, free sandbox)

#### 1.4 Create a Persona account (5 min)

1. Sign up at https://withpersona.com (free sandbox, no credit card).
2. Go to Dashboard → API Keys → copy your **sandbox API key**.

#### 1.5 Run locally with Persona (5 min)

```powershell
$env:PERSONA_API_KEY = "your_persona_api_key"
uvicorn tangible.api:app --reload
```

Verify it's live:

```powershell
curl http://127.0.0.1:8000/healthz
# → {"ok":true,"identity_live":true}
```

Start a real verification:

```powershell
curl -X POST http://127.0.0.1:8000/v1/actions/verify-identity `
  -H "Content-Type: application/json" `
  -d '{"name":"Your Name","email":"you@example.com"}'
```

The response includes a **`url`** — open it in a browser and complete Persona's hosted verification (in sandbox, use the test documents). Then poll:

```powershell
curl http://127.0.0.1:8000/v1/identity/<action_id>
```

When `status` is `verified`, the response contains a signed `proof`.

**Why Persona over Stripe?**
- More flexible verification flows (document + liveness + database checks)
- Better webhook support with richer event data
- Free sandbox with no setup fees
- Works well for international verification

---

## Part 2: PandaDoc Notary (real notarization)

### 2.1 Create a PandaDoc sandbox (5 min)

1. Sign up at https://signup.pandadoc.com/?ss=api-dev&plan=rec_plans_v8_api_ss_mn&lng=en-US (free sandbox, no credit card).
2. Go to https://app.pandadoc.com/a/#/api-dashboard/configuration.
3. Generate an **API Key** (sandbox mode).
4. Install the **Notary On-Demand** add-on from the PandaDoc integrations page.

### 2.2 Run locally with PandaDoc (5 min)

```powershell
$env:PANDADOC_API_KEY = "your_sandbox_api_key"
uvicorn tangible.api:app --reload
```

Test a notarization (sandbox):

```powershell
curl -X POST http://127.0.0.1:8000/v1/actions/notarize `
  -H "Content-Type: application/json" `
  -d '{"document_name":"Promissory Note","document_sha256":"7d784f...","jurisdiction":"TX","parties":[{"name":"Jordan","email":"jordan@acme.com"}]}'
```

In sandbox mode, the notarization is simulated. When `PANDADOC_API_KEY` is set, the system routes to PandaDoc for real fulfillment.

### 2.3 How PandaDoc Notarization works

1. An agent calls the notarize endpoint with a document.
2. Provenant uploads the PDF to PandaDoc and creates a notarization request.
3. The signer receives an email with a **notarization link**.
4. The signer opens the link, connects with a **commissioned online notary** via video.
5. The notary verifies identity, witnesses the signing, and completes the act.
6. The notarized document is available in PandaDoc; Provenant returns a signed proof.

**Notary On-Demand hours**: Mon–Fri, 9 AM – 9 PM Central Time. Notaries typically respond within 2 minutes.

### 2.4 Custom domain (5 min)

1. Render → Settings → Custom Domains → add `useprovenant.xyz`.
2. Create the CNAME record at your registrar.
3. Deploy both the API (web service) and the site (static site) on the same domain.

---

## Part 3: Deploy to Render (15 min)

### 3.1 Push to GitHub

```powershell
cd C:\Gopher\provenant
git init
git add .
git commit -m "Provenant v0.3: SDK, MCP server, interactive demo"
git remote add origin https://github.com/youruser/provenant.git
git push -u origin main
```

### 3.2 Deploy via Blueprint

1. Render → **New + → Blueprint** → pick the repo. It reads `render.yaml`.
2. Set environment variables:

| Variable | Value |
|---|---|
| `STRIPE_API_KEY` | `sk_test_...` (then `sk_live_...` for production) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` (after creating the webhook) |
| `PANDADOC_API_KEY` | Your PandaDoc sandbox API key |

3. Deploy. Hit `https://<your-service>.onrender.com/healthz` — should show both providers live.

### 3.3 Deploy the website

Render → **New + → Static Site** → point to the `web/` folder. Set the custom domain to `useprovenant.xyz`.

---

## Environment variables reference

| Variable | Purpose | Default |
|---|---|---|
| `STRIPE_API_KEY` | Enables real identity verification via Stripe | unset → simulated |
| `STRIPE_WEBHOOK_SECRET` | Verifies Stripe webhook signatures | unset → accepts unsigned (dev only) |
| `PERSONA_API_KEY` | Enables real identity verification via Persona | unset → simulated |
| `PANDADOC_API_KEY` | Enables real notarization via PandaDoc | unset → simulated |
| `TANGIBLE_IDENTITY_PROVIDER` | `auto` / `simulated` / `stripe` / `persona` | `auto` |
| `TANGIBLE_NOTARY_PROVIDER` | `auto` / `simulated` / `pandadoc` | `auto` |
| `PROVENANT_URL` | SDK/CLI base URL | `http://127.0.0.1:8000` |
| `PROVENANT_API_KEY` | SDK/CLI bearer token | unset → unauthenticated |

---

## What's real vs. simulated (updated)

| Component | When no key is set | When key is set |
|---|---|---|
| Identity verification | Simulated (deterministic) | **Real IAL2 via Stripe or Persona** |
| Notarization | Simulated (deterministic) | **Real RON via PandaDoc Notary** |
| Cryptographic proof | **Always real** (Ed25519) | **Always real** |
| Tamper-evident ledger | **Always real** (hash chain) | **Always real** |
| Key registry | **Always real** (pinned verification) | **Always real** |

---

## Go to production

1. Flip `STRIPE_API_KEY` to `sk_live_...` and complete Stripe's Identity production activation.
2. Flip `PANDADOC_API_KEY` to your live PandaDoc key and upgrade to a paid plan.
3. Move signing keys to Render's secret store / a KMS.
4. Set up monitoring and alerts.

---

## MCP Server for Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "provenant": {
      "command": "python",
      "args": ["C:\\Gopher\\provenant\\mcp_server.py"]
    }
  }
}
```

Then ask Claude: "Verify the identity of Jordan Borrower at jordan@acme.com" — it will call Provenant and return a signed proof.
