"""Chat-style Streamlit UI for the AI Learning Path Assistant."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import httpx  # noqa: E402
import streamlit as st  # noqa: E402

from services.user_service import UserService  # noqa: E402
from utils.chat_intent_parse import (  # noqa: E402
    explain_portal_resolution_failure,
    parse_learning_plan_intent,
    resolve_portal_id,
)

DEFAULT_API_BASE = "http://127.0.0.1:8000"


def _format_plan_markdown(data: dict) -> str:
    """Render API JSON as compact markdown for chat."""
    lines = [
        f"**{data.get('employee_name') or 'Employee'}** · Portal `{data.get('portal_id')}` · "
        f"{data.get('practice') or '—'}",
        "",
        f"- Training goal: **{data.get('annual_training_goal_hours') or 0}** h/yr  "
        f"· Completed: **{data.get('completed_hours', 0):.1f}** h  "
        f"· Remaining toward goal: **{data.get('remaining_target_hours', 0):.1f}** h",
        f"- Planned this recommendation: **{data.get('planned_hours', 0):.1f}** h  "
        f"· Gap after plan: **{data.get('remaining_gap_after_plan', 0):.1f}** h",
        "",
        "**Skills used for retrieval:** "
        + (", ".join(data.get("skills_used_for_retrieval") or []) or "—"),
        "",
        "**Recommended courses:**",
    ]
    for item in data.get("recommended_courses") or []:
        lines.append(
            f"- **{item.get('course_name')}** (`{item.get('course_id')}`) — "
            f"{item.get('hours')} h"
            + (
                f" · prereq: {item.get('prerequisite')}"
                if item.get("prerequisite")
                else ""
            ),
        )
    expl = data.get("explanation")
    if expl:
        lines.extend(["", "**Explanation:**", str(expl)])
    warns = data.get("warnings") or []
    if warns:
        lines.extend(["", "**Notes:**", *[f"- {w}" for w in warns]])
    return "\n".join(lines)


@st.cache_data(ttl=120)
def _cached_portal_ids() -> frozenset[int]:
    """Load valid portal IDs from processed user master (short TTL for refreshes)."""
    try:
        return frozenset(UserService().all_portal_ids())
    except (FileNotFoundError, OSError, KeyError):
        return frozenset()


def main() -> None:
    """Chat UI: natural language → parse portal & expertise → POST /generate-plan."""
    st.set_page_config(
        page_title="AI Intelligent Learning path finder",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        .main .block-container { max-width: 42rem; padding-top: 2rem; }
        h1.hero { text-align: center; font-weight: 600; margin-bottom: 0.25rem; }
        p.sub { text-align: center; color: #666; font-size: 0.95rem; margin-top: 0.35rem; line-height: 1.45; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h1 class="hero">AI Intelligent Learning path finder</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <p class="sub">Type in your own words. We look for a <strong>portal ID</strong> using phrases like
        <em>portal id 24463</em> or <em>employee 24463</em>. If none of those match, we take numbers from your
        message and use the first one that exists in the user directory (from your ingested user master).
        You can add an optional <strong>target expertise</strong> (e.g. <em>focus on Java</em>,
        <em>learn ServiceNow</em>). Use the <strong>+</strong> button to the left of the message box for extra options.</p>
        <p class="sub"><em>Example:</em> "I need a plan for portal id 24463 and want to deepen my Java skills."</p>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.markdown("### Connection")
        api_base = st.text_input(
            "API base URL",
            value=st.session_state.get("api_base", DEFAULT_API_BASE),
            key="api_base_input",
        )
        st.session_state["api_base"] = api_base.rstrip("/")
        st.caption("`LEARNING_PATH_TOP_K` is set on the API host (`.env`).")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    try:
        col_plus, col_chat = st.columns(
            [0.12, 0.88],
            gap="small",
            vertical_alignment="center",
        )
    except TypeError:
        col_plus, col_chat = st.columns([0.12, 0.88], gap="small")

    with col_plus:
        popover_fn = getattr(st, "popover", None)
        if popover_fn is not None:
            with popover_fn("➕"):
                st.caption("Applies to your next send.")
                st.checkbox(
                    "Include explanation",
                    value=False,
                    key="opt_include_explanation",
                )
                st.checkbox(
                    "Include optional courses",
                    value=False,
                    key="opt_include_optional_courses",
                    help="Extra ranked courses beyond the minimum for your hour target.",
                )
        else:
            with st.expander("➕", expanded=False):
                st.caption("Options for your next send.")
                st.checkbox(
                    "Include explanation",
                    value=False,
                    key="opt_include_explanation",
                )
                st.checkbox(
                    "Include optional courses",
                    value=False,
                    key="opt_include_optional_courses",
                )

    with col_chat:
        prompt = st.chat_input("Ask anything")

    if prompt:
        prompt = prompt.strip()
        if not prompt:
            return

        st.session_state.messages.append({"role": "user", "content": prompt})

        valid = _cached_portal_ids()
        intent = parse_learning_plan_intent(prompt)
        portal_id = resolve_portal_id(intent, valid)

        if not valid:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": "**Could not load user directory.** "
                    "Run `python run_ingestion.py` and ensure `data/processed/user_master.csv` exists.",
                },
            )
            st.rerun()

        if portal_id is None:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": explain_portal_resolution_failure(intent),
                },
            )
            st.rerun()

        payload = {
            "portal_id": portal_id,
            "target_expertise": intent.target_expertise,
            "include_explanation": bool(st.session_state.get("opt_include_explanation", False)),
            "include_optional_courses": bool(
                st.session_state.get("opt_include_optional_courses", False),
            ),
        }
        url = st.session_state["api_base"] + "/generate-plan"
        try:
            resp = httpx.post(url, json=payload, timeout=120.0)
        except httpx.RequestError as exc:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"**Could not reach the API** at `{url}`: {exc}",
                },
            )
            st.rerun()

        if resp.status_code >= 400:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"**API error {resp.status_code}**\n```\n{resp.text[:2000]}\n```",
                },
            )
            st.rerun()

        data = resp.json()
        summary = (
            f"Parsed **portal {portal_id}**"
            + (f" · focus **{intent.target_expertise}**" if intent.target_expertise else "")
            + "\n\n"
            + _format_plan_markdown(data)
        )
        st.session_state.messages.append({"role": "assistant", "content": summary})
        st.rerun()


main()
