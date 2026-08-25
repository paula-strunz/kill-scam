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


@dataclass(frozen=True)
class CheckResult:
    verdict: str
    summary: str
    reasons: list[str] = field(default_factory=list)
    advice: str = ""

    @property
    def label(self) -> str:
        return VERDICT_LABELS.get(self.verdict, self.verdict)


class MissingApiKeyError(RuntimeError):
    """Raised when the checker cannot run because OPENAI_API_KEY is missing."""

    user_message = (
        "This checker needs an OpenAI key to judge the message. "
        "Copy .env.example to .env, add OPENAI_API_KEY, then try again. "
        "You can still paste text; nothing is sent until a key is set."
    )


class CheckError(RuntimeError):
    """User-facing failure while checking a message."""
