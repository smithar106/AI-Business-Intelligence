"""Spend Attribution — ask plain-English questions about AI spend (demo mode).

Runs entirely on deterministic synthetic data. Only ANTHROPIC_API_KEY is used,
and only to answer natural-language questions; the dashboard renders without
any keys. No real billing data is exposed.
"""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.llm import claude_stream
from utils.secrets import has_secret
from utils.styles import (
    ACCENT,
    CHART_COLORS,
    DANGER,
    banner,
    inject_css,
    metric_tile,
    page_header,
    sidebar_credit,
    style_fig,
)
from utils.synthetic import (
    anomaly_days,
    build_context,
    by_provider,
    by_team,
    daily_total,
    generate_spend_df,
)

st.set_page_config(page_title="Spend Attribution", page_icon="\U0001F4B8", layout="wide")
inject_css()
sidebar_credit()

page_header(
    "Spend Attribution",
    "Ask anything about your AI spend — Claude reads the data and answers with numbers.",
    icon="\U0001F4B8",
)

banner(
    "<b>Demo mode</b> — showing synthetic data representative of a real AI ops environment. "
    "Contact <b>Arthur Smith</b> to deploy with your org's live data.",
    kind="info",
    icon="\U0001F9EA",
)


st.markdown(
    """
    <style>
    /* Indigo left-bordered response box for the streamed Q&A answer. */
    [data-testid="stVerticalBlockBorderWrapper"]:has(.qa-marker) {
        border: 1px solid #ECEDF2 !important;
        border-left: 4px solid #5B5FED !important;
        border-radius: 12px;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(16,24,40,0.05), 0 8px 24px -18px rgba(16,24,40,0.18);
    }
    .qa-marker { height: 0; margin: 0; }
    .qa-question {
        font-size: .8rem; font-weight: 600; color: #3F43C9;
        background: #EEF0FE; display: inline-block; padding: .22rem .6rem;
        border-radius: 999px; margin-bottom: .35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_df():
    return generate_spend_df()


df = load_df()
EXAMPLES = [
    "Which model cost the most last week?",
    "Are we trending up or down on spend?",
    "Which provider is more expensive?",
    "Were there any anomalies this month?",
]

st.session_state.setdefault("spend_q", "")
st.session_state.setdefault("spend_pending", "")
st.session_state.setdefault("spend_answer", "")
st.session_state.setdefault("spend_answered_q", "")

# ---------------------------------------------------------------------------
# Ask box + example chips
# ---------------------------------------------------------------------------
st.text_input(
    "Ask anything about your AI spend",
    key="spend_q",
    placeholder="e.g. Which provider is driving most of our cost this month?",
)

chip_cols = st.columns(len(EXAMPLES))
for col, q in zip(chip_cols, EXAMPLES):
    with col:
        if st.button(q, use_container_width=True, key=f"chip_{q}"):
            st.session_state["spend_q"] = q
            st.session_state["spend_pending"] = q
            st.rerun()

ask = st.button("\U0001F4AC Ask", type="primary")
if ask and st.session_state["spend_q"].strip():
    st.session_state["spend_pending"] = st.session_state["spend_q"].strip()

# ---------------------------------------------------------------------------
# Claude answer
# ---------------------------------------------------------------------------
question = st.session_state.get("spend_pending", "")
if question:
    if not has_secret("ANTHROPIC_API_KEY"):
        st.error("Set `ANTHROPIC_API_KEY` (standard key from console.anthropic.com) to enable Q&A. The dashboard below still works.")
    else:
        system = (
            "You are a precise FinOps analyst for an AI platform team. Answer the user's "
            "question using ONLY the dataset provided. Be conversational but cite specific "
            "numbers (USD, model names, team names, dates). If anomalies are relevant, call "
            "out the anomaly window explicitly. Keep it under ~150 words."
        )
        prompt = f"DATASET:\n{build_context(df)}\n\nQUESTION: {question}\n\nAnswer:"
        cached = (
            st.session_state.get("spend_answered_q") == question
            and st.session_state.get("spend_answer")
        )
        with st.container(border=True):
            st.markdown('<div class="qa-marker"></div>', unsafe_allow_html=True)
            st.markdown(f"<span class='qa-question'>{question}</span>", unsafe_allow_html=True)
            if cached:
                st.markdown(st.session_state["spend_answer"])
            else:
                answer = st.write_stream(
                    claude_stream(prompt, system=system, max_tokens=500, temperature=0.3)
                )
                st.session_state["spend_answer"] = answer
                st.session_state["spend_answered_q"] = question
        with st.expander("Supporting data"):
            c1, c2 = st.columns(2)
            c1.caption("By model (30d)")
            c1.dataframe(
                df.groupby("model", as_index=False)["cost"].sum().sort_values("cost", ascending=False),
                hide_index=True, use_container_width=True,
            )
            c2.caption("By team (30d)")
            c2.dataframe(by_team(df), hide_index=True, use_container_width=True)

st.markdown("<div style='height:.6rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Metric tiles
# ---------------------------------------------------------------------------
total = df["cost"].sum()
daily = daily_total(df)
last7 = daily.tail(7)["cost"].sum()
prev7 = daily.iloc[-14:-7]["cost"].sum()
delta = (last7 - prev7) / prev7 * 100 if prev7 else 0.0
top_team = by_team(df).iloc[0]

m = st.columns(4)
with m[0]:
    st.markdown(metric_tile("Total spend (30d)", f"${total:,.0f}"), unsafe_allow_html=True)
with m[1]:
    st.markdown(metric_tile("Last 7 days", f"${last7:,.0f}", f"{delta:+.0f}% vs prior week"), unsafe_allow_html=True)
with m[2]:
    st.markdown(metric_tile("Top team", top_team["team"], f"${top_team['cost']:,.0f}"), unsafe_allow_html=True)
with m[3]:
    n_anom = len(anomaly_days(df))
    st.markdown(metric_tile("Anomaly days", str(n_anom), "flagged below", accent=n_anom > 0), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Anomaly flag
# ---------------------------------------------------------------------------
anoms = anomaly_days(df)
if not anoms.empty:
    rng = f"{anoms['date'].min().date()} → {anoms['date'].max().date()}"
    spike = anoms["cost"].sum()
    banner(
        f"<b>Anomaly detected:</b> spend roughly doubled during {rng} "
        f"(${spike:,.0f} across {len(anoms)} days). Investigate before month-end.",
        kind="danger",
        icon="\U0001F6A8",
    )

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
st.markdown("### Spend dashboard")
row1 = st.columns([1, 1.4])

with row1[0]:
    st.markdown("**Total spend by provider**")
    prov = by_provider(df)
    fig = px.pie(prov, names="provider", values="cost", hole=0.55,
                 color_discrete_sequence=CHART_COLORS)
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(style_fig(fig, height=320), use_container_width=True)

with row1[1]:
    st.markdown("**Daily spend trend** (anomalies in red)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["cost"], mode="lines",
        line=dict(color=ACCENT, width=3), name="Daily spend",
        fill="tozeroy", fillcolor="rgba(91,95,237,0.08)",
    ))
    am = daily[daily["is_anomaly"]]
    if not am.empty:
        fig.add_trace(go.Scatter(
            x=am["date"], y=am["cost"], mode="markers",
            marker=dict(color=DANGER, size=10, line=dict(color="#fff", width=1)),
            name="Anomaly",
        ))
    st.plotly_chart(style_fig(fig, height=320), use_container_width=True)

st.markdown("**Spend by team**")
team = by_team(df)
fig = px.bar(team, x="team", y="cost", color="team", color_discrete_sequence=CHART_COLORS)
fig.update_layout(showlegend=False)
fig.update_traces(marker_line_width=0)
st.plotly_chart(style_fig(fig, height=320), use_container_width=True)

st.caption("All figures are synthetic and for demonstration only.")
