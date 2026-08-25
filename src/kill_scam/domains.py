"""Official-domain list and lookalike checks. Never fetch a destination URL."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Public suffixes where the registrable name has three labels (e.g. impots.gouv.fr).
_MULTI_PART_SUFFIXES = frozenset(
    {
        ("gouv", "fr"),
        ("com", "fr"),
        ("asso", "fr"),
        ("co", "uk"),
        ("gov", "uk"),
        ("ac", "uk"),
        ("org", "uk"),
        ("com", "au"),
        ("gov", "au"),
        ("co", "jp"),
        ("co", "in"),
        ("com", "br"),
    }
)

# Known URL shorteners. Opening them would visit the trap; we only flag the host.
SHORTENER_DOMAINS = frozenset(
    {
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "goo.gl",
        "ow.ly",
        "is.gd",
        "cutt.ly",
        "rebrand.ly",
        "tiny.cc",
        "lnkd.in",
        "buff.ly",
        "rb.gy",
        "t.ly",
        "shorturl.at",
        "s.id",
        "trib.al",
    }
)


@dataclass(frozen=True)
class OfficialOrg:
    org_id: str
    names: tuple[str, ...]
    domains: tuple[str, ...]
    region: str = ""


# Curated official sites only. Display names in a message are never trusted.
OFFICIAL_ORGS: tuple[OfficialOrg, ...] = (
    OfficialOrg("dgfip", ("impôts", "impots", "dgfip", "finances publiques", "tax office"), ("impots.gouv.fr",), "FR"),
    OfficialOrg("service_public", ("service-public", "service public"), ("service-public.fr",), "FR"),
    OfficialOrg("cybermalveillance", ("cybermalveillance",), ("cybermalveillance.gouv.fr",), "FR"),
    OfficialOrg("la_poste", ("la poste", "laposte", "colissimo"), ("laposte.fr",), "FR"),
    OfficialOrg("chronopost", ("chronopost",), ("chronopost.fr",), "FR"),
    OfficialOrg("edf", ("edf", "électricité de france", "electricite de france"), ("edf.fr",), "FR"),
    OfficialOrg("caf", ("caf", "caisse d'allocations", "allocations familiales"), ("caf.fr",), "FR"),
    OfficialOrg("ameli", ("ameli", "assurance maladie", "cpam"), ("ameli.fr",), "FR"),
    OfficialOrg("urssaf", ("urssaf",), ("urssaf.fr",), "FR"),
    OfficialOrg("cpf", ("cpf", "mon compte formation", "moncompteformation"), ("moncompteformation.gouv.fr",), "FR"),
    OfficialOrg("france_travail", ("france travail", "pôle emploi", "pole emploi"), ("francetravail.fr", "pole-emploi.fr"), "FR"),
    OfficialOrg("ants", ("ants", "permis de conduire"), ("ants.gouv.fr",), "FR"),
    OfficialOrg(
        "banque_postale",
        ("la banque postale", "banque postale"),
        ("labanquepostale.fr",),
        "FR",
    ),
    OfficialOrg("societe_generale", ("société générale", "societe generale"), ("societegenerale.fr", "societe-generale.fr"), "FR"),
    OfficialOrg("bnp", ("bnp paribas", "bnp"), ("bnpparibas.net", "mabanque.bnpparibas"), "FR"),
    OfficialOrg("credit_agricole", ("crédit agricole", "credit agricole"), ("credit-agricole.fr",), "FR"),
    OfficialOrg("credit_mutuel", ("crédit mutuel", "credit mutuel"), ("creditmutuel.fr",), "FR"),
    OfficialOrg("caisse_epargne", ("caisse d'épargne", "caisse d'epargne"), ("caisse-epargne.fr",), "FR"),
    OfficialOrg("microsoft", ("microsoft", "outlook", "xbox", "onedrive"), ("microsoft.com", "microsoftonline.com", "live.com", "office.com", "outlook.com"), "US"),
    OfficialOrg("apple", ("apple", "icloud", "app store"), ("apple.com", "icloud.com", "appleid.apple.com"), "US"),
    OfficialOrg("paypal", ("paypal",), ("paypal.com", "paypal.fr"), ""),
    OfficialOrg("amazon", ("amazon",), ("amazon.fr", "amazon.com"), ""),
    OfficialOrg("orange", ("orange",), ("orange.fr",), "FR"),
    OfficialOrg("sfr", ("sfr",), ("sfr.fr",), "FR"),
    OfficialOrg("cisa", ("cisa",), ("cisa.gov",), "US"),
    OfficialOrg("ftc", ("ftc", "federal trade commission"), ("ftc.gov", "consumer.ftc.gov"), "US"),
    OfficialOrg("signal_spam", ("signal-spam", "signal spam"), ("signal-spam.fr",), "FR"),
)


def all_official_domains() -> frozenset[str]:
    domains: set[str] = set()
    for org in OFFICIAL_ORGS:
        domains.update(decode_host(item) for item in org.domains)
    return frozenset(domains)


def decode_host(host: str) -> str:
    text = (host or "").strip().lower().rstrip(".")
    if not text:
        return ""
    try:
        return text.encode("ascii").decode("idna")
    except Exception:
        return text


def has_punycode(host: str) -> bool:
    return "xn--" in (host or "").lower()


def registered_domain(host: str) -> str:
    host_n = decode_host(host)
    parts = [part for part in host_n.split(".") if part]
    if len(parts) >= 3 and (parts[-2], parts[-1]) in _MULTI_PART_SUFFIXES:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host_n


def is_host_under(host: str, official: str) -> bool:
    host_n = decode_host(host)
    off_n = decode_host(official)
    if not host_n or not off_n:
        return False
    return host_n == off_n or host_n.endswith("." + off_n)


def is_official_host(host: str, official_domains: list[str] | frozenset[str] | tuple[str, ...]) -> bool:
    return any(is_host_under(host, official) for official in official_domains)


def is_shortener_host(host: str) -> bool:
    host_n = decode_host(host)
    return any(is_host_under(host_n, short) for short in SHORTENER_DOMAINS)


def levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, lch in enumerate(left, start=1):
        current = [i]
        for j, rch in enumerate(right, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            swap = previous[j - 1] + (lch != rch)
            current.append(min(insert, delete, swap))
        previous = current
    return previous[-1]


def _alnum(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", decode_host(text))


def is_lookalike(host: str, official: str) -> bool:
    """True when *host* pretends to be *official* but is not that site."""
    host_n = decode_host(host)
    off_n = decode_host(official)
    if not host_n or not off_n:
        return False
    if is_host_under(host_n, off_n):
        return False

    host_reg = registered_domain(host_n)
    dotted = f".{host_n}."
    if host_n.startswith(off_n + ".") or f".{off_n}." in dotted:
        return True
    if _alnum(host_reg) == _alnum(off_n) and host_reg != off_n:
        return True

    host_tokens = host_n.replace("-", ".").split(".")
    off_labels = off_n.split(".")
    if off_labels[0] in host_tokens and len(off_labels) >= 2:
        smashed = host_n.replace("-", ".")
        if all(label in smashed for label in off_labels[:2]):
            return True

    if min(len(host_reg), len(off_n)) >= 5 and 0 < levenshtein(host_reg, off_n) <= 2:
        return True
    return False


def lookalikes_against_list(host: str, officials: list[str] | frozenset[str] | tuple[str, ...]) -> list[str]:
    found = []
    for official in officials:
        if is_lookalike(host, official):
            found.append(decode_host(official))
    return found


def find_claimed_orgs(text: str) -> list[OfficialOrg]:
    blob = (text or "").lower()
    hits: list[OfficialOrg] = []
    for org in OFFICIAL_ORGS:
        for name in sorted(org.names, key=len, reverse=True):
            if _name_in_text(name, blob):
                hits.append(org)
                break
    return hits


def _name_in_text(name: str, blob: str) -> bool:
    if " " in name or "-" in name or "'" in name:
        return name.lower() in blob
    return re.search(rf"\b{re.escape(name.lower())}\b", blob) is not None
