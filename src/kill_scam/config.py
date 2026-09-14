"""Environment helpers. Never print secret values."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_NAME = "kill-scam"
MAX_MESSAGE_CHARS = 20_000
GMAIL_SCAN_LIMIT = 20
GMAIL_LOOKBACK_DAYS = 7
DEFAULT_MODEL = "gpt-4o-mini"
GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DEFAULT_GMAIL_REDIRECT_URI = "http://localhost:8501"


def load_env() -> None:
    """Load a local .env file if present. Safe to call more than once."""
    load_dotenv(override=False)


def env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def openai_api_key() -> str:
    return env("OPENAI_API_KEY")


def openai_model() -> str:
    return env("OPENAI_MODEL", DEFAULT_MODEL)


def arize_api_key() -> str:
    return env("ARIZE_API_KEY")


def arize_space_id() -> str:
    return env("ARIZE_SPACE_ID") or env("ARIZE_SPACE")


def gmail_client_id() -> str:
    return env("GOOGLE_CLIENT_ID")


def gmail_client_secret() -> str:
    return env("GOOGLE_CLIENT_SECRET")


def gmail_redirect_uri() -> str:
    """Public callback URL. Localhost for laptop; set GOOGLE_REDIRECT_URI when hosted."""
    raw = env("GOOGLE_REDIRECT_URI") or env("OAUTH_REDIRECT_URI")
    if raw:
        return raw
    return DEFAULT_GMAIL_REDIRECT_URI


def gmail_is_configured() -> bool:
    return bool(gmail_client_id() and gmail_client_secret())


def gmail_is_hosted() -> bool:
    """Shared hosts must not write one person's Gmail token to a disk file."""
    if env("KILL_SCAM_HOSTED") in {"1", "true", "yes"}:
        return True
    return bool(env("RENDER") or env("FLY_APP_NAME") or env("FLY_MACHINE_ID"))


def arize_is_configured() -> bool:
    return bool(arize_api_key() and arize_space_id())


def token_dir() -> Path:
    path = Path.home() / ".kill-scam"
    path.mkdir(parents=True, exist_ok=True)
    return path


def gmail_token_path() -> Path:
    return token_dir() / "gmail_token.json"
