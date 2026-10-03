from __future__ import annotations

import pytest

from kill_scam.agent import classify_message
from kill_scam.evals import load_fixtures
from kill_scam.models import CheckResult, StepResult
from kill_scam.share_card import (
    DISCLAIMER,
    MAX_REASONS,
    PRIMARY_ACTION,
    REASON_LIMIT,
    RESULT_LABELS,
    ShareResult,
    build_share_result,
    format_share_result,
    render_share_result_html,
    result_label,
    short_reasons,
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


def test_labels_and_safe_action() -> None:
    assert RESULT_LABELS == {
        "ok": "Looks okay",
        "suspicious": "Not sure",
        "likely_scam": "Likely scam",
    }
    assert result_label("likely_scam") == "Likely scam"
    assert PRIMARY_ACTION["likely_scam"] == "Don't reply"
    assert PRIMARY_ACTION["suspicious"] == "Don't reply yet"
    assert PRIMARY_ACTION["ok"] == "Close"


def test_warning_has_harm_and_at_most_two_reasons() -> None:
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
            advice="Do not click, do not pay, and do not share codes from this message.",
        )
    )
    assert view.label == "Likely scam"
    assert view.action == "Don't reply"
    assert view.mark == "!"
    assert "\n" not in view.harm
    assert len(view.reasons) == MAX_REASONS
    assert view.reasons == ("Asks for a password", "Lookalike link")
    assert all(len(reason) <= REASON_LIMIT for reason in view.reasons)
    text = format_share_result(view)
    assert text.startswith("Likely scam\n")
    assert "Don't reply" in text
    assert "Fake sender" not in text
    assert "1. What does it want" not in text
    assert "Result card" not in text
    html = render_share_result_html(view)
    assert "warn-screen" in html
    assert "result-chip" not in html
    assert "chip" not in html


def test_message_details_never_become_reasons() -> None:
    secret_tail = "UNIQUE_TAIL_NOT_ON_CARD"
    view = build_share_result(
        _result(
            "suspicious",
            ("Pay now.\n\n" * 40) + secret_tail,
            reasons=["Ask: no click demand.", secret_tail],
            advice="Call them.",
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
    assert secret_tail not in view.harm
    assert secret_tail not in format_share_result(view)
    assert view.reasons == ()
    assert view.label == "Not sure"
    assert view.action == "Don't reply yet"


def test_html_escapes_and_has_no_card_chrome() -> None:
    view = ShareResult(
        verdict="likely_scam",
        label="Likely scam",
        harm='<script>alert("x")</script>',
        reasons=("Lookalike link",),
        action="Don't reply",
        mark="!",
    )
    html = render_share_result_html(view)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "warn-title" in html
    assert "share-card" not in html
    assert "Result card" not in html
    assert "border:" not in html
    assert "background:" not in html
    text = format_share_result(
        build_share_result(
            _result(
                "likely_scam",
                "Confirm at http://nat-example-bank-secure.test/login now.",
                reasons=["Links: a lookalike host."],
            )
        )
    )
    assert "http://" not in text
    assert "https://" not in text
    assert DISCLAIMER in text
    assert DISCLAIMER not in html


def test_ok_result_has_no_reason_dump() -> None:
    view = build_share_result(
        _result(
            "ok",
            "The five checks did not find scam pressure.",
            reasons=[
                "Ask: no click / pay / code / silence demand.",
                "Links: no lookalike or hidden short link.",
                "Identity: no official-org impersonation with a fake address.",
            ],
        )
    )
    assert view.label == "Looks okay"
    assert view.reasons == ()
    assert view.action == "Close"
    html = render_share_result_html(view)
    assert "warn-reason" not in html


def test_fake_bank_fixture_omits_full_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    example = next(item for item in load_fixtures() if item.id == "scam-fake-bank")
    result = classify_message(example.message, allow_search=False)
    view = build_share_result(result)
    text = format_share_result(view)
    html = render_share_result_html(view)
    assert result.verdict == "likely_scam"
    assert view.label == "Likely scam"
    assert view.action == "Don't reply"
    assert view.reasons == ("Not the official site", "Asks for a password")
    assert short_reasons(result) == view.reasons
    assert example.message not in text
    assert example.message not in html
    assert "Your account will be closed tonight" not in text
    assert "http://" not in text
    assert "https://" not in text
    assert "result-chip" not in html
    assert "border:" not in html
