"""Provenant MCP server — exposes physical-action tools to LLM agents.

Run:  python -m provenant.mcp_server
       or add to Claude Desktop config:
       { "mcpServers": { "provenant": { "command": "python", "args": ["-m", "provenant.mcp_server"] } } }

The server exposes two tools:
  - provenant_verify_identity: verify a person's identity (IAL2), returns a signed proof
  - provenant_notarize: notarize a document, returns a cryptographically signed proof

Both tools return results the agent can verify independently.
"""
from __future__ import annotations

import json
import sys
from typing import Any

from tangible import crypto, mcp_tool
from tangible.keyring import default_keyring
from tangible.models import ACTION_NOTARIZE, ActionRequest, Party, new_id
from tangible.pay_service import PayError, PayService
from tangible.service import TangibleService

_service = TangibleService()


def _resolve_action(action_ref: str):
    action = _service.get_action(action_ref)
    if action is not None:
        kind = action.request.get("action_type", "action") if action.request else "action"
        return {"action_ref": action_ref, "kind": kind,
                "verified": action.status == "completed"}
    return None


_pay_service = PayService(action_resolver=_resolve_action)

TOOLS = [
    {
        "name": "provenant_verify_identity",
        "description": (
            "Verify a person's identity using IAL2 identity proofing. "
            "Returns a cryptographically signed proof of identity verification. "
            "Use this when a workflow requires confirming someone's real-world identity."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full legal name of the person to verify",
                },
                "email": {
                    "type": "string",
                    "description": "Email address of the person to verify",
                },
            },
            "required": ["name", "email"],
        },
    },
    {
        "name": "provenant_notarize",
        "description": (
            "Notarize a document via remote online notarization. "
            "Returns a cryptographically signed, tamper-evident proof of notarization. "
            "Use this when a workflow requires a legally binding notarized signature."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "Human-readable name of the document",
                },
                "document_sha256": {
                    "type": "string",
                    "description": "SHA-256 hex digest of the document bytes (64 hex characters)",
                },
                "jurisdiction": {
                    "type": "string",
                    "description": "2-letter US state code where notarization occurs (e.g. TX, NY)",
                },
                "parties": {
                    "type": "array",
                    "description": "List of parties involved in the notarization",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Full legal name"},
                            "email": {"type": "string", "description": "Email address"},
                            "role": {
                                "type": "string",
                                "enum": ["signer", "witness"],
                                "description": "Role in the notarization (default: signer)",
                            },
                        },
                        "required": ["name", "email"],
                    },
                },
                "reference": {
                    "type": "string",
                    "description": "Optional caller reference for tracking",
                },
                "idempotency_key": {
                    "type": "string",
                    "description": "Optional retry-safe key; same key returns the same result",
                },
            },
            "required": ["document_name", "document_sha256", "jurisdiction", "parties"],
        },
    },
    {
        "name": "provenant_pay",
        "description": (
            "Charge and return a cryptographically verifiable receipt. "
            "Pass action_ref to bind it to a proven action (e.g. a prior "
            "notarization or identity verification), so the receipt attests that "
            "money moved AND the real-world action behind it is verified."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "integer",
                    "description": "Amount in minor units (e.g. cents: 4200 = $42.00)",
                },
                "currency": {
                    "type": "string",
                    "description": "ISO 4217 currency code, e.g. usd",
                },
                "payment_method": {
                    "type": "string",
                    "description": "Rail payment-method token (use 'sim_ok' in test mode)",
                },
                "action_ref": {
                    "type": "string",
                    "description": "Optional prior action id to bind the receipt to",
                },
            },
            "required": ["amount", "currency", "payment_method"],
        },
    },
    {
        "name": "provenant_verify_proof",
        "description": (
            "Verify a Provenant proof. Checks the Ed25519 signature against the trusted key registry, "
            "confirms document binding, and checks revocation status. Use this to validate a proof "
            "before relying on it in a workflow."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "proof": {
                    "type": "object",
                    "description": "The proof object to verify (as returned by notarize or verify_identity)",
                },
            },
            "required": ["proof"],
        },
    },
]


