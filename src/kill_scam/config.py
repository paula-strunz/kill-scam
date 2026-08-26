"""Environment helpers. Never print secret values."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_NAME = "kill-scam"
MAX_MESSAGE_CHARS = 20_000
GMAIL_SCAN_LIMIT = 20
DEFAULT_MODEL = "gpt-4o-mini"
GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


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


def gmail_is_configured() -> bool:
    return bool(gmail_client_id() and gmail_client_secret())


def arize_is_configured() -> bool:
    return bool(arize_api_key() and arize_space_id())


def token_dir() -> Path:
    path = Path.home() / ".kill-scam"
    path.mkdir(parents=True, exist_ok=True)
    return path


def gmail_token_path() -> Path:
    return token_dir() / "gmail_token.json"
