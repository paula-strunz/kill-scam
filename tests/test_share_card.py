from __future__ import annotations

import pytest

from kill_scam.agent import classify_message
from kill_scam.evals import load_fixtures
from kill_scam.models import STEP_IDS, STEP_TITLES, CheckResult, StepResult
from kill_scam.share_card import (
    CARD_VERDICT_LABELS,
    DISCLAIMER,
    OMIT_NOTE,
    ONE_LINE_LIMIT,
    SHARE_HINT,
    build_share_card,
    format_share_card,
    render_share_card_html,
    verdict_headline,
)


def _result(verdict: str, summary: str, steps: list[StepResult] | None = None) -> CheckResult:
    return CheckResult(verdict=verdict, summary=summary, steps=steps or [])


def test_headlines_match_existing_verdict_words() -> None:
    assert CARD_VERDICT_LABELS == {
        "ok": "Looks OK",
        "suspicious": "Be careful",
        "likely_scam": "Likely a scam — do not click",
    }
    assert verdict_headline("ok") == "Looks OK"
    assert verdict_headline("suspicious") == "Be careful"
    assert verdict_headline("likely_scam") == "Likely a scam — do not click"


def test_card_lists_five_checks_in_order() -> None:
    steps = [
        StepResult(id=step_id, title=STEP_TITLES[step_id], status="done", summary=f"Note for {step_id}")
        for step_id in reversed(STEP_IDS)
    ]
    card = build_share_card(_result("suspicious", "Something is off.", steps))
    assert [line.step_id for line in card.lines] == list(STEP_IDS)
    assert [line.title for line in card.lines] == [STEP_TITLES[step_id] for step_id in STEP_IDS]
    assert card.lines[0].one_line == "Note for ask"
    text = format_share_card(card)
    assert text.index("1. What does it want you to do?") < text.index("5. Verdict and what to do")


def test_one_line_collapses_whitespace_and_truncates() -> None:
    secret_tail = "UNIQUE_TAIL_NOT_ON_CARD"
    long_summary = ("Pay now.\n\n" * 40) + secret_tail
    card = build_share_card(
        _result(
            "likely_scam",
            long_summary,
            [
                StepResult(
                    id="ask",
                    title=STEP_TITLES["ask"],
                    status="done",
                    summary="  click   the\nsite  ",
                    details=[secret_tail, "x" * 500],
                )
            ],
        )
    )
    ask = card.lines[0]
    assert "\n" not in ask.one_line
    assert ask.one_line == "click the site"
    assert len(card.summary) <= ONE_LINE_LIMIT
    assert secret_tail not in card.summary
    assert secret_tail not in format_share_card(card)
    assert all(len(line.one_line) <= ONE_LINE_LIMIT and "\n" not in line.one_line for line in card.lines)


def test_card_defangs_links_and_escapes_html() -> None:
    summary = 'Confirm at http://nat-example-bank-secure.test/login <script>alert("x")</script>'
    card = build_share_card(_result("likely_scam", summary))
    text = format_share_card(card)
    html = render_share_card_html(card, border="#a11c1c", background="#fde8e8")
    assert "http://" not in text
    assert "https://" not in text
    assert "nat-example-bank-secure[.]test" in text
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert SHARE_HINT in text
    assert DISCLAIMER in text
    assert OMIT_NOTE in text
    assert "helper, not a guarantee" in text


def test_missing_steps_still_show_five_titles() -> None:
    card = build_share_card(_result("ok", "The five checks did not find scam pressure."))
    assert len(card.lines) == 5
    assert all(line.one_line == "No extra note for this check." for line in card.lines)
    assert card.verdict_label == "Looks OK"


def test_fake_bank_fixture_omits_full_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    example = next(item for item in load_fixtures() if item.id == "scam-fake-bank")
    result = classify_message(example.message, allow_search=False)
    card = build_share_card(result)
    text = format_share_card(card)
    html = render_share_card_html(card, border="#a11c1c", background="#fde8e8")
    assert result.verdict == "likely_scam"
    assert card.verdict_label == "Likely a scam — do not click"
    assert example.message not in text
    assert example.message not in html
    assert "Your account will be closed tonight" not in text
    assert "http://" not in text
    assert "https://" not in text
    assert SHARE_HINT in html
    assert "Result card" in html
