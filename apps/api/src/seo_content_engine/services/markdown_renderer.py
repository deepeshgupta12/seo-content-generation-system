from __future__ import annotations

from seo_content_engine.services.output_formatter import OutputFormatter


class MarkdownRenderer:
    @staticmethod
    def _render_table(table: dict) -> str:
        columns = table["columns"]
        rows = table["rows"]

        if not rows:
            return f"### {table['title']}\n\nNo structured data available.\n"

        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        lines = [f"### {table['title']}", ""]
        if table.get("summary"):
            lines.append(table["summary"])
            lines.append("")

        lines.extend([header, separator])
        for row in rows:
            values = [str(row.get(column, "—")) for column in columns]
            lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines) + "\n"

    @staticmethod
    def render(draft: dict) -> str:
        metadata = draft["metadata"]
        sections = draft["sections"]
        tables = draft["tables"]
        faqs = draft["faqs"]
        internal_links = draft["internal_links"]
        quality_report = draft.get("quality_report", {})

        lines: list[str] = [
            f"# {metadata['h1']}",
            "",
            f"**Title:** {metadata['title']}",
            "",
            f"**Meta Description:** {metadata['meta_description']}",
            "",
            metadata["intro_snippet"],
            "",
        ]

        if quality_report:
            approval_status = quality_report.get("approval_status")
            score = quality_report.get("overall_quality_score", quality_report.get("overall_score"))
            warnings = quality_report.get("warning_reasons", quality_report.get("warnings", []))

            lines.append("## Quality Summary")
            lines.append("")
            if approval_status is not None:
                lines.append(f"**Approval Status:** {approval_status}")
            if score is not None:
                lines.append(f"**Overall Quality Score:** {score}")
            if warnings:
                lines.append("")
                lines.append("**Warnings:**")
                for warning in warnings:
                    lines.append(f"- {warning}")
                lines.append("")

        if draft.get("needs_review"):
            lines.extend(
                [
                    "> Review required: one or more sections, FAQs, or metadata fields were flagged by the factual validator.",
                    "",
                ]
            )

        for section in sections:
            lines.append(f"## {section['title']}")
            lines.append("")
            lines.append(section["body"])
            lines.append("")

        if tables:
            lines.append("## Key Data Tables")
            lines.append("")
            for table in tables:
                lines.append(MarkdownRenderer._render_table(table))

        if faqs:
            lines.append("## Frequently Asked Questions")
            lines.append("")
            for faq in faqs:
                lines.append(f"### {faq['question']}")
                lines.append("")
                lines.append(faq["answer"])
                lines.append("")

        if internal_links:
            lines.append("## Explore More")
            lines.append("")

            for group_name, group_links in internal_links.items():
                if not group_links:
                    continue

                lines.append(f"### {group_name.replace('_', ' ').title()}")
                lines.append("")

                if isinstance(group_links, list):
                    for item in group_links:
                        if isinstance(item, list):
                            for nested in item:
                                label = nested.get("unitType") or nested.get("propertyType") or nested.get("label")
                                url = OutputFormatter.resolve_url(nested.get("url"))
                                if label and url:
                                    lines.append(f"- {label}: {url}")
                        elif isinstance(item, dict):
                            label = item.get("label")
                            url = OutputFormatter.resolve_url(item.get("url"))
                            if label and url:
                                lines.append(f"- {label}: {url}")

                lines.append("")

        return "\n".join(lines).strip() + "\n"