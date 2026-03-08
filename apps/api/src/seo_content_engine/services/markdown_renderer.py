from __future__ import annotations


class MarkdownRenderer:
    @staticmethod
    def _render_table(table: dict) -> str:
        columns = table["columns"]
        rows = table["rows"]

        if not rows:
            return f"### {table['title']}\n\nNo structured data available.\n"

        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        lines = [f"### {table['title']}", "", header, separator]
        for row in rows:
            values = [str(row.get(column, "")) for column in columns]
            lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines) + "\n"

    @staticmethod
    def render(draft: dict) -> str:
        metadata = draft["metadata"]
        sections = draft["sections"]
        tables = draft["tables"]
        faqs = draft["faqs"]
        internal_links = draft["internal_links"]

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
                                url = nested.get("url")
                                if label and url:
                                    lines.append(f"- {label}: {url}")
                        elif isinstance(item, dict):
                            label = item.get("label")
                            url = item.get("url")
                            if label and url:
                                lines.append(f"- {label}: {url}")

                lines.append("")

        return "\n".join(lines).strip() + "\n"