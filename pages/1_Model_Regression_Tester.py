"""Model Regression Tester — compare two frontier models head-to-head.

Runs the same prompts across two models concurrently (asyncio), captures
latency / tokens / cost, then uses claude-sonnet-4-6 as a meta-evaluator to
score each output pair on accuracy, clarity and completeness.
"""
from __future__ import annotations

import asyncio
import json

import pandas as pd
import streamlit as st

from utils.llm import call_model, claude_json, claude_sync
from utils.pricing import MODELS, REGRESSION_MODELS
from utils.secrets import has_secret
from utils.styles import (
    ACCENT,
    banner,
    inject_css,
    metric_tile,
    page_header,
    sidebar_credit,
)

st.set_page_config(page_title="Model Regression Tester", page_icon="\U0001F9EA", layout="wide")
inject_css()
sidebar_credit()

page_header(
    "Model Regression Tester",
    "Compare two models on the same prompts — latency, cost, and Claude-judged quality.",
    icon="\U0001F9EA",
)

PROVIDER_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GEMINI_API_KEY",
}

EXAMPLE_PROMPTS = [
    "Explain the difference between concurrency and parallelism to a junior engineer, with one concrete analogy.",
    "Write a Python function that returns the nth Fibonacci number using memoization. Include a docstring.",
    "Summarize the key risks of deploying LLMs in production in exactly three bullet points.",
    "Extract the company, role, and salary from: 'Acme Corp is hiring a Staff ML Engineer at $220k base.' Return JSON.",
    "A train leaves at 3:15pm traveling 60mph. Another leaves the same station at 4:00pm at 80mph. When does the second catch up?",
]

NUM_SLOTS = 5

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
for i in range(NUM_SLOTS):
    st.session_state.setdefault(f"reg_prompt_{i}", "")

ctrl = st.columns([1, 1, 1.2])
with ctrl[0]:
    model_a = st.selectbox("Model A", REGRESSION_MODELS, index=0)
with ctrl[1]:
    model_b = st.selectbox("Model B", REGRESSION_MODELS, index=2)
with ctrl[2]:
    st.markdown("<div style='height:1.85rem;'></div>", unsafe_allow_html=True)
    if st.button("\U0001F4DD Load example prompts", use_container_width=True):
        for i, p in enumerate(EXAMPLE_PROMPTS):
            st.session_state[f"reg_prompt_{i}"] = p
        st.rerun()

st.markdown("**Test prompts** _(up to 5 — leave blank to skip)_")
pcols = st.columns(2)
for i in range(NUM_SLOTS):
    with pcols[i % 2]:
        st.text_area(f"Prompt {i + 1}", key=f"reg_prompt_{i}", height=90)

