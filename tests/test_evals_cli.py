from __future__ import annotations

from kill_scam.evals import main


def test_eval_cli_skips_live_scoring_without_key(monkeypatch, capsys) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "synthetic fixtures" in output.lower()
    assert "skipped" in output.lower()
