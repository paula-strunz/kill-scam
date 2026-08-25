"""Kill Scam home screen. The product is the five-step checklist."""

from __future__ import annotations

import logging
import time

import streamlit as st

from kill_scam import gmail as gmail_client
from kill_scam.agent import iter_checklist
from kill_scam.config import load_env
from kill_scam.models import (
    STEP_IDS,
    STEP_TITLES,
    VERDICT_LABELS,
    CheckError,
    CheckResult,
    StepResult,
)
from kill_scam.tracing import init_tracing

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kill_scam")

VERDICT_COLORS = {
    "ok": "#0f7b3a",
    "suspicious": "#8a5a00",
    "likely_scam": "#a11c1c",
}
VERDICT_BACKGROUNDS = {
    "ok": "#e7f6ec",
    "suspicious": "#fff4d6",
    "likely_scam": "#fde8e8",
}
VERDICT_MARKS = {
    "ok": "Looks OK",
    "suspicious": "Be careful",
    "likely_scam": "Likely a scam — do not click",
}
STEP_MARK = {
    "pending": "○",
    "running": "●",
    "done": "✓",
    "skipped": "–",
}


def main() -> None:
    load_env()
    init_tracing()
    st.set_page_config(page_title="Kill Scam", page_icon="🛡️", layout="centered")
    _inject_styles()

    st.title("Kill Scam")
    st.markdown("### Check a message **before** you click.")
    st.write(
        "Paste an email, text, or WhatsApp message. "
        "Kill Scam walks through **five checks** you can see. "
        "This is a process, not a magic score."
    )

    message = st.text_area(
        "Paste the suspicious message",
        height=240,
        placeholder="Paste the whole message here. Do not click any links in it.",
        label_visibility="visible",
        key="paste_box",
    )

    check_clicked = st.button("Check this message", type="primary", use_container_width=True)

    if check_clicked:
        _run_check(message, source="paste")
    elif st.session_state.get("last_result"):
        _show_checklist(st.session_state.get("last_steps") or [])
        _show_result(st.session_state["last_result"])

    st.divider()
    _gmail_section()

    st.caption(
        "Kill Scam never sends mail and never writes to your inbox. "
        "It never opens the suspicious website. "
        "Paste stays on this computer unless you turn on Arize tracing. "
        "This is a helper, not a guarantee."
    )


def _run_check(message: str, *, source: str) -> None:
    slot = st.empty()
    steps = {
        step_id: StepResult(id=step_id, title=STEP_TITLES[step_id], status="pending")
        for step_id in STEP_IDS
    }
    _draw_checklist(slot, list(steps.values()))
    result: CheckResult | None = None
    try:
        for event in iter_checklist(message, source=source, allow_search=True):
            if isinstance(event, StepResult):
                steps[event.id] = event
                _draw_checklist(slot, list(steps.values()))
                if event.status == "running":
                    time.sleep(0.12)
            elif isinstance(event, CheckResult):
                result = event
    except CheckError as exc:
        st.error(str(exc))
        return
    except Exception:
        logger.warning("Unexpected check failure (source=%s).", source)
        st.error("Something went wrong while checking. Please try again.")
        return
    if result is None:
        st.error("The checklist did not finish.")
        return
    st.session_state["last_steps"] = result.steps or list(steps.values())
    st.session_state["last_result"] = result
    _draw_checklist(slot, st.session_state["last_steps"])
    _show_result(result)


def _show_checklist(steps: list[StepResult]) -> None:
    if not steps:
        return
    st.markdown("**The five checks**")
    for step in steps:
        mark = STEP_MARK.get(step.status, "○")
        status_word = {
            "pending": "waiting",
            "running": "running",
            "done": "done",
            "skipped": "skipped",
        }.get(step.status, step.status)
        st.markdown(f"{mark} **{step.title}** — {status_word}")
        if step.summary and step.status in {"done", "skipped", "running"}:
            st.caption(step.summary)


def _draw_checklist(slot, steps: list[StepResult]) -> None:
    with slot.container():
        _show_checklist(steps)


def _show_result(result: CheckResult) -> None:
    color = VERDICT_COLORS.get(result.verdict, "#222")
    background = VERDICT_BACKGROUNDS.get(result.verdict, "#f4f4f4")
    headline = VERDICT_MARKS.get(result.verdict, VERDICT_LABELS.get(result.verdict, result.verdict))
    st.markdown(
        f"""
        <div class="verdict" style="background:{background}; border-color:{color};">
          <p class="verdict-kicker">After the five checks</p>
          <p class="verdict-title" style="color:{color};">{headline}</p>
          <p class="verdict-summary">{result.summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if result.reasons:
        st.markdown("**Why (tied to the checks)**")
        for reason in result.reasons:
            st.markdown(f"- {reason}")
    if result.advice:
        st.markdown("**What to do**")
        st.write(result.advice)


def _gmail_section() -> None:
    st.subheader("Optional: check recent Gmail")
    st.write(
        "This only reads recent mail. It never sends, never deletes, and never changes anything."
    )

    if not gmail_client.is_configured():
        st.info(
            "Connect Gmail is off until you add Google keys. "
            "You can still paste a message above. See the README to turn this on."
        )
        return

    cols = st.columns(2)
    with cols[0]:
        if st.button(
            "Connect Gmail (read-only)",
            use_container_width=True,
            disabled=gmail_client.is_connected(),
        ):
            try:
                status = gmail_client.connect()
                st.success(status)
            except gmail_client.GmailError as exc:
                st.error(str(exc))
    with cols[1]:
        if st.button(
            "Disconnect Gmail",
            use_container_width=True,
            disabled=not gmail_client.is_connected(),
        ):
            gmail_client.disconnect()
            st.session_state.pop("gmail_messages", None)
            st.info("Gmail disconnected on this computer.")

    if not gmail_client.is_connected():
        st.caption("After you connect, we will list your 20 most recent inbox messages.")
        return

    if st.button("Scan last 20 messages", use_container_width=True):
        try:
            st.session_state["gmail_messages"] = gmail_client.list_recent_messages()
        except gmail_client.GmailError as exc:
            st.error(str(exc))
            return

    messages = st.session_state.get("gmail_messages") or []
    if not messages:
        st.caption("Connected as read-only. Scan to see recent subject lines.")
        return

    st.write(f"Showing {len(messages)} recent messages. Choose one to check.")
    for item in messages:
        with st.container(border=True):
            st.markdown(f"**{item.subject}**")
            st.caption(f"{item.sender} · {item.date}")
            if item.snippet:
                st.write(item.snippet)
            if st.button("Check this Gmail", key=f"check-{item.id}"):
                _run_check(item.as_check_text(), source="gmail")


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
          html, body, [data-testid="stAppViewContainer"] {
            font-size: 20px;
          }
          .block-container { max-width: 820px; padding-top: 1.5rem; }
          h1 { font-size: 2.6rem !important; line-height: 1.15 !important; }
          textarea { font-size: 1.05rem !important; }
          .stButton > button { font-size: 1.15rem; min-height: 3.1rem; font-weight: 650; }
          .verdict {
            border: 3px solid;
            border-radius: 16px;
            padding: 1rem 1.2rem;
            margin: 0.8rem 0 1rem;
          }
          .verdict-kicker {
            margin: 0;
            font-size: 0.9rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
          }
          .verdict-title { margin: 0.15rem 0 0.4rem; font-size: 1.8rem; font-weight: 750; }
          .verdict-summary { margin: 0; font-size: 1.15rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


main()
