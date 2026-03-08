import pytest

from seo_content_engine.services.artifact_writer import ArtifactWriter


def test_artifact_writer_blocks_when_review_required(monkeypatch) -> None:
    from seo_content_engine.services import artifact_writer as artifact_writer_module

    monkeypatch.setattr(artifact_writer_module.settings, "block_artifact_write_on_review", True)

    draft = {
        "entity": {"entity_name": "Andheri West"},
        "page_type": "resale_locality",
        "needs_review": True,
        "markdown_draft": "# Draft",
    }

    with pytest.raises(ValueError, match="Draft still needs review"):
        ArtifactWriter.write_draft_bundle(draft)