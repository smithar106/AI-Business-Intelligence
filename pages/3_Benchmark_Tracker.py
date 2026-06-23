"""Benchmark Tracker — open-source models ranked by price-adjusted performance.

Pulls leaderboard data from Hugging Face (token-verified) with a clearly
labelled representative fallback, computes a price-adjusted score, flags
benchmark regressions vs. the last cached run, and asks Claude to summarize
what changed this week.
"""
from __future__ import annotations

from datetime import datetime

import plotly.express as px
import streamlit as st

from utils.leaderboard import diff_leaderboard, fetch_leaderboard
from utils.llm import claude_sync, md_escape
from utils.pricing import BENCHMARKS
from utils.secrets import get_secret, has_secret
from utils.styles import (
    ACCENT,
    CHART_COLORS,
    INK,
    banner,
    inject_css,
    metric_tile,
    page_header,
    sidebar_nav,
    style_fig,
)

st.set_page_config(page_title="Benchmark Tracker", page_icon="\U0001F3C6", layout="wide")
inject_css()
sidebar_nav()

page_header(
    "Benchmark Tracker",
    "Open-source models scored, priced, and ranked by bang-for-buck — with regression alerts.",
    icon="\U0001F3C6",
)

HF_TOKEN = get_secret("HUGGINGFACE_TOKEN")


def _load(jitter: int):
    return fetch_leaderboard(HF_TOKEN, jitter_seed=jitter)


# ---------------------------------------------------------------------------
# Initial load (cached in session_state)
# ---------------------------------------------------------------------------
if "bench_df" not in st.session_state:
    data = _load(0)
    st.session_state.bench_df = data["df"]
    st.session_state.bench_source = data["source"]
    st.session_state.bench_live = data["live"]
    st.session_state.bench_ts = datetime.now()
    st.session_state.bench_refresh = 0
    st.session_state.bench_prev = None
    st.session_state.bench_alerts = []
    st.session_state.bench_summary = None

# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------
top = st.columns([2.4, 1])
with top[0]:
    src = st.session_state.bench_source
    ts = st.session_state.bench_ts.strftime("%b %d, %Y %H:%M")
    tag = "good" if st.session_state.bench_live else "bad"
    st.markdown(
        f"<div class='statusbox'><span class='pill {tag}'>{src}</span>"
        f"<span>cached {ts}</span></div>",
        unsafe_allow_html=True,
    )
with top[1]:
    if st.button("\U0001F504 Refresh data", use_container_width=True):
        st.session_state.bench_prev = st.session_state.bench_df
        st.session_state.bench_refresh += 1
        data = _load(st.session_state.bench_refresh)
        st.session_state.bench_df = data["df"]
        st.session_state.bench_source = data["source"]
        st.session_state.bench_live = data["live"]
        st.session_state.bench_ts = datetime.now()
        st.session_state.bench_alerts = diff_leaderboard(
            st.session_state.bench_df, st.session_state.bench_prev
        )
        st.session_state.bench_summary = None
        st.rerun()

if not HF_TOKEN:
    banner(
        "No <b>HUGGINGFACE_TOKEN</b> set — showing a representative dataset. Add the token to verify a live connection.",
        kind="warn",
        icon="\u26A0\uFE0F",
    )

df = st.session_state.bench_df

# ---------------------------------------------------------------------------
# Best price-adjusted model (top tile)
# ---------------------------------------------------------------------------
best = df.sort_values("price_adjusted", ascending=False).iloc[0]
cheapest = df.sort_values("cost_per_1m").iloc[0]
strongest = df.sort_values("composite", ascending=False).iloc[0]

m = st.columns([1.4, 1, 1])
with m[0]:
    st.markdown(
        metric_tile(
            "Best price-adjusted model",
            best["model"],
            f"{best['price_adjusted']:.1f} pts per $/1M  •  composite {best['composite']:.1f}",
            accent=True,
        ),
        unsafe_allow_html=True,
    )
with m[1]:
    st.markdown(metric_tile("Strongest overall", strongest["model"], f"composite {strongest['composite']:.1f}"), unsafe_allow_html=True)
