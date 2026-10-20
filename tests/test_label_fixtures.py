from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

REQUIRED_FIELDS = {"id", "message", "gold_label", "gold_verdict", "category", "notes"}
VERDICT_COUNTS = {"likely_scam": 8, "suspicious": 6, "ok": 6}
ALLOWED_HOSTS = ("example.com", "example.fr")

# Email domains and http(s) hosts. Paths and query strings are not part of the host.
HOST_RE = re.compile(
    r"(?:https?://(?P<url>[A-Za-z0-9.-]+)|@(?P<email>[A-Za-z0-9.-]+\.[A-Za-z]{2,}))",
    re.IGNORECASE,
)


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[1] / "evals" / "fixtures_003_label.json"


def _is_example_host(host: str) -> bool:
    name = host.lower().rstrip(".")
    return any(name == suffix or name.endswith("." + suffix) for suffix in ALLOWED_HOSTS)


def test_label_threshold_fixtures_shape() -> None:
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))
    examples = payload["examples"]

    assert len(examples) == 20
    ids = [item["id"] for item in examples]
    assert len(ids) == len(set(ids))

    verdicts: Counter[str] = Counter()
    hosts: list[str] = []
    for raw in examples:
        assert REQUIRED_FIELDS.issubset(raw)
        for field in REQUIRED_FIELDS:
            assert str(raw[field]).strip()
        verdicts[raw["gold_verdict"]] += 1
        for match in HOST_RE.finditer(raw["message"]):
            hosts.append(match.group("url") or match.group("email"))

    assert dict(verdicts) == VERDICT_COUNTS
    assert hosts
    assert all(_is_example_host(host) for host in hosts)
