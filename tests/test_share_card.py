from __future__ import annotations

from pathlib import Path

import pytest

import kill_scam.share_card as share_card
from kill_scam.agent import classify_message
from kill_scam.evals import load_fixtures
from kill_scam.models import CheckResult, StepResult
from kill_scam.share_card import (
    NAME_LIMIT,
    PRIMARY_ACTION,
    RESULT_LABELS,
    WRONG_LINK,
    EmailName,
    ShareResult,
    build_share_result,
    email_name,
    harm_line,
    render_share_result_html,
    result_label,
)

APP = Path(__file__).resolve().parents[1] / "src" / "kill_scam" / "app.py"

BANK = (
    "From: La Banque Postale <securite@labanquepostale-verif.test>\n"
    "Subject: Votre compte sera bloque\n\n"
    "Confirmez votre mot de passe sur http://labanquepostale-verif.test/login BODY_SECRET"
)


def _result(verdict: str, reasons: list[str] | None = None, **kw) -> CheckResult:
    return CheckResult(verdict=verdict, summary=kw.pop("summary", ""), reasons=reasons or [], **kw)


def test_labels_and_safe_action() -> None:
    assert RESULT_LABELS == {"ok": "Looks okay", "suspicious": "Not sure", "likely_scam": "Likely scam"}
    assert result_label("likely_scam") == "Likely scam"
    assert PRIMARY_ACTION == {"likely_scam": "Don't reply", "suspicious": "Don't reply yet", "ok": "Close"}
    assert WRONG_LINK == "This is wrong"


def test_email_name_reads_sender_and_subject_only() -> None:
    name = email_name(BANK)
    assert name == EmailName(sender="La Banque Postale", subject="Votre compte sera bloque")
    assert "BODY_SECRET" not in name.sender + name.subject


def test_email_name_falls_back_to_address_then_nothing() -> None:
    assert email_name("From: alerts@bank.test\n\nhi").sender == "alerts@bank.test"
    assert email_name("Your parcel is waiting. Pay now.") == EmailName()


def test_email_name_is_capped() -> None:
    name = email_name("From: " + "A" * 200 + " <a@b.test>\nSubject: " + "S" * 200)
    assert len(name.sender) <= NAME_LIMIT
    assert len(name.subject) <= NAME_LIMIT


def test_harm_line_names_sender_and_target() -> None:
    reasons = ["Ask: it wants a password, code, or card number."]
    line = harm_line("likely_scam", email_name(BANK), reasons)
    assert line == "The email from 'La Banque Postale' may be trying to take your password."


def test_harm_line_uses_subject_without_sender() -> None:
    line = harm_line("likely_scam", EmailName(subject="Colis en attente"), ["Ask: pay the fee."])
    assert line == "The email 'Colis en attente' may be trying to take your money."


def test_harm_line_without_headers() -> None:
    assert harm_line("likely_scam", EmailName(), []).startswith("This message may be trying to take")
    assert harm_line("ok", EmailName(sender="Mum")) == "We did not see a scam trick in the email from 'Mum'."
    assert "is off" in harm_line("suspicious", EmailName())


def test_warning_has_no_reasons_and_no_copy_summary() -> None:
    view = build_share_result(
        _result("likely_scam", ["Ask: it wants a password.", "Links: a lookalike host."]),
        email_name(BANK),
    )
    assert not hasattr(view, "reasons")
    assert not hasattr(share_card, "format_share_result")
    assert not hasattr(share_card, "COPY_LABEL")
    html = render_share_result_html(view)
    assert "warn-reason" not in html
    assert "Lookalike" not in html
    source = APP.read_text(encoding="utf-8")
    assert "Copy summary" not in source
    assert "copy-summary" not in source


def test_body_never_reaches_the_screen() -> None:
    secret = "UNIQUE_TAIL_NOT_ON_SCREEN"
    message = BANK + "\n" + secret
    result = _result(
        "suspicious",
        [secret],
        summary=secret,
        steps=[StepResult(id="ask", title="1", status="done", summary=secret, details=[secret])],
    )
    view = build_share_result(result, email_name(message))
    html = render_share_result_html(view)
    for text in (view.harm, html):
        assert secret not in text
        assert "BODY_SECRET" not in text
        assert "http" not in text


def test_html_escapes_sender() -> None:
    view = build_share_result(_result("likely_scam"), email_name('From: <script>x</script> <a@b.test>'))
    html = render_share_result_html(view)
    assert "<script>" not in html
    escaped = ShareResult(verdict="likely_scam", label="Likely scam", harm="<b>x</b>", action="Don't reply", mark="!")
    assert "&lt;b&gt;" in render_share_result_html(escaped)


def test_this_is_wrong_is_centered_full_width() -> None:
    source = APP.read_text(encoding="utf-8")
    assert 'key="verdict-wrong", type="tertiary", use_container_width=True' in source
    assert 'div[class*="st-key-verdict-wrong"] { display: flex; justify-content: center; }' in source
    assert "margin: 0 auto 1.15rem !important;" in source


def test_fake_bank_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    example = next(item for item in load_fixtures() if item.id == "scam-fake-bank")
    result = classify_message(example.message, allow_search=False)
    view = build_share_result(result, email_name(example.message))
    html = render_share_result_html(view)
    assert result.verdict == "likely_scam"
    assert view.harm == (
        "The email from 'National Example Bank Security' may be trying to take your password."
    )
    assert "We detected unusual activity" not in html
    assert "http" not in html
