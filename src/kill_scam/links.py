"""Extract and inspect URLs without fetching the destination."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from kill_scam.domains import (
    all_official_domains,
    decode_host,
    has_punycode,
    is_official_host,
    is_shortener_host,
    lookalikes_against_list,
    registered_domain,
)

# http(s) and www. only — we never turn these into network requests.
_URL_RE = re.compile(
    r"""(?xi)
    (?:
        (?P<full>https?://[^\s<>"'\]\)]+)
        | (?P<www>www\.[^\s<>"'\]\)]+)
    )
    """
)


class UnsafeFetchError(RuntimeError):
    """Raised if code tries to fetch a destination that may be a trap."""


@dataclass(frozen=True)
class InspectedLink:
    raw: str
    host: str
    registered: str
    punycode: bool
    shortener: bool
    official_match: bool
    lookalike_of: tuple[str, ...] = ()


@dataclass(frozen=True)
class LinkReport:
    links: tuple[InspectedLink, ...] = ()
    findings: tuple[str, ...] = ()
    fetched: bool = False  # must always stay False

    @property
    def has_lookalike(self) -> bool:
        return any(item.lookalike_of for item in self.links)

    @property
    def has_shortener(self) -> bool:
        return any(item.shortener for item in self.links)

    @property
    def unofficial_click_targets(self) -> tuple[InspectedLink, ...]:
        return tuple(
            item
            for item in self.links
            if not item.official_match and not item.shortener
        )


def extract_urls(text: str) -> list[str]:
    found: list[str] = []
    for match in _URL_RE.finditer(text or ""):
        raw = match.group("full") or match.group("www") or ""
        cleaned = _trim_url(raw)
        if cleaned and cleaned not in found:
            found.append(cleaned)
    return found


def inspect_links(
    text: str,
    *,
    claimed_official_domains: list[str] | None = None,
) -> LinkReport:
    """Parse hosts and compare to official domains. Does not HTTP-GET anything."""
    officials = list(claimed_official_domains or [])
    catalog = list(all_official_domains())
    compare_against = list(dict.fromkeys(officials + catalog))

    inspected: list[InspectedLink] = []
    findings: list[str] = []
    for raw in extract_urls(text):
        host = _host_of(raw)
        if not host:
            findings.append(f"We found a link but could not read its website name: {raw}")
            continue
        lookalikes = tuple(lookalikes_against_list(host, compare_against))
        official = is_official_host(host, compare_against)
        item = InspectedLink(
            raw=raw,
            host=host,
            registered=registered_domain(host),
            punycode=has_punycode(host) or has_punycode(raw),
            shortener=is_shortener_host(host),
            official_match=official,
            lookalike_of=lookalikes,
        )
        inspected.append(item)
        findings.extend(_findings_for(item))

    if not inspected:
        findings.append("No web address was found in the message.")

    return LinkReport(links=tuple(inspected), findings=tuple(findings), fetched=False)


def _findings_for(item: InspectedLink) -> list[str]:
    notes: list[str] = []
    if item.punycode:
        notes.append(
            f"The address {item.host} uses a coded international spelling (punycode). "
            "That is a common lookalike trick."
        )
    if item.shortener:
        notes.append(
            f"{item.host} is a short link. Short links hide the real website. Do not open it."
        )
    if item.lookalike_of:
        official = item.lookalike_of[0]
        notes.append(
            f"The address {item.registered} looks like {official} but is not that official site."
        )
    elif item.official_match:
        notes.append(f"{item.host} matches an official website we know.")
    else:
        notes.append(
            f"The address {item.registered} is not on our official-site list. "
            "Do not trust the name shown in the message."
        )
    return notes


def _host_of(raw: str) -> str:
    url = raw if "://" in raw else f"http://{raw}"
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return ""
    return decode_host(host)


def _trim_url(raw: str) -> str:
    return raw.rstrip(".,;:!?)")


def refuse_destination_fetch(url: str) -> None:
    """Hard guard: destination pages must never be fetched."""
    raise UnsafeFetchError(
        f"Kill Scam will not open or download {url}. "
        "We only read the website name in the text."
    )
