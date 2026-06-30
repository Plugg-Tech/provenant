# Getting started — Provenant

Two parts: **A. run the sandbox** (no accounts, works offline) and **B. turn on real
identity verification with Stripe**. Commands shown for Windows PowerShell; macOS/Linux
notes inline. Requires Python 3.10+.

---

## Part A — Run the sandbox (5 minutes, no keys)

The sandbox runs the entire API with identity and notarization **simulated**, so you
can build and test without any provider accounts.

```powershell
cd C:\Gopher\tangible-prototype
py -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

**1. Run the tests** (should be 37 passing):

```powershell
py -m pytest -q
```

**2. Watch the end-to-end agent demo:**

```powershell
py agent_demo.py
```

It prints a mock agent hitting the notarization wall, calling the tool, and verifying
the signed proof (signature, document binding, tamper check, ledger, idempotency,
revocation). It writes `sample_proof.json` and `sample_certificate.pdf`.

**3. Run the API and call it:**

```powershell
uvicorn tangible.api:app --reload
```

In a second terminal, start a (simulated) identity verification — it returns a signed
proof immediately:

```powershell
curl -X POST http://127.0.0.1:8000/v1/actions/verify-identity `
  -H "Content-Type: application/json" `
  -d '{\"name\":\"Dana Lee\",\"email\":\"dana@example.com\"}'
```

Open `http://127.0.0.1:8000/docs` for the interactive API explorer, and
`http://127.0.0.1:8000/healthz` to confirm status (`identity_live:false` in sandbox).

Verify any saved proof offline:

```powershell
py -m tangible.verify sample_proof.json
```

That's a complete working system. Everything below makes the identity verb **real**.

---

## Part B — Turn on real identity verification (Stripe, ~15 minutes)

`verify_identity` becomes real the moment a Stripe key is present — no code change.
Stripe **test mode is free** and runs the full flow.

**1. Get Stripe test keys**
- Sign up at https://dashboard.stripe.com (toggle **Test mode** on, top-right).
- Developers → API keys → copy the **Secret key** (`sk_test_…`).
- Enable Identity: https://dashboard.stripe.com/identity (free in test mode).

**2. Run the API with the key**

```powershell
$env:STRIPE_API_KEY = "sk_test_xxx"
uvicorn tangible.api:app --reload
```

`GET /healthz` should now show `identity_live:true`.

**3. Start a real verification**

```powershell
curl -X POST http://127.0.0.1:8000/v1/actions/verify-identity `
  -H "Content-Type: application/json" `
  -d '{\"name\":\"Your Name\",\"email\":\"you@example.com\"}'
```

The response includes a real **`url`** and `status:"pending"`. Open the URL in a browser
and complete Stripe's hosted verification. In test mode use Stripe's test document
images: https://docs.stripe.com/identity/verification-sessions#test-mode

**4. Get the result + signed proof**

```powershell
curl http://127.0.0.1:8000/v1/identity/<action_id>
```

When `status` becomes `verified`, the response contains a signed `proof`. Save it and
verify offline with `py -m tangible.verify proof.json`.

**5. (Optional) Webhook so results arrive automatically**
- Stripe → Developers → Webhooks → Add endpoint: `https://<your-domain>/v1/webhooks/stripe`
- Subscribe to `identity.verification_session.verified`.
- Copy the signing secret (`whsec_…`) and set it:

```powershell
$env:STRIPE_WEBHOOK_SECRET = "whsec_xxx"
```

Now a completed verification triggers proof issuance without polling.

---

## Part C — Deploy on your domain

To put this live at `useprovenant.xyz`, follow **`SETUP_LIVE.md`** (push to GitHub →
Render Blueprint → set `STRIPE_API_KEY` → add the custom domain → wire the webhook).
The `web/` folder (the multi-page site) can deploy as a Render **static site** on the
same domain.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `STRIPE_API_KEY` | Enables real identity verification | unset → simulated |
| `STRIPE_WEBHOOK_SECRET` | Verifies Stripe webhook signatures | unset → accepts unsigned (dev only) |
| `TANGIBLE_IDENTITY_PROVIDER` | `auto` / `simulated` / `stripe` | `auto` |

## Next milestone — real notarization
Create a RON sandbox (PandaDoc Notary is free) and we add a notary adapter so a call
books a real notarial session. Send the sandbox key and we wire it to the live API.
