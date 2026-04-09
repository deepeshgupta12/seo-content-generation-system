from __future__ import annotations

from typing import Any

from seo_content_engine.services.output_formatter import OutputFormatter


class TableRenderer:
    # These table IDs must never render on resale pages. They carry new-project
    # or aggregate-status data that has no place on a resale listing page.
    RESALE_BLOCKED_TABLE_IDS: frozenset[str] = frozenset(
        {"property_status_table", "coverage_summary_table"}
    )

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
    def _filter_to_specific_property_type(
        rows: list[dict[str, Any]],
        specific_type: str,
    ) -> list[dict[str, Any]]:
        """Keep only the row(s) matching a specific property type (case-insensitive)."""
        target = specific_type.strip().lower()
        filtered = [
            row for row in rows
            if str(row.get("propertyType") or "").strip().lower() == target
        ]
        # Fall back to all residential rows if the specific type isn't found
        return filtered if filtered else rows

    @staticmethod
    def _filter_to_target_bhk(
        rows: list[dict[str, Any]],
        bhk_config: str,
    ) -> list[dict[str, Any]]:
        """Keep only the row(s) matching the target BHK configuration.

        The ``key`` field in unit-type distribution rows contains values like
        "2 BHK Flats in Gurgaon".  We match rows whose key *starts with* the
        bhk_config token (e.g. "2 BHK") case-insensitively.
        Falls back to all rows if no match is found.
        """
        target = bhk_config.strip().lower()
        filtered = [
            row for row in rows
            if str(row.get("key") or "").strip().lower().startswith(target)
        ]
        return filtered if filtered else rows

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

        pt_context = (data_context.get("page_property_type_context") or {})

        # Filter commercial property rows before formatting so the rendered table
        # only contains residential property types.
        if table_plan["id"] == "property_types_table":
            rows = TableRenderer._filter_property_type_rows(rows)
            # When the page is scoped to a single property type (e.g. "Flats" page →
            # property_type="Apartment"), further narrow the rows to that type only.
            if pt_context.get("scope") == "specific" and pt_context.get("property_type"):
                rows = TableRenderer._filter_to_specific_property_type(
                    rows, pt_context["property_type"]
                )

        # When the page is scoped to a specific BHK configuration, show ONLY that
        # BHK row in the unit-type distribution table.
        if table_plan["id"] == "sale_unit_type_distribution_table":
            if pt_context.get("scope") == "specific" and pt_context.get("bhk_config"):
                rows = TableRenderer._filter_to_target_bhk(rows, pt_context["bhk_config"])

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
    def should_render(table_id: str) -> bool:
        """Return False for table IDs that are blocked on all resale pages."""
        return table_id not in TableRenderer.RESALE_BLOCKED_TABLE_IDS

    @staticmethod
    def render_all(table_plans: list[dict], data_context: dict) -> list[dict]:
        return [
            TableRenderer.render_table(plan, data_context)
            for plan in table_plans
            if TableRenderer.should_render(plan.get("id", ""))
        ]