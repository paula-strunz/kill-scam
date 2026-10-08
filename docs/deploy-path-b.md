# Path B — paste-check on Render

A person who is not an engineer can put the existing Kill Scam paste checker on the public web. No Gmail sign-in. No new app code.

**Path B** means: open the website, expand **Check something else**, paste a message, and see the five checks. Connect Gmail stays off.

```text
You sign in to Render          <-- a person must do this
        |
        v
Render builds main
(Dockerfile + render.yaml already there)
        |
        v
Public https URL
        |
        v
Check something else
paste one sample message
        |
        v
Likely a scam + five steps
```

The secret file in this repo is `.env.example` (there is no `.env.template`). It lists Google and OpenAI names. **Path B does not need those filled in.**

---

## Blockers (read this first)

1. **Render account sign-in is a human step.** This page cannot sign in for you. Until someone is logged in at [render.com](https://render.com/), nothing deploys.
2. **Do not merge this docs pull request to unblock deploy.** `main` already has `Dockerfile` and `render.yaml`. Deploy **from `main` as it is**. Merging this page only updates the instructions.

---

## Before you start

- A GitHub login that can see [paula-strunz/kill-scam](https://github.com/paula-strunz/kill-scam).
- A Render account linked to that GitHub login.
- Branch to deploy: **`main`**.
- You do **not** need a Google Cloud project for this path.
- You do **not** need an OpenAI key. The five checks do **not** call a live language model. `.env.example` marks `OPENAI_API_KEY` as unused for those checks. Leave it empty. Add it later only if a future change says wording polish needs it.

`render.yaml` already sets `KILL_SCAM_HOSTED=1` and `PORT=8080`. The Dockerfile sets the same two. You do not type them.

---

## 1. Open Render and sign in

1. Go to [render.com](https://render.com/).
2. Sign in (or create the account) with the GitHub user that can see this repo.
3. If Render asks to connect GitHub, allow it to see **paula-strunz/kill-scam**.

Stop here if you cannot sign in. That is the blocker. It is not a missing file on `main`.

## 2. New Web Service from this repo

1. In the dashboard, choose **New** → **Web Service**.
2. Pick the GitHub repo **paula-strunz/kill-scam**.
3. Branch: **`main`**.
4. If Render offers **Blueprint** (or “use the `render.yaml` in the repo”), use that. The file is already on `main`. It chooses Docker, the service name `kill-scam`, and the health check `/`.
5. If you are on a plain Web Service form instead of Blueprint:
   - Language / runtime: **Docker** (not Python).
   - Dockerfile path: `Dockerfile` at the repo root.
   - Do not invent a start command. The Dockerfile already runs Streamlit.

## 3. Environment variables — paste path only

Set **nothing** that is only for Gmail or a live model.

| Name | Path B |
| --- | --- |
| `KILL_SCAM_HOSTED` | Already `1` in `render.yaml` and the Dockerfile. Leave it. |
| `PORT` | Already `8080` in those same files. Leave it. |
| `GOOGLE_CLIENT_ID` | **Leave blank.** Do not type a fake value. |
| `GOOGLE_CLIENT_SECRET` | **Leave blank.** |
| `GOOGLE_REDIRECT_URI` | **Leave blank.** |
| `OPENAI_API_KEY` | **Leave blank.** Not required. The checklist does not call OpenAI. |
| `OPENAI_MODEL` | **Leave unset.** |
| `ARIZE_API_KEY` | Optional. Blank is fine. The site still runs. |
| `ARIZE_SPACE_ID` | Optional. Blank is fine. |

Blueprint will show the Google, Arize, and OpenAI names because `render.yaml` lists them as dashboard secrets (`sync: false`). **Skip them.** Empty is correct.

If both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are non-empty, the home screen tries to turn on Connect Gmail. Path B wants the opposite: **Connect Gmail isn’t set up yet**, and paste still works.

Never paste real keys into git. The Render dashboard is the only place for secrets, and Path B does not need any.

## 4. Deploy

1. Confirm the branch is **`main`**.
2. Click **Deploy** / **Apply**.
3. Wait until the service says it is live. The first build can take several minutes.
4. If the build fails, read the log. A docs-only pull request will not fix a missing Dockerfile — those files are already on `main`.

## 5. Copy the public URL

1. On the service page, copy the public address. It looks like `https://kill-scam-xxxx.onrender.com`.
2. Open it in a browser. You should see the title **Kill Scam**.
3. You should also see **Connect Gmail isn’t set up yet**. That is expected. It is not a failed deploy.

You do **not** add this URL to Google Cloud for Path B. There is no OAuth redirect.

## 6. Smoke-test with one fixture

Use fixture **`scam-fake-bank`** from [`evals/fixtures.json`](../evals/fixtures.json). It is synthetic. It is not a real bank and not a real person. The checklist should land on **Likely a scam**.

1. On the live site, open **Check something else**.
2. Paste this text (the `message` for `scam-fake-bank`):

```text
From: National Example Bank Security <alerts@nat-example-bank-secure.test>
Subject: Your account will be closed tonight

We detected unusual activity. Confirm your password and card number at http://nat-example-bank-secure.test/login in the next 15 minutes or your account will be frozen.
```

3. Click **Check this message**.
4. Do not open the link in the sample. The app must not open it either.

**Pass looks like this:**

- A verdict of **Likely a scam** (the screen may say **Likely a scam — do not click**).
- Five checks you can see (what it wants, who it claims to be, web addresses, known patterns, verdict).
- Connect Gmail still says it is not set up. Paste still returned a verdict.
- The page still says this is a helper, not a guarantee.

**Not a Path B failure:**

- “Connect Gmail isn’t set up yet” with Google vars left blank.
- No OpenAI key.

**Stop and do not invent keys if:**

- The URL does not load.
- Paste returns no verdict.
- The site asks you to connect Google before it will check the sample.

---

## What this deploy does not do

- It does not connect Gmail. That stays in [SETUP.md](SETUP.md) (Google Cloud, test users, redirect URL).
- It does not replace a home computer host. That option is a separate change; do not add it here.
- It does not require this pull request to be merged. Deploy `main`.

Living specs for this path (`specs/001-paste-check-live/`) are **not** on `main`. They are proposed in [pull request #13](https://github.com/paula-strunz/kill-scam/pull/13). This runbook does not add that specs tree.
