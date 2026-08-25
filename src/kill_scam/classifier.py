"""Parse and run the scam classifier. Never log the full message body."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping

from kill_scam.config import MAX_MESSAGE_CHARS, openai_api_key, openai_model
from kill_scam.models import (
    VERDICTS,
    CheckError,
    CheckResult,
    MissingApiKeyError,
    VERDICT_ALIASES,
)
from kill_scam.prompts import SYSTEM_PROMPT, user_prompt
from kill_scam.tracing import record_verdict, start_check_span

logger = logging.getLogger("kill_scam")

_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def parse_verdict(raw: str | Mapping[str, object]) -> CheckResult:
    """Turn model output into a CheckResult. Used by tests without calling OpenAI."""
    payload = _as_mapping(raw)
    verdict = _normalize_verdict(payload.get("verdict"))
    if verdict is None:
        raise CheckError("The checker replied in a way we could not read. Please try again.")

    summary = _as_text(payload.get("summary")) or "We could not sum this up in one sentence."
    advice = _as_text(payload.get("advice"))
    reasons = _as_reasons(payload.get("reasons"))
    return CheckResult(verdict=verdict, summary=summary, reasons=reasons, advice=advice)


def classify_message(message: str, *, source: str = "paste") -> CheckResult:
    """Classify one message. Requires OPENAI_API_KEY. Does not print the body."""
    cleaned = (message or "").strip()
    if not cleaned:
        raise CheckError("Please paste a message first.")
    if len(cleaned) > MAX_MESSAGE_CHARS:
        raise CheckError(
            f"That text is too long (max {MAX_MESSAGE_CHARS:,} characters). "
            "Paste the suspicious part only."
        )

    api_key = openai_api_key()
    if not api_key:
        logger.info("Check skipped: OPENAI_API_KEY is not set (source=%s, length=%s).", source, len(cleaned))
        raise MissingApiKeyError(MissingApiKeyError.user_message)

    logger.info("Running scam check (source=%s, length=%s).", source, len(cleaned))

    with start_check_span(source, len(cleaned)):
        raw = _call_openai(cleaned, api_key)
        result = parse_verdict(raw)
        record_verdict(result.verdict)
        logger.info("Check finished with verdict=%s.", result.verdict)
        return result


def _call_openai(message: str, api_key: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise CheckError("The OpenAI library is not installed. Run: pip install -e .") from exc

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=openai_model(),
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(message)},
            ],
        )
    except Exception:
        logger.warning("OpenAI request failed. The message body was not logged.")
        raise CheckError(
            "We could not reach the checker. Check your internet connection and OpenAI key, then try again."
        ) from None

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise CheckError("The checker returned an empty reply. Please try again.")
    return content


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
        reasons = []
        for item in value:
            text = str(item).strip()
            if text:
                reasons.append(text)
        return reasons
    text = str(value).strip()
    return [text] if text else []
