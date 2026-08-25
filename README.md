# Kill Scam

## TL;DR

Kill Scam helps you check a suspicious **email, text, or WhatsApp message before you click**. It walks through **five checks you can see**, then gives a plain-language result: **Looks OK**, **Be careful**, or **Likely a scam**.

The product is the **process**, not a magic score.

```text
You paste a message
        |
        v
1. What does it want?     (click, pay, code, app, stay silent)
2. Who does it claim?     (name vs real address; official site)
3. Check the addresses    (lookalikes — we do NOT open the page)
4. Known scam patterns    (tax, parcel, EDF, CAF, …)
5. Verdict + what to do   (including 33700 / signal-spam.fr)
```

## What it is

- A simple page you run on your own computer
- A paste box (this is the main way to use it)
- A visible five-step checklist
- Optional Gmail: **read-only** scan of recent mail if you set that up
- Optional tracing to **your** Arize account

## What it is not

- It never sends email
- It never writes to your inbox
- It never opens the suspicious website (that would be walking into the trap)
- It does not replace calling your bank with a number **you already have**
- It will not catch every scam

## The five checks

| Step | In everyday words |
| --- | --- |
| 1. What does it want? | Click a link? Pay? Give a code? Install an app? Stay silent? |
| 2. Who does it claim to be? | We read the **address**, not the pretty name. We look up the official site for impôts, La Poste, Chronopost, EDF, CAF, banks, Microsoft, Apple, … |
| 3. Check the web addresses | We only look at the **website name** (lookalikes, extra words, coded letters, short links). We do **not** open the page. |
| 4. Known scam patterns | We compare with common campaigns (fake tax refund, parcel fees, energy bill, bank advisor, CPF, CAF). If live guidance sites cannot be reached, we continue with the built-in list and say so. |
| 5. Verdict | OK / be careful / likely a scam, with reasons tied to which steps fired. In France: SMS **33700**, email **signal-spam.fr**. |

We do not invent facts that were not in the message or in those checks.

## How to run (first time)

You need a computer and Python 3.11 or newer. An OpenAI key is **not** required for the five checks.

1. Open a terminal in this folder.
2. Optional: `cp .env.example .env` and fill only what you use.
3. Install and start:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
streamlit run src/kill_scam/app.py
```

4. A browser window should open. Paste a message. Select **Check this message**. Watch the five steps.

On Windows, use `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

## What you will see

| Result | Meaning |
| --- | --- |
| Looks OK | The five checks did not find scam pressure |
| Be careful | Something is off — pause and verify another way |
| Likely a scam | Do not click, do not pay, do not share codes |

Each result lists **which checks** led there.

## Privacy

```text
Paste box
  five local checks on your computer
  we never open the suspicious website
  not printed in full in the app log

Optional live guidance search
  only known search hosts
  never the link from the message

Optional Arize tracing
  parent check + each step, with a hash not the full paste
  stored in YOUR Arize space

Optional Gmail
  read-only, last 20 inbox items
  never send, never change mail
```

- **Do not paste secrets** you want nobody to see (passwords, one-time codes, bank PINs).
- App logs record length, a short hash, and the verdict — not the full message.
- If you set `ARIZE_API_KEY` and `ARIZE_SPACE_ID`, traces go to **your** Arize project named `kill-scam`. Leave those blank to skip tracing.
- Gmail: read-only. A sign-in token is saved under `.kill-scam/`, not in git.

## Settings (`.env`)

| Setting | Needed? | What it does |
| --- | --- | --- |
| `OPENAI_API_KEY` | No | Unused for the five checks today |
| `OPENAI_MODEL` | No | Defaults to `gpt-4o-mini` if you add a key later |
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

If anything fails, use the paste box.

## Optional Arize tracing

Set `ARIZE_API_KEY` and `ARIZE_SPACE_ID`. Each paste becomes a parent check with five child steps (tool name + summaries + message hash). Missing keys: the app still runs.

## Tests and evals

Synthetic examples live in `evals/fixtures.json` (made-up scams and ordinary messages, **no real inboxes**). Some examples **need the process** (a lookalike domain a quick glance can miss, and a legitimate-looking school/bank message).

```bash
pytest
python -m kill_scam.evals
```

The eval script scores **missed scams** vs **false alarms** using the local checklist (no live web search). Unit tests cover URL parsing and lookalike domains **without network**.

## Safety

This project is **defensive only**. It helps people pause before they click. It does not include phishing kits, attack how-tos, or tools for sending scam mail.

If you are unsure after a check, contact the company or person using a phone number or address you already trust — not a number from the suspicious message.

In France you can also:

- Forward a scam SMS to **33700** (free)
- Report a scam email at **signal-spam.fr**
