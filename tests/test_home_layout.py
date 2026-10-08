"""Paste-first home when Gmail is not configured, and the offline sample filler."""

from __future__ import annotations

from pathlib import Path

import pytest

from kill_scam.evals import load_fixtures
from kill_scam.home_layout import (
    GMAIL_OPTIONAL_NOTE,
    SAFETY_CAPTION,
    SAMPLE_FIXTURE_ID,
    home_layout,
    sample_fixture_message,
)

APP_SOURCE = Path(__file__).resolve().parents[1] / "src" / "kill_scam" / "app.py"


def test_paste_is_primary_when_gmail_is_not_configured() -> None:
    layout = home_layout(False)
    assert layout.paste_primary is True
    assert "Paste a suspicious message" in layout.headline
    assert "five checks" in layout.intro
    assert "Check this message" in layout.intro
    assert layout.french_line
    assert "lien" in layout.french_line


def test_gmail_stays_first_when_configured() -> None:
    layout = home_layout(True)
    assert layout.paste_primary is False
    assert layout.headline.startswith("Connect Gmail")
    assert "five checks" in layout.intro
    assert layout.french_line == ""


def test_sample_fixture_is_offline_scam_fake_bank() -> None:
    body = sample_fixture_message()
    match = next(item for item in load_fixtures() if item.id == SAMPLE_FIXTURE_ID)
    assert SAMPLE_FIXTURE_ID == "scam-fake-bank"
    assert body == match.message.strip()
    assert "nat-example-bank-secure.test" in body
    assert "no network" in (sample_fixture_message.__doc__ or "").lower()


def test_sample_fixture_rejects_unknown_id() -> None:
    with pytest.raises(LookupError, match="offline sample file"):
        sample_fixture_message("does-not-exist")


def test_app_uses_layout_branch_and_keeps_safety_captions() -> None:
    source = APP_SOURCE.read_text(encoding="utf-8")
    assert "home_layout(" in source
    assert "layout.paste_primary" in source
    assert "Try a sample" in source
    assert "sample_fixture_message" in source
    assert SAFETY_CAPTION.split(".")[0] in source or "SAFETY_CAPTION" in source
    assert "never deletes mail" in SAFETY_CAPTION
    assert "optional" in GMAIL_OPTIONAL_NOTE
    assert "isn’t set up yet" in GMAIL_OPTIONAL_NOTE
    assert "This is a helper, not a guarantee." in source
    assert "Do not click any links" in source
    assert "It never sends mail" in SAFETY_CAPTION
