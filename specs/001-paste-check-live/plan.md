# 001 — Plan: live paste-check on Render

Status: **plan written, waiting for Paula**  
Spec: [spec.md](spec.md)

## TL;DR

Deploy the app already on `main`. Do not write a new paste feature. Render builds the existing `Dockerfile` using `render.yaml`. Paste-check does not need a Gmail client.

```text
main (already has paste-check)
        |
        v
Render builds Dockerfile
        |
        v
Public https URL
        |
        +--> Check something else   (this feature)
        |
        +--> Connect Gmail          (stays "not set up" — no Google client)
```

## Approach

1. Use the service already described in `render.yaml`: Docker web service `kill-scam`, `KILL_SCAM_HOSTED=1`, `PORT=8080`, health check `/`.
2. Paula signs in to Render and connects this GitHub repo at `main`. No application code change is required for Path B.
3. Leave Google OAuth variables unset. The home screen already explains that Connect Gmail is not set up, and paste still runs.
4. Do not add a Gmail OAuth client, redirect URI, or test-user list for this feature.

## Environment

The repo template is `.env.example` (there is no `.env.template`). Set values in the Render dashboard. Do not commit secrets.

| Variable | Path B |
| --- | --- |
| `KILL_SCAM_HOSTED` | Already `1` in `render.yaml`. Keeps tokens off a shared disk. |
| `PORT` | Already `8080` in `render.yaml`. |
| `GOOGLE_CLIENT_ID` | Leave empty. Not required. |
| `GOOGLE_CLIENT_SECRET` | Leave empty. Not required. |
| `GOOGLE_REDIRECT_URI` | Leave empty. Not required. |
| `OPENAI_API_KEY` | Leave empty. The five checks do not call OpenAI today. |
| `OPENAI_MODEL` | Leave empty. Same reason. |
| `ARIZE_API_KEY` / `ARIZE_SPACE_ID` | Optional. A verdict still appears when they are missing. |

## What we will not change

- No new screens, checklist rules, or dependencies.
- No Gmail client library setup for Path B.
- No Mac Mini runbook (that is PR #11, separate).
- No CI change (that is PR #12, separate).

## Risks

- **Cold starts.** Render may sleep the service. The first visitor waits while it wakes up. The checklist itself is unchanged.
- **Key cost.** Path B should not spend OpenAI money, because the live checklist does not call a model. Cost appears only if someone later sets a key and new code starts using it. Arize, if turned on, is Paula’s own space.
- **False confidence without Gmail.** A paste has no verified From address. “Looks OK” means the five text checks did not find scam pressure. It does not mean the sender is real. The page must keep saying this is a helper, not a guarantee.
- **Public link.** Anyone with the URL can paste text. Do not paste passwords, one-time codes, or bank PINs. The app must not log full message bodies (existing rule).

## Open questions

- Confirm the Render account before anyone clicks Deploy.
- Confirm we ship from `main` as it is, with Connect Gmail visible and unconfigured.
- Decide whether Arize stays off for the first public URL so pasted mail is not traced until Paula opts in.
