from __future__ import annotations

from typing import Any

from seo_content_engine.core.config import settings


class OutputFormatter:
    CURRENCY_HINTS = {"price", "rate", "value", "cost", "cpc", "bid"}
    PERCENT_HINTS = {"changepercentage", "changepercent"}

    @staticmethod
    def format_number(value: int | float | None, decimals: int = 0) -> str:
        if value is None:
            return "—"

        if isinstance(value, float):
            if decimals == 0:
                value = round(value)
                return f"{int(value):,}"
            return f"{value:,.{decimals}f}"

        return f"{value:,}"

    @staticmethod
    def format_currency(value: int | float | None, decimals: int = 0) -> str:
        if value is None:
            return "—"

        if isinstance(value, float):
            if decimals == 0:
                value = round(value)
                return f"₹{int(value):,}"
            return f"₹{value:,.{decimals}f}"

        return f"₹{value:,}"

    @staticmethod
    def format_percentage(value: int | float | None, decimals: int = 2) -> str:
        if value is None:
            return "—"
        return f"{value:.{decimals}f}%"

    @staticmethod
    def resolve_url(url: str | None) -> str | None:
        if not url:
            return None
        if url.startswith("http://") or url.startswith("https://"):
            return url
        base = settings.squareyards_base_url.rstrip("/")
        clean = url.lstrip("/")
        return f"{base}/{clean}"

    @staticmethod
    def _column_hint(column_name: str) -> str:
        return column_name.lower().replace("_", "")

    @staticmethod
    def format_cell(column_name: str, value: Any) -> str:
        if value is None:
            return "—"

        hint = OutputFormatter._column_hint(column_name)

        if column_name.lower() in {"url", "producturl"} and isinstance(value, str):
            return OutputFormatter.resolve_url(value) or "—"

        if isinstance(value, (int, float)):
            if any(token in hint for token in OutputFormatter.PERCENT_HINTS):
                return OutputFormatter.format_percentage(value)

            if any(token in hint for token in OutputFormatter.CURRENCY_HINTS):
                decimals = 2 if isinstance(value, float) and not float(value).is_integer() else 0
                return OutputFormatter.format_currency(value, decimals=decimals)

            if "distance" in hint:
                return f"{value:.2f} km" if isinstance(value, float) else f"{value} km"

            if isinstance(value, float) and not float(value).is_integer():
                return OutputFormatter.format_number(value, decimals=2)

            return OutputFormatter.format_number(value)

        return str(value)