def _handle_verify_identity(args: dict) -> dict:
    from tangible.identity_service import IdentityService
    svc = IdentityService()
    party = Party(name=args["name"], email=args["email"])
    session = svc.start(party)
    result: dict[str, Any] = {
        "action_id": session.action_id,
        "status": session.status,
        "provider": session.provider,
    }
    if session.url:
        result["url"] = session.url
    if session.proof:
        result["proof"] = session.proof
        ok, reason = crypto.verify_proof(session.proof)
        result["verification"] = {"valid": ok, "reason": reason}
    return result


def _handle_notarize(args: dict) -> dict:
    parties = [
        Party(
            name=p["name"],
            email=p["email"],
            role=p.get("role", "signer"),
        )
        for p in args["parties"]
    ]
    req = ActionRequest(
        action_type=ACTION_NOTARIZE,
        document_name=args["document_name"],
        document_sha256=args["document_sha256"],
        parties=parties,
        jurisdiction=args["jurisdiction"],
        reference=args.get("reference"),
        idempotency_key=args.get("idempotency_key"),
    )
    result = _service.notarize(req)
    out: dict[str, Any] = {
        "action_id": result.action_id,
        "status": result.status,
    }
    if result.proof:
        out["proof"] = result.proof
        ok, reason = crypto.verify_proof(result.proof)
        out["verification"] = {"valid": ok, "reason": reason}
    if result.rejection_reason:
        out["rejection_reason"] = result.rejection_reason
    return out


def _handle_pay(args: dict) -> dict:
    idempotency_key = args.get("idempotency_key") or new_id("idem")
    try:
        receipt = _pay_service.pay(
            amount=args["amount"],
            currency=args["currency"],
            payment_method=args["payment_method"],
            idempotency_key=idempotency_key,
            action_ref=args.get("action_ref"),
        )
    except PayError as exc:
        return {"error": exc.to_dict()}
    ok, reason = _pay_service.verify_receipt(receipt)
    return {"receipt": receipt, "verification": {"valid": ok, "reason": reason}}


def _handle_verify_proof(args: dict) -> dict:
    from tangible.pay_service import is_receipt, reconstruct_proof

    proof = args["proof"]
    # Accept a pay receipt envelope as well as a flat proof (Decision 8).
    target = reconstruct_proof(proof) if is_receipt(proof) else proof
    ok, reason = crypto.verify_proof(target)
    result: dict[str, Any] = {"valid": ok, "reason": reason}
    if not is_receipt(proof) and proof.get("proof_id") in _service._revoked:
        result["valid"] = False
        result["reason"] = "proof has been revoked"
    return result


HANDLERS = {
    "provenant_verify_identity": _handle_verify_identity,
    "provenant_notarize": _handle_notarize,
    "provenant_pay": _handle_pay,
    "provenant_verify_proof": _handle_verify_proof,
}


def _make_response(req_id: int | str, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _make_error(req_id: int | str | None, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _handle_message(msg: dict) -> dict | None:
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        return _make_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "provenant",
                "version": "0.3.0",
            },
        })

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return _make_response(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        handler = HANDLERS.get(tool_name)
        if not handler:
            return _make_error(req_id, -32601, f"Unknown tool: {tool_name}")
        try:
            result = handler(arguments)
            return _make_response(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as exc:
            return _make_response(req_id, {
                "content": [{"type": "text", "text": f"Error: {exc}"}],
                "isError": True,
            })

    if method == "ping":
        return _make_response(req_id, {})

    return _make_error(req_id, -32601, f"Unknown method: {method}")


def main() -> None:
    """Run the MCP server over stdio (JSON-RPC)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            resp = _make_error(None, -32700, "Parse error")
            print(json.dumps(resp), flush=True)
            continue

        resp = _handle_message(msg)
        if resp is not None:
            print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
