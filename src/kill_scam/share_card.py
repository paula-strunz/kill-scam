"""Full-screen paste warning. One mark, one headline, one safe action.

Not a score, not a chip row, not a boxed report.
See specs/002-shareable-result-card.md.
"""

from __future__ import annotations

import html
from dataclasses import dataclass

from kill_scam.models import VERDICT_LABELS, CheckResult

RESULT_LABELS = {
    "ok": "Looks okay",
    "suspicious": "Not sure",
    "likely_scam": "Likely scam",
}

# Our words. Not copied from a browser or wallet warning page.
HARM = {
    "likely_scam": "This message may be trying to take money, a code, or a password.",
    "suspicious": "Something here is off. It may be trying to rush you.",
    "ok": "We did not see a scam trick in this message.",
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

COPY_LABEL = "Copy summary"
WRONG_LINK = "This is wrong"
WRONG_NOTE = "This check can be wrong. If you know the person, contact them a way you already trust."

MAX_REASONS = 2
REASON_LIMIT = 32
DISCLAIMER = "This is a helper, not a guarantee."

_REASON_RULES: tuple[tuple[str, str], ...] = (
    ("password", "Asks for a password"),
    ("card number", "Asks for card details"),
    ("gift card", "Wants gift cards"),
    ("install", "Wants an install"),
    ("stay silent", "Asks you to hide it"),
    ("pay", "Asks for money"),
    ("send money", "Asks for money"),
    ("web address looks like", "Lookalike link"),
    ("lookalike", "Lookalike link"),
    ("sending address looks like", "Fake sender"),
    ("looks like an official", "Fake sender"),
    ("not their real site", "Not the real sender"),
    ("not the official site", "Not the official site"),
    ("short link", "Hidden link"),
    ("not on our official", "Not the official site"),
    ("known pattern", "Known scam pattern"),
    ("persuasion hook", "Pressure wording"),
    ("click", "Pushes a click"),
)


@dataclass(frozen=True)
class ShareResult:
    verdict: str
    label: str
    harm: str
    reasons: tuple[str, ...]
    action: str
    mark: str


def result_label(verdict: str) -> str:
    """Short headline. Unknown values fall back to the model label."""
    if verdict in RESULT_LABELS:
        return RESULT_LABELS[verdict]
    return VERDICT_LABELS.get(verdict, verdict)


def build_share_result(result: CheckResult) -> ShareResult:
    """Build the warning from a finished check. The raw message is not an input."""
    verdict = result.verdict
    return ShareResult(
        verdict=verdict,
        label=result_label(verdict),
        harm=HARM.get(verdict, HARM["suspicious"]),
        reasons=short_reasons(result),
        action=PRIMARY_ACTION.get(verdict, "Don't reply"),
        mark=MARK.get(verdict, "!"),
    )


def short_reasons(result: CheckResult) -> tuple[str, ...]:
    """At most two short reasons. Benign notes are skipped. Not a chip row."""
    found: list[str] = []
    for reason in result.reasons:
        label = _reason_for(reason)
        if label and label not in found:
            found.append(label)
        if len(found) == MAX_REASONS:
            break
    return tuple(found)


def format_share_result(view: ShareResult) -> str:
    """Plain text for Copy summary. Same facts as the screen, no message body."""
    parts = [view.label, view.harm, ""]
    if view.reasons:
        parts.extend(view.reasons)
        parts.append("")
    parts.append(view.action)
    parts.append("")
    parts.append(DISCLAIMER)
    return "\n".join(parts).strip() + "\n"


def render_share_result_html(view: ShareResult) -> str:
    """Centered warning markup. No card chrome. Check text is escaped."""
    kind = view.verdict if view.verdict in RESULT_LABELS else "unknown"
    reason_html = "".join(
        f'<p class="warn-reason">{html.escape(reason)}</p>' for reason in view.reasons
    )
    reasons = f'<div class="warn-reasons">{reason_html}</div>' if reason_html else ""
    return (
        '<div class="warn-screen">'
        f'<div class="warn-mark warn-mark-{html.escape(kind, quote=True)}" aria-hidden="true">'
        f"{html.escape(view.mark)}</div>"
        f'<p class="warn-title">{html.escape(view.label)}</p>'
        f'<p class="warn-harm">{html.escape(view.harm)}</p>'
        f"{reasons}"
        "</div>"
    )


def _reason_for(reason: str) -> str | None:
    text = " ".join((reason or "").lower().split())
    if not text:
        return None
    if text.startswith(("ask: no", "links: no", "identity: no")):
        return None
    if "could not be reached" in text or "confidence is a bit lower" in text:
        return None
    for needle, label in _REASON_RULES:
        if needle in text and len(label) <= REASON_LIMIT:
            return label
    return None
