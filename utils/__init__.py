"""Shared helpers for the AI Ops Intelligence Suite."""
from .secrets import get_secret, has_secret, require_secret
from .styles import (
    inject_css,
    sidebar_credit,
    page_header,
    metric_tile,
    banner,
    style_fig,
    ACCENT,
    DANGER,
    SUCCESS,
    CHART_COLORS,
)

__all__ = [
    "get_secret",
    "has_secret",
    "require_secret",
    "inject_css",
    "sidebar_credit",
    "page_header",
    "metric_tile",
    "banner",
    "style_fig",
    "ACCENT",
    "DANGER",
    "SUCCESS",
    "CHART_COLORS",
]
