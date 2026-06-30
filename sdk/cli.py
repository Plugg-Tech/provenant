"""Provenant CLI — interact with the API from the terminal.

Usage:
    provenant verify-identity --name "Jordan" --email "jordan@acme.com"
    provenant notarize --doc "Promissory Note" --hash <sha256> --state TX --signer "Jordan <jordan@acme.com>"
    provenant verify --proof proof.json
    provenant revoke --proof-id prf_xxx
    provenant ledger
    provenant health

Config:
    Set PROVENANT_URL (default: http://127.0.0.1:8000) and
    PROVENANT_API_KEY for authenticated requests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys


def _client(args: argparse.Namespace):
    from .client import ProvenantClient
    base = args.url or os.environ.get("PROVENANT_URL", "http://127.0.0.1:8000")
    key = args.api_key or os.environ.get("PROVENANT_API_KEY")
    return ProvenantClient(base_url=base, api_key=key)


def _print_json(data):
    print(json.dumps(data, indent=2))


def cmd_health(args):
    c = _client(args)
    _print_json(c.health())


def cmd_verify_identity(args):
    c = _client(args)
    session = c.verify_identity(name=args.name, email=args.email)
    _print_json({
        "action_id": session.action_id,
        "status": session.status,
        "provider": session.provider,
        "url": session.url,
        "proof": session.proof,
    })
    if session.status == "verified" and session.proof:
        print(f"\n  Identity verified. Proof: {session.proof['proof_id']}", file=sys.stderr)
    elif session.url:
        print(f"\n  Pending. Open: {session.url}", file=sys.stderr)


def cmd_notarize(args):
    c = _client(args)
    doc_hash = args.hash
    if not doc_hash and args.file:
        with open(args.file, "rb") as f:
            doc_hash = hashlib.sha256(f.read()).hexdigest()
    if not doc_hash:
        print("error: provide --hash or --file", file=sys.stderr)
        return 1

    parties = []
    for s in args.signer:
        if "<" in s and ">" in s:
            name, email = s.split("<", 1)[0].strip(), s.split("<", 1)[1].rstrip(">").strip()
        else:
            name, email = s, s
        parties.append({"name": name, "email": email, "role": "signer"})

    result = c.notarize(
        document_name=args.doc,
        document_sha256=doc_hash,
        jurisdiction=args.state.upper(),
        parties=parties,
        reference=args.reference,
        idempotency_key=args.idempotency_key,
    )
    _print_json({
        "action_id": result.action_id,
        "status": result.status,
        "rejection_reason": result.rejection_reason,
        "proof": result.proof,
    })
    if result.status == "completed" and result.proof:
        print(f"\n  Notarized. Proof: {result.proof['proof_id']}", file=sys.stderr)
    elif result.rejection_reason:
        print(f"\n  Rejected: {result.rejection_reason}", file=sys.stderr)


def cmd_verify(args):
    c = _client(args)
    with open(args.proof_file) as f:
        proof = json.load(f)
    ok, reason = c.verify_proof(proof)
    print(f"  valid={ok}  reason={reason}")
    return 0 if ok else 1


def cmd_revoke(args):
    c = _client(args)
    c.revoke(args.proof_id)
    print(f"  Revoked: {args.proof_id}")


def cmd_ledger(args):
    c = _client(args)
    result = c.verify_ledger()
    _print_json(result)


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser(
        prog="provenant",
        description="Provenant CLI — the physical-action API for agents",
    )
    p.add_argument("--url", help="API base URL (default: $PROVENANT_URL or http://127.0.0.1:8000)")
    p.add_argument("--api-key", help="API key (default: $PROVENANT_API_KEY)")
    sub = p.add_subparsers(dest="command", required=True)

    # health
    sub.add_parser("health", help="Check API health")

    # verify-identity
    s_id = sub.add_parser("verify-identity", help="Verify a person's identity")
    s_id.add_argument("--name", required=True, help="Full legal name")
    s_id.add_argument("--email", required=True, help="Email address")

    # notarize
    s_not = sub.add_parser("notarize", help="Notarize a document")
    s_not.add_argument("--doc", required=True, help="Document name")
    s_not.add_argument("--hash", dest="hash", help="SHA-256 hex of document bytes")
    s_not.add_argument("--file", help="Document file (hash computed automatically)")
    s_not.add_argument("--state", required=True, help="2-letter US state code")
    s_not.add_argument("--signer", action="append", required=True,
                       help="Signer as 'Name <email>' or just email")
    s_not.add_argument("--reference", help="Optional caller reference")
    s_not.add_argument("--idempotency-key", help="Retry-safe key")

    # verify
    s_ver = sub.add_parser("verify", help="Verify a saved proof")
    s_ver.add_argument("proof_file", help="Path to proof JSON file")

    # revoke
    s_rev = sub.add_parser("revoke", help="Revoke a proof")
    s_rev.add_argument("--proof-id", required=True, help="Proof ID to revoke")

    # ledger
    sub.add_parser("ledger", help="Verify the tamper-evident ledger chain")

    args = p.parse_args(argv)

    handlers = {
        "health": cmd_health,
        "verify-identity": cmd_verify_identity,
        "notarize": cmd_notarize,
        "verify": cmd_verify,
        "revoke": cmd_revoke,
        "ledger": cmd_ledger,
    }
    return handlers[args.command](args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
