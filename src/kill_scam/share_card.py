"""Calm, phone-first snapshot of a paste-check verdict.

The on-screen result is a short label, one sentence, up to three chips,
and one next step. It never includes the raw message.
See specs/002-shareable-result-card.md.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from kill_scam.links import defang_for_display
from kill_scam.models import VERDICT_LABELS, CheckResult

# Short labels for the paste result. Not the longer Gmail verdict box.
RESULT_LABELS = {
    "ok": "Looks okay",
    "suspicious": "Not sure",
    "likely_scam": "Likely scam",
}

WHY_LIMIT = 140
NEXT_LIMIT = 120
CHIP_LIMIT = 28
MAX_CHIPS = 3
DISCLAIMER = "This is a helper, not a guarantee."
EMPTY_WHY = "We could not sum this up in one sentence."

_DEFAULT_NEXT = {
    "likely_scam": "Do not click, pay, or share a code.",
    "suspicious": "Pause and check with a number you already trust.",
    "ok": "Nothing urgent. Still ignore surprise links.",
}

# First match wins. Keep each label short enough to scan as a chip.
_CHIP_RULES: tuple[tuple[str, str], ...] = (
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
    ("known pattern", "Known scam pattern"),
    ("persuasion hook", "Pressure wording"),
    ("click", "Pushes a click"),
)

_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class ShareResult:
    verdict: str
    label: str
    why: str
    chips: tuple[str, ...]
    next_step: str


def result_label(verdict: str) -> str:
    """Short paste-result label. Unknown values fall back to the model label."""
    if verdict in RESULT_LABELS:
        return RESULT_LABELS[verdict]
    return VERDICT_LABELS.get(verdict, verdict)


def build_share_result(result: CheckResult) -> ShareResult:
    """Build the calm result from a finished check. The raw message is not an input."""
    why = _one_sentence(result.summary, WHY_LIMIT) if result.summary else EMPTY_WHY
    return ShareResult(
        verdict=result.verdict,
        label=result_label(result.verdict),
        why=why,
        chips=signal_chips(result),
        next_step=_next_step(result),
    )


def signal_chips(result: CheckResult) -> tuple[str, ...]:
    """At most three short signals, in checklist order. Benign notes are skipped."""
    found: list[str] = []
    for reason in result.reasons:
        chip = _chip_for(reason)
        if chip and chip not in found:
            found.append(chip)
        if len(found) == MAX_CHIPS:
            break
    return tuple(found)


def format_share_result(view: ShareResult) -> str:
    """Plain text for the quiet copy button. Same facts as the screen, no message body."""
    parts = [view.label, view.why, ""]
    if view.chips:
        parts.extend(view.chips)
        parts.append("")
    parts.append(view.next_step)
    parts.append("")
    parts.append(DISCLAIMER)
    return "\n".join(parts).strip() + "\n"


def render_share_result_html(view: ShareResult, *, color: str) -> str:
    """Light HTML for the verdict lead. No boxed card chrome. Check text is escaped."""
    color_safe = html.escape(color, quote=True)
    chips = ""
    if view.chips:
        pills = "".join(
            f'<span class="result-chip">{html.escape(chip)}</span>' for chip in view.chips
        )
        chips = f'<div class="result-chips">{pills}</div>'
    return (
        '<div class="result-lead">'
        f'<p class="result-label" style="color:{color_safe};">{html.escape(view.label)}</p>'
        f'<p class="result-why">{html.escape(view.why)}</p>'
        f"{chips}"
        f'<p class="result-next">{html.escape(view.next_step)}</p>'
        "</div>"
    )


def _next_step(result: CheckResult) -> str:
    sentence = _one_sentence(result.advice, NEXT_LIMIT) if result.advice else ""
    if sentence and sentence != EMPTY_WHY:
        return sentence
    return _DEFAULT_NEXT.get(result.verdict, "Pause before you click or pay.")


def _chip_for(reason: str) -> str | None:
    text = " ".join((reason or "").lower().split())
    if not text:
        return None
    if " no " in f" {text} " and text.startswith(("ask: no", "links: no", "identity: no")):
        return None
    if "could not be reached" in text or "confidence is a bit lower" in text:
        return None
    for needle, label in _CHIP_RULES:
        if needle in text:
            return label
    return None


def _one_sentence(text: str, limit: int) -> str:
    collapsed = " ".join(defang_for_display(text or "").split())
    if not collapsed:
        return EMPTY_WHY
    sentence = _SENTENCE_BREAK.split(collapsed, maxsplit=1)[0].strip()
    if len(sentence) <= limit:
        return sentence
    return sentence[: limit - 3].rstrip() + "..."
