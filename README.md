# Provenant — prototype (v0.3)

**The physical-action API for agents.** Both identity verification and notarization
are **live-ready** with real providers (Stripe Identity + PandaDoc Notary).

> **Go live:** see [`SETUP_LIVE.md`](SETUP_LIVE.md) — make both verbs real
> with free accounts and deploy on Render in ~45 min.

An AI agent submits a typed action request; Provenant orchestrates identity
proofing, jurisdiction/RON routing, and the notarial act, then returns a
**cryptographically signed, registry-verified, ledgered proof** the agent can
check before it continues its workflow.

Proof-of-concept for the betaworks AI Camp application — rough on purpose, but
the core loop and all the security properties genuinely run end-to-end.

---

## What's new in v0.3

- **Python SDK** — `pip install`-able client with typed responses:
  ```python
  from sdk import ProvenantClient
  client = ProvenantClient("http://127.0.0.1:8000")
  result = client.verify_identity(name="Jordan", email="jordan@acme.com")
  ```
- **MCP Server** — exposes Provenant tools to LLM agents (Claude, GPT, etc.):
  ```json
  { "mcpServers": { "provenant": { "command": "python", "args": ["mcp_server.py"] } } }
  ```
- **CLI tool** — `py -m sdk.cli verify-identity --name "Jordan" --email "jordan@acme.com"`
- **Interactive web demo** — visitors try identity verification and notarization live at `/try`
- **PandaDoc Notary provider** — real notarization via PandaDoc Notary On-Demand (set `PANDADOC_API_KEY`)
- **Provider system** — identity and notary providers auto-select based on env vars (`auto | simulated | stripe | pandadoc`)
- **37/37 tests passing** (fixed pre-existing ledger test bug)

---

## What's real vs. simulated

**Real (actually executes):**
- The action API and orchestration pipeline (`service.py`).
- The cryptographic proof — real **Ed25519** signing/verification, with
  **pinned-key verification** against a trusted registry, document binding, and
  tamper detection (`crypto.py`, `keyring.py`).
- A **tamper-evident hash-chained ledger** of every issued proof (`ledger.py`).
- **Idempotency, revocation, and hardened input validation**.
- The agent → tool → proof → verify loop, including a **forged-key attack that
  gets rejected** (`agent_demo.py`).
- The HTTP API and the full test suite.

**Simulated (clearly labeled in code):**
- Identity proofing — would call an IAL2 IDV vendor (`identity.py`).
- The commissioned notary performing the act — a licensed human / RON-platform
  partner (`notary.py`).
- External anchoring — would hit an RFC 3161 TSA / public ledger (`timestamp.py`).

These require a legal commission and vendor contracts, not code.

---

## Hardening in v0.2

- **Pinned-key verification.** Proofs carry a fingerprint `key_id`; verification
  checks the signature against the *trusted registry* key for that id, never the
  public key embedded in the proof. A forged proof re-signed with an attacker's
  key is rejected (`untrusted key_id`). Key rotation is supported; old proofs
  stay verifiable.
- **Tamper-evident ledger.** Every proof is appended to a hash chain; any insert,
  delete, reorder, or edit breaks `verify_chain()`.
- **External anchoring hook** for the ledger head (simulated locally).
- **Idempotency** — a retried call with the same key returns the original proof
  instead of notarizing twice.
- **Revocation** — a revoked proof fails verification.
- **Input validation** — sha256 format, email format, duplicate-party and size
  limits.

---

## Run it (Windows)

```bat
cd C:\Gopher\tangible-prototype
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

py -m pytest -v            REM run the test suite
py agent_demo.py           REM watch the agent notarize + the hardening checks
```

macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`. Python 3.10+.

> Note: v0.2 introduces a key registry (`tangible_keyring.json`). If you have a
> `sample_proof.json` from v0.1, regenerate it by re-running `py agent_demo.py`;
> old proofs lack a `key_id` and will not verify under the new registry.

### Optional: HTTP API
```bat
uvicorn tangible.api:app --reload
```
Endpoints: `POST /v1/actions/notarize`, `GET /v1/actions/{id}`, `POST /v1/verify`,
`POST /v1/proofs/{id}/revoke`, `GET /v1/ledger/verify`,
`POST /v1/actions/verify-identity`, `GET /v1/identity/{id}`,
`POST /v1/webhooks/stripe`. Docs at `/docs`.

The `verify_identity` verb is real: set `STRIPE_API_KEY` and an agent call starts
an actual Stripe Identity session and issues a signed proof on success. With no
key set, it runs simulated so tests and the demo work offline.

### Verify a saved proof offline
```bat
py -m tangible.verify sample_proof.json
```

### MCP Server (for LLM agents)
Add to your Claude Desktop config (`claude_desktop_config.json`):
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
The server exposes 3 tools: `provenant_verify_identity`, `provenant_notarize`, `provenant_verify_proof`.

### Python SDK
```python
from sdk import ProvenantClient

