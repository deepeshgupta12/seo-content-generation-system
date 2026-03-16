from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx import Document
from docx.shared import Pt

from seo_content_engine.core.config import settings
from seo_content_engine.services.output_formatter import OutputFormatter
from seo_content_engine.utils.formatters import slugify


class ArtifactWriter:
    @staticmethod
    def _ensure_artifacts_dir() -> Path:
        artifacts_dir = Path(settings.artifacts_dir)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        return artifacts_dir

    @staticmethod
    def write_json_artifact(payload: dict, file_stem: str) -> str:
        artifacts_dir = ArtifactWriter._ensure_artifacts_dir()
        output_path = artifacts_dir / f"{slugify(file_stem)}.json"

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

        return str(output_path)

    @staticmethod
    def write_markdown_artifact(markdown_text: str, file_stem: str) -> str:
        artifacts_dir = ArtifactWriter._ensure_artifacts_dir()
        output_path = artifacts_dir / f"{slugify(file_stem)}.md"

        with output_path.open("w", encoding="utf-8") as file:
            file.write(markdown_text)

        return str(output_path)

    @staticmethod
    def _set_base_doc_styles(document: Document) -> None:
        styles = document.styles
        if "Normal" in styles:
            styles["Normal"].font.name = "Arial"
            styles["Normal"].font.size = Pt(10.5)

    @staticmethod
    def _safe_text(value: Any) -> str:
        if value is None:
            return "—"
        return str(value).strip() or "—"

    @staticmethod
    def _add_metadata(document: Document, metadata: dict) -> None:
        h1 = ArtifactWriter._safe_text(metadata.get("h1"))
        title = ArtifactWriter._safe_text(metadata.get("title"))
        meta_description = ArtifactWriter._safe_text(metadata.get("meta_description"))
        intro_snippet = ArtifactWriter._safe_text(metadata.get("intro_snippet"))

        document.add_heading(h1, level=1)

        intro_para = document.add_paragraph()
        intro_para.add_run(intro_snippet)

        document.add_heading("SEO Metadata", level=2)
        document.add_paragraph(f"Title: {title}")
        document.add_paragraph(f"Meta Description: {meta_description}")

    @staticmethod
    def _add_sections(document: Document, sections: list[dict]) -> None:
        if not sections:
            return

        document.add_heading("Editorial Sections", level=2)
        for section in sections:
            title = ArtifactWriter._safe_text(section.get("title"))
            body = str(section.get("body") or "").strip()

            document.add_heading(title, level=3)
            if not body:
                document.add_paragraph("No grounded narrative available for this section.")
                continue

            for paragraph in body.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    document.add_paragraph(paragraph)

    @staticmethod
    def _add_tables(document: Document, tables: list[dict]) -> None:
        if not tables:
            return

        document.add_heading("Key Data Tables", level=2)
        for table_block in tables:
            title = ArtifactWriter._safe_text(table_block.get("title"))
            summary = str(table_block.get("summary") or "").strip()
            columns = table_block.get("columns", []) or []
            rows = table_block.get("rows", []) or []

            document.add_heading(title, level=3)
            if summary:
                document.add_paragraph(summary)

            if not columns:
                document.add_paragraph("No structured columns available.")
                continue

            doc_table = document.add_table(rows=1, cols=len(columns))
            doc_table.style = "Table Grid"
            header_cells = doc_table.rows[0].cells
            for index, column_name in enumerate(columns):
                header_cells[index].text = str(column_name)

            if rows:
                for row in rows:
                    cells = doc_table.add_row().cells
                    for index, column_name in enumerate(columns):
                        cells[index].text = OutputFormatter.format_cell(
                            column_name,
                            row.get(column_name),
                        )
            else:
                cells = doc_table.add_row().cells
                for index in range(len(columns)):
                    cells[index].text = "—"

            document.add_paragraph("")

    @staticmethod
    def _add_faqs(document: Document, faqs: list[dict]) -> None:
        if not faqs:
            return

        document.add_heading("Frequently Asked Questions", level=2)
        for faq in faqs:
            question = ArtifactWriter._safe_text(faq.get("question"))
            answer = str(faq.get("answer") or "").strip()

            document.add_heading(question, level=3)
            if not answer:
                document.add_paragraph("No grounded answer available.")
                continue

            for paragraph in answer.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    document.add_paragraph(paragraph)

    @staticmethod
    def _normalize_link_items(links: list[Any]) -> list[dict]:
        normalized_links: list[dict] = []

        for item in links or []:
            if isinstance(item, list):
                for nested in item:
                    if isinstance(nested, dict):
                        normalized_links.append(nested)
            elif isinstance(item, dict):
                normalized_links.append(item)

        return normalized_links

    @staticmethod
    def _add_internal_links(document: Document, internal_links: dict) -> None:
        if not internal_links:
            return

        title_map = {
            "sale_unit_type_links": "Unit Type Links",
            "sale_property_type_links": "Property Type Links",
            "sale_quick_links": "Quick Links",
            "nearby_locality_links": "Nearby Locality Links",
            "top_project_links": "Top Project Links",
            "featured_project_links": "Featured Project Links",
        }

        document.add_heading("Internal Links", level=2)

        for key, group_title in title_map.items():
            group_links = ArtifactWriter._normalize_link_items(internal_links.get(key, []))
            if not group_links:
                continue

            document.add_heading(group_title, level=3)
            for item in group_links:
                label = ArtifactWriter._safe_text(
                    item.get("label")
                    or item.get("unitType")
                    or item.get("propertyType")
                    or "Link"
                )
                url = ArtifactWriter._safe_text(item.get("url"))
                if url != "—":
                    document.add_paragraph(f"{label}: {url}", style="List Bullet")
                else:
                    document.add_paragraph(label, style="List Bullet")

    @staticmethod
    def write_docx_artifact(draft: dict, file_stem: str) -> str:
        artifacts_dir = ArtifactWriter._ensure_artifacts_dir()
        output_path = artifacts_dir / f"{slugify(file_stem)}.docx"

        document = Document()
        ArtifactWriter._set_base_doc_styles(document)

        ArtifactWriter._add_metadata(document, draft.get("metadata", {}))
        ArtifactWriter._add_sections(document, draft.get("sections", []))
        ArtifactWriter._add_tables(document, draft.get("tables", []))
        ArtifactWriter._add_faqs(document, draft.get("faqs", []))
        ArtifactWriter._add_internal_links(document, draft.get("internal_links", {}))

        document.save(output_path)
        return str(output_path)

    @staticmethod
    def write_blueprint(blueprint: dict) -> str:
        entity = blueprint["entity"]["entity_name"]
        page_type = blueprint["page_type"]
        file_stem = f"{entity}-{page_type}-blueprint"
        return ArtifactWriter.write_json_artifact(blueprint, file_stem)

    @staticmethod
    def write_keyword_intelligence(keyword_intelligence: dict) -> str:
        entity = keyword_intelligence["entity"]["entity_name"]
        page_type = keyword_intelligence["page_type"]
        file_stem = f"{entity}-{page_type}-keyword-intelligence"
        return ArtifactWriter.write_json_artifact(keyword_intelligence, file_stem)

    @staticmethod
    def write_content_plan(content_plan: dict) -> str:
        entity = content_plan["entity"]["entity_name"]
        page_type = content_plan["page_type"]
        file_stem = f"{entity}-{page_type}-content-plan"
        return ArtifactWriter.write_json_artifact(content_plan, file_stem)

    @staticmethod
    def write_draft_bundle(
        draft: dict,
        export_formats: list[str] | None = None,
    ) -> dict[str, str]:
        if settings.block_artifact_write_on_review and draft.get("needs_review"):
            raise ValueError(
                "Draft still needs review. Artifact writing is blocked by configuration."
            )

        requested_formats = export_formats or list(settings.draft_default_export_formats)
        requested_formats = list(dict.fromkeys(requested_formats))

        entity = draft["entity"]["entity_name"]
        page_type = draft["page_type"]
        file_stem = f"{entity}-{page_type}-draft"

        artifact_paths: dict[str, str] = {}

        if "json" in requested_formats:
            artifact_paths["json_path"] = ArtifactWriter.write_json_artifact(draft, file_stem)

        if "markdown" in requested_formats:
            artifact_paths["markdown_path"] = ArtifactWriter.write_markdown_artifact(
                draft["markdown_draft"],
                file_stem,
            )

        if "docx" in requested_formats:
            artifact_paths["docx_path"] = ArtifactWriter.write_docx_artifact(draft, file_stem)

        return artifact_paths