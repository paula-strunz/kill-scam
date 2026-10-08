# Kill Scam (project-specific)

This repo is a Python Streamlit app. Shared agent rules stay in `AGENTS.md`.

- Stack: Python 3.11+, Streamlit, optional OpenAI, Arize AX (`arize-otel` + OpenAI OpenInference).
- The product is a **five-step defensive checklist** (ask, identity, links, campaigns, verdict), not a single LLM vibe check.
- When Gmail is configured, Connect Gmail (read-only, `gmail.readonly`) is first and paste is the “Check something else” backup. When Gmail is not configured, paste is the primary door (visible, no expander). The app must never send, delete, or modify mail.
- Never HTTP-GET a pasted destination URL. Domain parsing + official-domain comparison only. Search, if any, is allowlisted.
- Do not log full message bodies. Trace parent + child tool spans with hashes/summaries. Arize is the user's own space.
- Evals live in `evals/fixtures.json` (synthetic only) and `src/kill_scam/evals.py`.
- Fail gracefully when Arize or Google client env vars are missing (show “Connect Gmail isn’t set up yet”). OpenAI is not required for the checklist.
- Defensive use only: no phishing kits, exploit PoCs, payloads, or instructions for sending scam mail.
- Env placeholders belong in `.env.example` only. Never commit secrets.
