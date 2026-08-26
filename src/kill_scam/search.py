"""Allowlisted HTTP only. Never fetch a pasted destination URL."""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger("kill_scam")

ALLOWED_SEARCH_HOSTS = frozenset(
    {
        "html.duckduckgo.com",
        "lite.duckduckgo.com",
        "api.duckduckgo.com",
    }
)

GUIDANCE_SITES = (
    "cybermalveillance.gouv.fr",
    "service-public.fr",
    "signal-spam.fr",
    "cisa.gov",
    "consumer.ftc.gov",
    "ftc.gov",
)


class UnsafeFetchError(RuntimeError):
    """Outbound HTTP to a host that is not on the search allowlist."""


def host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().rstrip(".")
    except Exception:
        return ""


def assert_allowlisted(url: str) -> str:
    host = host_of(url)
    if host not in ALLOWED_SEARCH_HOSTS:
        raise UnsafeFetchError(
            f"Refusing to fetch {host or url}. Kill Scam only queries known search hosts, "
            "never a link from the pasted message."
        )
    return host


def safe_get(url: str, *, timeout: float = 5.0) -> str:
    """GET only allowlisted search hosts. Timeouts become empty text, not a crash."""
    assert_allowlisted(url)
    request = Request(
        url,
        headers={"User-Agent": "KillScam/0.1 (defensive checklist; +https://github.com/paula-strunz/kill-scam)"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 — host allowlisted above
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read(80_000).decode(charset, errors="replace")
    except UnsafeFetchError:
        raise
    except Exception:
        logger.info("Guidance search request failed. Continuing with the local list.")
        return ""