run = st.button("\u25B6 Run Regression Test", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Async execution
# ---------------------------------------------------------------------------
async def _run_all(prompts: list[str], ma: str, mb: str) -> list[dict]:
    tasks = []
    for p in prompts:
        tasks.append(call_model(ma, p))
        tasks.append(call_model(mb, p))
    flat = await asyncio.gather(*tasks)
    paired = []
    for idx, p in enumerate(prompts):
        paired.append({"prompt": p, "a": flat[idx * 2], "b": flat[idx * 2 + 1]})
    return paired


def _evaluate(results: list[dict], ma: str, mb: str) -> list[dict]:
    """One batched Claude call → quality scores for every prompt/output pair."""
    blocks = []
    for i, r in enumerate(results):
        a_out = (r["a"]["output"] or "(no output / error)")[:1500]
        b_out = (r["b"]["output"] or "(no output / error)")[:1500]
        blocks.append(
            f"### Prompt {i}\nPROMPT: {r['prompt']}\n\n"
            f"[MODEL_A = {ma}] OUTPUT:\n{a_out}\n\n"
            f"[MODEL_B = {mb}] OUTPUT:\n{b_out}\n"
        )
    body = "\n".join(blocks)
    system = (
        "You are a rigorous, impartial LLM output evaluator. Score each model's output "
        "from 1-10 (integers) on accuracy, clarity, and completeness. Be discriminating."
    )
    prompt = (
        f"Evaluate the following {len(results)} prompt/output pairs.\n\n{body}\n\n"
        "Return ONLY a JSON array, one object per prompt, in order, shaped exactly like:\n"
        '[{"index":0,"model_a":{"accuracy":7,"clarity":8,"completeness":6},'
        '"model_b":{"accuracy":9,"clarity":8,"completeness":9}}]'
    )
    try:
        data = claude_json(prompt, system=system, max_tokens=1200)
        if isinstance(data, dict):
            data = data.get("results", [])
        return data
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Meta-evaluation failed: {exc}")
        return []


def _verdict(summary: dict) -> str:
    prompt = (
        "Two models were compared on identical prompts. Here are the aggregates:\n"
        f"{json.dumps(summary, indent=2)}\n\n"
        "In 2-4 sentences, declare which model 'won' overall and explain why, explicitly "
        "weighing quality against cost and latency. Be concrete and decisive."
    )
    try:
        return claude_sync(prompt, max_tokens=350, temperature=0.3)
    except Exception as exc:  # noqa: BLE001
        return f"_Verdict unavailable: {exc}_"


# ---------------------------------------------------------------------------
# Trigger
# ---------------------------------------------------------------------------
if run:
    prompts = [st.session_state[f"reg_prompt_{i}"].strip() for i in range(NUM_SLOTS)]
    prompts = [p for p in prompts if p]

    needed = {PROVIDER_KEYS[MODELS[m]["provider"]] for m in (model_a, model_b)}
    needed.add("ANTHROPIC_API_KEY")  # evaluator
    missing = [k for k in needed if not has_secret(k)]

    if model_a == model_b:
        st.error("Pick two **different** models to compare.")
    elif not prompts:
        st.error("Add at least one prompt (or click **Load example prompts**).")
    elif missing:
        st.error("Missing API key(s): " + ", ".join(sorted(missing)) + ". Add them in secrets / env vars.")
    else:
        with st.spinner(f"Running {len(prompts)} prompt(s) on {model_a} and {model_b} in parallel…"):
            results = asyncio.run(_run_all(prompts, model_a, model_b))
        with st.spinner("Claude is scoring every output pair…"):
            scores = _evaluate(results, model_a, model_b)

        score_by_index = {s.get("index", i): s for i, s in enumerate(scores)}
        for i, r in enumerate(results):
            s = score_by_index.get(i, {})
            r["a"]["scores"] = s.get("model_a", {})
            r["b"]["scores"] = s.get("model_b", {})

        st.session_state["reg_results"] = results
        st.session_state["reg_models"] = (model_a, model_b)
        # Build verdict from aggregates.
        def _avg(side: str, field: str) -> float:
            vals = [r[side]["scores"].get(field) for r in results if r[side]["scores"].get(field)]
            return round(sum(vals) / len(vals), 1) if vals else 0.0

        summary = {
            model_a: {
                "avg_quality": round((_avg("a", "accuracy") + _avg("a", "clarity") + _avg("a", "completeness")) / 3, 1),
                "avg_latency_ms": round(sum(r["a"]["latency_ms"] for r in results) / len(results)),
                "total_cost_usd": round(sum(r["a"]["cost"] for r in results), 4),
            },
            model_b: {
                "avg_quality": round((_avg("b", "accuracy") + _avg("b", "clarity") + _avg("b", "completeness")) / 3, 1),
                "avg_latency_ms": round(sum(r["b"]["latency_ms"] for r in results) / len(results)),
                "total_cost_usd": round(sum(r["b"]["cost"] for r in results), 4),
            },
        }
        with st.spinner("Writing the verdict…"):
            st.session_state["reg_verdict"] = _verdict(summary)


# ---------------------------------------------------------------------------
# Render results (persisted in session_state)
# ---------------------------------------------------------------------------
results = st.session_state.get("reg_results")
if results:
    model_a, model_b = st.session_state.get("reg_models", (model_a, model_b))
    n = len(results)

    all_calls = [r["a"] for r in results] + [r["b"] for r in results]
    total_cost = sum(c["cost"] for c in all_calls)
    avg_latency = round(sum(c["latency_ms"] for c in all_calls) / len(all_calls))
    total_in = sum(c["input_tokens"] for c in all_calls)
    total_out = sum(c["output_tokens"] for c in all_calls)
    total_tokens = max(total_in + total_out, 1)
    cost_per_token = total_cost / total_tokens
    projected_1m_day = cost_per_token * 1_000_000

    st.markdown("### Run summary")
    m = st.columns(3)
    with m[0]:
        st.markdown(metric_tile("Avg latency", f"{avg_latency:,} ms", "across both models"), unsafe_allow_html=True)
    with m[1]:
        st.markdown(metric_tile("Avg cost / run", f"${total_cost / n:.4f}", f"{n} prompt(s), both models"), unsafe_allow_html=True)
    with m[2]:
        st.markdown(
            metric_tile("Projected @ 1M tok/day", f"${projected_1m_day:,.2f}", "blended at observed mix", accent=True),
            unsafe_allow_html=True,
        )

    # Verdict
    verdict = st.session_state.get("reg_verdict")
    if verdict:
        st.markdown("### \U0001F3C5 Verdict")
        with st.container(border=True):
            st.markdown(verdict)

    # Quality bar chart (st.bar_chart): quality score per prompt per model
    st.markdown("### Quality scores by prompt")

    def _composite(side_scores: dict) -> float:
        vals = [side_scores.get(k) for k in ("accuracy", "clarity", "completeness")]
        vals = [v for v in vals if isinstance(v, (int, float))]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    chart_df = pd.DataFrame(
        {
            model_a: [_composite(r["a"]["scores"]) for r in results],
            model_b: [_composite(r["b"]["scores"]) for r in results],
        },
        index=[f"P{i + 1}" for i in range(n)],
    )
    st.bar_chart(chart_df, height=320, color=[ACCENT, "#22B8CF"])
    st.caption("Composite quality = mean of accuracy, clarity & completeness (1–10), judged by claude-sonnet-4-6.")

    # Side-by-side outputs
    st.markdown("### Side-by-side outputs")

    def _stat_row(call: dict) -> str:
        if call["error"]:
            return f"<span class='pill bad'>error</span>"
        s = call["scores"] or {}
        sc = " ".join(
            f"<span class='pill'>{k[:3].title()} {s.get(k, '–')}</span>"
            for k in ("accuracy", "clarity", "completeness")
        )
        return (
            f"<span class='pill'>{call['latency_ms']:,} ms</span> "
            f"<span class='pill'>{call['input_tokens']}\u2192{call['output_tokens']} tok</span> "
            f"<span class='pill'>${call['cost']:.4f}</span> {sc}"
        )

    for i, r in enumerate(results):
        st.markdown(f"**Prompt {i + 1}.** {r['prompt']}")
        c1, c2 = st.columns(2)
        for col, side, model in ((c1, "a", model_a), (c2, "b", model_b)):
            call = r[side]
            with col:
                st.markdown(
                    f"<div class='card'><h3 style='font-size:.95rem;'>{model}</h3>"
                    f"<div style='margin-bottom:.6rem;'>{_stat_row(call)}</div></div>",
                    unsafe_allow_html=True,
                )
                if call["error"]:
                    st.error(call["error"])
                else:
                    st.markdown(call["output"] or "_(empty response)_")
        st.markdown("---")
else:
    banner("Add prompts (or load the examples) and hit <b>Run Regression Test</b> to begin.", kind="info", icon="\U0001F4A1")
