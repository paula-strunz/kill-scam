"""Gmail helper. The only mailbox change allowed is adding the Likely scam label.

Never send, never delete, never trash, never archive, never move, never draft.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC
from typing import Any

from kill_scam.config import (
    GMAIL_LOOKBACK_DAYS,
    GMAIL_MODIFY_SCOPE,
    GMAIL_SCAN_LIMIT,
    gmail_client_id,
    gmail_client_secret,
    gmail_is_configured,
    gmail_is_hosted,
    gmail_redirect_uri,
    gmail_token_path,
    token_dir,
)

logger = logging.getLogger("kill_scam")

# Hard rule: request modify only so we can add one label. Every other write is refused in code.
SCOPES = (GMAIL_MODIFY_SCOPE,)
LIKELY_SCAM_LABEL_NAME = "Likely scam"
# Real Gmail user-label ids look like Label_42. System ids (INBOX, TRASH, SPAM) never match.
_USER_LABEL_ID = re.compile(r"^Label_[0-9]+$")
FORBIDDEN_SCOPE_FRAGMENTS = (
    "gmail.send",
    "gmail.compose",
    "gmail.insert",
    "gmail.settings",
    "mail.google.com",
)
# Exact Gmail methods this app may run. Anything else raises GmailError.
ALLOWED_GMAIL_CALLS = frozenset(
    {
        ("messages", "list"),
        ("messages", "get"),
        ("messages", "modify"),
        ("labels", "list"),
        ("labels", "create"),
    }
)
_MODIFY_BODY_KEYS = frozenset({"addLabelIds", "removeLabelIds"})
_LABEL_CREATE_KEYS = frozenset(
    {"name", "color", "messageListVisibility", "labelListVisibility"}
)
_REFUSE_CALL = "Kill Scam refuses any Gmail call except adding the Likely scam label."
_REFUSE_SCOPE = "Kill Scam refuses any Gmail permission that can send or change mail."
NOT_CONFIGURED_HEADLINE = "Connect Gmail isn’t set up yet."
NOT_CONFIGURED_DETAIL = (
    "This copy is for Paula and invited family testers. "
    "Google will not let an unverified app read everyone’s inbox. "
    "Add GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and a matching redirect URI "
    "to turn Connect Gmail on. Until then, use Check something else below."
)
_HTML_TAG = re.compile(r"<[^>]+>")
_OAUTH_STATE_TTL_SECONDS = 15 * 60


class GmailError(RuntimeError):
    """User-facing Gmail failure."""


@dataclass(frozen=True)
class GmailSetupStatus:
    configured: bool
    headline: str
    detail: str
    redirect_uri: str


@dataclass(frozen=True)
class GmailMessage:
    id: str
    sender: str
    subject: str
    date: str
    snippet: str
    body: str = ""

    def as_check_text(self) -> str:
        content = (self.body or self.snippet).strip()
        return (
            f"From: {self.sender}\n"
            f"Subject: {self.subject}\n"
            f"Date: {self.date}\n\n"
            f"{content}"
        )


def assert_allowed_scopes(scopes: tuple[str, ...] = SCOPES) -> None:
    """Require gmail.modify, and refuse send, compose, insert, settings, or full mail access."""
    joined = " ".join(scopes).lower()
    for fragment in FORBIDDEN_SCOPE_FRAGMENTS:
        if fragment in joined:
            raise GmailError(_REFUSE_SCOPE)
    if GMAIL_MODIFY_SCOPE not in scopes:
        raise GmailError(
            "Kill Scam only connects to Gmail with permission to add the Likely scam label."
        )


def is_configured() -> bool:
    return gmail_is_configured()


def setup_status() -> GmailSetupStatus:
    """Safe to call with missing env. Never raises."""
    redirect = gmail_redirect_uri()
    if not is_configured():
        return GmailSetupStatus(
            configured=False,
            headline=NOT_CONFIGURED_HEADLINE,
            detail=NOT_CONFIGURED_DETAIL,
            redirect_uri=redirect,
        )
    return GmailSetupStatus(
        configured=True,
        headline="Connect Gmail",
        detail=(
            "This reads recent inbox mail. It only adds a Likely scam label. "
            "It never sends or deletes mail."
        ),
        redirect_uri=redirect,
    )


def is_connected(token_info: dict[str, Any] | None = None) -> bool:
    if token_info:
        return True
    return (not gmail_is_hosted()) and gmail_token_path().is_file()


def authorization_url(redirect_uri: str | None = None) -> tuple[str, str]:
    """Return (Google sign-in URL, CSRF state). Does not talk to the mailbox."""
    if not is_configured():
        raise GmailError(NOT_CONFIGURED_HEADLINE)
    assert_allowed_scopes()
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as exc:
        raise GmailError("Gmail libraries are not installed. Run: pip install -e .") from exc

    redirect = redirect_uri or gmail_redirect_uri()
    _allow_localhost_http(redirect)
    flow = Flow.from_client_config(_client_config(redirect), list(SCOPES), redirect_uri=redirect)
    url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="false",
    )
    _remember_oauth_state(state)
    logger.info("Gmail OAuth URL created (modify, label only).")
    return url, state


def finish_connect(
    code: str,
    state: str,
    expected_state: str = "",
    redirect_uri: str | None = None,
) -> dict[str, Any]:
    """Exchange the one-time code for a token. Requests gmail.modify and nothing broader."""
    if not is_configured():
        raise GmailError(NOT_CONFIGURED_HEADLINE)
    if not (code or "").strip():
        raise GmailError("Google sign-in did not finish. Try Connect Gmail again.")
    if not _state_is_known(state, expected_state):
        raise GmailError("Sign-in could not be verified. Try Connect Gmail again.")
    assert_allowed_scopes()
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as exc:
        raise GmailError("Gmail libraries are not installed. Run: pip install -e .") from exc

    redirect = redirect_uri or gmail_redirect_uri()
    _allow_localhost_http(redirect)
    flow = Flow.from_client_config(_client_config(redirect), list(SCOPES), redirect_uri=redirect)
    try:
        flow.fetch_token(code=code.strip())
    except Exception:
        logger.warning("Gmail OAuth token exchange failed.")
        raise GmailError(
            "Could not finish Google sign-in. Try Connect Gmail again, "
            "or use Check something else."
        ) from None

    creds = flow.credentials
    granted = tuple(creds.scopes or SCOPES)
    assert_allowed_scopes(granted if granted else SCOPES)
    info = json.loads(creds.to_json())
    if persist_token_to_disk():
        gmail_token_path().write_text(json.dumps(info), encoding="utf-8")
        logger.info("Gmail connected with label-only access. Token stored locally.")
    else:
        logger.info("Gmail connected with label-only access. Token kept in this browser session.")
    _forget_oauth_state(state)
    return info


def load_persisted_token() -> dict[str, Any] | None:
    if gmail_is_hosted():
        return None
    path = gmail_token_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def persist_token_to_disk() -> bool:
    return not gmail_is_hosted()


def disconnect(token_info: dict[str, Any] | None = None) -> None:
    del token_info  # session token is cleared by the UI
    path = gmail_token_path()
    if path.is_file():
        path.unlink()
    logger.info("Gmail local token removed.")


def list_recent_messages(
    token_info: dict[str, Any] | None = None,
    limit: int = GMAIL_SCAN_LIMIT,
) -> list[GmailMessage]:
    """Fetch recent inbox headers and snippets. Never sends."""
    assert_allowed_scopes()
    service = _service(token_info)
    cap = max(1, min(limit, GMAIL_SCAN_LIMIT))
    query = f"newer_than:{GMAIL_LOOKBACK_DAYS}d"
    try:
        listed = gmail_call(
            service,
            "messages",
            "list",
            userId="me",
            maxResults=cap,
            labelIds=["INBOX"],
            q=query,
        )
    except GmailError:
        raise
    except Exception:
        logger.warning("Gmail list failed.")
        raise GmailError(
            "Could not read recent Gmail. Try Connect Gmail again, or use Check something else."
        ) from None

    messages: list[GmailMessage] = []
    for item in listed.get("messages", []):
        msg_id = item.get("id")
        if not msg_id:
            continue
        try:
            raw = gmail_call(
                service,
                "messages",
                "get",
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
        except Exception:
            logger.warning("Gmail message fetch failed for one item.")
            continue
        messages.append(message_from_api(raw))
    return messages


def get_message(message_id: str, token_info: dict[str, Any] | None = None) -> GmailMessage:
    """Read one message for the checklist. Never sends, never deletes."""
    if not (message_id or "").strip():
        raise GmailError("That message could not be opened.")
    assert_allowed_scopes()
    service = _service(token_info)
    try:
        raw = gmail_call(
            service,
            "messages",
            "get",
            userId="me",
            id=message_id.strip(),
            format="full",
        )
    except GmailError:
        raise
    except Exception:
        logger.warning("Gmail message get failed.")
        raise GmailError(
            "Could not open that message. Try again, or use Check something else."
        ) from None
    return message_from_api(raw, include_body=True)


def message_from_api(raw: dict[str, Any], *, include_body: bool = False) -> GmailMessage:
    payload = raw.get("payload") or {}
    headers = {
        str(h.get("name", "")).lower(): str(h.get("value", ""))
        for h in payload.get("headers", [])
        if isinstance(h, dict)
    }
    snippet = (raw.get("snippet") or "").strip()
    if len(snippet) > 280:
        snippet = snippet[:277] + "..."
    body = extract_plain_text(payload) if include_body else ""
    if len(body) > 8_000:
        body = body[:8_000]
    return GmailMessage(
        id=str(raw.get("id") or ""),
        sender=headers.get("from", "(unknown sender)"),
        subject=headers.get("subject", "(no subject)"),
        date=_short_date(headers.get("date", "")),
        snippet=snippet,
        body=body,
    )


def extract_plain_text(payload: dict[str, Any]) -> str:
    """Pull text/plain (or stripped HTML) from a Gmail payload. No network."""
    plain_parts: list[str] = []
    html_parts: list[str] = []
    _collect_text_parts(payload, plain_parts, html_parts)
    text = "\n".join(part.strip() for part in plain_parts if part.strip())
    if text:
        return text
    html = "\n".join(part.strip() for part in html_parts if part.strip())
    if not html:
        return ""
    stripped = _HTML_TAG.sub(" ", html)
    return re.sub(r"\s+", " ", stripped).strip()


def _collect_text_parts(payload: dict[str, Any], plain: list[str], html: list[str]) -> None:
    mime = str(payload.get("mimeType") or "")
    data = (payload.get("body") or {}).get("data")
    if data and mime.startswith("text/plain"):
        decoded = _decode_b64(data)
        if decoded:
            plain.append(decoded)
    elif data and mime.startswith("text/html"):
        decoded = _decode_b64(data)
        if decoded:
            html.append(decoded)
    for part in payload.get("parts") or []:
        if isinstance(part, dict):
            _collect_text_parts(part, plain, html)


def _decode_b64(data: str) -> str:
    raw = (data or "").encode("ascii", errors="ignore")
    padded = raw + b"=" * (-len(raw) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
    except Exception:
        return ""


def gmail_call(
    service: Any,
    resource: str,
    method: str,
    *,
    label_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Run one allowlisted Gmail call.

    ``messages.modify`` is accepted only when ``label_id`` is our Likely scam
    label and the body adds that id alone, with an empty remove list.
    The underlying method is not called when the guard refuses.
    """
    key = (resource, method)
    if key not in ALLOWED_GMAIL_CALLS:
        raise GmailError(_REFUSE_CALL)
    if key == ("messages", "modify"):
        _assert_label_only_modify(kwargs.get("body"), label_id)
        _reject_unknown_params(kwargs, {"userId", "id", "body"})
    elif key == ("labels", "create"):
        _assert_likely_scam_create(kwargs.get("body"))
        _reject_unknown_params(kwargs, {"userId", "body"})
    collection = _users_resource(service, resource)
    result = getattr(collection, method)(**kwargs).execute()
    if not isinstance(result, dict):
        raise GmailError("Gmail returned an unexpected response.")
    return result


