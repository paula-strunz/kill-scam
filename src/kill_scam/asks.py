"""Step 1: what the message wants the person to do, and which hook it uses."""

from __future__ import annotations

import re
from dataclasses import dataclass

ASK_KINDS = ("click", "pay", "code", "install", "silence")

# PRD table: name the psychological hook when it is in the text.
HOOK_IDS = (
    "authority",
    "fear_loss",
    "fake_confirmation",
    "reward",
    "urgency",
    "liking",
    "reciprocity",
    "curiosity",
)

HOOK_LABELS = {
    "authority": "authority",
    "fear_loss": "fear / loss",
    "fake_confirmation": "fake confirmation",
    "reward": "reward",
    "urgency": "urgency",
    "liking": "liking / familiarity",
    "reciprocity": "reciprocity",
    "curiosity": "curiosity",
}

HOOK_WHY = {
    "authority": "it sounds like an official office or a company that can lock your account",
    "fear_loss": "it says you will lose money, a parcel, or access if you do not act",
    "fake_confirmation": "it says you already bought or approved something, and should cancel it",
    "reward": "it offers a refund, trop-perçu, or prize",
    "urgency": "it wants you to act right now (24h, last warning, today)",
    "liking": "it looks like a brand or person you already trust",
    "reciprocity": "it offers to help you undo a problem",
    "curiosity": "it wants you to open an invoice or document",
}

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

_HOOK_PATTERNS: dict[str, tuple[str, ...]] = {
    "authority": (
        r"\bimp[oô]ts\b",
        r"\bdgfip\b",
        r"\btax office\b",
        r"\binternal revenue\b",
        r"\birs\b",
        r"\byour bank\b",
        r"\bbanque\b",
        r"\bsecurity team\b",
        r"\bmicrosoft\b",
        r"\badministration\b",
        r"\bpolice\b",
        r"\bgouvernement\b",
        r"\bgovernment\b",
        r"\bfinances publiques\b",
        r"\btrésorerie\b",
    ),
    "fear_loss": (
        r"\bunpaid\b",
        r"\baccount will (be )?(close|frozen|suspend)",
        r"\bwill be (closed|frozen|deleted|suspended)\b",
        r"\byou were charged\b",
        r"\byou have been charged\b",
        r"\bdébité\b",
        r"\bfacture impay",
        r"\bbloqué\b",
        r"\bwill lose\b",
        r"\bunless you\b",
        r"\bor your (account|package|parcel|colis)\b",
        r"\bsera fermé\b",
        r"\bsuspendu\b",
    ),
    "fake_confirmation": (
        r"\byou already (bought|purchased|ordered|paid)\b",
        r"\byou (bought|purchased|ordered) this\b",
        r"\bclick to cancel\b",
        r"\bcancel (this|the) (order|purchase|transaction)\b",
        r"\bannuler (cette|la) commande\b",
        r"\bvous avez acheté\b",
        r"\bunrecognized (purchase|transaction|charge)\b",
        r"\btransaction (you|that you)\b",
        r"\bsi ce n['’]est pas vous\b",
    ),
    "reward": (
        r"\brefund\b",
        r"\btrop[- ]?per[cç]u\b",
        r"\bremboursement\b",
        r"\byou won\b",
        r"\byou have won\b",
        r"\bfélicitations\b",
        r"\bcongratulations\b",
        r"\bprize\b",
        r"\bgift card\b",
        r"\bcarte cadeau\b",
    ),
    "urgency": (
        r"\bact now\b",
        r"\bimmediately\b",
        r"\bimmédiatement\b",
        r"\bwithin 24\b",
        r"\b24h\b",
        r"\b24 heures\b",
        r"\blast warning\b",
        r"\bderni[eè]re (relance|avertissement|chance)\b",
        r"\bexpires?\b",
        r"\btoday only\b",
        r"\burgent\b",
        r"\baujourd['’]hui\b",
        r"\bright now\b",
        r"\btonight\b",
        r"\bdans les \d+",
    ),
    "liking": (
        r"\bla poste\b",
        r"\bchronopost\b",
        r"\bcolissimo\b",
        r"\bamazon\b",
        r"\bpaypal\b",
        r"\bnetflix\b",
        r"\bwhatsapp\b",
        r"\bapple\b",
        r"\bicloud\b",
        r"\bbanque postale\b",
        r"\byour usual\b",
        r"\bespace habituel\b",
    ),
    "reciprocity": (
        r"\bwe('ll| will) help you\b",
        r"\bwe can (undo|help|fix|cancel)\b",
        r"\bto help you\b",
        r"\bpour vous aider\b",
        r"\bnous (allons|pouvons) vous aider\b",
        r"\bcancel (it )?for you\b",
        r"\bwe('ve| have) paused\b",
        r"\bnous avons mis en pause\b",
    ),
    "curiosity": (
        r"\binvoice attached\b",
        r"\bopen the (document|invoice|attachment|file)\b",
        r"\bview (the )?(document|invoice|attachment)\b",
        r"\bpi[eè]ce jointe\b",
        r"\bouvrir le document\b",
        r"\bvoir (la facture|le document)\b",
        r"\btélécharger (le |la )?(document|facture|pdf)\b",
        r"\bdocument to open\b",
        r"\bsee the invoice\b",
    ),
}


@dataclass(frozen=True)
class AskReport:
    kinds: tuple[str, ...]
    findings: tuple[str, ...]
    hooks: tuple[str, ...] = ()

    @property
    def pressure(self) -> bool:
        return bool(self.kinds)


def extract_asks(text: str) -> AskReport:
    blob = text or ""
    kinds: list[str] = []
    findings: list[str] = []
    hooks: list[str] = []
    for kind, patterns in _PATTERNS.items():
        if _kind_present(blob, patterns):
            kinds.append(kind)
            findings.append(f"It wants you to {_KIND_LABELS[kind]}.")
    for hook, patterns in _HOOK_PATTERNS.items():
        if _kind_present(blob, patterns):
            hooks.append(hook)
            findings.append(f"Persuasion hook: {HOOK_LABELS[hook]} — {HOOK_WHY[hook]}.")
    if not kinds:
        findings.insert(
            0,
            "It does not clearly ask you to click, pay, give a code, or stay silent.",
        )
    return AskReport(kinds=tuple(kinds), findings=tuple(findings), hooks=tuple(hooks))


def _kind_present(text: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            if not _is_negated(text, match.start()):
                return True
    return False


def _is_negated(text: str, start: int) -> bool:
    window = text[max(0, start - 48) : start].lower()
    return any(token in window for token in _NEGATION)
