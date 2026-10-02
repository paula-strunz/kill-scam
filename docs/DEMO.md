# Path B demo: shareable result card

Path B is paste-check only. Open **Check something else**, paste a message, and read the five checks. No Gmail. No OpenAI key. No hosted site.

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
Five checks, then the Result card
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

## See the result card

1. Open **Check something else**.
2. Copy the `message` for fixture `scam-fake-bank` in `evals/fixtures.json` (a made-up bank alert).
3. Paste it into the box. Do not click the link inside it.
4. Press **Check this message**.
5. Under the verdict, the **Result card** shows **Likely a scam — do not click**, one line for each of the five checks, and the words **Screenshot this card to share with family.**

The full pasted message is not on the card. **Copy this summary** uses the same short text.

More on the five checks: [README](../README.md). Product brief: [docs/PRD.md](PRD.md).
