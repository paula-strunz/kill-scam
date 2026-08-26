"""Step 4: known campaigns. Local catalog first; optional guidance search."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote_plus

from kill_scam.search import GUIDANCE_SITES, safe_get

CAMPAIGNS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("fake_tax_refund", "fake tax refund / impôts", (r"\bimp[oô]ts\b", r"\bremboursement\b", r"\btax refund\b", r"\bdgfip\b", r"\btax office\b")),
    ("parcel_fees", "parcel / Chronopost / La Poste fees", (r"\bparcel\b", r"\bcolis\b", r"\bchronopost\b", r"\bcolissimo\b", r"\bla poste\b", r"\bdelivery\b")),
    ("energy_bill", "energy bill / EDF", (r"\bedf\b", r"\bénergie\b", r"\benergy bill\b", r"\bfacture\b")),
    ("bank_advisor", "bank advisor", (r"\bconseiller\b", r"\bbank advisor\b", r"\byour account will be (closed|frozen)\b", r"\bunusual activity\b")),
    ("cpf", "CPF / training account", (r"\bcpf\b", r"\bcompte formation\b")),
    ("caf", "CAF / benefits", (r"\bcaf\b", r"\ballocations\b")),
    ("family_emergency", "family emergency money request", (r"\bmom its me\b", r"\bmom it's me\b", r"\bi broke my phone\b", r"\bcar crash\b", r"\bnew number\b")),
    ("credential_theft", "password or one-time code theft", (r"\bmailbox is full\b", r"\b6-digit code\b")),
    ("prize", "too-good-to-be-true prize", (r"\byou won\b", r"\bfélicitations\b", r"\bcongratulations\b", r"\bgift card\b")),
)


@dataclass(frozen=True)
class CampaignHit:
    campaign_id: str
    label: str
    source: str


@dataclass(frozen=True)
class CampaignReport:
    hits: tuple[CampaignHit, ...]
    findings: tuple[str, ...]
    search_attempted: bool
    search_ok: bool

    @property
    def matched(self) -> bool:
        return bool(self.hits)


class NullSearcher:
    """Used in tests and CI. No network."""

    def search(self, query: str) -> list[str]:
        return []


class DuckDuckGoSearcher:
    """Queries DuckDuckGo HTML only (allowlisted host). Never opens pasted links."""

    def search(self, query: str) -> list[str]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        html = safe_get(url)
        if not html:
            return []
        titles = re.findall(r'(?:class="result__a"[^>]*>)([^<]+)', html)
        snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)', html)
        return [re.sub(r"\s+", " ", item).strip() for item in (*titles, *snippets) if item.strip()][:8]


def extract_campaigns(text: str, *, searcher: object | None = None) -> CampaignReport:
    blob = text or ""
    hits: list[CampaignHit] = []
    findings: list[str] = []
    for campaign_id, label, patterns in CAMPAIGNS:
        if any(re.search(pattern, blob, flags=re.IGNORECASE) for pattern in patterns):
            hits.append(CampaignHit(campaign_id, label, "local_list"))
            findings.append(f"This matches a known pattern: {label}.")

    search_attempted = False
    search_ok = False
    if searcher is not None and not isinstance(searcher, NullSearcher) and hits:
        search_attempted = True
        try:
            keywords = hits[0].label
            site = GUIDANCE_SITES[0]
            results = searcher.search(f"site:{site} {keywords}")
            search_ok = True
            if results:
                snippet = results[0][:180]
                findings.append(f"Live guidance search ({site}): {snippet}")
                hits.append(CampaignHit(hits[0].campaign_id, hits[0].label, "web_search"))
            else:
                findings.append(
                    f"Live guidance search on {site} returned nothing extra. "
                    "Using the built-in list only."
                )
        except Exception:
            search_ok = False
            findings.append(
                "Live guidance search failed. Continuing with the built-in list. "
                "Treat this result with a bit less confidence."
            )
    elif isinstance(searcher, NullSearcher):
        findings.append("Live guidance search was skipped. Using the built-in list only.")

    if not hits:
        findings.append("No well-known tax / parcel / bank / CAF campaign jumped out.")

    return CampaignReport(
        hits=tuple(hits),
        findings=tuple(findings),
        search_attempted=search_attempted,
        search_ok=search_ok,
    )
