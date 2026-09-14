"""Classification eval path: missed scams vs false alarms.

Fixture JSON is shaped so it can later become an Arize dataset:
id, message, gold_label, gold_verdict, category.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from kill_scam.models import CheckResult

GOLD_SCAM = "scam"
GOLD_HAM = "ham"
CAUGHT_VERDICTS = {"suspicious", "likely_scam"}


@dataclass(frozen=True)
class Example:
    id: str
    message: str
    gold_label: str
    gold_verdict: str
    category: str
    notes: str = ""


@dataclass(frozen=True)
class ScoredExample:
    example: Example
    predicted: str
    missed_scam: bool
    false_alarm: bool
    caught_scam: bool
    true_ham: bool


@dataclass(frozen=True)
class EvalReport:
    total: int
    scam_count: int
    ham_count: int
    missed_scams: int
    false_alarms: int
    caught_scams: int
    true_ham: int
    rows: list[ScoredExample]

    @property
    def missed_scam_rate(self) -> float:
        return self.missed_scams / self.scam_count if self.scam_count else 0.0

    @property
    def false_alarm_rate(self) -> float:
        return self.false_alarms / self.ham_count if self.ham_count else 0.0


def fixture_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "fixtures.json"


def load_fixtures(path: Path | None = None) -> list[Example]:
    target = path or fixture_path()
    payload = json.loads(target.read_text(encoding="utf-8"))
    examples = []
    for raw in payload["examples"]:
        examples.append(
            Example(
                id=str(raw["id"]),
                message=str(raw["message"]),
                gold_label=str(raw["gold_label"]),
                gold_verdict=str(raw["gold_verdict"]),
                category=str(raw.get("category", "")),
                notes=str(raw.get("notes", "")),
            )
        )
    return examples


def score_predictions(
    examples: Sequence[Example],
    predictions: Sequence[str],
) -> EvalReport:
    if len(examples) != len(predictions):
        raise ValueError("Each example needs exactly one predicted verdict.")

    rows: list[ScoredExample] = []
    missed = false_alarms = caught = true_ham = scam_count = ham_count = 0

    for example, predicted in zip(examples, predictions, strict=True):
        is_scam = example.gold_label == GOLD_SCAM
        is_ham = example.gold_label == GOLD_HAM
        missed_scam = is_scam and predicted == "ok"
        false_alarm = is_ham and predicted in CAUGHT_VERDICTS
        caught_scam = is_scam and predicted in CAUGHT_VERDICTS
        ham_ok = is_ham and predicted == "ok"
        if is_scam:
            scam_count += 1
        if is_ham:
            ham_count += 1
        if missed_scam:
            missed += 1
        if false_alarm:
            false_alarms += 1
        if caught_scam:
            caught += 1
        if ham_ok:
            true_ham += 1
        rows.append(
            ScoredExample(
                example=example,
                predicted=predicted,
                missed_scam=missed_scam,
                false_alarm=false_alarm,
                caught_scam=caught_scam,
                true_ham=ham_ok,
            )
        )

    return EvalReport(
        total=len(examples),
        scam_count=scam_count,
        ham_count=ham_count,
        missed_scams=missed,
        false_alarms=false_alarms,
        caught_scams=caught,
        true_ham=true_ham,
        rows=rows,
    )


def run_eval(
    classify: Callable[[str], CheckResult] | None = None,
    path: Path | None = None,
) -> EvalReport:
    examples = load_fixtures(path)
    if classify is None:
        from kill_scam.agent import classify_message

        def classify(message: str) -> CheckResult:
            return classify_message(message, source="eval", allow_search=False)

    predictions = [classify(example.message).verdict for example in examples]
    return score_predictions(examples, predictions)


def format_report(report: EvalReport) -> str:
    lines = [
        "Kill Scam classification eval",
        f"  examples: {report.total} ({report.scam_count} scam, {report.ham_count} ham)",
        f"  missed scams: {report.missed_scams} ({report.missed_scam_rate:.0%})",
        f"  false alarms: {report.false_alarms} ({report.false_alarm_rate:.0%})",
        f"  caught scams: {report.caught_scams}",
        f"  true ham: {report.true_ham}",
    ]
    problems = [row for row in report.rows if row.missed_scam or row.false_alarm]
    if problems:
        lines.append("  problems:")
        for row in problems:
            kind = "missed scam" if row.missed_scam else "false alarm"
            lines.append(f"    - {row.example.id}: {kind} (predicted {row.predicted})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    from kill_scam.config import load_env

    load_env()
    parser = argparse.ArgumentParser(
        description="Score Kill Scam fixtures: missed scams vs false alarms."
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Path to fixtures JSON (default: evals/fixtures.json)",
    )
    args = parser.parse_args(argv)

    examples = load_fixtures(args.fixtures)
    print(f"Loaded {len(examples)} synthetic fixtures from {args.fixtures or fixture_path()}")
    print("Scoring the local five-step checklist (no live web search).")
    report = run_eval(path=args.fixtures)
    print(format_report(report))
    return 1 if report.missed_scams else 0


if __name__ == "__main__":
    sys.exit(main())
