# Kill Scam (project-specific)

This repo is a Python Streamlit app. Shared agent rules stay in `AGENTS.md`.

- Stack: Python 3.11+, Streamlit, OpenAI, Arize AX (`arize-otel` + OpenAI OpenInference instrumentor).
- Primary path is paste-in. Gmail is optional, read-only (`gmail.readonly`), and must never send or modify mail.
- Do not log full message bodies to the console. Arize tracing, when enabled, goes to the user's own space and must be documented in the README.
- Classifier evals live in `evals/fixtures.json` (synthetic only, no real inboxes) and `src/kill_scam/evals.py`.
- Fail gracefully when `OPENAI_API_KEY`, `ARIZE_API_KEY` / `ARIZE_SPACE_ID`, or Google client env vars are missing.
- Defensive use only: no phishing kits, exploit PoCs, payloads, or instructions for sending scam mail.
- Env placeholders belong in `.env.example` only. Never commit secrets.
