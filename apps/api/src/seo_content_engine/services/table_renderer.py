from __future__ import annotations

from typing import Any

from seo_content_engine.services.output_formatter import OutputFormatter


class TableRenderer:
    COMMERCIAL_PROPERTY_TERMS = {
        "shop",
        "office space",
        "office spaces",
        "co-working space",
        "co working space",
        "warehouse",
        "showroom",
        "commercial",
    }

    @staticmethod
    def _resolve_path(data: dict[str, Any], path: str) -> Any:
        current: Any = data
        for key in path.split("."):
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    @staticmethod
    def _filter_property_type_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []
        for row in rows:
            property_type = str(row.get("propertyType") or "").strip().lower()
            if property_type and any(term in property_type for term in TableRenderer.COMMERCIAL_PROPERTY_TERMS):
                continue
            filtered.append(row)
        return filtered

    @staticmethod
    def _build_table_summary(
        table_id: str,
        title: str,
        columns: list[str],
        rows: list[dict[str, Any]],
    ) -> str:
        if table_id == "property_types_table":
            rows = TableRenderer._filter_property_type_rows(rows)

        if not rows:
            return (
                f"{title} is empty for this page right now. "
                "When data is available, it will help users review the related pricing or inventory details more quickly."
            )

        first_row = rows[0]
        first_non_empty_parts: list[str] = []

        for column in columns[:4]:
            value = first_row.get(column)
            if value in {None, "", "—"}:
                continue
            first_non_empty_parts.append(f"{column} is {value}")

        preview_clause = ""
        if first_non_empty_parts:
            preview_clause = " For example, the first row shows " + ", ".join(first_non_empty_parts[:3]) + "."

        if table_id == "price_trend_table":
            return (
                f"{title} helps compare the latest asking-price trend with broader local benchmarks."
                f"{preview_clause}"
            )

        if table_id == "sale_unit_type_distribution_table":
            return (
                f"{title} makes it easier to see which BHK configurations are showing up most often in the resale stock here."
                f"{preview_clause}"
            )

        if table_id == "nearby_localities_table":
            return (
                f"{title} helps users compare nearby areas when they want more resale options around the current location."
                f"{preview_clause}"
            )

        if table_id == "location_rates_table":
            return (
                f"{title} gives a quick read on how asking-rate signals vary across the covered locations."
                f"{preview_clause}"
            )

        if table_id == "property_types_table":
            return (
                f"{title} helps compare how different residential property types are showing up in the available pricing view."
                f"{preview_clause}"
            )

        if table_id == "coverage_summary_table":
            return (
                f"{title} gives a quick sense of how much resale inventory and project coverage is represented on this page."
                f"{preview_clause}"
            )

        return (
            f"{title} gives a compact view of the key values behind this page."
            f"{preview_clause}"
        )

    @staticmethod
    def render_table(table_plan: dict, data_context: dict) -> dict:
        rows_source = TableRenderer._resolve_path(data_context, table_plan["source_data_path"])
        columns = table_plan["columns"]

        if rows_source is None:
            rows = []
        elif isinstance(rows_source, list):
            rows = []
            for item in rows_source:
                if isinstance(item, dict):
                    rows.append({column: item.get(column) for column in columns})
        elif isinstance(rows_source, dict):
            rows = [{column: rows_source.get(column) for column in columns}]
        else:
            rows = []

        formatted_rows: list[dict[str, Any]] = []
        for row in rows:
            formatted_rows.append(
                {column: OutputFormatter.format_cell(column, row.get(column)) for column in columns}
            )

        summary = TableRenderer._build_table_summary(
            table_id=table_plan["id"],
            title=table_plan["title"],
            columns=columns,
            rows=formatted_rows,
        )

        return {
            "id": table_plan["id"],
            "title": table_plan["title"],
            "summary": summary,
            "columns": columns,
            "rows": formatted_rows,
        }

    @staticmethod
    def render_all(table_plans: list[dict], data_context: dict) -> list[dict]:
        return [TableRenderer.render_table(plan, data_context) for plan in table_plans]