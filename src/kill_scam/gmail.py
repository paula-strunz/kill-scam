"""Optional Gmail read-only scaffold. Never send, never write to the inbox."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import timezone
from typing import Any

from kill_scam.config import (
    GMAIL_READONLY_SCOPE,
    GMAIL_SCAN_LIMIT,
    gmail_client_id,
    gmail_client_secret,
    gmail_is_configured,
    gmail_token_path,
)

logger = logging.getLogger("kill_scam")

# Hard rule: this app may only request read-only Gmail access.
SCOPES = (GMAIL_READONLY_SCOPE,)
FORBIDDEN_SCOPE_FRAGMENTS = (
    "gmail.send",
    "gmail.compose",
    "gmail.modify",
    "gmail.insert",
    "gmail.settings",
)


class GmailError(RuntimeError):
    """User-facing Gmail failure."""


@dataclass(frozen=True)
class GmailMessage:
    id: str
    sender: str
    subject: str
    date: str
    snippet: str

    def as_check_text(self) -> str:
        return (
            f"From: {self.sender}\n"
            f"Subject: {self.subject}\n"
            f"Date: {self.date}\n\n"
            f"{self.snippet}"
        )


def assert_readonly_scopes(scopes: tuple[str, ...] = SCOPES) -> None:
    joined = " ".join(scopes).lower()
    for fragment in FORBIDDEN_SCOPE_FRAGMENTS:
        if fragment in joined:
            raise GmailError("Kill Scam refuses any Gmail permission that can send or change mail.")
    if GMAIL_READONLY_SCOPE not in scopes:
        raise GmailError("Kill Scam only connects to Gmail with read-only permission.")


def is_configured() -> bool:
    return gmail_is_configured()


def is_connected() -> bool:
    return gmail_token_path().is_file()


def connect() -> str:
    """Start a local read-only OAuth flow. Returns a short status for the UI."""
    if not is_configured():
        raise GmailError(
            "Gmail is not set up. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env, "
            "or keep using the paste box."
        )
    assert_readonly_scopes()
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise GmailError("Gmail libraries are not installed. Run: pip install -e .") from exc

    flow = InstalledAppFlow.from_client_config(_client_config(), list(SCOPES))
    try:
        creds = flow.run_local_server(port=0, prompt="consent")
    except Exception:
        logger.warning("Gmail OAuth did not finish.")
        raise GmailError(
            "Could not finish Google sign-in. Try again on this computer in a browser, "
            "or use the paste box instead."
        ) from None

    token_path = gmail_token_path()
    token_path.write_text(creds.to_json(), encoding="utf-8")
    logger.info("Gmail connected with read-only access. Token stored locally.")
    return "Gmail is connected as read-only. This app never sends mail."


def disconnect() -> None:
    path = gmail_token_path()
    if path.is_file():
        path.unlink()
    logger.info("Gmail local token removed.")


def list_recent_messages(limit: int = GMAIL_SCAN_LIMIT) -> list[GmailMessage]:
    """Fetch recent message headers and snippets. Never sends."""
    assert_readonly_scopes()
    service = _service()
    cap = max(1, min(limit, GMAIL_SCAN_LIMIT))
    try:
        listed = (
            service.users()
            .messages()
            .list(userId="me", maxResults=cap, labelIds=["INBOX"])
            .execute()
        )
    except Exception:
        logger.warning("Gmail list failed.")
        raise GmailError("Could not read recent Gmail. Try Connect Gmail again, or paste the text.") from None

    messages: list[GmailMessage] = []
    for item in listed.get("messages", []):
        msg_id = item.get("id")
        if not msg_id:
            continue
        try:
            raw = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg_id,
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
        except Exception:
            logger.warning("Gmail message fetch failed for one item.")
            continue
        messages.append(_to_message(raw))
    return messages


def _client_config() -> dict[str, Any]:
    return {
        "installed": {
            "client_id": gmail_client_id(),
            "client_secret": gmail_client_secret(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def _service():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise GmailError("Gmail libraries are not installed. Run: pip install -e .") from exc

    path = gmail_token_path()
    if not path.is_file():
        raise GmailError("Gmail is not connected yet.")

    info = json.loads(path.read_text(encoding="utf-8"))
    creds = Credentials.from_authorized_user_info(info, list(SCOPES))
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            path.write_text(creds.to_json(), encoding="utf-8")
        except Exception:
            disconnect()
            raise GmailError("Gmail sign-in expired. Connect Gmail again.") from None
    if not creds.valid:
        raise GmailError("Gmail is not connected yet.")

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _to_message(raw: dict[str, Any]) -> GmailMessage:
    headers = {h.get("name", "").lower(): h.get("value", "") for h in raw.get("payload", {}).get("headers", [])}
    date_raw = headers.get("date", "")
    date = _short_date(date_raw)
    snippet = (raw.get("snippet") or "").strip()
    if len(snippet) > 280:
        snippet = snippet[:277] + "..."
    return GmailMessage(
        id=str(raw.get("id") or ""),
        sender=headers.get("from", "(unknown sender)"),
        subject=headers.get("subject", "(no subject)"),
        date=date,
        snippet=snippet,
    )


def _short_date(value: str) -> str:
    if not value:
        return ""
    try:
        from email.utils import parsedate_to_datetime

        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value[:32]
