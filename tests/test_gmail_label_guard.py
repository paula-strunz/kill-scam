"""Label-only Gmail guard. Fakes only: no Google calls and no credentials."""

from __future__ import annotations

import pytest

from kill_scam.config import GMAIL_MODIFY_SCOPE, GMAIL_READONLY_SCOPE
from kill_scam.gmail import (
    ALLOWED_GMAIL_CALLS,
    FORBIDDEN_SCOPE_FRAGMENTS,
    LIKELY_SCAM_LABEL_NAME,
    SCOPES,
    GmailError,
    add_likely_scam_label,
    assert_allowed_scopes,
    get_message,
    gmail_call,
    list_recent_messages,
)

OUR_LABEL = "Label_42"


class _Request:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def execute(self) -> dict:
        return dict(self._payload)


class _Collection:
    """Records a method only when the guard actually calls it."""

    def __init__(self, name: str, calls: list[tuple]) -> None:
        self._name = name
        self._calls = calls

    def __getattr__(self, method: str):
        def _invoke(**kwargs):
            self._calls.append((self._name, method, kwargs))
            if self._name == "messages" and method == "list":
                return _Request({"messages": [{"id": "m1"}]})
            if self._name == "messages" and method == "get":
                return _Request(
                    {
                        "id": kwargs.get("id") or "m1",
                        "snippet": "A short snippet.",
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "School Office"},
                                {"name": "Subject", "value": "Picnic"},
                                {"name": "Date", "value": "Sat, 29 Aug 2026 10:00:00 +0000"},
                            ]
                        },
                    }
                )
            if self._name == "messages" and method == "modify":
                added = list((kwargs.get("body") or {}).get("addLabelIds") or [])
                return _Request({"id": kwargs.get("id"), "labelIds": ["INBOX", *added]})
            if self._name == "labels" and method == "list":
                return _Request({"labels": [{"id": OUR_LABEL, "name": LIKELY_SCAM_LABEL_NAME}]})
            if self._name == "labels" and method == "create":
                return _Request({"id": OUR_LABEL, "name": (kwargs.get("body") or {}).get("name")})
            raise AssertionError(f"{self._name}.{method} must not run")

        return _invoke


class FakeGmail:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.opened: list[str] = []

    def users(self):
        return self

    def messages(self):
        self.opened.append("messages")
        return _Collection("messages", self.calls)

    def labels(self):
        self.opened.append("labels")
        return _Collection("labels", self.calls)

    def drafts(self):
        self.opened.append("drafts")
        return _Collection("drafts", self.calls)

    def threads(self):
        self.opened.append("threads")
        return _Collection("threads", self.calls)

    def settings(self):
        self.opened.append("settings")
        return _Collection("settings", self.calls)

    def history(self):
        self.opened.append("history")
        return _Collection("history", self.calls)


def test_scopes_are_modify_only() -> None:
    assert SCOPES == (GMAIL_MODIFY_SCOPE,)
    assert GMAIL_READONLY_SCOPE not in SCOPES
    joined = " ".join(SCOPES).lower()
    for fragment in FORBIDDEN_SCOPE_FRAGMENTS:
        assert fragment not in joined
    assert_allowed_scopes()
    assert_allowed_scopes((GMAIL_MODIFY_SCOPE, "openid", "email"))


@pytest.mark.parametrize(
    "scope",
    [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.insert",
        "https://www.googleapis.com/auth/gmail.settings.basic",
        "https://mail.google.com/",
        GMAIL_MODIFY_SCOPE + " https://www.googleapis.com/auth/gmail.send",
    ],
)
def test_broader_scopes_are_refused(scope: str) -> None:
    scopes = tuple(scope.split())
    with pytest.raises(GmailError, match="refuses"):
        assert_allowed_scopes(scopes)


def test_readonly_scope_alone_is_refused() -> None:
    with pytest.raises(GmailError, match="Likely scam label"):
        assert_allowed_scopes((GMAIL_READONLY_SCOPE,))


