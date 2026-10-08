# 001 — Live paste-check hosting (Path B)

Status: **spec written, waiting for Paula**  
Owner: Paula  
Product brief: [docs/PRD.md](../../docs/PRD.md) (unchanged)

## TL;DR

Ship a public website of the app that already exists on `main`, so anyone can paste email text and see the five-step checklist. No Gmail sign-in. No new product behavior.

```text
Person opens the public URL
        |
        v
Opens "Check something else"
        |
        v
Pastes email text  -->  Check this message
        |
        v
Five visible steps
        |
        v
Looks OK  /  Be careful  /  Likely a scam
```

Gmail Connect stays on the page and stays blocked until Google is ready. That is a different feature ([002](../002-gmail-connect-v0/spec.md)).

## Intent

People need a link they can open when the laptop is closed. Today paste-check works on a machine that is running the app. Path B hosts that same screen on Render so a friend can paste an email and read the verdict without connecting a mailbox.

This is an interim door. The PRD still says Connect Gmail is the main product. Path B does not replace that.

## Users

- Anyone with the link who wants a second look at **email text** they can copy.
- Paula, to share one URL without asking people to install Python.
- Not: people who expect Kill Scam to read their Gmail inbox. That is feature 002.

## In scope

- A public Streamlit URL built from current `main` (`Dockerfile`, `render.yaml`).
- Paste email text into **Check something else** and press **Check this message**.
- The five steps stay visible, then one of: **Looks OK**, **Be careful**, **Likely a scam**.
- The check runs with Google OAuth settings left empty.
- The app still never sends, deletes, or changes mail.

## Out of scope

- Gmail OAuth, Connect Gmail, or reading a real inbox
- Mac Mini hosting (separate docs PR, not this feature)
- SMS as a product (no carrier, no phone-scam workflow)
- Auto-delete, auto-report, or auto-reply
- New checklist rules, new screens, or a live LLM judge
- Google verification for a public OAuth app

The existing paste box may still accept other pasted text (SMS or WhatsApp). Path B does not add an SMS product.

## Acceptance criteria

Each item is something a person can try on the live URL, or confirm from the running app without a mailbox.

1. The public URL loads in a normal browser and shows the Kill Scam title. It does not require a Google login to see the page.
2. **Check something else** is on the page. Pasting sample email text and pressing **Check this message** finishes with a visible verdict of **Looks OK**, **Be careful**, or **Likely a scam** (the scam line may include “do not click”).
3. The same check shows the five steps on screen: what it wants, who it claims to be, web addresses, known scam patterns, and the verdict / what to do.
4. A paste check does not send, delete, label, or otherwise write to any mailbox. No Gmail account is required to complete criteria 2 and 3.
5. The page still works when `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` are unset. Connect Gmail may say it is not set up yet. Paste still returns a verdict.
6. The live checklist does not need an OpenAI key. The five checks on `main` are rules in the app, not a live model call. `OPENAI_API_KEY` may stay empty. Tests use synthetic examples in `evals/fixtures.json` and do not call OpenAI. Optional Arize keys are not required for a verdict.
7. An empty paste does not pretend to be a verdict. The app asks for a message first.
8. The page still says this is a helper, not a guarantee, and that it does not open the links inside the pasted mail.

## Open questions / human gates

Paula must say yes before this spec is treated as accepted.

- Is a **public** paste URL acceptable while the PRD still limits V0 Gmail to invited testers?
- Which Render account and service name? Deploy cannot start until Paula signs in.
- Is a slow first load (Render cold start) acceptable for family?
- Should the shared URL be unlisted (link only) or easy to find?
- After Path B is live, do we leave Connect Gmail visible but not configured, or hide it? Default in this spec: leave the current screen as it is. Hiding it would be new product code and needs its own spec.

Do not deploy, and do not merge a deploy PR, until Paula accepts this spec and the plan.
