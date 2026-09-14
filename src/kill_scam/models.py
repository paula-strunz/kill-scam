"""Structured result of one scam check."""

from __future__ import annotations

from dataclasses import dataclass, field

VERDICTS = ("ok", "suspicious", "likely_scam")

VERDICT_LABELS = {
    "ok": "Looks OK",
    "suspicious": "Be careful",
    "likely_scam": "Likely a scam",
}

VERDICT_ALIASES = {
    "ok": "ok",
    "safe": "ok",
    "ham": "ok",
    "not_scam": "ok",
    "not a scam": "ok",
    "looks ok": "ok",
    "suspicious": "suspicious",
    "caution": "suspicious",
    "be careful": "suspicious",
    "likely_scam": "likely_scam",
    "likely scam": "likely_scam",
    "scam": "likely_scam",
    "phishing": "likely_scam",
}

STEP_IDS = ("ask", "identity", "links", "campaigns", "verdict")

STEP_TITLES = {
    "ask": "1. What does it want you to do?",
    "identity": "2. Who does it claim to be?",
    "links": "3. Check the web addresses (we do not open them)",
    "campaigns": "4. Known scam patterns",
    "verdict": "5. Verdict and what to do",
}


@dataclass
class StepResult:
    id: str
    title: str
    status: str
    summary: str = ""
    details: list[str] = field(default_factory=list)

    def as_public_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "summary": self.summary,
            "detail_count": len(self.details),
        }


@dataclass
class CheckResult:
    verdict: str
    summary: str
    reasons: list[str] = field(default_factory=list)
    advice: str = ""
    steps: list[StepResult] = field(default_factory=list)
    search_used: bool = False
    message_hash: str = ""

    @property
    def label(self) -> str:
        return VERDICT_LABELS.get(self.verdict, self.verdict)


class MissingApiKeyError(RuntimeError):
    """Optional wording helper is off. The checklist itself does not need a key."""

    user_message = (
        "Wording polish needs an OpenAI key. The five checks still run without it."
    )


class CheckError(RuntimeError):
    """User-facing failure while checking a message."""
