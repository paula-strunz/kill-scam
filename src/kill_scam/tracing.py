"""Arize AX tracing. Fail gracefully when keys are missing.

Parent check is a CHAIN span. Each checklist step is a child TOOL span.
Inputs/outputs are summaries plus a message hash — not the pasted body.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from kill_scam.config import PROJECT_NAME, arize_api_key, arize_is_configured, arize_space_id

logger = logging.getLogger("kill_scam")

_STATE: dict[str, object] = {"tried": False, "enabled": False}


def message_fingerprint(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def tracing_enabled() -> bool:
    return bool(_STATE["enabled"])


def init_tracing() -> bool:
    """Register Arize + OpenAI instrumentor. Safe to call on every Streamlit rerun."""
    if _STATE["tried"]:
        return bool(_STATE["enabled"])
    _STATE["tried"] = True

    if not arize_is_configured():
        logger.info(
            "Arize tracing is off. Set ARIZE_API_KEY and ARIZE_SPACE_ID to send checks "
            "to your own Arize space. Project name is %s.",
            PROJECT_NAME,
        )
        return False

    try:
        from arize.otel import register
        from openinference.instrumentation.openai import OpenAIInstrumentor

        tracer_provider = register(
            space_id=arize_space_id(),
            api_key=arize_api_key(),
            project_name=PROJECT_NAME,
        )
        OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
        _STATE["enabled"] = True
        logger.info("Arize AX tracing is on for project %s.", PROJECT_NAME)
        return True
    except Exception:
        logger.warning("Arize tracing could not start. The app will still run without it.")
        _STATE["enabled"] = False
        return False


@contextmanager
def start_check_span(source: str, message_length: int, message_hash: str = "") -> Iterator[Any]:
    if not tracing_enabled():
        yield None
        return

    try:
        from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
        from opentelemetry import trace

        tracer = trace.get_tracer(PROJECT_NAME)
    except Exception:
        yield None
        return

    with tracer.start_as_current_span("scam_check") as span:
        try:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.CHAIN.value,
            )
            span.set_attribute("check.source", source)
            span.set_attribute("check.message_length", message_length)
            span.set_attribute("check.message_hash", message_hash)
            span.set_attribute(SpanAttributes.INPUT_VALUE, f"hash={message_hash} length={message_length}")
        except Exception:
            pass
        yield span


@contextmanager
def start_tool_span(name: str, input_summary: dict[str, object]) -> Iterator[Any]:
    if not tracing_enabled():
        yield None
        return

    try:
        from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
        from opentelemetry import trace

        tracer = trace.get_tracer(PROJECT_NAME)
    except Exception:
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        try:
            span.set_attribute(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.TOOL.value,
            )
            span.set_attribute(SpanAttributes.TOOL_NAME, name)
            span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(input_summary, ensure_ascii=True))
        except Exception:
            pass
        yield span


def record_tool_output(span: Any, output_summary: dict[str, object]) -> None:
    if span is None:
        return
    try:
        from openinference.semconv.trace import SpanAttributes

        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(output_summary, ensure_ascii=True))
    except Exception:
        return


def record_verdict(verdict: str) -> None:
    if not tracing_enabled():
        return
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        span.set_attribute("check.verdict", verdict)
    except Exception:
        return
