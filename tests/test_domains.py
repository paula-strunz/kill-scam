from __future__ import annotations

import pytest

from kill_scam.domains import (
    decode_host,
    has_punycode,
    is_host_under,
    is_lookalike,
    is_official_host,
    is_shortener_host,
    lookalikes_against_list,
    registered_domain,
)
from kill_scam.links import UnsafeFetchError, extract_urls, inspect_links, refuse_destination_fetch
from kill_scam.search import UnsafeFetchError as SearchUnsafeFetchError
from kill_scam.search import assert_allowlisted


def test_registered_domain_handles_gouv_fr() -> None:
    assert registered_domain("www.impots.gouv.fr") == "impots.gouv.fr"
    assert registered_domain("login.microsoftonline.com") == "microsoftonline.com"
    assert registered_domain("mail.edf.fr") == "edf.fr"


def test_official_subdomain_is_not_lookalike() -> None:
    assert is_host_under("mail.edf.fr", "edf.fr")
    assert is_official_host("www.labanquepostale.fr", ["labanquepostale.fr"])
    assert not is_lookalike("www.impots.gouv.fr", "impots.gouv.fr")
    assert not is_lookalike("mail.edf.fr", "edf.fr")


def test_hyphen_lookalike_impots() -> None:
    assert is_lookalike("impots-gouv.fr", "impots.gouv.fr")
    assert "impots.gouv.fr" in lookalikes_against_list("impots-gouv.fr", ["impots.gouv.fr"])


def test_nested_lookalike_does_not_count_as_official() -> None:
    host = "chronopost.fr.suivi-colis.test"
    assert not is_official_host(host, ["chronopost.fr"])
    assert is_lookalike(host, "chronopost.fr")


def test_punycode_and_shortener_flags() -> None:
    assert has_punycode("xn--impots-gouv-xx.fr")
    assert decode_host("xn--nxasmq.xn--zckzah")
    assert is_shortener_host("bit.ly")
    assert is_shortener_host("tinyurl.com")
    assert not is_shortener_host("impots.gouv.fr")


def test_extract_urls_and_inspect_without_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("must not fetch the destination page")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    text = "Cliquez https://impots-gouv.fr/connexion et ignorez https://www.impots.gouv.fr"
    urls = extract_urls(text)
    assert any("impots-gouv.fr" in item for item in urls)
    report = inspect_links(text, claimed_official_domains=["impots.gouv.fr"])
    assert report.fetched is False
    assert report.has_lookalike
    hosts = {item.host for item in report.links}
    assert "impots-gouv.fr" in hosts


def test_refuse_destination_fetch() -> None:
    with pytest.raises(UnsafeFetchError, match="will not open"):
        refuse_destination_fetch("http://evil-bank-login.test/steal")


def test_search_allowlist_blocks_pasted_hosts() -> None:
    with pytest.raises(SearchUnsafeFetchError):
        assert_allowlisted("http://impots-gouv.fr/connexion")
    assert assert_allowlisted("https://html.duckduckgo.com/html/?q=test") == "html.duckduckgo.com"
