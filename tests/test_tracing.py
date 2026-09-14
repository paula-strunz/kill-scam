from __future__ import annotations

from kill_scam.config import PROJECT_NAME, arize_is_configured
from kill_scam.tracing import init_tracing, start_check_span, tracing_enabled


def test_tracing_is_off_without_arize_keys(monkeypatch) -> None:
    monkeypatch.delenv("ARIZE_API_KEY", raising=False)
    monkeypatch.delenv("ARIZE_SPACE_ID", raising=False)
    monkeypatch.delenv("ARIZE_SPACE", raising=False)
    from kill_scam import tracing as tracing_mod

    tracing_mod._STATE["tried"] = False
    tracing_mod._STATE["enabled"] = False
    assert arize_is_configured() is False
    assert init_tracing() is False
    assert tracing_enabled() is False
    with start_check_span("paste", 12) as span:
        assert span is None
    assert PROJECT_NAME == "kill-scam"
