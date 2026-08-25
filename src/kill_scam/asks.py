"""Step 1: what the message wants the person to do."""

from __future__ import annotations

import re
from dataclasses import dataclass

ASK_KINDS = ("click", "pay", "code", "install", "silence")

_PATTERNS: dict[str, tuple[str, ...]] = {
    "click": (
        r"\bclick\b",
        r"\btap\b",
        r"\bcliquez\b",
        r"\bcliquer\b",
        r"\bverify (your )?account\b",
        r"\bconfirmez\b",
        r"\bconfirm (your )?(identity|account|password)\b",
        r"\bsign in\b",
        r"\blog[- ]?in\b",
        r"https?://",
        r"\bwww\.",
    ),
    "pay": (
        r"\bpay\b",
        r"\bpayment\b",
        r"\bpayer\b",
        r"\bvirement\b",
        r"\bwires?\b",
        r"\bgift cards?\b",
        r"\bcartes? cadeaux\b",
        r"\bbitcoin\b",
        r"\bcrypto\b",
        r"\bcash ?app\b",
        r"\bwestern union\b",
        r"\bfrais\b",
        r"\brelease fee\b",
        r"\bsend .{0,20}(money|\$|€)",
        r"\bneed \$\d+",
    ),
    "code": (
        r"\bpassword\b",
        r"\bmot de passe\b",
        r"\bone[- ]time code\b",
        r"\b6[- ]digit\b",
        r"\botp\b",
        r"\bcvv\b",
        r"\bpin\b",
        r"\bidentifiant\b",
        r"\bcard number\b",
        r"\bnuméro de carte\b",
    ),
    "install": (
        r"\banydesk\b",
        r"\bteamviewer\b",
        r"\binstall (the )?app\b",
        r"\binstaller l['’]application\b",
        r"\bremote access\b",
        r"\bcontrôle à distance\b",
    ),
    "silence": (
        r"\bdo not tell\b",
        r"\bdon't tell\b",
        r"\bdon['’]t tell\b",
        r"\bne dites rien\b",
        r"\bne prévenez pas\b",
        r"\bne prevenez pas\b",
        r"\bkeep this secret\b",
        r"\bdo not call\b",
        r"\bne pas appeler\b",
    ),
}

_NEGATION = (
    "not ",
    "n't ",
    "never ",
    "no ",
    "pas ",
    "jamais",
    "aucune",
    "won't",
    "will not",
    "ne vous",
    "do not ask",
    "n'est demand",
    "aucune action",
    "no action",
    "no payment",
    "pas de paiement",
)

_KIND_LABELS = {
    "click": "click a link or sign in",
    "pay": "pay or send money",
    "code": "give a password, code, or card number",
    "install": "install an app or remote-access tool",
    "silence": "stay silent / not tell anyone",
}


@dataclass(frozen=True)
class AskReport:
    kinds: tuple[str, ...]
    findings: tuple[str, ...]

    @property
    def pressure(self) -> bool:
        return bool(self.kinds)


def extract_asks(text: str) -> AskReport:
    blob = text or ""
    kinds: list[str] = []
    findings: list[str] = []
    for kind, patterns in _PATTERNS.items():
        if _kind_present(blob, patterns):
            kinds.append(kind)
            findings.append(f"It wants you to {_KIND_LABELS[kind]}.")
    if not kinds:
        findings.append("It does not clearly ask you to click, pay, give a code, or stay silent.")
    return AskReport(kinds=tuple(kinds), findings=tuple(findings))


def _kind_present(text: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            if not _is_negated(text, match.start()):
                return True
    return False


def _is_negated(text: str, start: int) -> bool:
    window = text[max(0, start - 48) : start].lower()
    return any(token in window for token in _NEGATION)
