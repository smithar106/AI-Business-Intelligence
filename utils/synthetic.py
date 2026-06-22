"""Synthetic spend dataset for the Spend Attribution demo (page 2).

Deterministic, realistic-looking data: weekday spikes, weekend dips, and a
single anomaly week where spend roughly doubles. No real API keys / no real
billing data are used.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from .pricing import PROVIDER_OF, SPEND_MODELS, cost_for

TEAMS = ["Engineering", "Product", "Marketing", "Data"]

# Daily baseline INPUT tokens per team (before weekday/model weighting).
_TEAM_BASE = {
    "Engineering": 48_000_000,
    "Product": 26_000_000,
    "Marketing": 16_000_000,
    "Data": 32_000_000,
}

# How each team splits its usage across models (rows sum to 1.0).
_TEAM_MODEL_MIX = {
    "Engineering": {"claude-sonnet-4-6": 0.45, "gpt-4o": 0.30, "claude-haiku-4-5": 0.15, "gpt-4o-mini": 0.10},
    "Product":     {"claude-sonnet-4-6": 0.30, "gpt-4o": 0.25, "claude-haiku-4-5": 0.25, "gpt-4o-mini": 0.20},
    "Marketing":   {"claude-sonnet-4-6": 0.10, "gpt-4o": 0.15, "claude-haiku-4-5": 0.30, "gpt-4o-mini": 0.45},
    "Data":        {"claude-sonnet-4-6": 0.35, "gpt-4o": 0.20, "claude-haiku-4-5": 0.20, "gpt-4o-mini": 0.25},
}

DAYS = 30
ANOMALY_START = 9   # 0-indexed day; a 7-day window that ~doubles spend
ANOMALY_LEN = 7


def generate_spend_df(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    today = date.today()
    start = today - timedelta(days=DAYS - 1)

    rows = []
    for d in range(DAYS):
        day = start + timedelta(days=d)
        weekday = day.weekday()  # 0=Mon … 6=Sun
        weekend = weekday >= 5
        # Weekday spike / weekend dip.
        day_factor = 0.42 if weekend else rng.uniform(0.92, 1.12)
        anomaly = ANOMALY_START <= d < ANOMALY_START + ANOMALY_LEN
        if anomaly:
            day_factor *= rng.uniform(1.9, 2.15)  # spend roughly doubles

        for team in TEAMS:
            base = _TEAM_BASE[team] * day_factor
            for model, weight in _TEAM_MODEL_MIX[team].items():
                noise = rng.uniform(0.85, 1.15)
                in_tok = int(base * weight * noise)
                out_tok = int(in_tok * rng.uniform(0.35, 0.55))
                rows.append(
                    {
                        "date": pd.Timestamp(day),
                        "team": team,
                        "model": model,
                        "provider": PROVIDER_OF[model],
                        "input_tokens": in_tok,
                        "output_tokens": out_tok,
                        "cost": round(cost_for(model, in_tok, out_tok), 2),
                        "is_anomaly": anomaly,
                    }
                )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------
def by_provider(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("provider", as_index=False)["cost"].sum().sort_values("cost", ascending=False)


def by_model(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("model", as_index=False)["cost"].sum().sort_values("cost", ascending=False)


def by_team(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("team", as_index=False)["cost"].sum().sort_values("cost", ascending=False)


def daily_total(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("date", as_index=False).agg(cost=("cost", "sum"), is_anomaly=("is_anomaly", "max"))
    return g.sort_values("date")


def anomaly_days(df: pd.DataFrame) -> pd.DataFrame:
    return daily_total(df).query("is_anomaly")


def build_context(df: pd.DataFrame) -> str:
    """Compact-but-complete text view of the dataset for Claude."""
    total = df["cost"].sum()
    daily = daily_total(df)
    last7 = daily.tail(7)["cost"].sum()
    prev7 = daily.iloc[-14:-7]["cost"].sum() if len(daily) >= 14 else 0.0

    lines = [
        "AI SPEND DATASET (synthetic, last 30 days, USD)",
        f"Total spend: ${total:,.0f}",
        f"Spend last 7 days: ${last7:,.0f} | previous 7 days: ${prev7:,.0f}",
        "",
        "Spend by provider:",
    ]
    for _, r in by_provider(df).iterrows():
        lines.append(f"  - {r['provider']}: ${r['cost']:,.0f}")
    lines.append("\nSpend by model:")
    for _, r in by_model(df).iterrows():
        lines.append(f"  - {r['model']}: ${r['cost']:,.0f}")
    lines.append("\nSpend by team:")
    for _, r in by_team(df).iterrows():
        lines.append(f"  - {r['team']}: ${r['cost']:,.0f}")

    lines.append("\nDaily total spend (date | cost | anomaly):")
    for _, r in daily.iterrows():
        flag = " <-- ANOMALY" if r["is_anomaly"] else ""
        lines.append(f"  {r['date'].date()} | ${r['cost']:,.0f}{flag}")

    anoms = anomaly_days(df)
    if not anoms.empty:
        rng = f"{anoms['date'].min().date()} to {anoms['date'].max().date()}"
        lines.append(f"\nAnomaly window detected: {rng} (spend ~2x normal).")
    return "\n".join(lines)
