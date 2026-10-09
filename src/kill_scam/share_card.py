"""Full-screen paste warning. One mark, one headline, one harm line, one safe action.

The harm line names the email by sender and subject only. The body never
reaches the screen. See specs/002-shareable-result-card.md.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from kill_scam.models import VERDICT_LABELS, CheckResult

RESULT_LABELS = {
    "ok": "Looks okay",
    "suspicious": "Not sure",
    "likely_scam": "Likely scam",
}

PRIMARY_ACTION = {
    "likely_scam": "Don't reply",
    "suspicious": "Don't reply yet",
    "ok": "Close",
}

MARK = {
    "likely_scam": "!",
    "suspicious": "!",
    "ok": "✓",
}

WRONG_LINK = "This is wrong"
WRONG_NOTE = "This check can be wrong. If you know the person, contact them a way you already trust."

NAME_LIMIT = 40

# What the scam is after, picked from the check reasons. First match wins.
_TARGETS: tuple[tuple[str, str], ...] = (
    ("password", "your password"),
    ("card number", "your card details"),
    ("gift card", "your money"),
    ("send money", "your money"),
    ("pay", "your money"),
    ("code", "a code"),
)
_DEFAULT_TARGET = "your money or your password"

_FROM_NAME = re.compile(r"(?im)^From:[ \t]*\"?(?P<name>[^\"<\n@]+?)\"?[ \t]*<[^>\n]*>[ \t]*$")
_FROM_ADDR = re.compile(r"(?im)^From:[ \t]*<?(?P<addr>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)>?[ \t]*$")
_SUBJECT = re.compile(r"(?im)^Subject:[ \t]*(?P<subject>[^\n]+?)[ \t]*$")


@dataclass(frozen=True)
class EmailName:
    """Sender name and subject only. Never the body."""

    sender: str = ""
    subject: str = ""


@dataclass(frozen=True)
class ShareResult:
    verdict: str
    label: str
    harm: str
    action: str
    mark: str


def email_name(message: str) -> EmailName:
    """Read the From name and Subject headers. The body is ignored."""
    text = message or ""
    sender = ""
    match = _FROM_NAME.search(text)
    if match:
        sender = match.group("name")
    else:
        match = _FROM_ADDR.search(text)
        if match:
            sender = match.group("addr")
    match = _SUBJECT.search(text)
    subject = match.group("subject") if match else ""
    return EmailName(sender=_clean(sender), subject=_clean(subject))


def result_label(verdict: str) -> str:
    """Short headline. Unknown values fall back to the model label."""
    if verdict in RESULT_LABELS:
        return RESULT_LABELS[verdict]
    return VERDICT_LABELS.get(verdict, verdict)


def harm_line(verdict: str, name: EmailName, reasons: list[str] | tuple[str, ...] = ()) -> str:
    """One sentence. Names the email by sender, else subject, else 'This message'."""
    if name.sender:
        who = f"The email from '{name.sender}'"
    elif name.subject:
        who = f"The email '{name.subject}'"
    else:
        who = "This message"
    if verdict == "likely_scam":
        return f"{who} may be trying to take {_target(reasons)}."
    if verdict == "ok":
        return f"We did not see a scam trick in {who[0].lower() + who[1:]}."
    return f"Something in {who[0].lower() + who[1:]} is off. It may be trying to rush you."


def build_share_result(result: CheckResult, name: EmailName | None = None) -> ShareResult:
    """Build the warning from a finished check and the email's name. No body input."""
    verdict = result.verdict
    return ShareResult(
        verdict=verdict,
        label=result_label(verdict),
        harm=harm_line(verdict, name or EmailName(), result.reasons),
        action=PRIMARY_ACTION.get(verdict, "Don't reply"),
        mark=MARK.get(verdict, "!"),
    )


def render_share_result_html(view: ShareResult) -> str:
    """Centered warning markup. No card chrome. All text is escaped."""
    kind = view.verdict if view.verdict in RESULT_LABELS else "unknown"
    return (
        '<div class="warn-screen">'
        f'<div class="warn-mark warn-mark-{html.escape(kind, quote=True)}" aria-hidden="true">'
        f"{html.escape(view.mark)}</div>"
        f'<p class="warn-title">{html.escape(view.label)}</p>'
        f'<p class="warn-harm">{html.escape(view.harm)}</p>'
        "</div>"
    )


def _target(reasons: list[str] | tuple[str, ...]) -> str:
    for reason in reasons:
        text = " ".join((reason or "").lower().split())
        if text.startswith(("ask: no", "links: no", "identity: no")):
            continue
        for needle, target in _TARGETS:
            if needle in text:
                return target
    return _DEFAULT_TARGET


def _clean(value: str) -> str:
    text = " ".join((value or "").split()).strip("\"' ")
    text = text.replace("'", "\u2019")
    if len(text) > NAME_LIMIT:
        text = text[: NAME_LIMIT - 1].rstrip() + "\u2026"
    return text
