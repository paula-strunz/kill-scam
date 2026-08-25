from __future__ import annotations

import pytest

from kill_scam.config import GMAIL_READONLY_SCOPE, gmail_is_configured
from kill_scam.gmail import (
    FORBIDDEN_SCOPE_FRAGMENTS,
    SCOPES,
    GmailError,
    GmailMessage,
    assert_readonly_scopes,
    list_recent_messages,
)


def test_gmail_scope_is_readonly_only() -> None:
    assert SCOPES == (GMAIL_READONLY_SCOPE,)
    joined = " ".join(SCOPES).lower()
    for fragment in FORBIDDEN_SCOPE_FRAGMENTS:
        assert fragment not in joined
    assert_readonly_scopes()


def test_gmail_refuses_send_scopes() -> None:
    with pytest.raises(GmailError, match="refuses"):
        assert_readonly_scopes(("https://www.googleapis.com/auth/gmail.send",))


def test_gmail_hidden_without_client_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    assert gmail_is_configured() is False


def test_gmail_list_requires_connection(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr("kill_scam.gmail.gmail_token_path", lambda: tmp_path / "missing.json")
    with pytest.raises(GmailError, match="not connected"):
        list_recent_messages()


def test_gmail_message_text_for_checker() -> None:
    item = GmailMessage(
        id="abc",
        sender="Maple Street School Office",
        subject="Friday picnic reminder",
        date="2026-08-25 09:00",
        snippet="Picnic is still at 12:00.",
    )
    text = item.as_check_text()
    assert "Maple Street School Office" in text
    assert "Friday picnic reminder" in text
    assert "Picnic is still at 12:00." in text
