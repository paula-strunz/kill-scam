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

WRONG_LINK = "This is wrong"
WRONG_NOTE = "This check can be wrong. If you know the person, contact them a way you already trust."


@dataclass(frozen=True)
class ShareResult:
    verdict: str
    label: str
    harm: str
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
        action=PRIMARY_ACTION.get(verdict, "Don't reply"),
        mark=MARK.get(verdict, "!"),
    )


def render_share_result_html(view: ShareResult) -> str:
    """Centered warning markup. No card chrome. Check text is escaped."""
    kind = view.verdict if view.verdict in RESULT_LABELS else "unknown"
    return (
        '<div class="warn-screen">'
        f'<div class="warn-mark warn-mark-{html.escape(kind, quote=True)}" aria-hidden="true">'
        f"{html.escape(view.mark)}</div>"
        f'<p class="warn-title">{html.escape(view.label)}</p>'
        f'<p class="warn-harm">{html.escape(view.harm)}</p>'
        "</div>"
    )
