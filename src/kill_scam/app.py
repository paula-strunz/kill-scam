"""Kill Scam home screen. V0 first path is Connect Gmail, then the five-step checklist."""

from __future__ import annotations

import html
import logging
import time

import streamlit as st

from kill_scam import gmail as gmail_client
from kill_scam.agent import iter_checklist
from kill_scam.config import GMAIL_LOOKBACK_DAYS, GMAIL_SCAN_LIMIT, load_env
from kill_scam.links import defang_for_display
from kill_scam.models import (
    STEP_IDS,
    STEP_TITLES,
    CheckError,
    CheckResult,
    StepResult,
)
from kill_scam.share_card import (
    WRONG_LINK,
    WRONG_NOTE,
    EmailName,
    build_share_result,
    email_name,
    render_share_result_html,
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
# Longer words kept for the Gmail message box. Paste uses the short labels.
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
    _handle_oauth_callback()

    paste_result = _paste_result()
    if paste_result is not None:
        _show_warning_screen(paste_result)
        return

    st.title("Kill Scam")
    st.markdown("### Connect Gmail. We look at recent mail. You see every check.")
    st.write(
        "Kill Scam reads recent inbox messages and walks through **five checks** "
        "you can see: what it wants, who it claims to be, the web addresses, "
        "known campaigns, then **Looks OK / Be careful / Likely a scam**."
    )
    st.caption(
        "It never sends mail. It never deletes mail. It never writes to your mailbox. "
        "It never opens a suspicious website."
    )

    _gmail_home()

    with st.expander("Check something else", expanded=False):
        st.write(
            "Paste a message that is not in this Gmail — for example an SMS, "
            "WhatsApp text, or mail someone forwarded. This is the backup path, "
            "not the usual one."
        )
        message = st.text_area(
            "Paste the suspicious message",
            height=200,
            placeholder="Paste the whole message here. Do not click any links in it.",
            label_visibility="visible",
            key="paste_box",
        )
        if st.button("Check this message", use_container_width=True, key="paste-check"):
            _run_check(message, source="paste")

    st.divider()
    st.caption(
        "It never sends mail and never deletes mail. "
        "V0 is for Paula and invited family testers on a Google testing-mode app. "
        "Public sign-in for everyone is not part of this version. "
        "Paste stays on this computer unless you turn on Arize tracing. "
        "This is a helper, not a guarantee. Product spec: docs/PRD.md."
    )


def _handle_oauth_callback() -> None:
    params = st.query_params
    error = params.get("error")
    if error:
        st.error("Google sign-in was cancelled or blocked. You can try again.")
        st.query_params.clear()
        return
    code = params.get("code")
    if not code:
        return
    state = params.get("state") or ""
    expected = str(st.session_state.get("oauth_state") or "")
    try:
        token = gmail_client.finish_connect(str(code), str(state), expected)
    except gmail_client.GmailError as exc:
        st.error(str(exc))
        st.query_params.clear()
        return
    except Exception:
        logger.warning("Unexpected OAuth callback failure.")
        st.error("Could not finish Google sign-in. Try Connect Gmail again.")
        st.query_params.clear()
        return
    st.session_state["gmail_token"] = token
    st.session_state.pop("gmail_messages", None)
    st.session_state.pop("oauth_auth_url", None)
    st.query_params.clear()
    st.rerun()


def _gmail_token() -> dict | None:
    existing = st.session_state.get("gmail_token")
    if existing:
        return existing
    persisted = gmail_client.load_persisted_token()
    if persisted:
        st.session_state["gmail_token"] = persisted
        return persisted
    return None


def _gmail_home() -> None:
    status = gmail_client.setup_status()
    st.subheader(status.headline)

    if not status.configured:
        st.warning(status.detail)
        st.info(
            "Connect Gmail isn’t set up yet on this server. "
            "The five checks still work if you open **Check something else**."
        )
        return

    st.write(status.detail)
    st.caption(
        "Google may show an “unverified app” warning. That is expected in testing mode. "
        "Only testers Paula invited should continue. Public-everyone access is out of V0."
    )

    token = _gmail_token()
    connected = gmail_client.is_connected(token)

    cols = st.columns(2)
    with cols[0]:
        if not connected:
            try:
                if "oauth_auth_url" not in st.session_state:
                    url, state = gmail_client.authorization_url()
                    st.session_state["oauth_auth_url"] = url
                    st.session_state["oauth_state"] = state
                st.link_button(
                    "Connect Gmail (read-only)",
                    st.session_state["oauth_auth_url"],
                    type="primary",
                    use_container_width=True,
                )
            except gmail_client.GmailError as exc:
                st.error(str(exc))
    with cols[1]:
        if st.button(
            "Disconnect Gmail",
            use_container_width=True,
            disabled=not connected,
            key="gmail-disconnect",
        ):
            gmail_client.disconnect(token)
            st.session_state.pop("gmail_token", None)
            st.session_state.pop("gmail_messages", None)
            st.session_state.pop("oauth_auth_url", None)
            st.session_state.pop("oauth_state", None)
            st.info("Gmail disconnected. Kill Scam no longer reads this inbox.")
            st.rerun()

    if not connected:
        st.caption(
            f"After you connect, we list up to {GMAIL_SCAN_LIMIT} inbox messages "
            f"from the last {GMAIL_LOOKBACK_DAYS} days. One tap on Check runs the five steps."
        )
        return

    if st.session_state.get("gmail_messages") is None:
        try:
            st.session_state["gmail_messages"] = gmail_client.list_recent_messages(token)
        except gmail_client.GmailError as exc:
            st.error(str(exc))
            st.session_state["gmail_messages"] = []

    if st.button("Refresh recent mail", use_container_width=True, key="gmail-refresh"):
        try:
            st.session_state["gmail_messages"] = gmail_client.list_recent_messages(token)
        except gmail_client.GmailError as exc:
            st.error(str(exc))
            return

    messages = st.session_state.get("gmail_messages") or []
    if not messages:
        st.info(
            f"No inbox messages in the last {GMAIL_LOOKBACK_DAYS} days. "
            "You can still use Check something else."
        )
        return

    st.write(
        f"Showing {len(messages)} recent inbox messages "
        f"(last {GMAIL_LOOKBACK_DAYS} days, up to {GMAIL_SCAN_LIMIT}). "
        "Tap **Check** on a message."
    )
    for item in messages:
        with st.container(border=True):
            st.markdown(f"**{item.subject}**")
            st.caption(f"{defang_for_display(item.sender)} · {item.date}")
            if item.snippet:
                st.write(defang_for_display(item.snippet))
            if st.button("Check", key=f"check-{item.id}", type="primary"):
                _check_gmail_message(item.id, token)

            if st.session_state.get("last_gmail_id") == item.id and st.session_state.get("last_result"):
                _show_checklist(st.session_state.get("last_steps") or [])
                _show_result(st.session_state["last_result"])


def _check_gmail_message(message_id: str, token: dict | None) -> None:
    try:
        full = gmail_client.get_message(message_id, token)
    except gmail_client.GmailError as exc:
        st.error(str(exc))
        return
    st.session_state["last_gmail_id"] = message_id
    _run_check(full.as_check_text(), source="gmail")


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
    st.session_state["last_source"] = source
    st.session_state["last_email_name"] = email_name(message) if source == "paste" else None
    st.session_state["verdict_wrong"] = False
    _draw_checklist(slot, st.session_state["last_steps"])
    if source != "gmail":
        st.rerun()


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
            st.caption(defang_for_display(step.summary))


def _draw_checklist(slot, steps: list[StepResult]) -> None:
    with slot.container():
        _show_checklist(steps)


def _paste_result() -> CheckResult | None:
    if st.session_state.get("last_source") != "paste":
        return None
    result = st.session_state.get("last_result")
    if isinstance(result, CheckResult):
        return result
    return None


def _leave_warning() -> None:
    """Safe exit. Does not send or delete mail."""
    for key in (
        "last_result",
        "last_source",
        "last_steps",
        "last_email_name",
        "verdict_wrong",
    ):
        st.session_state.pop(key, None)


def _show_warning_screen(result: CheckResult) -> None:
    """One centered warning. Spec: specs/004-warning-screen.md."""
    name = st.session_state.get("last_email_name")
    view = build_share_result(result, name if isinstance(name, EmailName) else None)
    st.markdown(render_share_result_html(view), unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.35, 1])
    with mid:
        if st.button(view.action, key="safe-action", type="primary", use_container_width=True):
            _leave_warning()
            st.rerun()
        if st.button(WRONG_LINK, key="verdict-wrong", type="tertiary", use_container_width=True):
            st.session_state["verdict_wrong"] = True
        if st.session_state.get("verdict_wrong"):
            st.markdown(f'<p class="warn-note">{html.escape(WRONG_NOTE)}</p>', unsafe_allow_html=True)