client = ProvenantClient("http://127.0.0.1:8000")

# Verify identity
session = client.verify_identity(name="Jordan", email="jordan@acme.com")
print(session.proof)

# Notarize a document
result = client.notarize(
    document_name="Promissory Note",
    document_sha256="7d784f...",
    jurisdiction="TX",
    parties=[{"name": "Jordan", "email": "jordan@acme.com"}],
)

# Verify a proof
ok, reason = client.verify_proof(result.proof)
```

### CLI tool
```bat
py -m sdk.cli health
py -m sdk.cli verify-identity --name "Jordan" --email "jordan@acme.com"
py -m sdk.cli notarize --doc "Promissory Note" --hash <sha256> --state TX --signer "Jordan <jordan@acme.com>"
py -m sdk.cli notarize --doc "Promissory Note" --file document.pdf --state TX --signer "Jordan <jordan@acme.com>"
py -m sdk.cli verify proof.json
py -m sdk.cli revoke --proof-id prf_xxx
py -m sdk.cli ledger

REM Point at a remote API:
py -m sdk.cli --url https://api.useprovenant.xyz --api-key pk_live_xxx health
```
Config via env vars: `PROVENANT_URL`, `PROVENANT_API_KEY`.

---

## What the demo shows (for the betaworks "product demo" video)

Two demo scripts:

- **`py demo_full.py`** — the polished demo with 10 security checks, clean
  output, and a PASS/FAIL summary. Best for screen recording.
- **`py agent_demo.py`** — the original narrated agent trace.

Both run the same core loop: the agent drafts a document, hits the
notarization wall, calls the tool, then exercises the hardening:
registry-pinned verification, document binding, tamper detection,
**forged-key attack rejection**, **ledger chain**, external anchoring,
**idempotency**, and **revocation**. Screen-record `demo_full.py` for
the betaworks video.

See `VIDEO_SCRIPTS.md` for the three 2-minute video scripts.

---

## Layout

```
tangible/
  models.py        typed action/proof data structures
  crypto.py        REAL Ed25519 proof: sign / pinned-key verify / tamper-detect
  keyring.py       trusted key registry + fingerprint key_ids + rotation
  ledger.py        tamper-evident hash-chained ledger
  timestamp.py     external anchor hook (simulated)
  identity.py      SIMULATED IAL2 identity proofing
  compliance.py    request validation + RON eligibility by state
  notary.py        SIMULATED commissioned notary + journal
  service.py       orchestration: idempotency, revocation, ledgering (the core)
  identity_service.py  verify_identity verb (async session -> signed proof)
  providers/       fulfillment adapters (Simulated + real Stripe Identity)
  mcp_tool.py      agent-facing tool schema + call_tool()
  certificate.py   text (+ optional PDF) certificate rendering
  api.py           FastAPI HTTP layer
  verify.py        CLI proof verifier
sdk/
  __init__.py      ProvenantClient + exceptions
  client.py        typed HTTP client (sync, httpx-based)
  exceptions.py    ProvenantError, AuthenticationError, etc.
  cli.py           CLI tool (health, verify-identity, notarize, verify, revoke, ledger)
mcp_server.py      MCP server (stdio JSON-RPC, 3 tools exposed)
agent_demo.py      the end-to-end agent demo (narrated trace)
demo_full.py       polished demo with 10 security checks (for recording)
VIDEO_SCRIPTS.md   betaworks 3-video scripts + recording checklist
web/
  try.html         interactive demo (try identity + notarization live)
  index.html       landing page
  product.html     product overview
  docs.html        API documentation
  pricing.html     pricing tiers
  company.html     about / careers
  security.html    security & trust
  privacy.html     privacy policy
  terms.html       terms of service
  styles.css       shared styles
tests/             pytest e2e, hardening, API, and identity tests
```

## Next steps toward production
- Swap `identity.py` for a real IAL2 IDV integration.
- Swap `notary.py` for a RON-platform partner / commissioned-notary network.
- Move private keys to an HSM/KMS; publish the public registry.
- Replace `timestamp.py` with an RFC 3161 TSA or public-ledger anchor.
- Add verbs: identity verification, witnessing, inspection, apostille.