def test_allowlist_is_list_get_modify_and_label_setup_only() -> None:
    assert ALLOWED_GMAIL_CALLS == frozenset(
        {
            ("messages", "list"),
            ("messages", "get"),
            ("messages", "modify"),
            ("labels", "list"),
            ("labels", "create"),
        }
    )


def test_allowed_label_add_keeps_inbox() -> None:
    fake = FakeGmail()
    result = add_likely_scam_label(fake, "m1", OUR_LABEL)
    assert result["labelIds"] == ["INBOX", OUR_LABEL]
    assert fake.opened == ["messages"]
    assert fake.calls == [
        (
            "messages",
            "modify",
            {
                "userId": "me",
                "id": "m1",
                "body": {"addLabelIds": [OUR_LABEL], "removeLabelIds": []},
            },
        )
    ]


def test_allowed_reads_and_likely_scam_label_create() -> None:
    fake = FakeGmail()
    listed = gmail_call(fake, "messages", "list", userId="me", labelIds=["INBOX"])
    fetched = gmail_call(fake, "messages", "get", userId="me", id="m1", format="full")
    labels = gmail_call(fake, "labels", "list", userId="me")
    created = gmail_call(
        fake,
        "labels",
        "create",
        userId="me",
        body={
            "name": LIKELY_SCAM_LABEL_NAME,
            "messageListVisibility": "show",
            "labelListVisibility": "labelShow",
            "color": {"backgroundColor": "#cc3a21", "textColor": "#ffffff"},
        },
    )
    assert listed["messages"] == [{"id": "m1"}]
    assert fetched["id"] == "m1"
    assert labels["labels"][0]["name"] == LIKELY_SCAM_LABEL_NAME
    assert created["id"] == OUR_LABEL
    assert [call[:2] for call in fake.calls] == [
        ("messages", "list"),
        ("messages", "get"),
        ("labels", "list"),
        ("labels", "create"),
    ]


def test_recent_list_and_get_go_through_the_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGmail()
    monkeypatch.setattr("kill_scam.gmail._service", lambda token_info=None: fake)
    messages = list_recent_messages({"token": "fake"})
    opened = get_message("m1", {"token": "fake"})
    assert len(messages) == 1
    assert messages[0].id == "m1"
    assert opened.subject == "Picnic"
    assert [call[:2] for call in fake.calls] == [
        ("messages", "list"),
        ("messages", "get"),
        ("messages", "get"),
    ]


@pytest.mark.parametrize(
    ("resource", "method", "kwargs"),
    [
        ("messages", "send", {"userId": "me", "body": {"raw": "abc"}}),
        ("messages", "delete", {"userId": "me", "id": "m1"}),
        ("messages", "trash", {"userId": "me", "id": "m1"}),
        ("messages", "batchDelete", {"userId": "me", "body": {"ids": ["m1"]}}),
        ("messages", "untrash", {"userId": "me", "id": "m1"}),
        ("messages", "insert", {"userId": "me", "body": {}}),
        ("messages", "import", {"userId": "me", "body": {}}),
        ("messages", "batchModify", {"userId": "me", "body": {}}),
        ("drafts", "create", {"userId": "me", "body": {}}),
        ("drafts", "send", {"userId": "me", "body": {}}),
        ("drafts", "update", {"userId": "me", "id": "d1", "body": {}}),
        ("drafts", "delete", {"userId": "me", "id": "d1"}),
        ("threads", "modify", {"userId": "me", "id": "t1", "body": {}}),
        ("threads", "trash", {"userId": "me", "id": "t1"}),
        ("threads", "delete", {"userId": "me", "id": "t1"}),
        ("threads", "untrash", {"userId": "me", "id": "t1"}),
        ("labels", "delete", {"userId": "me", "id": OUR_LABEL}),
        ("labels", "update", {"userId": "me", "id": OUR_LABEL, "body": {"name": "Other"}}),
        ("labels", "patch", {"userId": "me", "id": OUR_LABEL, "body": {}}),
        ("settings", "updateAutoForwarding", {"userId": "me", "body": {}}),
        ("history", "list", {"userId": "me"}),
    ],
)
def test_forbidden_gmail_calls_are_refused(resource: str, method: str, kwargs: dict) -> None:
    fake = FakeGmail()
    with pytest.raises(GmailError, match="refuses"):
        gmail_call(fake, resource, method, **kwargs)
    assert fake.calls == []
    assert fake.opened == []


