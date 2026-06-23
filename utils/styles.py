"""Shared visual styling for the AI Ops Intelligence Suite.

A single indigo-accented, light dashboard theme used across every page so the
suite feels cohesive. The full CSS block is also injected from ``app.py``.
"""
from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------
ACCENT = "#5B5FED"          # indigo
ACCENT_SOFT = "#EEF0FE"     # indigo tint for fills / chips
ACCENT_DARK = "#3F43C9"
BG = "#F6F7FB"              # app background (cool, premium light)
SURFACE = "#FFFFFF"         # cards
INK = "#101426"            # primary text (high contrast)
MUTED = "#5A6275"          # secondary text (AA contrast on white)
BORDER = "#E6E8F2"
GRID = "#EEF0F7"           # subtle chart gridlines
SUCCESS = "#15A34A"
DANGER = "#E11D48"
WARNING = "#D97706"

# Categorical palette for charts — indigo-led, high-contrast, harmonious.
CHART_COLORS = ["#5B5FED", "#0EA5E9", "#F59E0B", "#10B981", "#F43F5E", "#8B5CF6"]

GITHUB_URL = "https://github.com/arthursmith"  # placeholder — update me


def _css() -> str:
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: {INK};
    }}

    .stApp {{ background-color: {BG}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }}

    h1, h2, h3, h4 {{ font-family: 'Inter', sans-serif; color: {INK}; font-weight: 700; letter-spacing: -0.01em; }}
    h1 {{ font-weight: 800; }}
    a {{ color: {ACCENT}; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
    [data-testid="stSidebar"] .block-container {{ padding-top: 1.5rem; }}

    /* ---- Hero ---- */
    .hero {{
        background: linear-gradient(135deg, {ACCENT} 0%, {ACCENT_DARK} 100%);
        border-radius: 18px; padding: 2.4rem 2.4rem; color: #fff;
        box-shadow: 0 18px 40px -18px rgba(91,95,237,0.55); margin-bottom: 1.6rem;
    }}
    .hero h1 {{ color: #fff; font-size: 2.1rem; margin: 0 0 .55rem 0; }}
    .hero p {{ color: rgba(255,255,255,0.92); font-size: 1.02rem; line-height: 1.6; margin: 0; max-width: 760px; }}
    .hero .eyebrow {{
        display:inline-block; font-size:.72rem; font-weight:600; letter-spacing:.14em;
        text-transform:uppercase; background:rgba(255,255,255,.16); padding:.32rem .7rem;
        border-radius:999px; margin-bottom:1rem;
    }}

    /* ---- Cards ---- */
    .card {{
        background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 16px;
        padding: 1.4rem 1.4rem; box-shadow: 0 1px 3px rgba(16,24,40,0.04), 0 8px 24px -16px rgba(16,24,40,0.18);
        transition: transform .15s ease, box-shadow .15s ease; height: 100%;
    }}
    .card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 32px -14px rgba(91,95,237,0.35); }}
    .card .ico {{
        width: 42px; height: 42px; border-radius: 11px; background: {ACCENT_SOFT}; color: {ACCENT};
        display:flex; align-items:center; justify-content:center; font-size: 1.25rem; margin-bottom: .85rem;
    }}
    .card h3 {{ margin: 0 0 .4rem 0; font-size: 1.08rem; }}
    .card p {{ color: {MUTED}; font-size: .9rem; line-height: 1.55; margin: 0 0 .9rem 0; }}
    .card .go {{ color: {ACCENT}; font-weight: 600; font-size: .88rem; }}

    /* ---- Metric tiles ---- */
    .tile {{
        background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
        padding: 1.05rem 1.2rem; box-shadow: 0 1px 3px rgba(16,24,40,0.05); height: 100%;
    }}
    .tile .label {{ color: {MUTED}; font-size: .76rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; }}
    .tile .value {{ color: {INK}; font-size: 1.7rem; font-weight: 800; line-height: 1.15; margin-top: .25rem; letter-spacing: -0.02em; }}
    .tile .sub {{ color: {MUTED}; font-size: .8rem; margin-top: .2rem; }}
    .tile.accent {{ background: linear-gradient(135deg, {ACCENT} 0%, {ACCENT_DARK} 100%); border: none; }}
    .tile.accent .label, .tile.accent .sub {{ color: rgba(255,255,255,.85); }}
    .tile.accent .value {{ color: #fff; }}

    /* ---- Streamlit native metric polish ---- */
    [data-testid="stMetric"] {{
        background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
        padding: 1rem 1.1rem; box-shadow: 0 1px 3px rgba(16,24,40,0.05);
    }}
    [data-testid="stMetricLabel"] {{ color: {MUTED}; }}

    /* ---- Banners / chips ---- */
    .banner {{
        border-radius: 12px; padding: .8rem 1.05rem; font-size: .9rem; font-weight: 500;
        display:flex; align-items:flex-start; gap:.6rem; margin-bottom: 1.2rem; line-height: 1.5;
    }}
    .banner .banner-ico {{ flex: 0 0 auto; font-size: 1.05rem; line-height: 1.45; }}
    .banner .banner-text {{ flex: 1 1 auto; }}
    .banner .banner-text b {{ font-weight: 700; }}
    .banner.info {{ background: {ACCENT_SOFT}; color: {ACCENT_DARK}; border: 1px solid #DDE0FB; }}
    .banner.danger {{ background: #FEF0F3; color: {DANGER}; border: 1px solid #FBD5DE; }}
    .banner.warn {{ background: #FEF6E7; color: {WARNING}; border: 1px solid #FBE6C0; }}

    .pill {{
        display:inline-block; padding:.22rem .6rem; border-radius:999px; font-size:.74rem;
        font-weight:600; background:{ACCENT_SOFT}; color:{ACCENT_DARK};
    }}
    .pill.good {{ background:#E7F7EE; color:{SUCCESS}; }}
    .pill.bad  {{ background:#FEEAEF; color:{DANGER}; }}

    /* ---- Buttons ---- */
    .stButton > button {{
        border-radius: 10px; border: 1px solid {BORDER}; font-weight: 600; padding: .45rem 1rem;
        transition: all .15s ease;
    }}
    .stButton > button:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
    .stButton > button[kind="primary"] {{ background: {ACCENT}; border-color: {ACCENT}; color: #fff; }}
    .stButton > button[kind="primary"]:hover {{ background: {ACCENT_DARK}; border-color: {ACCENT_DARK}; color: #fff; }}

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {{ gap: .4rem; }}
    .stTabs [data-baseweb="tab"] {{ border-radius: 10px 10px 0 0; }}

    /* ---- Credit ---- */
    .credit {{ font-size: .82rem; color: {MUTED}; line-height: 1.5; }}
    .credit b {{ color: {INK}; }}
    .credit a {{ color: {ACCENT}; font-weight: 600; }}

    /* Hide Streamlit's auto-generated page nav — we render a branded one. */
    [data-testid="stSidebarNav"] {{ display: none; }}

    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    </style>
    """


def inject_css() -> None:
    """Inject the suite-wide CSS theme. Call once near the top of every page."""
    st.markdown(_css(), unsafe_allow_html=True)


def sidebar_credit() -> None:
    """Small 'Built by Arthur Smith' credit with a GitHub link placeholder."""
    with st.sidebar:
        st.markdown("---")
        st.markdown(
            f"""
            <div class="credit">
              Built by <b>Arthur Smith</b><br/>
              <a href="{GITHUB_URL}" target="_blank">GitHub &rarr;</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


def sidebar_nav() -> None:
    """Branded sidebar navigation (replaces Streamlit's hidden auto-nav)."""
    with st.sidebar:
        st.markdown(
            f"<h2 style='margin-bottom:.1rem;'>\U0001F4CA AI Ops</h2>"
            f"<div style='color:{ACCENT}; font-weight:600; font-size:.78rem; "
            f"letter-spacing:.1em; text-transform:uppercase;'>Intelligence Suite</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        st.markdown("**Navigate**")
        st.page_link("app.py", label="Home", icon="\U0001F3E0")
        st.page_link("pages/1_Model_Regression_Tester.py", label="Model Regression Tester", icon="\U0001F9EA")
        st.page_link("pages/2_Spend_Attribution.py", label="Spend Attribution", icon="\U0001F4B8")
        st.page_link("pages/3_Benchmark_Tracker.py", label="Benchmark Tracker", icon="\U0001F3C6")
    sidebar_credit()


def page_header(title: str, subtitle: str, icon: str = "") -> None:
    st.markdown(
        f"""
        <div style="margin-bottom:1.3rem;">
          <h1 style="margin-bottom:.25rem;">{icon} {title}</h1>
          <p style="color:{MUTED}; font-size:1rem; margin:0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_tile(label: str, value: str, sub: str = "", accent: bool = False) -> str:
    cls = "tile accent" if accent else "tile"
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="{cls}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'


def banner(text: str, kind: str = "info", icon: str = "") -> None:
    st.markdown(
        f'<div class="banner {kind}"><span class="banner-ico">{icon}</span>'
        f'<span class="banner-text">{text}</span></div>',
        unsafe_allow_html=True,
    )


def style_fig(fig, height: int = 360):
    """Apply the suite's clean, high-contrast look to a Plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=12, t=36, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        title_font=dict(family="Inter, sans-serif", size=15, color=INK),
        colorway=CHART_COLORS,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font=dict(size=12, color=MUTED), bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF", bordercolor=BORDER,
            font=dict(family="Inter, sans-serif", size=12, color=INK),
        ),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False, linecolor=BORDER, ticks="outside",
        tickcolor=BORDER, tickfont=dict(color=MUTED, size=12),
        title_font=dict(color=MUTED, size=12),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)",
        tickfont=dict(color=MUTED, size=12), title_font=dict(color=MUTED, size=12),
    )
    return fig
