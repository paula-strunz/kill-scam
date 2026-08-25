# Kill Scam

## TL;DR

Kill Scam helps you check a suspicious **email, text, or WhatsApp message before you click**. Paste the text, get a plain-language verdict: **Looks OK**, **Be careful**, or **Likely a scam**, plus a short why.

It is a helper for people at home. It is **not** a guarantee, a spam filter for your whole inbox, or a tool for sending mail.

```text
You paste a message
        |
        v
Kill Scam reads the words
        |
        v
You get: OK / be careful / likely a scam
        + a short why in everyday language
```

## What it is

- A simple web page you run on your own computer
- A paste box (this is the main way to use it)
- Optional Gmail: **read-only** scan of recent mail if you set that up
- Optional tracing to **your** Arize account so you can see how checks went

## What it is not

- It never sends email
- It never writes to your inbox, never deletes mail, never reports mail for you
- It does not click links for you
- It does not replace calling your bank with a number **you already have**
- It will not catch every scam

## How to run (first time)

You need a computer, Python 3.11 or newer, and an OpenAI key.

1. Open a terminal in this folder.
2. Create a private settings file:

```bash
cp .env.example .env
```

3. Open `.env` and paste your OpenAI key after `OPENAI_API_KEY=`.
   Get a key from the OpenAI website. Do not share it. Do not commit `.env`.

4. Install and start:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
streamlit run src/kill_scam/app.py
```

5. A browser window should open. Paste a message. Select **Check this message**.

On Windows, use `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

If you skip the OpenAI key, the page still opens. Checking a message will show a clear “needs a key” note instead of crashing.

## What you will see

| Result | Meaning |
| --- | --- |
| Looks OK | No scam pressure jumped out |
| Be careful | Something feels off — pause and verify another way |
| Likely a scam | Do not click, do not pay, do not share codes |

## Privacy

```text
Paste box (default)
  message stays on your computer
  then goes to OpenAI to judge the words
  not printed in full in the app log

Optional Arize tracing
  same check can be stored in YOUR Arize space
  so you can review quality later

Optional Gmail
  read-only, last 20 inbox items
  never send, never change mail
```

- **Paste stays local to this app** unless you turn on Arize. The checker still sends the text to OpenAI so it can judge it.
- **Do not paste secrets you want nobody to see** (passwords, one-time codes, bank PINs). You can hide those lines and still check the rest.
- App logs record only things like “check ran, length=…, verdict=…”. They do **not** print the full message.
- If you set `ARIZE_API_KEY` and `ARIZE_SPACE_ID`, traces go to **your** Arize project named `kill-scam`. That can include prompt text. Leave those blank to skip tracing.
- Gmail: this app only asks for permission to **read**. A sign-in token is saved on your computer under `.kill-scam/`, not in git.

## Settings (`.env`)

Copy `.env.example` to `.env`. Fill in only what you use.

| Setting | Needed? | What it does |
| --- | --- | --- |
| `OPENAI_API_KEY` | Yes, to judge messages | Lets the checker run |
| `OPENAI_MODEL` | No | Defaults to `gpt-4o-mini` |
| `ARIZE_API_KEY` | No | Turns on tracing to your Arize space |
| `ARIZE_SPACE_ID` | No | Your Arize space. Project name is always `kill-scam` |
| `GOOGLE_CLIENT_ID` | No | Turns on Connect Gmail |
| `GOOGLE_CLIENT_SECRET` | No | Turns on Connect Gmail |

If Google keys are missing, **Connect Gmail is hidden**. Paste still works.

## Optional Gmail (read-only)

1. In Google Cloud, create a desktop OAuth client.
2. Put the client id and secret in `.env`.
3. Restart the app. **Connect Gmail (read-only)** appears.
4. Sign in, then scan the last 20 inbox messages and check one.

If anything fails, use the paste box. That path does not need Gmail.

## Optional Arize tracing

Set `ARIZE_API_KEY` and `ARIZE_SPACE_ID` from Arize space settings. Restart the app. Each check can show up in project **kill-scam**. If those values are missing, the app still runs.

## Tests and evals

Synthetic examples live in `evals/fixtures.json` (made-up scams and ordinary messages, no real inboxes). They are shaped so they can later become an Arize dataset.

```bash
pytest
python -m kill_scam.evals
```

The eval script scores **missed scams** (a scam marked OK) vs **false alarms** (ordinary mail marked risky). Without `OPENAI_API_KEY` it only loads the fixtures and tells you live scoring was skipped.

## Safety

This project is **defensive only**. It helps people pause before they click. It does not include phishing kits, attack how-tos, or tools for sending scam mail.

If you are unsure after a check, contact the company or person using a phone number or address you already trust — not a number from the suspicious message.
