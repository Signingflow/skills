#!/usr/bin/env python3
"""Verify a Signingflow webhook HMAC.

The signature is lowercase hex HMAC-SHA256 over the raw body bytes.
The MAC does not include a timestamp.
Current headers are X-Signingflow-Signature and X-Webhook-Signature.
During a secret grace period the same MAC for the previous secret is sent as
X-Signingflow-Signature-Previous and X-Webhook-Signature-Previous.

The secret is read from the environment. The signature is read from a file.
Neither value is a command argument.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import sys


def sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a Signingflow webhook HMAC.")
    parser.add_argument("--body", required=True, help="Path to the raw request body.")
    parser.add_argument("--signature-file", required=True, help="Path to a file that contains the hex signature.")
    parser.add_argument(
        "--previous",
        action="store_true",
        help="Compare against SIGNINGFLOW_WEBHOOK_SECRET_PREVIOUS.",
    )
    args = parser.parse_args()
    env_name = "SIGNINGFLOW_WEBHOOK_SECRET_PREVIOUS" if args.previous else "SIGNINGFLOW_WEBHOOK_SECRET"
    secret = os.environ.get(env_name, "")
    if not secret:
        print(f"{env_name} is required", file=sys.stderr)
        return 2
    with open(args.body, "rb") as handle:
        body = handle.read()
    with open(args.signature_file, "r", encoding="utf-8") as handle:
        signature_text = handle.read()
    expected = sign(secret, body)
    supplied = signature_text.strip().lower()
    if hmac.compare_digest(expected, supplied):
        print("signature matches")
        return 0
    print("signature does not match", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
