"""Compact, copy-friendly snapshot of a paste-check verdict.

The card is for a screenshot or a short copy. It never includes the raw message.
"""

from __future__ import annotations

import html
from dataclasses import dataclass

from kill_scam.links import defang_for_display
from kill_scam.models import STEP_IDS, STEP_TITLES, VERDICT_LABELS, CheckResult

# Same headlines as the verdict box in the app.
CARD_VERDICT_LABELS = {
    "ok": "Looks OK",
    "suspicious": "Be careful",
    "likely_scam": "Likely a scam — do not click",
}

ONE_LINE_LIMIT = 120
DISCLAIMER = "This is a helper, not a guarantee. It never sends mail and never deletes mail."
SHARE_HINT = "Screenshot this card to share with family."
OMIT_NOTE = "The original message is not on this card."
EMPTY_LINE = "No extra note for this check."


@dataclass(frozen=True)
class ShareCardLine:
    step_id: str
    title: str
    one_line: str


@dataclass(frozen=True)
class ShareCard:
    verdict: str
    verdict_label: str
    summary: str
    lines: tuple[ShareCardLine, ...]
    disclaimer: str
    share_hint: str
    omit_note: str


def verdict_headline(verdict: str) -> str:
    """On-screen verdict words. Unknown values fall back to the short label."""
    if verdict in CARD_VERDICT_LABELS:
        return CARD_VERDICT_LABELS[verdict]
    return VERDICT_LABELS.get(verdict, verdict)


def build_share_card(result: CheckResult) -> ShareCard:
    """Build a share card from a finished check. The raw message is not an input."""
    by_id = {step.id: step for step in result.steps}
    lines: list[ShareCardLine] = []
    for step_id in STEP_IDS:
        step = by_id.get(step_id)
        title = step.title if step and step.title else STEP_TITLES[step_id]
        summary = step.summary if step else ""
        lines.append(ShareCardLine(step_id=step_id, title=title, one_line=_one_line(summary)))
    summary = _one_line(result.summary) if result.summary else EMPTY_LINE
    return ShareCard(
        verdict=result.verdict,
        verdict_label=verdict_headline(result.verdict),
        summary=summary,
        lines=tuple(lines),
        disclaimer=DISCLAIMER,
        share_hint=SHARE_HINT,
        omit_note=OMIT_NOTE,
    )


def format_share_card(card: ShareCard) -> str:
    """Plain text a person can copy. Same facts as the on-screen card."""
    parts = [
        "Kill Scam result card",
        "",
        card.verdict_label,
        card.summary,
        "",
    ]
    for line in card.lines:
        parts.append(line.title)
        parts.append(line.one_line)
        parts.append("")
    parts.append(card.omit_note)
    parts.append(card.disclaimer)
    parts.append(card.share_hint)
    return "\n".join(parts).strip() + "\n"


def render_share_card_html(card: ShareCard, *, border: str, background: str) -> str:
    """Compact HTML block for the result card. Check text is escaped."""
    border_safe = html.escape(border, quote=True)
    background_safe = html.escape(background, quote=True)
    rows = []
    for line in card.lines:
        rows.append(
            "<div class=\"share-line\">"
            f"<span class=\"share-line-title\">{html.escape(line.title)}</span>"
            f"<span class=\"share-line-text\">{html.escape(line.one_line)}</span>"
            "</div>"
        )
    body = "\n".join(rows)
    return (
        f'<div class="share-card" style="background:{background_safe}; border-color:{border_safe};">'
        '<p class="share-kicker">Result card</p>'
        f'<p class="share-title" style="color:{border_safe};">{html.escape(card.verdict_label)}</p>'
        f'<p class="share-summary">{html.escape(card.summary)}</p>'
        f"{body}"
        f'<p class="share-note">{html.escape(card.omit_note)}</p>'
        f'<p class="share-disclaimer">{html.escape(card.disclaimer)}</p>'
        f'<p class="share-hint">{html.escape(card.share_hint)}</p>'
        "</div>"
    )


def _one_line(text: str) -> str:
    collapsed = " ".join((text or "").split())
    if not collapsed:
        return EMPTY_LINE
    defanged = " ".join(defang_for_display(collapsed).split())
    if len(defanged) <= ONE_LINE_LIMIT:
        return defanged
    return defanged[: ONE_LINE_LIMIT - 3].rstrip() + "..."
