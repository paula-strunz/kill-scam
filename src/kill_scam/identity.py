"""Step 2: who the message claims to be. Never trust the display name."""

from __future__ import annotations

import re
from dataclasses import dataclass

from kill_scam.domains import (
    OfficialOrg,
    decode_host,
    find_claimed_orgs,
    is_official_host,
    lookalikes_against_list,
    registered_domain,
)

_FROM_LINE = re.compile(
    r"(?im)^From:\s*(?:(?P<name>[^<\n]+?)\s*)?<(?P<email>[^>\s]+)>\s*$"
)
_FROM_EMAIL_ONLY = re.compile(r"(?im)^From:\s*(?P<email>[A-Za-z0-9._%+-]+@[^\s>]+)\s*$")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


@dataclass(frozen=True)
class IdentityReport:
    display_name: str
    address: str
    address_domain: str
    claimed_orgs: tuple[OfficialOrg, ...]
    official_domains: tuple[str, ...]
    findings: tuple[str, ...]
    mismatch: bool = False
    lookalike_sender: bool = False


def extract_identity(text: str) -> IdentityReport:
    display_name, address = _parse_sender(text)
    address_domain = registered_domain(address.split("@", 1)[-1]) if "@" in address else ""
    claimed = tuple(find_claimed_orgs(f"{display_name}\n{text}"))
    official_domains = tuple(
        dict.fromkeys(decode_host(domain) for org in claimed for domain in org.domains)
    )
    findings: list[str] = []
    mismatch = False
    lookalike_sender = False

    if display_name and address:
        findings.append(
            f"It shows the name “{display_name.strip()}” but the real address is {address}."
        )
        findings.append("The name on the screen is not proof. The address matters more.")
    elif address:
        findings.append(f"The sending address is {address}.")
    elif display_name:
        findings.append(f"It claims to be “{display_name.strip()}”, with no email address shown.")
    else:
        findings.append("No From line was found. Treat any claimed name as unproven.")

    if claimed:
        names = ", ".join(sorted({org.names[0] for org in claimed}))
        findings.append(f"It claims to be: {names}.")
        if address_domain and official_domains:
            if is_official_host(address_domain, official_domains) or is_official_host(
                decode_host(address.split("@", 1)[-1]), official_domains
            ):
                findings.append(f"The sending domain {address_domain} matches that organisation’s official site.")
            else:
                looks = lookalikes_against_list(address_domain, official_domains)
                if looks:
                    lookalike_sender = True
                    findings.append(
                        f"The sending domain {address_domain} looks like {looks[0]} but is not official."
                    )
                else:
                    mismatch = True
                    findings.append(
                        f"The sending domain {address_domain} is not the official site "
                        f"({official_domains[0]}). Do not trust the display name."
                    )
    else:
        findings.append("It does not clearly match a known bank, tax office, or delivery firm.")

    return IdentityReport(
        display_name=display_name.strip(),
        address=address,
        address_domain=address_domain,
        claimed_orgs=claimed,
        official_domains=official_domains,
        findings=tuple(findings),
        mismatch=mismatch,
        lookalike_sender=lookalike_sender,
    )


def _parse_sender(text: str) -> tuple[str, str]:
    match = _FROM_LINE.search(text or "")
    if match:
        return (match.group("name") or "").strip().strip('"'), (match.group("email") or "").strip()
    match = _FROM_EMAIL_ONLY.search(text or "")
    if match:
        return "", (match.group("email") or "").strip()
    emails = _EMAIL.findall(text or "")
    if emails:
        return "", emails[0]
    return "", ""
