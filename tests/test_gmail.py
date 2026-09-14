from __future__ import annotations

from pathlib import Path

import pytest

from kill_scam.config import GMAIL_READONLY_SCOPE, gmail_is_configured, gmail_redirect_uri
from kill_scam.gmail import (
    FORBIDDEN_SCOPE_FRAGMENTS,
    NOT_CONFIGURED_HEADLINE,
    SCOPES,
    GmailError,
    GmailMessage,
    _readonly_call,
    assert_readonly_scopes,
    authorization_url,
    extract_plain_text,
    finish_connect,
    get_message,
    list_recent_messages,
    message_from_api,
    setup_status,
)

GMAIL_SOURCE = Path(__file__).resolve().parents[1] / "src" / "kill_scam" / "gmail.py"


def test_gmail_scope_is_readonly_only() -> None:
    assert SCOPES == (GMAIL_READONLY_SCOPE,)
    joined = " ".join(SCOPES).lower()
    for fragment in FORBIDDEN_SCOPE_FRAGMENTS:
        assert fragment not in joined
    assert_readonly_scopes()


def test_gmail_refuses_send_scopes() -> None:
    with pytest.raises(GmailError, match="refuses"):
        assert_readonly_scopes(("https://www.googleapis.com/auth/gmail.send",))


def test_gmail_helper_source_cannot_send() -> None:
    source = GMAIL_SOURCE.read_text(encoding="utf-8")
    for needle in (
        "messages().send",
        "messages().delete",
        "messages().modify",
        "messages().insert",
        "users().drafts",
        ".send(",
    ):
        assert needle not in source
    assert "GMAIL_READONLY_SCOPE" in source
    assert "Never send" in source or "never send" in source.lower()


def test_gmail_hidden_without_client_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    assert gmail_is_configured() is False


def test_oauth_missing_does_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    status = setup_status()
    assert status.configured is False
    assert "isn’t set up yet" in status.headline or "isn't set up yet" in status.headline
    assert status.headline == NOT_CONFIGURED_HEADLINE
    with pytest.raises(GmailError, match="set up yet"):
        authorization_url()
    with pytest.raises(GmailError, match="set up yet"):
        finish_connect("fake-code", "fake-state", "fake-state")


def test_gmail_list_requires_connection(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr("kill_scam.gmail.gmail_token_path", lambda: tmp_path / "missing.json")
    monkeypatch.setattr("kill_scam.gmail.load_persisted_token", lambda: None)
    with pytest.raises(GmailError, match="not connected"):
        list_recent_messages()
    with pytest.raises(GmailError, match="not connected"):
        get_message("abc")


def test_finish_connect_rejects_unknown_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")
    with pytest.raises(GmailError, match="verified"):
        finish_connect("abc", "unknown-state", "other-state")


def test_redirect_uri_defaults_to_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_REDIRECT_URI", raising=False)
    monkeypatch.delenv("OAUTH_REDIRECT_URI", raising=False)
    assert gmail_redirect_uri() == "http://localhost:8501"


def test_redirect_uri_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://kill-scam.example/oauth")
    assert gmail_redirect_uri() == "https://kill-scam.example/oauth"


def test_gmail_message_text_for_checker() -> None:
    item = GmailMessage(
        id="abc",
        sender="Maple Street School Office",
        subject="Friday picnic reminder",
        date="2026-08-25 09:00",
        snippet="Picnic is still at 12:00.",
        body="Picnic is still at 12:00. Bring a blanket.",
    )
    text = item.as_check_text()
    assert "Maple Street School Office" in text
    assert "Friday picnic reminder" in text
    assert "Bring a blanket." in text


def test_message_from_api_metadata() -> None:
    raw = {
        "id": "m1",
        "snippet": "Please confirm your password at a lookalike site.",
        "payload": {
            "headers": [
                {"name": "From", "value": "DGFiP <service@impots-gouv.fr>"},
                {"name": "Subject", "value": "Remboursement"},
                {"name": "Date", "value": "Sat, 29 Aug 2026 10:00:00 +0000"},
            ]
        },
    }
    item = message_from_api(raw)
    assert item.id == "m1"
    assert "impots-gouv.fr" in item.sender
    assert item.subject == "Remboursement"
    assert item.body == ""
    assert "password" in item.snippet


def test_extract_plain_text_prefers_text_plain() -> None:
    import base64

    plain = base64.urlsafe_b64encode(b"Hello family. No payment.").decode("ascii")
    html = base64.urlsafe_b64encode(b"<a href='http://evil.test'>click</a>").decode("ascii")
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": plain}},
            {"mimeType": "text/html", "body": {"data": html}},
        ],
    }
    assert extract_plain_text(payload) == "Hello family. No payment."


def test_readonly_call_refuses_send_method() -> None:
    class FakeSend:
        __name__ = "send"
        methodId = "gmail.users.messages.send"

        def __call__(self, **_kwargs):
            raise AssertionError("send must not run")

    with pytest.raises(GmailError, match="refuses"):
        _readonly_call(FakeSend(), userId="me")


def test_extract_plain_text_strips_html_when_needed() -> None:
    import base64

    html = base64.urlsafe_b64encode(b"<p>Invoice to open</p>").decode("ascii")
    payload = {"mimeType": "text/html", "body": {"data": html}}
    assert "Invoice to open" in extract_plain_text(payload)
    assert "<p>" not in extract_plain_text(payload)
