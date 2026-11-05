---
name: signingflow-envelope-status
description: >
  Check who has signed a Signingflow envelope, who has not opened it, who opened
  it and has not signed, send a reminder after confirmation, or download the
  file after everyone has signed.
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

# Envelope status

Prefer the MCP tools `envelope_status`, `waiting_to_sign`, `send_reminder`, and `download_signed`. Envelope names look like `envelopes/{id}`.

Reads need capability `envelope:read`. A reminder needs capability `envelope:send`. The hosted sign-in can read. It cannot remind: the call returns `WRITES_DISABLED`.

## What is waiting

`envelope_status` without an envelope calls `EnvelopeService_ListEnvelopes` (`GET /v1/{parent}`, capability `envelope:read`, effect `read`) with `parent=envelopes`, `pageSize=10`, and `directory=needAction`. It then calls `EnvelopeService_ViewEnvelope` (`GET /v1/{name_1}:view`) for up to five rows.

With an envelope, it only views that envelope. The sentence names the title, the state, who has signed, and who is next.

## Who has not signed

`waiting_to_sign` lists envelopes you sent with `EnvelopeService_ListEnvelopes` and `directory=waitingOthers`, then views each one with `read_mask=participants,documents`.

The groups are:

- `notOpened` — the recipient has not opened the envelope
- `openedNotSigned` — they opened it and have not signed
- `signed`
- `declined`

`olderThanDays` keeps people who have been waiting at least that many whole days. It does not send a reminder.

## Reminder

`send_reminder` calls `EnvelopeService_RemindEnvelopeSigners` (`POST /v1/{name}:remind`, capability `envelope:send`, effect `irreversible`). Confirm with the person first. The tool returns `CONFIRMATION_REQUIRED` until `confirm` is true. The call is not idempotent, so do not retry it blindly. It queues a notice for people who can still sign. It does not change the automatic reminder schedule. The hosted connection keeps this off.

## Download

`download_signed` views the envelope, then calls `EnvelopeService_DownloadEnvelope` (`GET /v1/{name}:download`, capability `envelope:read`, effect `read`) only when the state is `COMPLETED`. Any earlier state returns `INVALID_ARGUMENT` and no file.

This skill does not void or delete an envelope.
