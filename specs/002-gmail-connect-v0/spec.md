# 002 — Gmail Connect V0

Status: **stub spec — blocked / deferred**  
Owner: Paula  
Product brief: [docs/PRD.md](../../docs/PRD.md)

## TL;DR

The product door in the PRD is still: connect Gmail, read recent mail, show the same five checks. Do **not** implement this until Paula accepts a full spec **and** a Google OAuth client in testing mode exists.

```text
This spec (stub)
        |
        v
BLOCKED — no Google OAuth client yet
        |
        x  do not write Plan detail
        x  do not write Tasks beyond "wait"
        x  do not open a feature PR
```

Path B ([001](../001-paste-check-live/spec.md)) may go live without this feature.

## Intent

A Gmail-connected, read-only scan for invited test users. The person connects once. Kill Scam looks at new or recent mail and says whether a flagged message looks like a scam, with the reason visible. It never sends, deletes, or writes to the mailbox.

V0 is Paula plus invited family or test users on a Google Cloud OAuth consent screen in **testing** mode. It is not a public app for everyone.

## Users

- Paula
- Family or test users she adds on the Google testing-mode consent screen

## In scope (when unblocked)

- Connect Gmail with `gmail.readonly` only
- Show recent mail and run the five-step checklist on a chosen message
- Traces in Arize for a real check, when Arize keys are set

## Out of scope

- Unverified OAuth for the whole internet
- Sending, deleting, labeling, or otherwise writing mail
- SMS, letters, phone scams
- Auto-delete and auto-reply
- Mac Mini as a requirement for this spec

## Acceptance criteria

Taken from the PRD **Success** section. They are not met yet.

1. Paula can connect her Gmail and see recent mail classified without pasting.
2. A lookalike impôts / parcel / unpaid-bill mail is caught.
3. A normal school or newsletter mail is not called a scam.
4. Family can be added as Google test users and complete Connect Gmail with help once.
5. Arize shows traces for a real check.

## Blocked on

- A Google OAuth client (id, secret, and exact redirect URI)
- OAuth consent screen in testing mode, with only invited test users
- Paula saying yes to a finished spec, then a plan, then tasks

Google MFA / verification for a **public** app is a later track. It is not V0. Testing-mode consent is the V0 path, and it is not done.

## Human gate

Do not implement, and do not open a production feature PR for Gmail Connect, until:

1. Paula accepts this spec (it will need a fuller pass than this stub), and
2. The OAuth client and testing-mode consent are actually ready.

Until then this feature stays deferred.