def add_likely_scam_label(service: Any, message_id: str, label_id: str) -> dict[str, Any]:
    """Add the Likely scam label and leave every other label, including INBOX, alone."""
    if not (message_id or "").strip():
        raise GmailError("That message could not be opened.")
    return gmail_call(
        service,
        "messages",
        "modify",
        label_id=label_id,
        userId="me",
        id=message_id.strip(),
        body={"addLabelIds": [label_id], "removeLabelIds": []},
    )


def _assert_label_only_modify(body: Any, label_id: str) -> None:
    if not isinstance(body, dict) or set(body) - _MODIFY_BODY_KEYS:
        raise GmailError(_REFUSE_CALL)
    if not _USER_LABEL_ID.fullmatch(label_id or ""):
        raise GmailError(_REFUSE_CALL)
    remove = body.get("removeLabelIds", [])
    if not isinstance(remove, list) or remove:
        raise GmailError(_REFUSE_CALL)
    if body.get("addLabelIds") != [label_id]:
        raise GmailError(_REFUSE_CALL)


def _assert_likely_scam_create(body: Any) -> None:
    if not isinstance(body, dict) or set(body) - _LABEL_CREATE_KEYS:
        raise GmailError(_REFUSE_CALL)
    if body.get("name") != LIKELY_SCAM_LABEL_NAME:
        raise GmailError(_REFUSE_CALL)
    visibility = body.get("messageListVisibility")
    if visibility is not None and visibility != "show":
        raise GmailError(_REFUSE_CALL)


