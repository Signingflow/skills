#!/usr/bin/env python3
"""The webhook helper matches hex(HMAC-SHA256(secret, raw_body))."""

from __future__ import annotations

import hashlib
import hmac
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "signingflow-webhooks" / "scripts" / "verify_webhook.py"
SECRET = "example-secret"
BODY = b'{"event":"DOC_ENVELOPE_COMPLETED"}'


def sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def run(signature: str, *, previous: bool = False) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile() as body, tempfile.NamedTemporaryFile("w") as signature_file:
        body.write(BODY)
        body.flush()
        signature_file.write(signature)
        signature_file.flush()
        command = [
            sys.executable,
            str(SCRIPT),
            "--body",
            body.name,
            "--signature-file",
            signature_file.name,
        ]
        if previous:
            command.append("--previous")
        env_name = "SIGNINGFLOW_WEBHOOK_SECRET_PREVIOUS" if previous else "SIGNINGFLOW_WEBHOOK_SECRET"
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env={env_name: SECRET},
        )


def main() -> None:
    digest = sign(SECRET, BODY)
    matched = run(digest)
    if matched.returncode != 0:
        print(matched.stderr, file=sys.stderr)
        raise SystemExit(1)
    if SECRET in matched.stdout or SECRET in matched.stderr:
        print("verifier printed the secret", file=sys.stderr)
        raise SystemExit(1)
    rejected = run("00" * 32)
    if rejected.returncode == 0:
        print("verifier accepted a bad signature", file=sys.stderr)
        raise SystemExit(1)
    previous = run(digest, previous=True)
    if previous.returncode != 0:
        print(previous.stderr, file=sys.stderr)
        raise SystemExit(1)
    print("webhook signature ok")


if __name__ == "__main__":
    main()
