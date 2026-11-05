---
name: signingflow-webhooks
description: >
  Create a Signingflow webhook destination, store the signing secret from the
  create response, and verify X-Signingflow-Signature or X-Webhook-Signature
  as HMAC-SHA256 of the raw body. Use when someone asks for envelope events
  or webhook signature checks.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - SIGNINGFLOW_API_KEY
        - SIGNINGFLOW_WORKSPACE_ID
        - SIGNINGFLOW_BASE_URL
    primaryEnv: SIGNINGFLOW_API_KEY
---

# Webhooks

Create a destination with `WebhookUrlService_AddWebhookUrl` (`POST /v1/webhookUrls:add`, capability `webhook:write`, effect `write`). Confirm with the person first. The call returns `CONFIRMATION_REQUIRED` until `confirm` is true. It accepts `idempotencyKey`. Generate a new UUID version 4 for this request. Never copy a key from this document or reuse a key across requests. The key is stored for the whole environment, so a reused key returns `ALREADY_EXISTS` and can name the earlier resource.

`displayName` is 1 to 100 characters. `httpRequestUri` must be a public `https://` URL. `events` uses catalog values such as `DOC_ENVELOPE_COMPLETED`. An empty method is stored as `POST`. An empty `httpConfig` is stored as `{"auth":"HMAC"}`.

```json
{
  "idempotencyKey": "NEW_UUID_V4",
  "webhookUrl": {
    "displayName": "Envelope events",
    "httpRequestUri": "https://example.com/webhooks/signingflow",
    "events": ["DOC_ENVELOPE_COMPLETED"]
  }
}
```

The 201 body includes `signingSecret`, 64 hex characters. Store it in `SIGNINGFLOW_WEBHOOK_SECRET` immediately. Do not repeat the secret in the chat, a log, a committed file, or a destination credential. A repeated idempotency key returns `ALREADY_EXISTS` and does not return the original destination, so the secret is not recoverable from a replay.

`WebhookUrlService_ViewWebhookUrl` (`GET /v1/{name}:view`, capability `webhook:read`, effect `read`) does not return the signing secret. Do not read the destination to recover it.

Leave `httpConfig` empty so the server stores `{"auth":"HMAC"}`. Do not set `auth` to `NONE`. A `NONE` destination has no signature. `BEARER`, `BASIC`, and `API_KEY` are extra credentials sent to your URL. They do not replace the HMAC, and they must not be the Signingflow API key or `signingSecret`.

Rotation is not an operation in the agent catalog. Do not invent a rotate `operationId`. When a destination is rotated in the product, the create-time rule still holds: the new secret is shown on that write. The previous secret can stay valid for 0, 1, 24, or 168 hours.

An operator can list deliveries with `WebhookService_ListWebhooks` (`GET /v1/{parent}`, capability `webhook:read`, effect `read`) and read one with `WebhookService_ViewWebhook` (`GET /v1/{name}:view`, capability `webhook:read`, effect `read`). Parent for the list is `webhooks`. The public receiver does not call these. Do not put `SIGNINGFLOW_API_KEY` on that host.

## Verify the signature

For `HMAC`, the sender computes lowercase hex HMAC-SHA256 over the stored body and posts those same bytes. The MAC does not include a timestamp. The same value is sent as `X-Signingflow-Signature` and `X-Webhook-Signature`. During the grace window the previous secret is sent as `X-Signingflow-Signature-Previous` and `X-Webhook-Signature-Previous`.

Verify the exact bytes you received. Parse the JSON only after the MAC matches. Do not serialize the parsed object and hash that.

```python
import hashlib
import hmac

secret = b"example-secret"
body = b'{"event":"DOC_ENVELOPE_COMPLETED"}'
print(hmac.new(secret, body, hashlib.sha256).hexdigest())
```

The helper `scripts/verify_webhook.py` reads the secret from `SIGNINGFLOW_WEBHOOK_SECRET`. Pass `--previous` to use `SIGNINGFLOW_WEBHOOK_SECRET_PREVIOUS`. Put the hex signature in a file. Do not pass it as a command argument.

```bash
python3 scripts/verify_webhook.py --body body.bin --signature-file signature.txt
```

Because the MAC has no timestamp, a captured request can be sent again until you remember it or the secret rotates. After a match, store a hash of the raw body in your own system and reject a repeat. The signature alone is not a nonce.

A test delivery from `WebhookUrlService_TestWebhookUrl` (`POST /v1/{name}:test`, capability `webhook:write`, effect `write`, confirm required) is not the production event body. Verify a production delivery against the body you actually received.
