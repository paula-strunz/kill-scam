from __future__ import annotations

from pathlib import Path

import pytest

import kill_scam.share_card as share_card
from kill_scam.agent import classify_message
from kill_scam.evals import load_fixtures
from kill_scam.models import CheckResult, StepResult
from kill_scam.share_card import (
    PRIMARY_ACTION,
    RESULT_LABELS,
    WRONG_LINK,
    ShareResult,
    build_share_result,
    render_share_result_html,
    result_label,
)

APP = Path(__file__).resolve().parents[1] / "src" / "kill_scam" / "app.py"


def _result(
    verdict: str,
    summary: str = "",
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
    assert WRONG_LINK == "This is wrong"


def test_warning_has_no_reasons_and_no_copy_summary() -> None:
    view = build_share_result(
        _result(
            "likely_scam",
            "Several checks say this is a scam.",
            reasons=[
                "Ask: it wants a password, code, or card number.",
                "Links: a web address looks like an official site but is not.",
            ],
        )
    )
    assert view.label == "Likely scam"
    assert view.action == "Don't reply"
    assert view.mark == "!"
    assert not hasattr(view, "reasons")
    assert not hasattr(share_card, "format_share_result")
    assert not hasattr(share_card, "COPY_LABEL")
    html = render_share_result_html(view)
    assert "warn-screen" in html
    assert "warn-reason" not in html
    source = APP.read_text(encoding="utf-8")
    assert "Copy summary" not in source
    assert "copy-summary" not in source


def test_message_details_never_reach_the_screen() -> None:
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
    html = render_share_result_html(view)
    assert secret_tail not in view.harm
    assert secret_tail not in html
    assert view.label == "Not sure"
    assert view.action == "Don't reply yet"


def test_html_escapes_and_has_no_card_chrome() -> None:
    view = ShareResult(
        verdict="likely_scam",
        label="Likely scam",
        harm='<script>alert("x")</script>',
        action="Don't reply",
        mark="!",
    )
    html = render_share_result_html(view)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "warn-title" in html
    assert "share-card" not in html
    assert "Result card" not in html


def test_this_is_wrong_is_centered_full_width() -> None:
    source = APP.read_text(encoding="utf-8")
    assert 'key="verdict-wrong", type="tertiary", use_container_width=True' in source
    assert 'div[class*="st-key-verdict-wrong"] { display: flex; justify-content: center; }' in source


def test_fake_bank_fixture_omits_full_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    example = next(item for item in load_fixtures() if item.id == "scam-fake-bank")
    result = classify_message(example.message, allow_search=False)
    view = build_share_result(result)
    html = render_share_result_html(view)
    assert result.verdict == "likely_scam"
    assert view.label == "Likely scam"
    assert view.action == "Don't reply"
    assert example.message not in html
    assert "http" not in html
    assert "result-chip" not in html
