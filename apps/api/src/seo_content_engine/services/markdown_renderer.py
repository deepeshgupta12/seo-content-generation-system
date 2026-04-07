from __future__ import annotations

from typing import Any


class MarkdownRenderer:
    @staticmethod
    def _string(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None or value == "":
            return "—"
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f"{value:.2f}".rstrip("0").rstrip(".")
        return str(value)

    @staticmethod
    def _render_metadata(metadata: dict) -> list[str]:
        lines: list[str] = []

        title = MarkdownRenderer._string(metadata.get("title"))
        meta_description = MarkdownRenderer._string(metadata.get("meta_description"))
        h1 = MarkdownRenderer._string(metadata.get("h1"))
        intro_snippet = MarkdownRenderer._string(metadata.get("intro_snippet"))

        if h1:
            lines.append(f"# {h1}")
            lines.append("")

        if intro_snippet:
            lines.append(intro_snippet)
            lines.append("")

        if title or meta_description:
            lines.append("## SEO Metadata")
            lines.append("")

        if title:
            lines.append(f"**Title:** {title}")
        if meta_description:
            lines.append(f"**Meta Description:** {meta_description}")

        if title or meta_description:
            lines.append("")

        return lines

    @staticmethod
    def _render_sections(sections: list[dict]) -> list[str]:
        lines: list[str] = []
        if not sections:
            return lines

        lines.append("## Editorial Sections")
        lines.append("")

        for section in sections:
            title = MarkdownRenderer._string(section.get("title"))
            body = MarkdownRenderer._string(section.get("body"))
            key_points: list[str] = [
                MarkdownRenderer._string(point)
                for point in (section.get("key_points") or [])
                if point and MarkdownRenderer._string(point)
            ]

            if title:
                lines.append(f"### {title}")
                lines.append("")

            if body:
                for paragraph in body.split("\n"):
                    paragraph = paragraph.strip()
                    if paragraph:
                        # Preserve any bullet lines the model may have written inline
                        lines.append(paragraph)
                        lines.append("")
            else:
                lines.append("No grounded narrative available for this section.")
                lines.append("")

            if key_points:
                for point in key_points:
                    lines.append(f"- {point}")
                lines.append("")

        return lines

    @staticmethod
    def _render_single_table(table: dict) -> list[str]:
        lines: list[str] = []

        title = MarkdownRenderer._string(table.get("title")) or "Table"
        summary = MarkdownRenderer._string(table.get("summary"))
        columns = table.get("columns", []) or []
        rows = table.get("rows", []) or []

        lines.append(f"### {title}")
        lines.append("")

        if summary:
            lines.append(summary)
            lines.append("")

        if not columns:
            lines.append("No structured columns available.")
            lines.append("")
            return lines

        header = "| " + " | ".join(str(column) for column in columns) + " |"
        divider = "| " + " | ".join("---" for _ in columns) + " |"

        lines.append(header)
        lines.append(divider)

        if rows:
            for row in rows:
                lines.append(
                    "| "
                    + " | ".join(MarkdownRenderer._format_value(row.get(column)) for column in columns)
                    + " |"
                )
        else:
            lines.append("| " + " | ".join("—" for _ in columns) + " |")

        lines.append("")
        return lines

    @staticmethod
    def _render_tables(tables: list[dict]) -> list[str]:
        lines: list[str] = []
        if not tables:
            return lines

        lines.append("## Key Data Tables")
        lines.append("")

        for table in tables:
            lines.extend(MarkdownRenderer._render_single_table(table))

        return lines

    @staticmethod
    def _render_faq_answer(answer: str) -> list[str]:
        lines: list[str] = []
        for paragraph in answer.split("\n"):
            paragraph = paragraph.strip()
            if paragraph:
                lines.append(paragraph)
                lines.append("")
        return lines

    @staticmethod
    def _render_faqs(faqs: list[dict]) -> list[str]:
        lines: list[str] = []
        if not faqs:
            return lines

        lines.append("## Frequently Asked Questions")
        lines.append("")

        for faq in faqs:
            question = MarkdownRenderer._string(faq.get("question"))
            answer = MarkdownRenderer._string(faq.get("answer"))

            if question:
                lines.append(f"### {question}")
                lines.append("")

            if answer:
                lines.extend(MarkdownRenderer._render_faq_answer(answer))
            else:
                lines.append("No grounded answer available.")
                lines.append("")

        return lines

    @staticmethod
    def _render_link_group(title: str, links: list[Any]) -> list[str]:
        lines: list[str] = []
        normalized_links: list[dict] = []

        for item in links or []:
            if isinstance(item, list):
                for nested in item:
                    if isinstance(nested, dict):
                        normalized_links.append(nested)
            elif isinstance(item, dict):
                normalized_links.append(item)

        if not normalized_links:
            return lines

        lines.append(f"### {title}")
        lines.append("")

        for link in normalized_links:
            label = MarkdownRenderer._string(
                link.get("label") or link.get("unitType") or link.get("propertyType") or "Link"
            )
            url = MarkdownRenderer._string(link.get("url"))
            if url:
                lines.append(f"- {label}: {url}")
            else:
                lines.append(f"- {label}")

        lines.append("")
        return lines

    @staticmethod
    def _render_internal_links(internal_links: dict) -> list[str]:
        lines: list[str] = []
        if not internal_links:
            return lines

        lines.append("## Internal Links")
        lines.append("")

        title_map = {
            "sale_unit_type_links": "Unit Type Links",
            "sale_property_type_links": "Property Type Links",
            "sale_quick_links": "Quick Links",
            "nearby_locality_links": "Nearby Locality Links",
            "featured_project_links": "Featured Project Links",
        }

        for key, title in title_map.items():
            lines.extend(MarkdownRenderer._render_link_group(title, internal_links.get(key, [])))

        return lines

    @staticmethod
    def render(draft: dict) -> str:
        lines: list[str] = []

        # E3: Prepend a review banner for drafts that failed hard validation.
        if draft.get("needs_review"):
            approval = draft.get("quality_report", {}).get("approval_status", "unknown")
            lines.append(
                f"> ⚠️ **DRAFT STATUS: Validation failed (approval_status={approval}) — "
                "review required before publishing.**"
            )
            lines.append("")

        lines.extend(MarkdownRenderer._render_metadata(draft.get("metadata", {})))
        lines.extend(MarkdownRenderer._render_sections(draft.get("sections", [])))
        lines.extend(MarkdownRenderer._render_tables(draft.get("tables", [])))
        lines.extend(MarkdownRenderer._render_faqs(draft.get("faqs", [])))
        lines.extend(MarkdownRenderer._render_internal_links(draft.get("internal_links", {})))

        while lines and lines[-1] == "":
            lines.pop()

        return "\n".join(lines) + "\n"