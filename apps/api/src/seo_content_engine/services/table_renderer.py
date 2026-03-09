from __future__ import annotations

from typing import Any

from seo_content_engine.services.output_formatter import OutputFormatter


class TableRenderer:
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
    def _build_table_summary(
        table_id: str,
        title: str,
        columns: list[str],
        rows: list[dict[str, Any]],
    ) -> str:
        if not rows:
            return (
                f"{title} is currently empty for this page. "
                "No grounded rows were available in the structured source data for this table. "
                "Once the underlying inputs are available, this section can help summarize the visible dataset in a more usable format."
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
            preview_clause = " In the first visible row, " + ", ".join(first_non_empty_parts[:3]) + "."

        if table_id == "price_trend_table":
            return (
                f"{title} shows how the visible asking-rate trend is distributed across the available time periods for this page. "
                "It helps compare the locality signal with the broader micromarket and city context wherever those values are present."
                f"{preview_clause} "
                "This gives reviewers and content editors a quick way to ground any narrative around pricing movement in the actual table values."
            )

        if table_id == "sale_unit_type_distribution_table":
            return (
                f"{title} highlights the visible BHK mix currently present in the resale inventory for this page. "
                "It makes it easier to understand which home configurations appear most often in the structured listing data."
                f"{preview_clause} "
                "This table is useful when writing buyer-facing copy around inventory spread without making unsupported assumptions."
            )

        if table_id == "nearby_localities_table":
            return (
                f"{title} captures nearby alternatives that can also be explored alongside the current location. "
                "It brings together proximity, visible resale inventory, and page-level pricing signals in one place."
                f"{preview_clause} "
                "This can support grounded exploration-oriented copy for users comparing nearby options."
            )

        if table_id == "location_rates_table":
            return (
                f"{title} lists the visible rate snapshot for local pockets available within the dataset. "
                "It helps show how pricing signals vary across the locations surfaced on this page."
                f"{preview_clause} "
                "This is useful for adding grounded locality-level context without drifting into unsupported commentary."
            )

        if table_id == "property_types_table":
            return (
                f"{title} summarizes the property-type level pricing inputs available in the underlying source data. "
                "It helps show which property categories are visible on the page and how their listed values compare."
                f"{preview_clause} "
                "This can support grounded prose about inventory mix and rate variation across property types."
            )

        if table_id == "property_status_table":
            return (
                f"{title} brings together the visible status buckets and their associated pricing inputs for this page. "
                "It helps clarify how the currently surfaced inventory is distributed across readiness or completion states."
                f"{preview_clause} "
                "This is especially helpful for grounded content around ready-to-move or status-led inventory mix."
            )

        if table_id == "top_projects_table":
            return (
                f"{title} surfaces the projects currently highlighted by the structured source inputs for this page. "
                "Depending on the available dataset, this may reflect transactions, listing rates, or value-led ranking signals."
                f"{preview_clause} "
                "It provides a grounded project snapshot that can support internal review and controlled narrative generation."
            )

        if table_id == "coverage_summary_table":
            return (
                f"{title} provides a compact overview of the visible resale coverage for this page. "
                "It helps summarize listing scale and project presence at the page level using direct source-backed values."
                f"{preview_clause} "
                "This gives a quick factual baseline before deeper section-level review."
            )

        return (
            f"{title} summarizes the structured source-backed data available for this page. "
            "It helps organize the visible inputs into a format that is easier to inspect and use in grounded content generation."
            f"{preview_clause} "
            "The values shown here should be treated as the factual reference point for related narrative sections."
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