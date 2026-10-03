# Kill Scam

[![CI](https://github.com/paula-strunz/kill-scam/actions/workflows/ci.yml/badge.svg)](https://github.com/paula-strunz/kill-scam/actions/workflows/ci.yml)

Product requirements: [docs/PRD.md](docs/PRD.md). Gmail OAuth + hosting: [docs/SETUP.md](docs/SETUP.md). Next work is spec-first: [specs/README.md](specs/README.md).

## TL;DR

**What works today without secrets:** open **Check something else**, paste SMS, WhatsApp, or email text, and watch **five visible checks**. You get **Looks OK**, **Be careful**, or **Likely a scam**.

**Connect Gmail** is still the product door in the [PRD](docs/PRD.md). It needs a Google OAuth client and host env vars ([docs/SETUP.md](docs/SETUP.md)). Until those are set, the app says **Connect Gmail isn’t set up yet** — paste still works.

It **never sends mail**. It **never deletes mail**. It **never writes to your mailbox**. It never opens a suspicious website.

```text
Open Kill Scam
      |
      v
Check something else  (paste SMS / WhatsApp / email)
      |
      v
Five visible steps
      |
      +--> 1. What does it want?  + which hook (authority, fear, …)
      +--> 2. Who does it claim to be?
      +--> 3. Check the web addresses (we do NOT open the page)
      +--> 4. Known scam patterns
      +--> 5. Looks OK / Be careful / Likely a scam
```

Connect Gmail (read-only) is the intended inbox path once OAuth is configured: last 7 days, up to 20 messages, same five checks.

## Who it is for

Family and anyone who is not going to inspect email headers. V0 is **Paula plus invited family testers**. It is not yet an app the whole internet can sign into.

## What you will see

1. **Check something else** — paste SMS, WhatsApp, or email text. This is the demo that works today with no secrets.
2. Five steps run live, then **Looks OK / Be careful / Likely a scam**, plus which persuasion trick fired and **what to do**.
3. A **Connect Gmail** button on the home screen. That is still the product door from the [PRD](docs/PRD.md). After you connect: recent inbox mail, then **Check** on one message.
4. Connect Gmail needs a Google OAuth client and host env vars ([docs/SETUP.md](docs/SETUP.md)). If those are missing, the home screen says **Connect Gmail isn’t set up yet**. Paste still works.

| Result | Meaning |
| --- | --- |
| Looks OK | The five checks did not find scam pressure |
| Be careful | Something is off — pause and verify another way |
| Likely a scam | Do not click, do not pay, do not share codes |

## Share a result with family

After you press **Check this message**, the page becomes one warning: a mark, **Likely scam**, **Not sure**, or **Looks okay**, a short note of the harm, and one button. For a likely scam the button says **Don't reply**. The full pasted message is left off. Try it with `scam-fake-bank`: [docs/DEMO.md](docs/DEMO.md).

## It never sends

```text
Kill Scam  --read only-->  your Gmail inbox
Kill Scam  --x-->  send
Kill Scam  --x-->  delete
Kill Scam  --x-->  change labels / drafts / settings
Kill Scam  --x-->  open the phishing page
```

Google permission requested: `gmail.readonly` only.

## Testing-mode Gmail (Paula + family)

Google will **not** let an unverified app read everyone’s Gmail. Public “everybody on earth” is out of V0.

Paula (or whoever hosts this) turns on a **Google Cloud OAuth consent screen in Testing**:

1. Create a Google Cloud project.
2. Enable the **Gmail API**.
3. OAuth consent screen: **External**, status **Testing**.
4. Add **test users** — Paula’s Gmail and each invited family address. Only those people can connect.
5. Create an OAuth client of type **Web application**.
6. Authorized redirect URIs must match exactly:
   - Laptop: `http://localhost:8501`
   - Hosted: the public URL you set as `GOOGLE_REDIRECT_URI` (for example `https://your-app.onrender.com`)
7. Put the client id and secret in the server environment (see below).

The first time a tester clicks Connect Gmail, Google often shows **“Google hasn’t verified this app.”** That is expected. Testers Paula invited can choose **Advanced** → **Go to Kill Scam (unsafe)** — it is Paula’s app, not a stranger’s. Do not invite the whole internet here.

If `GOOGLE_CLIENT_ID` or `GOOGLE_CLIENT_SECRET` (or the matching redirect) is missing, the home screen says **Connect Gmail isn’t set up yet**. The app does not crash. **Check something else** still works.

## Privacy

- Gmail: read-only, recent inbox only. A sign-in token is kept in your browser session. On a laptop it may also be saved under `~/.kill-scam/` on that computer, not in git. On a hosted server, tokens are not written to a shared disk file.
- We do not log full message bodies. Optional Arize traces use a short hash, not the full mail.
- Do not paste passwords, one-time codes, or bank PINs into **Check something else**.
- This is a helper, not a guarantee.

## Settings (environment)

Copy `.env.example` to `.env` on a laptop, or set the same names on the host.

| Setting | Needed? | What it does |
| --- | --- | --- |
| `GOOGLE_CLIENT_ID` | For Connect Gmail | OAuth client id |
| `GOOGLE_CLIENT_SECRET` | For Connect Gmail | OAuth client secret |
| `GOOGLE_REDIRECT_URI` | For hosted Gmail | Public callback, e.g. `https://your-app.onrender.com`. Laptop default is `http://localhost:8501` |
| `ARIZE_API_KEY` | No | Turns on tracing to **your** Arize space. Missing keys: the app still runs |
| `ARIZE_SPACE_ID` | No | Your Arize space. Project name is always `kill-scam` |
| `OPENAI_API_KEY` | No | Unused for the five checks today |
| `KILL_SCAM_HOSTED` | Set to `1` on a host | Do not save Gmail tokens to disk |

## Run locally

You need Python 3.11 or newer.

```bash
git clone https://github.com/paula-strunz/kill-scam.git
cd kill-scam
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -e .
streamlit run src/kill_scam/app.py
```

On Windows, use `.venv\Scripts\activate`.

Open the browser at `http://localhost:8501`. **Check something else** works with an empty `.env`. Fill `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` only if you want Connect Gmail ([docs/SETUP.md](docs/SETUP.md)).

For tests, install extras: `pip install -e ".[dev]"`.

## How to host it (so it works when the laptop is closed)

This is a long-running website, not a `pip` install for family.

```bash
docker build -t kill-scam .
docker run --rm -p 8080:8080 --env-file .env -e KILL_SCAM_HOSTED=1 -e PORT=8080 kill-scam
```

There is a `Dockerfile`, plus `render.yaml` (Render) and `fly.toml` (Fly.io). On the host, set `GOOGLE_REDIRECT_URI` to the public https URL and add that **same** URL in the Google Cloud client.

Paste-check only, no Gmail OAuth: [docs/deploy-path-b.md](docs/deploy-path-b.md).

## The five checks

| Step | In everyday words |
| --- | --- |
| 1. What does it want? | Click, pay, give a code, install an app, stay silent — and which hook: authority, fear / loss, fake confirmation, reward, urgency, liking, reciprocity, curiosity |
| 2. Who does it claim to be? | We read the **address**, not the pretty name |
| 3. Check the web addresses | Lookalikes and short links only. We do **not** open the page |
| 4. Known scam patterns | Tax refund, parcel fees, and similar. If live guidance sites are down, we continue and say so |
| 5. Verdict | Looks OK / Be careful / Likely a scam, with what to do. In France: SMS **33700**, email **signal-spam.fr** |

## Tests

```bash
pytest
python -m kill_scam.evals
```

Synthetic examples live in `evals/fixtures.json` (no real inboxes).

## Safety

This project is **defensive only**. It helps people pause before they click. It does not include phishing kits, attack how-tos, or tools for sending scam mail.

If you are unsure after a check, contact the company or person using a phone number or address you already trust — not a number from the suspicious message.
