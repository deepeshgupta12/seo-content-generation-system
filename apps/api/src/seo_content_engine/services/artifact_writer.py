from __future__ import annotations

import json
from pathlib import Path

from seo_content_engine.core.config import settings
from seo_content_engine.utils.formatters import slugify


class ArtifactWriter:
    @staticmethod
    def write_blueprint(blueprint: dict) -> str:
        artifacts_dir = Path(settings.artifacts_dir)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        entity = blueprint["entity"]["entity_name"]
        page_type = blueprint["page_type"]
        file_name = f"{slugify(entity)}-{page_type}-blueprint.json"
        output_path = artifacts_dir / file_name

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(blueprint, file, ensure_ascii=False, indent=2)

        return str(output_path)