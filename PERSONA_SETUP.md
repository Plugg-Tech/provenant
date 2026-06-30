# Persona Identity — Quick Setup

Your API key works. One step left: create an inquiry template.

## 1. Create a template (2 min)

1. Go to https://app.withpersona.com/dashboard/login
2. Navigate to **Inquiries → Templates**
3. Click **Create Template**
4. Name it something like "Provenant Identity Check"
5. Add these steps:
   - **Government ID** (document capture)
   - **Selfie** (liveness check)
6. Click **Save & Publish**
7. Copy the **Template ID** (starts with `itmpl_`)

## 2. Set the template ID

The template ID needs to be configured in the provider. Update the Persona provider in `tangible/providers/identity_providers.py`:

```python
class PersonaIdentityProvider:
    def __init__(self, api_key=None, template_id=None):
        self.api_key = api_key or os.environ.get("PERSONA_API_KEY", "")
        self.template_id = template_id or os.environ.get("PERSONA_TEMPLATE_ID", "")
        self.base_url = "https://api.withpersona.com/api/v1"
```

Or set the environment variable:

```powershell
$env:PERSONA_TEMPLATE_ID = "itmpl_YOUR_TEMPLATE_ID"
```

## 3. Test it

```powershell
$env:PERSONA_API_KEY = "persona_sandbox_YOUR_API_KEY"
$env:PERSONA_TEMPLATE_ID = "itmpl_YOUR_TEMPLATE_ID"
$env:TANGIBLE_IDENTITY_PROVIDER = "persona"
uvicorn tangible.api:app --reload
```

Then:

```powershell
curl -X POST http://127.0.0.1:8000/v1/actions/verify-identity `
  -H "Content-Type: application/json" `
  -d '{"name":"Jordan Borrower","email":"jordan@acme.com"}'
```

The response will include a URL — open it to complete the verification flow.

## Sandbox test data

In sandbox mode, Persona returns templated responses. You don't need real documents — just click through the flow and it will complete automatically.
