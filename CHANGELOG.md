# Changelog

## 1.1.1 - 2026-11-05

### Changed

- The public copy of these skills is https://github.com/Signingflow/skills.

## 1.1.0 - 2026-11-05

### Changed

- `signingflow-integration` is the pasteable prompt. It builds only the selected products: send a document, webhooks, and envelope status. The same text is on the API reference.

## 1.0.1 - 2026-11-05

### Fixed

- Sample `idempotencyKey` values are no longer real UUIDs. Each request needs a new UUID version 4.
- Webhook guidance keeps `HMAC` on, refuses `NONE`, and keeps the API key and signing secret off the public receiver and off destination credentials.
- `verify_webhook.py` reads the signature from a file.
- The sender posts the same body bytes it signs.

## 1.0.0 - 2026-11-05

### Added

- `signingflow-send-document` documents the sender path used by `send_for_signature` and stops at `EnvelopeService_SendEnvelope`.
- `signingflow-envelope-status` documents status, waiting recipients, reminder, and download.
- `signingflow-webhooks` documents destination create and HMAC verification. `scripts/verify_webhook.py` checks the raw body.
- `signingflow-mcp` documents hosted read-only sign-in and the local API key connection.
- `signingflow-integration` is the single integration prompt. Published SDK packages are not included.
