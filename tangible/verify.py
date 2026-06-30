"""CLI: verify a saved proof. Usage: python -m tangible.verify proof.json"""
from __future__ import annotations

import json
import sys

from . import crypto


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m tangible.verify <proof.json>")
        return 2
    with open(argv[1]) as f:
        proof = json.load(f)
    ok, reason = crypto.verify_proof(proof)
    print(f"valid={ok}  reason={reason}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