def _reject_unknown_params(kwargs: dict[str, Any], allowed: set[str]) -> None:
    if set(kwargs) - allowed:
        raise GmailError(_REFUSE_CALL)


def _users_resource(service: Any, resource: str) -> Any:
    users = service.users()
    if resource == "messages":
        return users.messages()
    if resource == "labels":
        return users.labels()
    raise GmailError(_REFUSE_CALL)


def _client_config(redirect: str) -> dict[str, Any]:
    return {
        "web": {
            "client_id": gmail_client_id(),
            "client_secret": gmail_client_secret(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect, "http://localhost:8501", "http://localhost:8501/"],
        }
    }


def _service(token_info: dict[str, Any] | None = None):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise GmailError("Gmail libraries are not installed. Run: pip install -e .") from exc

    info = token_info or load_persisted_token()
    if not info:
        raise GmailError("Gmail is not connected yet.")

    creds = Credentials.from_authorized_user_info(info, list(SCOPES))
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            refreshed = json.loads(creds.to_json())
            info.update(refreshed)
            if persist_token_to_disk():
                gmail_token_path().write_text(json.dumps(info), encoding="utf-8")
        except Exception:
            disconnect()
            raise GmailError("Gmail sign-in expired. Connect Gmail again.") from None
    if not creds.valid:
        raise GmailError("Gmail is not connected yet.")

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _allow_localhost_http(redirect: str) -> None:
    if redirect.startswith("http://localhost") or redirect.startswith("http://127.0.0.1"):
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def _oauth_state_path():
    return token_dir() / "oauth_states.json"


def _remember_oauth_state(state: str) -> None:
    if not state:
        return
    path = _oauth_state_path()
    payload = _load_oauth_states()
    now = time.time()
    payload = {key: ts for key, ts in payload.items() if now - ts < _OAUTH_STATE_TTL_SECONDS}
    payload[state] = now
    path.write_text(json.dumps(payload), encoding="utf-8")


def _forget_oauth_state(state: str) -> None:
    payload = _load_oauth_states()
    payload.pop(state, None)
    _oauth_state_path().write_text(json.dumps(payload), encoding="utf-8")


def _load_oauth_states() -> dict[str, float]:
    path = _oauth_state_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def _state_is_known(state: str, expected_state: str) -> bool:
    if not state:
        return False
    if expected_state and state == expected_state:
        return True
    payload = _load_oauth_states()
    ts = payload.get(state)
    if ts is None:
        return False
    return (time.time() - ts) < _OAUTH_STATE_TTL_SECONDS


def _short_date(value: str) -> str:
    if not value:
        return ""
    try:
        from email.utils import parsedate_to_datetime

        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value[:32]
