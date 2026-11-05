# Signingflow agent skills

Skills that teach an agent how to call Signingflow. They describe calls the API and the MCP server already support. They do not add an endpoint.

Five skills:

- `signingflow-send-document` sends one PDF to named people and stops before anyone signs.
- `signingflow-envelope-status` reports who has signed, who is waiting, sends a reminder after confirmation, and downloads the file after everyone has signed.
- `signingflow-webhooks` creates a destination, stores the signing secret from that response, and verifies the HMAC on the raw body.
- `signingflow-mcp` connects a hosted read-only agent or a local API key.
- `signingflow-integration` is the pasteable prompt for send, webhooks, and envelope status. The same text is on the API reference.

## Use them

Point the agent at `<name>/SKILL.md`. `npx skills add` is not the install command.

Set these in the environment. Do not pass them as command arguments.

- `SIGNINGFLOW_API_KEY` — secret from the API console, shaped like `df_sk_...`
- `SIGNINGFLOW_WORKSPACE_ID` — workspace the key should act in
- `SIGNINGFLOW_BASE_URL` — API host, with no trailing slash
- `SIGNINGFLOW_ENV` — `SANDBOX` or `LIVE`
- `SIGNINGFLOW_UPLOAD_ROOT` — local directory for PDF upload. The hosted connection cannot read files.
- `SIGNINGFLOW_WEBHOOK_SECRET` — signing secret returned when a destination is created

Create the key in the console: activate the API platform, create a project and an application, then create a key with `storage:write`, `envelope:write`, and `envelope:send` for sending. A hosted Claude or ChatGPT sign-in is `envelope:read` only.

## What an agent must not do

- Send, remind, upload, or create a draft until the person agrees. The MCP tools return `CONFIRMATION_REQUIRED` until `confirm` is true.
- Sign, request a signing confirmation, or fill the form with the sender key.
- Place signature fields. The send path adds recipients only.
- Register an account through the API. There is no registration call.
- Reuse an `idempotencyKey`. Generate a new UUID version 4 for every request. A reused key is stored for the whole environment and the error can name the earlier resource.
- Put the API key or the webhook signing secret on the public webhook receiver, or into a destination's bearer, basic, or API key credential.
- Create a webhook destination with auth `NONE`. Leave the auth empty so it stays `HMAC`.

## Checks

From the repository root:

```bash
python3 tests/test_skill_structure.py
python3 tests/test_webhook_signature.py
```

No API key is required.