with m[2]:
    st.markdown(metric_tile("Cheapest", cheapest["model"], f"${cheapest['cost_per_1m']:.2f} / 1M tok"), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Regression alerts
# ---------------------------------------------------------------------------
st.markdown("### \U0001F6A8 Regression alerts")
alerts = st.session_state.bench_alerts
if st.session_state.bench_prev is None:
    banner("No prior run cached yet. Hit <b>Refresh data</b> to capture a new snapshot and compare.", kind="info", icon="\u2139\uFE0F")
elif alerts:
    for a in alerts:
        banner(
            f"<b>{a['model']}</b> · {a['benchmark']} dropped <b>{a['delta']:.2f}</b> pts "
            f"({a['old']:.1f} → {a['new']:.1f}) since last run.",
            kind="danger",
            icon="\U0001F4C9",
        )
else:
    banner("No regressions over 2 points since the last cached run.", kind="info", icon="\u2705")

# ---------------------------------------------------------------------------
# Leaderboard table (sortable)
# ---------------------------------------------------------------------------
st.markdown("### Leaderboard")
display_cols = ["model"] + BENCHMARKS + ["composite", "cost_per_1m", "price_adjusted", "n_benchmarks"]
st.dataframe(
    df[display_cols],
    hide_index=True,
    use_container_width=True,
    column_config={
        "model": st.column_config.TextColumn("Model"),
        "cost_per_1m": st.column_config.NumberColumn("Cost / 1M", format="$%.2f"),
        "composite": st.column_config.NumberColumn("Composite", format="%.1f"),
        "price_adjusted": st.column_config.NumberColumn("Price-adjusted", format="%.1f"),
        "n_benchmarks": st.column_config.NumberColumn("# Benchmarks"),
        **{b: st.column_config.NumberColumn(b, format="%.1f") for b in BENCHMARKS},
    },
)
st.caption("Click any column header to sort. Composite = mean of the 5 benchmarks (MT-Bench scaled ×10).")

# ---------------------------------------------------------------------------
# Price-adjusted ranking (the screenshot chart)
# ---------------------------------------------------------------------------
st.markdown("### Price-adjusted ranking")
pa = df.sort_values("price_adjusted", ascending=True)  # ascending → best on top in h-bar
fig = px.bar(
    pa, x="price_adjusted", y="model", orientation="h",
    color="price_adjusted", color_continuous_scale=["#C7CBDD", ACCENT],
    text=pa["price_adjusted"].map(lambda v: f"{v:.0f}"),
)
fig.update_traces(
    textposition="outside", textfont=dict(color=INK, size=12),
    marker_line_width=0,
    hovertemplate="<b>%{y}</b><br>%{x:.1f} pts per $/1M tokens<extra></extra>",
)
fig.update_layout(
    coloraxis_showscale=False,
    xaxis_title="Price-adjusted score  (composite ÷ cost per 1M tokens)",
    yaxis_title=None,
    xaxis_range=[0, pa["price_adjusted"].max() * 1.15],
)
st.plotly_chart(style_fig(fig, height=360), use_container_width=True)
st.caption("Higher = more quality per dollar. Best bang-for-buck sits at the top.")

# ---------------------------------------------------------------------------
# Scatter: cost vs composite (bubble = # benchmarks)
# ---------------------------------------------------------------------------
st.markdown("### Price vs. performance")
_ABBR = {
    "Llama 3 8B": "L3-8B", "Llama 3 70B": "L3-70B", "Mistral 7B": "M-7B",
    "Mixtral 8x7B": "MX-8x7B", "Gemma 7B": "G-7B", "Falcon 40B": "F-40B",
}
sc = df.copy()
sc["abbr"] = sc["model"].map(_ABBR).fillna(sc["model"])
fig = px.scatter(
    sc, x="cost_per_1m", y="composite", color="model", text="abbr",
    color_discrete_sequence=CHART_COLORS,
    custom_data=["model", "cost_per_1m", "composite"],
)
fig.update_traces(
    marker=dict(size=12, line=dict(width=1.5, color="#FFFFFF"), opacity=0.95),
    textposition="top center", textfont=dict(size=11, color=INK),
    hovertemplate="<b>%{customdata[0]}</b><br>$%{customdata[1]:.2f}/1M tokens"
                  "  ·  composite %{customdata[2]:.1f}<extra></extra>",
)
xmin, xmax = sc["cost_per_1m"].min(), sc["cost_per_1m"].max()
ymin, ymax = sc["composite"].min(), sc["composite"].max()
xpad = max((xmax - xmin) * 0.20, 0.15)
ypad = max((ymax - ymin) * 0.22, 4)
fig.update_layout(
    showlegend=False,
    xaxis_title="Cost per 1M tokens ($)",
    yaxis_title="Composite score",
    xaxis_range=[xmin - xpad, xmax + xpad],
    yaxis_range=[ymin - ypad, ymax + ypad],
)
st.plotly_chart(style_fig(fig, height=440), use_container_width=True)

# ---------------------------------------------------------------------------
# Claude summary: what changed this week
# ---------------------------------------------------------------------------
st.markdown("### \U0001F4DD What changed in the leaderboard this week")
if not has_secret("ANTHROPIC_API_KEY"):
    st.info("Set `ANTHROPIC_API_KEY` to generate the narrative summary.")
else:
    if st.session_state.bench_summary is None:
        table_txt = df[display_cols].to_string(index=False)
        alert_txt = (
            "\n".join(f"- {a['model']} {a['benchmark']} {a['delta']:+.2f}" for a in alerts)
            if alerts else "None over 2 points."
        )
        prompt = (
            "You are an ML analyst writing a weekly leaderboard briefing. Use EXACTLY this "
            "structure and nothing else:\n"
            "- Line 1: a single plain sentence summarizing the week (no emoji, no bold).\n"
            "- Then exactly 3 lines, each on its own line, each starting with one emoji and a "
            "bold label, in this order:\n"
            "    \U0001F3C6 Best price-adjusted pick: ...\n"
            "    \u26A0\uFE0F Worst cost/quality tradeoff: ...\n"
            "    \U0001F4CA Notable tradeoff: ...\n"
            "Keep each line to one sentence. Do not add headers, intros, or extra lines. "
            "Under 130 words total.\n\n"
            f"LEADERBOARD:\n{table_txt}\n\nREGRESSIONS SINCE LAST RUN:\n{alert_txt}"
        )
        with st.spinner("Claude is summarizing the leaderboard…"):
            try:
                st.session_state.bench_summary = claude_sync(prompt, max_tokens=420, temperature=0.3)
            except Exception as exc:  # noqa: BLE001
                st.session_state.bench_summary = f"_Summary unavailable: {exc}_"

    # Render every line in one consistent format: each non-empty line as its own
    # paragraph (uniform spacing), regardless of how the model spaced them.
    _lines = [ln.strip() for ln in (st.session_state.bench_summary or "").splitlines() if ln.strip()]
    with st.container(border=True):
        st.markdown(md_escape("\n\n".join(_lines)))
