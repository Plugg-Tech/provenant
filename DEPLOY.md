# Deploy Provenant

Two services: **Render** (API backend) and **Netlify** (static website).

---

## 1. Deploy the API on Render (free tier)

1. Go to https://dashboard.render.com → **New +** → **Web Service**
2. Connect the `Plugg-Tech/provenant` GitHub repo
3. Settings:
   - **Name:** `provenant-api`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn tangible.api:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/healthz`
4. Click **Create Web Service**
5. Go to **Environment** tab and add these variables:

| Variable | Value |
|---|---|
| `TANGIBLE_IDENTITY_PROVIDER` | `auto` |
| `TANGIBLE_NOTARY_PROVIDER` | `auto` |
| `STRIPE_API_KEY` | `sk_test_xxx` (then `sk_live_xxx`) |
| `PERSONA_API_KEY` | your Persona sandbox key |
| `PERSONA_TEMPLATE_ID` | `itmpl_xxx` |
| `PANDADOC_API_KEY` | your PandaDoc sandbox key |

6. Deploy. API will be at `https://provenant-api.onrender.com`
7. Verify: `https://provenant-api.onrender.com/healthz`

---

## 2. Deploy the Website on Netlify

### Option A: Netlify CLI

```bash
npm install -g netlify-cli
netlify login
cd C:\Gopher\provenant
netlify init
# Select "Create & configure a new site"
# Set publish directory to: web
netlify deploy --prod
```

### Option B: Git-based deployment

1. Go to https://app.netlify.com → **Add new site** → **Import an existing project**
2. Select the `Plugg-Tech/provenant` repo
3. Build settings:
   - **Base directory:** (leave empty)
   - **Build command:** `echo 'Static site'`
   - **Publish directory:** `web`
4. Deploy

### Option C: Drag & drop

1. Go to https://app.netlify.com/drop
2. Drag the `web/` folder onto the page
3. Done — instant deploy

### Custom domain on Netlify

1. Netlify → Site settings → **Domain management** → **Add custom domain**
2. Enter `useprovenant.xyz`
3. Update DNS at your registrar:
   - Type: `CNAME`, Name: `@`, Value: `your-site.netlify.app`
   - Type: `CNAME`, Name: `www`, Value: `your-site.netlify.app`

---

## 3. Connect the site to the API

Update the API URL in `web/try.html` (it auto-detects based on hostname):

```javascript
const API = window.location.hostname === 'useprovenant.xyz'
  ? 'https://provenant-api.onrender.com'
  : window.location.origin;
```

If you want the site to proxy API calls through Netlify, the `netlify.toml` redirect is already configured:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://provenant-api.onrender.com/:splat"
  status = 200
```

---

## 4. Post-deploy checklist

- [ ] API health check returns `{"ok": true}`
- [ ] Website loads at your custom domain
- [ ] `/try` page calls the API and returns a proof
- [ ] Stripe webhook points to `https://your-api.onrender.com/v1/webhooks/stripe`
- [ ] PandaDoc notary add-on installed (for real notarization)
- [ ] Persona template created (for real identity verification)

---

## Environment variables summary

| Variable | Render (API) | Netlify (Site) |
|---|---|---|
| `TANGIBLE_IDENTITY_PROVIDER` | `auto` | — |
| `TANGIBLE_NOTARY_PROVIDER` | `auto` | — |
| `STRIPE_API_KEY` | `sk_test_xxx` | — |
| `STRIPE_WEBHOOK_SECRET` | `whsec_xxx` | — |
| `PERSONA_API_KEY` | `persona_sandbox_xxx` | — |
| `PERSONA_TEMPLATE_ID` | `itmpl_xxx` | — |
| `PANDADOC_API_KEY` | `xxx` | — |
