from __future__ import annotations

from seo_content_engine.services.artifact_writer import ArtifactWriter


class DraftPublishService:
    @staticmethod
    def publish_draft(
        draft: dict,
        export_formats: list[str] | None = None,
    ) -> dict[str, str]:
        return ArtifactWriter.write_draft_bundle(
            draft=draft,
            export_formats=export_formats,
        )