"""LLM client helpers: async multi-provider calls + sync Claude utilities.

Every Claude call uses the standard ``ANTHROPIC_API_KEY`` (console.anthropic.com).
No admin / workspace endpoints are touched anywhere.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from .pricing import MODELS, EVALUATOR_MODEL, cost_for
from .secrets import get_secret

# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------
def parse_json(text: str) -> Any:
    """Best-effort extraction of a JSON object/array from a model response."""
    if not text:
        raise ValueError("empty response")
    text = text.strip()
    # Strip ```json ... ``` fences.
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise


# ---------------------------------------------------------------------------
# Sync Claude (evaluator / narratives / Q&A)
# ---------------------------------------------------------------------------
def _anthropic_sync_client():
    import anthropic

    key = get_secret("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    return anthropic.Anthropic(api_key=key)


def claude_sync(
    prompt: str,
    system: str | None = None,
    model: str = EVALUATOR_MODEL,
    max_tokens: int = 1500,
    temperature: float = 0.2,
) -> str:
    """Single synchronous Claude completion → plain text."""
    client = _anthropic_sync_client()
    api_model = MODELS.get(model, {}).get("api_model", model)
    kwargs: dict[str, Any] = {
        "model": api_model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return "".join(block.text for block in resp.content if block.type == "text").strip()


def claude_stream(
    prompt: str,
    system: str | None = None,
    model: str = EVALUATOR_MODEL,
    max_tokens: int = 700,
    temperature: float = 0.3,
):
    """Yield Claude's response incrementally — designed for st.write_stream."""
    api_model = MODELS.get(model, {}).get("api_model", model)
    kwargs: dict[str, Any] = {
        "model": api_model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    try:
        client = _anthropic_sync_client()
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as exc:  # noqa: BLE001 — surface to the UI as text
        yield f"\n\n_Could not generate an answer: {exc}_"


def claude_json(prompt: str, system: str | None = None, max_tokens: int = 1500) -> Any:
    return parse_json(claude_sync(prompt, system=system, max_tokens=max_tokens))


# ---------------------------------------------------------------------------
# Async multi-provider calls (page 1)
# ---------------------------------------------------------------------------
async def _call_anthropic(api_model: str, prompt: str) -> tuple[str, int, int]:
    import anthropic

    key = get_secret("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    client = anthropic.AsyncAnthropic(api_key=key)
    resp = await client.messages.create(
        model=api_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return text, resp.usage.input_tokens, resp.usage.output_tokens


async def _call_openai(api_model: str, prompt: str) -> tuple[str, int, int]:
    from openai import AsyncOpenAI

    key = get_secret("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    client = AsyncOpenAI(api_key=key)
    resp = await client.chat.completions.create(
        model=api_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = (resp.choices[0].message.content or "").strip()
    usage = resp.usage
    return text, usage.prompt_tokens, usage.completion_tokens


async def _call_gemini(api_model: str, prompt: str) -> tuple[str, int, int]:
    import google.generativeai as genai

    key = get_secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(api_model)
    resp = await model.generate_content_async(prompt)
    text = (resp.text or "").strip()
    um = getattr(resp, "usage_metadata", None)
    in_tok = getattr(um, "prompt_token_count", 0) if um else 0
    out_tok = getattr(um, "candidates_token_count", 0) if um else 0
    return text, in_tok, out_tok


_DISPATCH = {
    "anthropic": _call_anthropic,
    "openai": _call_openai,
    "google": _call_gemini,
}


async def call_model(display_name: str, prompt: str) -> dict:
    """Call one model and capture output, latency, tokens, cost, errors."""
    spec = MODELS[display_name]
    fn = _DISPATCH[spec["provider"]]
    start = time.perf_counter()
    result = {
        "model": display_name,
        "prompt": prompt,
        "output": "",
        "latency_ms": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost": 0.0,
        "error": None,
    }
    try:
        text, in_tok, out_tok = await fn(spec["api_model"], prompt)
        result["output"] = text
        result["input_tokens"] = in_tok
        result["output_tokens"] = out_tok
        result["cost"] = cost_for(display_name, in_tok, out_tok)
    except Exception as exc:  # noqa: BLE001 — surface to UI, don't crash gather
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        result["latency_ms"] = int((time.perf_counter() - start) * 1000)
    return result