@pytest.mark.parametrize(
    "body",
    [
        {"addLabelIds": ["TRASH"], "removeLabelIds": []},
        {"addLabelIds": ["SPAM"], "removeLabelIds": []},
        {"addLabelIds": ["INBOX"], "removeLabelIds": []},
        {"addLabelIds": [OUR_LABEL], "removeLabelIds": ["INBOX"]},
        {"addLabelIds": [OUR_LABEL], "removeLabelIds": [OUR_LABEL]},
        {"addLabelIds": [OUR_LABEL], "removeLabelIds": ["UNREAD"]},
        {"addLabelIds": [OUR_LABEL, "TRASH"], "removeLabelIds": []},
        {"addLabelIds": [OUR_LABEL, "SPAM"], "removeLabelIds": []},
        {"addLabelIds": ["Label_99"], "removeLabelIds": []},
        {"addLabelIds": [], "removeLabelIds": []},
        {"removeLabelIds": ["INBOX"]},
        {"addLabelIds": [OUR_LABEL], "removeLabelIds": [], "extra": True},
    ],
)
def test_modify_rejects_anything_except_our_label(body: dict) -> None:
    fake = FakeGmail()
    with pytest.raises(GmailError, match="refuses"):
        gmail_call(
            fake,
            "messages",
            "modify",
            label_id=OUR_LABEL,
            userId="me",
            id="m1",
            body=body,
        )
    assert fake.calls == []
    assert fake.opened == []


def test_modify_with_omitted_remove_list_still_adds_only_our_label() -> None:
    fake = FakeGmail()
    result = gmail_call(
        fake,
        "messages",
        "modify",
        label_id=OUR_LABEL,
        userId="me",
        id="m1",
        body={"addLabelIds": [OUR_LABEL]},
    )
    assert result["labelIds"] == ["INBOX", OUR_LABEL]
    assert fake.calls[0][2]["body"] == {"addLabelIds": [OUR_LABEL]}


def test_system_label_cannot_pose_as_our_label() -> None:
    fake = FakeGmail()
    for system_id in ("INBOX", "TRASH", "SPAM", "DRAFT", "Label_TRASH"):
        with pytest.raises(GmailError, match="refuses"):
            gmail_call(
                fake,
                "messages",
                "modify",
                label_id=system_id,
                userId="me",
                id="m1",
                body={"addLabelIds": [system_id], "removeLabelIds": []},
            )
    assert fake.calls == []


def test_other_label_names_cannot_be_created() -> None:
    fake = FakeGmail()
    with pytest.raises(GmailError, match="refuses"):
        gmail_call(
            fake,
            "labels",
            "create",
            userId="me",
            body={"name": "Archive", "messageListVisibility": "show"},
        )
    with pytest.raises(GmailError, match="refuses"):
        gmail_call(
            fake,
            "labels",
            "create",
            userId="me",
            body={"name": LIKELY_SCAM_LABEL_NAME, "messageListVisibility": "hide"},
        )
    assert fake.calls == []
    assert fake.opened == []


def test_blank_message_is_not_modified() -> None:
    fake = FakeGmail()
    with pytest.raises(GmailError, match="could not be opened"):
        add_likely_scam_label(fake, "  ", OUR_LABEL)
    assert fake.calls == []
