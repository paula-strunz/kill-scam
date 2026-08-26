"""Five-step defensive checklist agent. Process over vibe."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterator, Mapping

from kill_scam.asks import extract_asks
from kill_scam.campaigns import DuckDuckGoSearcher, NullSearcher, extract_campaigns
from kill_scam.config import MAX_MESSAGE_CHARS
from kill_scam.identity import extract_identity
from kill_scam.links import inspect_links
from kill_scam.models import (
    STEP_IDS,
    STEP_TITLES,
    VERDICT_ALIASES,
    VERDICTS,
    CheckError,
    CheckResult,
    StepResult,
)
from kill_scam.tracing import (
    message_fingerprint,
    record_tool_output,
    record_verdict,
    start_check_span,
    start_tool_span,
)

logger = logging.getLogger("kill_scam")

_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)

FR_REPORTING = (
    "If this came by SMS in France, forward it to 33700 (free). "
    "If it came by email, you can report it at signal-spam.fr. "
    "Do not click the links."
)


def classify_message(
    message: str,
    *,
    source: str = "paste",
    allow_search: bool = False,
) -> CheckResult:
    """Run the full checklist and return the final verdict."""
    result: CheckResult | None = None
    for event in iter_checklist(message, source=source, allow_search=allow_search):
        if isinstance(event, CheckResult):
            result = event
    if result is None:
        raise CheckError("The checklist did not finish.")
    return result


def iter_checklist(
    message: str,
    *,
    source: str = "paste",
    allow_search: bool = False,
) -> Iterator[StepResult | CheckResult]:
    cleaned = (message or "").strip()
    if not cleaned:
        raise CheckError("Please paste a message first.")
    if len(cleaned) > MAX_MESSAGE_CHARS:
        raise CheckError(
            f"That text is too long (max {MAX_MESSAGE_CHARS:,} characters). "
            "Paste the suspicious part only."
        )

    fingerprint = message_fingerprint(cleaned)
    logger.info("Running checklist (source=%s, length=%s, hash=%s).", source, len(cleaned), fingerprint)

    searcher = DuckDuckGoSearcher() if allow_search else NullSearcher()
    steps: dict[str, StepResult] = {
        step_id: StepResult(id=step_id, title=STEP_TITLES[step_id], status="pending")
        for step_id in STEP_IDS
    }

    with start_check_span(source, len(cleaned), fingerprint):
        ask = identity = links = campaigns = None
        for step_id in STEP_IDS:
            running = StepResult(
                id=step_id,
                title=STEP_TITLES[step_id],
                status="running",
                summary="Checking…",
            )
            steps[step_id] = running
            yield running

            input_summary = {"step": step_id, "message_hash": fingerprint, "source": source}
            with start_tool_span(step_id, input_summary) as span:
                if step_id == "ask":
                    ask = extract_asks(cleaned)
                    done = _step(
                        "ask",
                        "done",
                        "; ".join(ask.findings),
                        list(ask.findings),
                    )
                    record_tool_output(span, {"kinds": list(ask.kinds)})
                elif step_id == "identity":
                    identity = extract_identity(cleaned)
                    done = _step(
                        "identity",
                        "done",
                        "; ".join(identity.findings[:2]),
                        list(identity.findings),
                    )
                    record_tool_output(
                        span,
                        {
                            "claimed": [org.org_id for org in identity.claimed_orgs],
                            "mismatch": identity.mismatch,
                            "lookalike_sender": identity.lookalike_sender,
                            "address_domain": identity.address_domain,
                        },
                    )
                elif step_id == "links":
                    links = inspect_links(
                        cleaned,
                        claimed_official_domains=list(identity.official_domains) if identity else None,
                    )
                    status = "done"
                    done = _step("links", status, "; ".join(links.findings[:2]), list(links.findings))
                    record_tool_output(
                        span,
                        {
                            "url_count": len(links.links),
                            "lookalike": links.has_lookalike,
                            "shortener": links.has_shortener,
                            "fetched": links.fetched,
                            "hosts": [item.host for item in links.links],
                        },
                    )
                elif step_id == "campaigns":
                    campaigns = extract_campaigns(cleaned, searcher=searcher)
                    status = "skipped" if campaigns.search_attempted and not campaigns.search_ok else "done"
                    if not campaigns.search_attempted:
                        status = "done"
                    done = _step(
                        "campaigns",
                        status,
                        "; ".join(campaigns.findings[:2]),
                        list(campaigns.findings),
                    )
                    record_tool_output(
                        span,
                        {
                            "hits": [hit.campaign_id for hit in campaigns.hits],
                            "search_attempted": campaigns.search_attempted,
                            "search_ok": campaigns.search_ok,
                        },
                    )
                else:
                    result = _build_verdict(ask, identity, links, campaigns, fingerprint)
                    done = _step("verdict", "done", result.summary, result.reasons + [result.advice])
                    record_tool_output(
                        span,
                        {"verdict": result.verdict, "reason_count": len(result.reasons)},
                    )
                    record_verdict(result.verdict)
                    steps[step_id] = done
                    yield done
                    result.steps = [steps[item] for item in STEP_IDS]
                    result.search_used = bool(campaigns and campaigns.search_ok)
                    logger.info("Checklist finished with verdict=%s.", result.verdict)
                    yield result
                    return

            steps[step_id] = done
            yield done


def parse_verdict(raw: str | Mapping[str, object]) -> CheckResult:
    """Parse optional wording JSON. Used by tests. Does not run the checklist."""
    payload = _as_mapping(raw)
    verdict = _normalize_verdict(payload.get("verdict"))
    if verdict is None:
        raise CheckError("The checker replied in a way we could not read. Please try again.")
    summary = _as_text(payload.get("summary")) or "We could not sum this up in one sentence."
    advice = _as_text(payload.get("advice"))
    reasons = _as_reasons(payload.get("reasons"))
    return CheckResult(verdict=verdict, summary=summary, reasons=reasons, advice=advice)


def _build_verdict(ask, identity, links, campaigns, fingerprint: str) -> CheckResult:
    reasons: list[str] = []
    likely_flags: list[str] = []
    suspicious_flags: list[str] = []
    french = False

    if identity:
        french = any(org.region == "FR" for org in identity.claimed_orgs)
        if identity.lookalike_sender:
            likely_flags.append("identity")
            reasons.append("Identity: the sending address looks like an official site but is not.")
        elif identity.mismatch:
            likely_flags.append("identity")
            reasons.append(
                "Identity: it claims to be an official organisation, but the address is not their real site."
            )
        elif identity.claimed_orgs:
            reasons.append("Identity: it names a known organisation. We still did not trust the display name.")

    if links:
        if links.has_lookalike:
            likely_flags.append("links")
            reasons.append("Links: a web address looks like an official site but is not. We did not open it.")
        if links.has_shortener:
            suspicious_flags.append("links")
            reasons.append("Links: it uses a short link that hides the real website. We did not open it.")
        unofficial = links.unofficial_click_targets
        if unofficial and identity and identity.claimed_orgs:
            likely_flags.append("links")
            reasons.append(
                "Links: the address is not the official site for the organisation it claims to be."
            )
        elif unofficial and ask and "click" in ask.kinds:
            suspicious_flags.append("links")
            reasons.append("Links: it asks you to click a site that is not on our official list.")

    if ask:
        if "code" in ask.kinds:
            likely_flags.append("ask")
            reasons.append("Ask: it wants a password, code, or card number. Official services do not ask that this way.")
        if "install" in ask.kinds:
            likely_flags.append("ask")
            reasons.append("Ask: it wants you to install remote-access software.")
        if "pay" in ask.kinds and "silence" in ask.kinds:
            likely_flags.append("ask")
            reasons.append("Ask: it wants money and also wants you to stay silent.")
        elif "pay" in ask.kinds:
            suspicious_flags.append("ask")
            reasons.append("Ask: it wants you to pay or send money.")
        if "click" in ask.kinds and not (links and links.links):
            suspicious_flags.append("ask")
            reasons.append("Ask: it pushes you to click, without a clear official website.")

    if campaigns and campaigns.matched:
        labels = ", ".join(sorted({hit.label for hit in campaigns.hits}))
        if any(hit.campaign_id in {"family_emergency", "credential_theft", "fake_tax_refund", "parcel_fees"} for hit in campaigns.hits):
            likely_flags.append("campaigns")
        else:
            suspicious_flags.append("campaigns")
        reasons.append(f"Campaigns: this matches a known pattern ({labels}).")
        if campaigns.search_attempted and not campaigns.search_ok:
            reasons.append("Campaigns: live official guidance could not be reached, so confidence is a bit lower.")

    if likely_flags:
        verdict = "likely_scam"
        summary = "Several checks say this is a scam. Do not click, pay, or share a code."
    elif suspicious_flags:
        verdict = "suspicious"
        summary = "Something is off. Pause and check another way before you do anything."
    else:
        verdict = "ok"
        summary = "The five checks did not find scam pressure. Stay careful with unexpected links anyway."
        if not reasons:
            reasons.append("Ask: no click / pay / code / silence demand.")
            reasons.append("Links: no lookalike or hidden short link.")
            reasons.append("Identity: no official-org impersonation with a fake address.")

    advice_parts = [
        "Use a phone number or website you already have — not one from this message.",
    ]
    if verdict != "ok":
        advice_parts.insert(0, "Do not click, do not pay, and do not share codes from this message.")
        if french or verdict == "likely_scam":
            advice_parts.append(FR_REPORTING)

    return CheckResult(
        verdict=verdict,
        summary=summary,
        reasons=reasons,
        advice=" ".join(advice_parts),
        message_hash=fingerprint,
    )


def _step(step_id: str, status: str, summary: str, details: list[str]) -> StepResult:
    text = summary if len(summary) <= 280 else summary[:277] + "..."
    return StepResult(
        id=step_id,
        title=STEP_TITLES[step_id],
        status=status,
        summary=text,
        details=details,
    )


def _as_mapping(raw: str | Mapping[str, object]) -> dict[str, object]:
    if isinstance(raw, Mapping):
        return dict(raw)
    text = raw.strip()
    if not text:
        raise CheckError("The checker returned an empty reply. Please try again.")
    candidates = []
    fenced = _JSON_FENCE.search(text)
    if fenced:
        candidates.append(fenced.group(1))
    obj = _JSON_OBJECT.search(text)
    if obj:
        candidates.append(obj.group(0))
    candidates.append(text)
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise CheckError("The checker replied in a way we could not read. Please try again.")


def _normalize_verdict(value: object) -> str | None:
    if value is None:
        return None
    key = str(value).strip().lower().replace("-", "_")
    key = " ".join(key.split())
    if key in VERDICTS:
        return key
    return VERDICT_ALIASES.get(key)


def _as_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_reasons(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []
