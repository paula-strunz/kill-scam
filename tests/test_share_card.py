from __future__ import annotations

import pytest

from kill_scam.agent import classify_message
from kill_scam.evals import load_fixtures
from kill_scam.models import CheckResult, StepResult
from kill_scam.share_card import (
    CHIP_LIMIT,
    DISCLAIMER,
    MAX_CHIPS,
    RESULT_LABELS,
    build_share_result,
    format_share_result,
    render_share_result_html,
    result_label,
    signal_chips,
)


def _result(
    verdict: str,
    summary: str,
    *,
    reasons: list[str] | None = None,
    advice: str = "",
    steps: list[StepResult] | None = None,
) -> CheckResult:
    return CheckResult(
        verdict=verdict,
        summary=summary,
        reasons=reasons or [],
        advice=advice,
        steps=steps or [],
    )


def test_labels_are_the_short_verdict_words() -> None:
    assert RESULT_LABELS == {
        "ok": "Looks okay",
        "suspicious": "Not sure",
        "likely_scam": "Likely scam",
    }
    assert result_label("ok") == "Looks okay"
    assert result_label("suspicious") == "Not sure"
    assert result_label("likely_scam") == "Likely scam"


def test_result_leads_with_one_sentence_and_at_most_three_chips() -> None:
    reasons = [
        "Ask: it wants a password, code, or card number.",
        "Links: a web address looks like an official site but is not.",
        "Identity: the sending address looks like an official site but is not.",
        "Campaigns: this matches a known pattern (bank login).",
        "Ask: the fear persuasion hook fired.",
    ]
    view = build_share_result(
        _result(
            "likely_scam",
            "Several checks say this is a scam. Do not click, pay, or share a code.",
            reasons=reasons,
            advice="Do not click, do not pay, and do not share codes from this message. Call the bank.",
        )
    )
    assert view.label == "Likely scam"
    assert view.why == "Several checks say this is a scam."
    assert "\n" not in view.why
    assert len(view.chips) == MAX_CHIPS
    assert view.chips == ("Asks for a password", "Lookalike link", "Fake sender")
    assert all(len(chip) <= CHIP_LIMIT for chip in view.chips)
    assert view.next_step == "Do not click, do not pay, and do not share codes from this message."
    assert "\n" not in view.next_step
    text = format_share_result(view)
    assert text.startswith("Likely scam\n")
    assert "1. What does it want" not in text
    assert "Result card" not in text


def test_why_collapses_whitespace_truncates_and_skips_message_details() -> None:
    secret_tail = "UNIQUE_TAIL_NOT_ON_CARD"
    view = build_share_result(
        _result(
            "suspicious",
            ("Pay now.\n\n" * 40) + secret_tail,
            reasons=["Ask: no click demand.", secret_tail],
            advice="",
            steps=[
                StepResult(
                    id="ask",
                    title="1. What does it want you to do?",
                    status="done",
                    summary="full pasted novel " + secret_tail,
                    details=[secret_tail],
                )
            ],
        )
    )
    assert "\n" not in view.why
    assert secret_tail not in view.why
    assert secret_tail not in format_share_result(view)
    assert view.chips == ()
    assert view.label == "Not sure"


def test_html_is_light_and_escapes_check_text() -> None:
    summary = 'Confirm at http://nat-example-bank-secure.test/login <script>alert("x")</script> now.'
    view = build_share_result(
        _result(
            "likely_scam",
            summary,
            reasons=["Links: a lookalike host."],
            advice="Do not click.",
        )
    )
    text = format_share_result(view)
    html = render_share_result_html(view, color="#9b1c1c")
    assert "http://" not in text
    assert "https://" not in text
    assert "nat-example-bank-secure[.]test" in text
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "result-lead" in html
    assert "result-label" in html
    assert "Likely scam" in html
    assert "Lookalike link" in html
    assert "share-card" not in html
    assert "Result card" not in html
    assert "border" not in html
    assert DISCLAIMER in text
    assert DISCLAIMER not in html


def test_ok_result_has_no_chip_dump() -> None:
    view = build_share_result(
        _result(
            "ok",
            "The five checks did not find scam pressure.",
            reasons=[
                "Ask: no click / pay / code / silence demand.",
                "Links: no lookalike or hidden short link.",
                "Identity: no official-org impersonation with a fake address.",
            ],
            advice="Use a phone number you already have.",
        )
    )
    assert view.label == "Looks okay"
    assert view.chips == ()
    assert view.next_step == "Use a phone number you already have."
    html = render_share_result_html(view, color="#0f7b3a")
    assert "result-chip" not in html


def test_fake_bank_fixture_omits_full_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    example = next(item for item in load_fixtures() if item.id == "scam-fake-bank")
    result = classify_message(example.message, allow_search=False)
    view = build_share_result(result)
    text = format_share_result(view)
    html = render_share_result_html(view, color="#9b1c1c")
    assert result.verdict == "likely_scam"
    assert view.label == "Likely scam"
    assert len(view.chips) <= MAX_CHIPS
    assert view.chips
    assert signal_chips(result) == view.chips
    assert example.message not in text
    assert example.message not in html
    assert "Your account will be closed tonight" not in text
    assert "http://" not in text
    assert "https://" not in text
    assert "Result card" not in html
    assert "border" not in html
