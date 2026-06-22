"""Secret/config access that works on both Streamlit Cloud and Railway.

Order of resolution:
  1. st.secrets  (``.streamlit/secrets.toml`` or Streamlit Cloud secrets)
  2. os.environ  (Railway / Docker / local ``.env`` via python-dotenv)

All Claude calls in this app use a STANDARD ``ANTHROPIC_API_KEY`` from
console.anthropic.com. No admin / workspace-management keys are used.
"""
from __future__ import annotations

import os

try:  # python-dotenv is optional at runtime
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def get_secret(name: str, default: str | None = None) -> str | None:
    """Return a secret by name, checking st.secrets then environment."""
    # st.secrets raises if no secrets file exists, so guard with try/except.
    try:
        import streamlit as st

        if name in st.secrets:
            value = st.secrets[name]
            if value:
                return str(value)
    except Exception:
        pass

    value = os.environ.get(name)
    if value:
        return value
    return default


def has_secret(name: str) -> bool:
    return bool(get_secret(name))


def require_secret(name: str) -> str:
    value = get_secret(name)
    if not value:
        raise RuntimeError(
            f"Missing required secret '{name}'. Add it to .streamlit/secrets.toml "
            "or set it as an environment variable."
        )
    return value
