# Path B demo: paste warning

Path B is paste-check only. Open **Check something else**, paste a message, and read one warning screen. No Gmail. No OpenAI key. No hosted site.

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
One centered warning
mark, Likely scam, harm, Don't reply
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
5. The page becomes one light, centered warning. A mark, a large **Likely scam**, one short paragraph, at most two short reasons, and one button: **Don't reply**. **Copy summary** and **This is wrong** are quiet text under that button.

```text
              ( ! )

          Likely scam

  This message may be trying to take
  money, a code, or a password.

       Asks for a password
         Lookalike link

         [ Don't reply ]

          Copy summary
          This is wrong
```

The full pasted message is not on that screen. **Don't reply** leaves the warning. It does not send or delete mail. Spec: [specs/002-shareable-result-card.md](../specs/002-shareable-result-card.md).

More on the five checks: [README](../README.md). Product brief: [docs/PRD.md](PRD.md).
