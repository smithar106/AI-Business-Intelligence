# AI Ops Intelligence Suite

A polished, light, multi-page **Streamlit** dashboard for teams running AI in
production. Three tools in one app:

| Tool | What it does |
| --- | --- |
| **🧪 Model Regression Tester** | Run the same prompts across two frontier models **in parallel** (asyncio), capture latency / tokens / cost, and use `claude-sonnet-4-6` as a meta-evaluator to score every output on accuracy, clarity & completeness. |
| **💸 Spend Attribution** | Ask plain-English questions about AI spend. Claude reads 30 days of synthetic usage attributed across teams & providers, flags anomalies, and answers with supporting data. *(Demo mode.)* |
| **🏆 Benchmark Tracker** | Track open-source models across MMLU, HumanEval, MATH, HellaSwag & MT-Bench, rank by **price-adjusted** performance, and get alerted on benchmark regressions. |

The suite uses a single indigo-accented light theme (Inter font, `#F8F9FA`
background, `#5B5FED` accent, soft-shadow cards & metric tiles).

## Project structure

```
ai-ops-intelligence-suite/
├── app.py                              # Landing page + CSS theme + sidebar nav
├── pages/
│   ├── 1_Model_Regression_Tester.py
│   ├── 2_Spend_Attribution.py
│   └── 3_Benchmark_Tracker.py
├── utils/
│   ├── __init__.py
│   ├── secrets.py                      # st.secrets → os.environ resolver
│   ├── styles.py                       # Theme/CSS, cards, tiles, plotly styling
│   ├── pricing.py                      # Model registry + pricing dicts
│   ├── llm.py                          # Async multi-provider calls + sync Claude
│   ├── synthetic.py                    # Synthetic spend dataset (page 2)
│   └── leaderboard.py                  # HF leaderboard fetch + fallback (page 3)
├── .streamlit/
│   ├── config.toml                     # Light theme
│   └── secrets.toml.example
├── requirements.txt
├── Procfile                            # Railway: web: streamlit run app.py ...
├── .env.example
└── README.md
```

## Environment variables

All Claude features use a **standard** `ANTHROPIC_API_KEY` from
[console.anthropic.com](https://console.anthropic.com) — *not* an admin /
workspace key. No admin or workspace-management endpoints are used anywhere.

| Variable | Used by |
| --- | --- |
| `ANTHROPIC_API_KEY` | All three pages |
| `DEEPSEEK_API_KEY` | Model Regression Tester |
| `GEMINI_API_KEY` | Model Regression Tester |
| `HUGGINGFACE_TOKEN` | Benchmark Tracker |

Keys are read via `st.secrets` first, then `os.environ` — so the same code works
on Streamlit Cloud, Railway, Docker, and local `.env`.

## Run locally

```bash
pip install -r requirements.txt

# Option A — Streamlit secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit
# Option B — environment variables
cp .env.example .env                                         # then edit

streamlit run app.py
```

## Deploy on Railway

1. Push this repo to GitHub and create a new Railway project from it.
2. Add the environment variables above in the Railway dashboard.
3. Railway uses the `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

## Notes

- **Spend Attribution runs in demo mode** on deterministic synthetic data
  (weekday spikes, weekend dips, one anomaly week where spend doubles). No real
  billing data is exposed.
- **Benchmark Tracker** verifies your `HUGGINGFACE_TOKEN` for a live connection.
  Because the public Open LLM Leaderboard was archived and has no stable
  endpoint for this exact benchmark set, the app displays curated
  *representative* scores and labels the data source in the UI. Pricing and the
  6 tracked models live in `utils/pricing.py`.
- Frontier model IDs are centralized in `utils/pricing.py` — update them there if
  a provider renames a model.

---

Built by **Arthur Smith** · [GitHub](https://github.com/arthursmith) *(placeholder — update the link)*
