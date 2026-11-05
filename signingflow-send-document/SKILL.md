---
name: signingflow-send-document
description: >
  Send one PDF for signature in Signingflow. Use when someone asks to upload a
  file, add signers, prepare a draft, or send an envelope. Stop after the
  envelope is sent. Do not place signature fields and do not sign for a recipient.
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

# Send a document

This skill follows the sender path in the MCP tools `prepare_draft` and `send_for_signature`. Prefer those tools. Use `call_operation` only when you must repeat one step, and only with an `operationId` returned by `search_operations`.

The hosted connection cannot upload or send. It returns `WRITES_DISABLED`. Upload runs on the local connection, and the PDF path must stay inside `SIGNINGFLOW_UPLOAD_ROOT`.

Every call below whose catalog effect is `write` or `irreversible` needs an explicit yes from the person first. Pass `confirm: true` only after that yes. A missing yes returns `CONFIRMATION_REQUIRED`.

Required capabilities: `storage:write`, `envelope:write`, and `envelope:send`. A missing capability returns `CAPABILITY_DENIED`.

This skill does not place signature fields. Recipients are people on the first document. Field coordinates are not part of this path.

## Headers

Send the API key as `Authorization: Bearer`. Send `X-Request-Workspace-Id` and `X-Request-Env` (`SANDBOX` or `LIVE`). Do not put the key in a query string or a command argument.

## 1. Store the PDF

`upload_file` does this. The steps are `StorageService_BatchAddStorage` (`POST /v1/storages:batchAddStorage`, capability `storage:write`, effect `write`, confirm required) and then a PUT of the file bytes to the returned upload URL. The bytes do not go in `call_operation`.

```json
{
  "storages": [
    {
      "originalName": "contract.pdf",
      "displayName": "contract.pdf",
      "size": "1200",
      "extension": "pdf",
      "mimeType": "application/pdf"
    }
  ]
}
```

Then `StorageService_BatchAcknowledgeUpload` (`POST /v1/storages:batchAcknowledgeUpload`, capability `storage:write`, effect `write`, confirm required). Both storage calls accept `idempotencyKey`. Generate a new UUID version 4 for each request. Never copy a key from this document or reuse a key across requests. The key is stored for the whole environment, so a reused key returns `ALREADY_EXISTS` and can name the earlier resource. Reuse the same key only to retry that same request after a timeout.

```json
{
  "names": ["storages/00000000-0000-4000-8000-000000000004"]
}
```

Keep the storage name from the acknowledge response.

## 2. Create the draft

`EnvelopeService_AddEnvelope` (`POST /v1/envelopes:addEnvelope`, capability `envelope:write`, effect `write`, confirm required). It accepts `idempotencyKey`. `prepare_draft` stops here and does not email anyone. It still needs confirm.

```json
{
  "idempotencyKey": "NEW_UUID_V4",
  "envelope": {
    "display_name": "NDA",
    "description": "Please sign",
    "documents": [
      {
        "display_name": "NDA",
        "attachments": [{ "storage_id": "STORAGE_ID" }],
        "supplemental": false
      }
    ]
  }
}
```

Save the envelope name. It looks like `envelopes/{id}`.

## 3. Read the draft, then add recipients

`EnvelopeService_ViewEnvelope` (`GET /v1/{name_1}:view`, capability `envelope:read`, effect `read`). Ask for `read_mask=documents,compliance`. Copy `documents[].uid` from that response. Do not invent a document id.

`EnvelopeService_UpdateEnvelope` (`PATCH /v1/{envelope.name}`, capability `envelope:write`, effect `write`, confirm required). This call is not idempotent. Read the draft again before you retry it. Put every recipient on the first document only.

```json
{
  "name": "envelopes/00000000-0000-4000-8000-000000000001",
  "display_name": "NDA",
  "description": "Please sign",
  "compliance": { "profile": "STANDARD" },
  "documents": [
    {
      "uid": "00000000-0000-4000-8000-000000000002",
      "display_name": "NDA",
      "participants": [
        {
          "uid": "00000000-0000-4000-8000-000000000003",
          "display_name": "Ada Lovelace",
          "alternate_email": "ada@example.com",
          "role": "SIGNER",
          "type": "PERSONAL",
          "action_order_type": "SERIAL",
          "action_order_number": 1
        }
      ]
    }
  ]
}
```

Each recipient needs a display name and an email. Order numbers start at 1. A new recipient uid is a new UUID. The document uid is the one from the view.

## 4. Send

`EnvelopeService_SendEnvelope` (`POST /v1/{name}:send`, capability `envelope:send`, effect `irreversible`, confirm required). Say who will receive the email and that sending cannot be undone. It accepts `idempotencyKey`. Generate a new UUID version 4 for this send. Do not reuse the create key or a sample key. If the HTTP call times out, view the envelope before you send again. A replay of the same key returns `ALREADY_EXISTS` and can name the earlier resource. If send committed and billing failed, the envelope is already sent.

```json
{
  "idempotencyKey": "NEW_UUID_V4"
}
```

`send_for_signature` performs steps 1 through 4. If update or send fails, the draft remains and nothing was emailed for the failed step. Tell the person the envelope name.

## Stop after send

`next_step` for variant `standard` continues after `EnvelopeService_SendEnvelope` into signer calls. Do not run them with the sender key, and do not confirm them:

- `EnvelopeService_RequestFillFormEnvelopeSigningConfirmation`
- `EnvelopeService_VerifyFillFormEnvelopeSigningConfirmation`
- `EnvelopeService_FillFormEnvelope` (capability `envelope:sign`)

Those calls belong to the recipient. This skill ends when the envelope is sent.