def _show_result(result: CheckResult) -> None:
    color = VERDICT_COLORS.get(result.verdict, "#222")
    background = VERDICT_BACKGROUNDS.get(result.verdict, "#f4f4f4")
    headline = VERDICT_MARKS.get(result.verdict, result.label)
    st.markdown(
        f"""
        <div class="verdict" style="background:{background}; border-color:{color};">
          <p class="verdict-kicker">After the five checks</p>
          <p class="verdict-title" style="color:{color};">{headline}</p>
          <p class="verdict-summary">{html.escape(defang_for_display(result.summary))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if result.reasons:
        st.markdown("**Why (tied to the checks)**")
        for reason in result.reasons:
            st.markdown(f"- {defang_for_display(reason)}")
    if result.advice:
        st.markdown("**What to do**")
        st.write(defang_for_display(result.advice))


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
          [data-testid="stAppViewContainer"] { background: #f7f6f3; }
          [data-testid="stHeader"] { background: transparent; }
          .warn-screen {
            text-align: center;
            max-width: 34rem;
            margin: 7vh auto 0;
            padding: 0 0.5rem 0.5rem;
          }
          .warn-mark {
            width: 5.25rem;
            height: 5.25rem;
            margin: 0 auto 1.4rem;
            border-radius: 50%;
            border: 2px solid #1a1a1a;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.6rem;
            font-weight: 700;
            line-height: 1;
            color: #1a1a1a;
            background: transparent;
          }
          .warn-mark-likely_scam { color: #9b1c1c; border-color: #9b1c1c; }
          .warn-mark-suspicious { color: #8a5a00; border-color: #8a5a00; }
          .warn-mark-ok { color: #0f7b3a; border-color: #0f7b3a; }
          .warn-title {
            margin: 0 0 0.8rem;
            color: #1a1a1a;
            font-size: 3.15rem !important;
            font-weight: 720 !important;
            letter-spacing: -0.03em;
            line-height: 1.05;
          }
          .warn-harm {
            margin: 0 auto 1.15rem !important;
            max-width: 26rem;
            color: #1a1a1a;
            font-size: 1.28rem !important;
            line-height: 1.4;
          }
          .warn-note {
            margin: 0.4rem auto 0;
            max-width: 22rem;
            text-align: center;
            color: #444;
            font-size: 0.95rem;
            line-height: 1.4;
          }
          div[class*="st-key-safe-action"] { margin-top: 1.6rem; }
          div[class*="st-key-safe-action"] button {
            background: #1a1a1a;
            color: #f7f6f3;
            border: 0;
            border-radius: 999px;
            min-height: 3.3rem;
            font-size: 1.15rem;
            font-weight: 680;
          }
          div[class*="st-key-safe-action"] button:hover,
          div[class*="st-key-safe-action"] button:focus {
            background: #000;
            color: #f7f6f3;
          }
          div[class*="st-key-verdict-wrong"] { display: flex; justify-content: center; }
          div[class*="st-key-verdict-wrong"] button {
            background: transparent;
            border: 0;
            box-shadow: none;
            color: #1a1a1a;
            font-size: 1rem;
            font-weight: 500;
            min-height: 0;
            padding: 0.2rem 0;
            text-decoration: underline;
            text-underline-offset: 0.18em;
          }
          div[class*="st-key-verdict-wrong"] button:hover,
          div[class*="st-key-verdict-wrong"] button:focus {
            color: #1a1a1a;
            border: 0;
            background: transparent;
          }
          @media (max-width: 640px) {
            .block-container { padding-top: 0.6rem; }
            .warn-screen { margin-top: 2.5rem; }
            .warn-title { font-size: 2.6rem !important; }
            .warn-harm { font-size: 1.15rem !important; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


main()
