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
    wants_ragas_scores,
)

DEFAULT_API_BASE = "http://127.0.0.1:8000"


def _format_plan_markdown(data: dict) -> str:
    """Render API JSON as compact markdown for chat."""
    intro = (data.get("employee_intro") or "").strip()
    if not intro:
        portal = data.get("portal_id")
        practice = (data.get("practice") or "").strip() or "—"
        intro = (
            f"Hello.\n\nYour **portal id** is **{portal}**. "
            f"You belong to the employee practice **{practice}**."
        )
    lines = [
        intro,
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
    if "portal_run_ids" not in st.session_state:
        st.session_state.portal_run_ids = {}
    if "last_plan_run_id" not in st.session_state:
        st.session_state.last_plan_run_id = None

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

        if wants_ragas_scores(prompt):
            run_id = st.session_state.get("last_plan_run_id")
            if not run_id:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "**No plan run in this session yet.** "
                            "Ask for a learning plan first (include a valid **portal id**), "
                            "then request RAGAS scores."
                        ),
                    },
                )
                st.rerun()
            api_base = st.session_state.get("api_base", DEFAULT_API_BASE).rstrip("/")
            metrics_url = f"{api_base}/evaluation/ragas-metrics/{run_id}"
            try:
                mresp = httpx.get(metrics_url, timeout=120.0)
            except httpx.RequestError as exc:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"**Could not reach the API** at `{metrics_url}`: {exc}",
                    },
                )
                st.rerun()
            if mresp.status_code >= 400:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"**RAGAS API error {mresp.status_code}**\n```\n"
                            f"{mresp.text[:2000]}\n```"
                        ),
                    },
                )
                st.rerun()
            metrics = mresp.json()
            score_lines = ["### RAGAS scores", ""]
            rid_display = metrics.get("run_id") or run_id
            pid_display = metrics.get("portal_id")
            score_lines.append(f"- **Run ID:** `{rid_display}`")
            score_lines.append(
                f"- **Portal ID:** `{pid_display}`"
                if pid_display is not None
                else "- **Portal ID:** _not available_",
            )
            score_lines.append("")
            err = metrics.get("error")
            scores = metrics.get("scores") or {}
            if err:
                score_lines.append(f"**Evaluator note:** {err}")
                score_lines.append("")
            if scores:
                score_lines.append("| Metric | Score |")
                score_lines.append("| --- | --- |")
                for name in sorted(scores.keys()):
                    val = scores[name]
                    try:
                        score_lines.append(f"| {name} | {float(val):.4f} |")
                    except (TypeError, ValueError):
                        score_lines.append(f"| {name} | {val} |")
            else:
                score_lines.append("_No numeric scores returned._")
            score_lines.extend(["", "### What these metrics mean", ""])
            for name, desc in (metrics.get("metric_descriptions") or {}).items():
                score_lines.append(f"- **{name}:** {desc}")
            st.session_state.messages.append(
                {"role": "assistant", "content": "\n".join(score_lines)},
            )
            st.rerun()

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
        prev_run = st.session_state.portal_run_ids.get(portal_id)
        if prev_run:
            payload["session_run_id"] = prev_run
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
        new_run = data.get("run_id")
        if new_run:
            st.session_state.portal_run_ids[portal_id] = new_run
            st.session_state.last_plan_run_id = new_run
        summary = _format_plan_markdown(data)
        st.session_state.messages.append({"role": "assistant", "content": summary})
        st.rerun()


main()
