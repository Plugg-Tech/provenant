"""Agent-facing tool surface.

This is the shape an AI agent sees: a single tool, `tangible_notarize`, with a
JSON input schema (the same thing you would register with an MCP server). The
agent_demo calls `call_tool(...)` exactly as an LLM agent would invoke the tool.
"""
from __future__ import annotations

from dataclasses import asdict

from .models import ACTION_NOTARIZE, ActionRequest, Party
from .service import TangibleService

NOTARIZE_TOOL = {
    "name": "tangible_notarize",
    "description": (
        "Notarize a document in the physical world and get back a cryptographically "
        "verifiable proof. Call this when a workflow requires a notarized signature."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "document_name": {"type": "string"},
            "document_sha256": {"type": "string", "description": "sha256 hex of the document bytes"},
            "jurisdiction": {"type": "string", "description": "2-letter US state code, e.g. TX"},
            "parties": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "role": {"type": "string", "enum": ["signer", "witness"]},
                    },
                    "required": ["name", "email"],
                },
            },
            "reference": {"type": "string"},
            "idempotency_key": {"type": "string", "description": "retry-safe key"},
        },
        "required": ["document_name", "document_sha256", "jurisdiction", "parties"],
    },
}

# A single shared service instance backs the tool (in-memory store + ledger).
_service = TangibleService()


def get_service() -> TangibleService:
    return _service


def call_tool(name: str, arguments: dict) -> dict:
    if name != "tangible_notarize":
        return {"error": f"unknown tool '{name}'"}

    parties = [
        Party(
            name=p["name"],
            email=p["email"],
            role=p.get("role", "signer"),
            force_identity_fail=p.get("force_identity_fail", False),
        )
        for p in arguments["parties"]
    ]
    req = ActionRequest(
        action_type=ACTION_NOTARIZE,
        document_name=arguments["document_name"],
        document_sha256=arguments["document_sha256"],
        parties=parties,
        jurisdiction=arguments["jurisdiction"],
        reference=arguments.get("reference"),
        idempotency_key=arguments.get("idempotency_key"),
    )
    return asdict(_service.notarize(req))
