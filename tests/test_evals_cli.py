from __future__ import annotations

from kill_scam.evals import load_fixtures, main


def test_eval_cli_scores_local_checklist(monkeypatch, capsys) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    code = main([])
    output = capsys.readouterr().out
    assert "synthetic fixtures" in output.lower()
    assert "missed scams" in output.lower()
    assert load_fixtures()
    assert code in {0, 1}
