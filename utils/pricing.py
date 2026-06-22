"""Central pricing + model registry.

Prices are USD per 1,000,000 tokens and reflect public list pricing at the
time of writing. They are intentionally easy to edit in one place.

``api_model`` is the literal ID sent to each provider's API. If a provider
renames a model, change it here only.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Frontier models — Model Regression Tester (page 1)
# ---------------------------------------------------------------------------
# display name -> provider / api id / price per 1M input / price per 1M output
MODELS: dict[str, dict] = {
    "claude-sonnet-4-6": {
        "provider": "anthropic",
        "api_model": "claude-sonnet-4-6",
        "price_in": 3.00,
        "price_out": 15.00,
    },
    "claude-haiku-4-5": {
        "provider": "anthropic",
        "api_model": "claude-haiku-4-5",
        "price_in": 1.00,
        "price_out": 5.00,
    },
    "gpt-4o": {
        "provider": "openai",
        "api_model": "gpt-4o",
        "price_in": 2.50,
        "price_out": 10.00,
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "api_model": "gpt-4o-mini",
        "price_in": 0.15,
        "price_out": 0.60,
    },
    "gemini-1.5-pro": {
        "provider": "google",
        "api_model": "gemini-1.5-pro",
        "price_in": 1.25,
        "price_out": 5.00,
    },
}

REGRESSION_MODELS = list(MODELS.keys())

# Claude model used as the meta-evaluator + narrative generator everywhere.
EVALUATOR_MODEL = "claude-sonnet-4-6"


def cost_for(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return USD cost for a single call given a registry display name."""
    p = MODELS[model]
    return (input_tokens / 1_000_000) * p["price_in"] + (
        output_tokens / 1_000_000
    ) * p["price_out"]


def blended_price_per_million(model: str, out_ratio: float = 0.5) -> float:
    """Blended $/1M tokens for projections (default 50/50 in:out)."""
    p = MODELS[model]
    return p["price_in"] * (1 - out_ratio) + p["price_out"] * out_ratio


# ---------------------------------------------------------------------------
# Spend Attribution (page 2) — same frontier pricing, blended
# ---------------------------------------------------------------------------
SPEND_MODELS = ["claude-sonnet-4-6", "claude-haiku-4-5", "gpt-4o", "gpt-4o-mini"]

PROVIDER_OF = {
    "claude-sonnet-4-6": "Anthropic",
    "claude-haiku-4-5": "Anthropic",
    "gpt-4o": "OpenAI",
    "gpt-4o-mini": "OpenAI",
}

# ---------------------------------------------------------------------------
# Open-source models — Benchmark Tracker (page 3)
# Blended cost per 1M tokens (typical hosted-inference list pricing).
# ---------------------------------------------------------------------------
OSS_PRICING: dict[str, float] = {
    "Llama 3 8B": 0.20,
    "Llama 3 70B": 0.90,
    "Mistral 7B": 0.20,
    "Mixtral 8x7B": 0.60,
    "Gemma 7B": 0.20,
    "Falcon 40B": 0.80,
}

# Hugging Face repo ids used when querying the leaderboard API.
OSS_HF_REPOS: dict[str, str] = {
    "Llama 3 8B": "meta-llama/Meta-Llama-3-8B-Instruct",
    "Llama 3 70B": "meta-llama/Meta-Llama-3-70B-Instruct",
    "Mistral 7B": "mistralai/Mistral-7B-Instruct-v0.2",
    "Mixtral 8x7B": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "Gemma 7B": "google/gemma-7b-it",
    "Falcon 40B": "tiiuae/falcon-40b-instruct",
}

BENCHMARKS = ["MMLU", "HumanEval", "MATH", "HellaSwag", "MT-Bench"]
