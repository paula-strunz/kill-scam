from __future__ import annotations

import pytest

from kill_scam.agent import classify_message, parse_verdict
from kill_scam.models import STEP_IDS, CheckError


def test_parse_plain_json() -> None:
    result = parse_verdict(
        """
        {
          "verdict": "likely_scam",
          "summary": "This asks you to pay with gift cards.",
          "reasons": ["Gift cards are a common scam payment.", "It says not to tell anyone."],
          "advice": "Do not buy gift cards. Hang up and check another way."
        }
        """
    )
    assert result.verdict == "likely_scam"
    assert result.label == "Likely a scam"
    assert len(result.reasons) == 2
    assert "gift cards" in result.advice.lower()


def test_parse_json_in_markdown_fence() -> None:
    raw = """Here you go:
```json
{
  "verdict": "ok",
  "summary": "This is a picnic reminder.",
  "reasons": ["No payment ask"],
  "advice": "No special steps."
}
```
"""
    result = parse_verdict(raw)
    assert result.verdict == "ok"
    assert "picnic" in result.summary.lower()


def test_parse_verdict_aliases_and_string_reasons() -> None:
    result = parse_verdict(
        {"verdict": "Be careful", "summary": "Odd wording.", "reasons": "The sender is vague."}
    )
    assert result.verdict == "suspicious"
    assert result.reasons == ["The sender is vague."]


def test_parse_dict_payload() -> None:
    result = parse_verdict(
        {
            "verdict": "likely_scam",
            "summary": "Fake bank login.",
            "reasons": ["Lookalike website", "", 12],
            "advice": "Call the bank using a number you already have.",
        }
    )
    assert result.verdict == "likely_scam"
    assert result.reasons == ["Lookalike website", "12"]


def test_parse_rejects_empty_and_unknown() -> None:
    with pytest.raises(CheckError):
        parse_verdict("")
    with pytest.raises(CheckError):
        parse_verdict("not json at all")
    with pytest.raises(CheckError):
        parse_verdict({"verdict": "banana", "summary": "nope"})


def test_empty_paste_does_not_need_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(CheckError, match="provide a message"):
        classify_message("   ")


def test_checklist_runs_without_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = classify_message(
        "Please send gift cards today or your account closes. Do not tell anyone.",
        allow_search=False,
    )
    assert result.verdict in {"suspicious", "likely_scam"}
    assert [step.id for step in result.steps] == list(STEP_IDS)


def test_message_too_long(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(CheckError, match="too long"):
        classify_message("x" * 20_001)
