from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from kill_scam.evals import (
    GOLD_HAM,
    GOLD_SCAM,
    Example,
    format_report,
    load_fixtures,
    score_predictions,
)

PERSONAL_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|icloud|outlook)\.com", re.I)
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE = re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b")
ALLOWED_TEST_DOMAINS = (".test", ".example", "example.com", "example.org", "example.net")


def test_fixtures_exist_and_are_balanced() -> None:
    examples = load_fixtures()
    scams = [item for item in examples if item.gold_label == GOLD_SCAM]
    hams = [item for item in examples if item.gold_label == GOLD_HAM]
    assert len(examples) >= 8
    assert len(scams) >= 4
    assert len(hams) >= 4
    assert {item.gold_verdict for item in scams} == {"likely_scam"}
    assert {item.gold_verdict for item in hams} == {"ok"}
    assert len({item.id for item in examples}) == len(examples)


def test_fixtures_are_synthetic_without_pii() -> None:
    examples = load_fixtures()
    blob = "\n".join(item.message for item in examples)
    assert PERSONAL_EMAIL.search(blob) is None
    assert SSN.search(blob) is None
    assert PHONE.search(blob) is None
    for match in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", blob):
        assert any(match.lower().endswith(domain) for domain in ALLOWED_TEST_DOMAINS)


def test_fixture_file_has_arize_shaped_columns() -> None:
    path = Path(__file__).resolve().parents[1] / "evals" / "fixtures.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["name"] == "kill-scam-v1-classification"
    assert payload["metrics"] == ["missed_scam", "false_alarm"]
    required = {"id", "message", "gold_label", "gold_verdict", "category"}
    for raw in payload["examples"]:
        assert required.issubset(raw)


def _sample() -> list[Example]:
    return [
        Example("s1", "gift cards now", GOLD_SCAM, "likely_scam", "payment_pressure"),
        Example("s2", "fake bank login", GOLD_SCAM, "likely_scam", "fake_bank"),
        Example("h1", "picnic at noon", GOLD_HAM, "ok", "newsletter"),
        Example("h2", "see you at 7", GOLD_HAM, "ok", "personal"),
    ]


def test_all_ok_predictions_are_missed_scams() -> None:
    report = score_predictions(_sample(), ["ok", "ok", "ok", "ok"])
    assert report.missed_scams == 2
    assert report.false_alarms == 0
    assert report.caught_scams == 0
    assert report.true_ham == 2
    assert report.missed_scam_rate == 1.0
    assert "missed scam" in format_report(report)


def test_all_scam_predictions_are_false_alarms_on_ham() -> None:
    report = score_predictions(
        _sample(), ["likely_scam", "likely_scam", "likely_scam", "suspicious"]
    )
    assert report.missed_scams == 0
    assert report.false_alarms == 2
    assert report.caught_scams == 2
    assert report.true_ham == 0
    assert report.false_alarm_rate == 1.0


def test_perfect_predictions() -> None:
    report = score_predictions(_sample(), ["likely_scam", "suspicious", "ok", "ok"])
    assert report.missed_scams == 0
    assert report.false_alarms == 0
    assert report.caught_scams == 2
    assert report.true_ham == 2


def test_score_length_mismatch() -> None:
    with pytest.raises(ValueError):
        score_predictions(_sample(), ["ok"])


def test_run_eval_with_stub_classifier() -> None:
    from kill_scam.evals import run_eval
    from kill_scam.models import CheckResult

    def stub(message: str) -> CheckResult:
        if "gift card" in message.lower() or "password" in message.lower() or "http://" in message.lower():
            verdict = "likely_scam"
        elif "Mom its me" in message:
            verdict = "likely_scam"
        else:
            verdict = "ok"
        return CheckResult(verdict=verdict, summary="stub", reasons=["stub"], advice="stub")

    report = run_eval(classify=stub)
    assert report.total == 12
    assert report.missed_scams == 0
    assert report.false_alarms == 0
