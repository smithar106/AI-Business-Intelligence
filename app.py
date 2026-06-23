"""
AI Ops Intelligence Suite — main entry point.

A polished, light multi-page Streamlit dashboard for AI operations teams:
regression-test frontier models, attribute AI spend, and track open-source
benchmarks. Deployed on Railway via the included Procfile.

The suite-wide CSS theme (Inter font, #F8F9FA background, #5B5FED indigo
accent, soft-shadow cards and metric tiles) is injected from inject_css().
"""
from __future__ import annotations

import streamlit as st

from utils.styles import inject_css, sidebar_credit, ACCENT

st.set_page_config(
    page_title="AI Ops Intelligence Suite",
    page_icon="\U0001F4CA",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

TOOLS = [
    {
        "icon": "\U0001F9EA",
        "title": "Model Regression Tester",
        "desc": "Run the same prompts across two frontier models in parallel, capture "
        "latency, tokens and cost, and let Claude score every output on accuracy, "
        "clarity and completeness.",
        "page": "pages/1_Model_Regression_Tester.py",
        "label": "Open Regression Tester",
    },
    {
        "icon": "\U0001F4B8",
        "title": "Spend Attribution",
        "desc": "Ask plain-English questions about your AI spend. Claude reads 30 days of "
        "usage attributed across teams and models, flags anomalies, and answers "
        "with supporting data. (Demo mode.)",
        "page": "pages/2_Spend_Attribution.py",
        "label": "Open Spend Attribution",
    },
    {
        "icon": "\U0001F3C6",
        "title": "Benchmark Tracker",
        "desc": "Track open-source models across MMLU, HumanEval, MATH, HellaSwag and "
        "MT-Bench, rank them by price-adjusted performance, and get alerted when a "
        "benchmark regresses.",
        "page": "pages/3_Benchmark_Tracker.py",
        "label": "Open Benchmark Tracker",
    },
]


def sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"<h2 style='margin-bottom:.1rem;'>\U0001F4CA AI Ops</h2>"
            f"<div style='color:{ACCENT}; font-weight:600; font-size:.8rem; "
            f"letter-spacing:.08em; text-transform:uppercase;'>Intelligence Suite</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:.8rem;'></div>", unsafe_allow_html=True)
        st.markdown("**Navigate**")
        st.page_link("app.py", label="Home", icon="\U0001F3E0")
        st.page_link("pages/1_Model_Regression_Tester.py", label="Model Regression Tester", icon="\U0001F9EA")
        st.page_link("pages/2_Spend_Attribution.py", label="Spend Attribution", icon="\U0001F4B8")
        st.page_link("pages/3_Benchmark_Tracker.py", label="Benchmark Tracker", icon="\U0001F3C6")
    sidebar_credit()


def hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <span class="eyebrow">AI Operations Platform</span>
          <h1>AI Ops Intelligence Suite</h1>
          <p>
            A unified control center for teams running AI in production. Compare frontier
            models head-to-head with cost and quality scoring, attribute every dollar of
            spend across teams and providers in plain English, and keep an eye on the
            open-source leaderboard — all in one clean, fast dashboard.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def cards() -> None:
    st.markdown("#### Explore the tools")
    cols = st.columns(3, gap="large")
    for col, tool in zip(cols, TOOLS):
        with col:
            st.markdown(
                f"""
                <div class="card">
                  <div class="ico">{tool['icon']}</div>
                  <h3>{tool['title']}</h3>
                  <p>{tool['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.page_link(tool["page"], label=f"{tool['label']}  \u2192")


sidebar()
hero()
cards()
