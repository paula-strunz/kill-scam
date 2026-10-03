# Path B demo: calm paste result

Path B is paste-check only. Open **Check something else**, paste a message, and read the verdict. No Gmail. No OpenAI key. No hosted site.

```text
localhost:8501
      |
      v
Check something else
      |
      v
Paste fixture scam-fake-bank
      |
      v
Likely scam
one sentence, up to three chips, one next step
```

## Run locally

From the repo root, with Python 3.11 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
streamlit run src/kill_scam/app.py
```

Open `http://localhost:8501`. An empty `.env` is enough. The app never sends mail and never deletes mail.

## What you should see

1. Open **Check something else**.
2. Copy the `message` for fixture `scam-fake-bank` in `evals/fixtures.json` (a made-up bank alert).
3. Paste it into the box. Do not click the link inside it.
4. Press **Check this message**.
5. The screen leads with a large **Likely scam**, then one sentence of why. Under that: at most three short chips, then one next step. **Copy summary** is a quiet text button, not a boxed report.

```text
Likely scam

Several checks say this is a scam.

[ Asks for a password ]  [ Lookalike link ]  [ Fake sender ]

Do not click, do not pay, and do not share codes from this message.

Copy summary
```

The full pasted message is not in that result. On a phone, the verdict is the first thing you read. Spec: [specs/002-shareable-result-card.md](../specs/002-shareable-result-card.md).

More on the five checks: [README](../README.md). Product brief: [docs/PRD.md](PRD.md).
