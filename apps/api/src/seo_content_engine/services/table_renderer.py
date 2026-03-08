from __future__ import annotations

from typing import Any


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

        return {
            "id": table_plan["id"],
            "title": table_plan["title"],
            "columns": columns,
            "rows": rows,
        }

    @staticmethod
    def render_all(table_plans: list[dict], data_context: dict) -> list[dict]:
        return [TableRenderer.render_table(plan, data_context) for plan in table_plans]