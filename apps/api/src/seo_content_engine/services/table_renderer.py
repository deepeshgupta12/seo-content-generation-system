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
    def _build_table_summary(table_plan: dict, formatted_rows: list[dict]) -> str | None:
        title = table_plan.get("title", "This table")
        row_count = len(formatted_rows)

        if row_count == 0:
            return f"{title} is not available in the current grounded dataset for this page."

        first_row = formatted_rows[0]
        key_parts: list[str] = []
        for key, value in first_row.items():
            if value not in {"—", None, ""}:
                key_parts.append(f"{key} is {value}")
            if len(key_parts) >= 3:
                break

        summary_lines = [
            f"{title} presents {row_count} grounded row{'s' if row_count != 1 else ''} from the current source data.",
        ]

        if key_parts:
            summary_lines.append("The first visible row indicates that " + ", ".join(key_parts) + ".")

        summary_lines.append(
            "This snapshot is intended to help reviewers inspect structured values quickly before publication."
        )

        return " ".join(summary_lines)

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

        formatted_rows = []
        for row in rows:
            formatted_rows.append(
                {column: OutputFormatter.format_cell(column, row.get(column)) for column in columns}
            )

        return {
            "id": table_plan["id"],
            "title": table_plan["title"],
            "columns": columns,
            "rows": formatted_rows,
            "summary": TableRenderer._build_table_summary(table_plan, formatted_rows),
        }

    @staticmethod
    def render_all(table_plans: list[dict], data_context: dict) -> list[dict]:
        return [TableRenderer.render_table(plan, data_context) for plan in table_plans]