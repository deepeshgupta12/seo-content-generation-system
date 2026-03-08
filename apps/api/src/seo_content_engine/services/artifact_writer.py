from __future__ import annotations

import json
from pathlib import Path

from seo_content_engine.core.config import settings
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
    def write_draft_bundle(draft: dict) -> dict[str, str]:
        if settings.block_artifact_write_on_review and draft.get("needs_review"):
            raise ValueError("Draft still needs review. Artifact writing is blocked by configuration.")

        entity = draft["entity"]["entity_name"]
        page_type = draft["page_type"]
        file_stem = f"{entity}-{page_type}-draft"

        json_path = ArtifactWriter.write_json_artifact(draft, file_stem)
        markdown_path = ArtifactWriter.write_markdown_artifact(draft["markdown_draft"], file_stem)

        return {
            "json_path": json_path,
            "markdown_path": markdown_path,
        }