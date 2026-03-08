from fastapi.testclient import TestClient
from seo_content_engine.main import app

client = TestClient(app)


def test_draft_publish_route_blocks_when_review_required() -> None:
    payload = {
        "draft": {
            "entity": {"entity_name": "Andheri West"},
            "page_type": "resale_locality",
            "needs_review": True,
            "markdown_draft": "# Draft",
        }
    }

    response = client.post("/v1/generate/draft/publish", json=payload)
    assert response.status_code == 400
    assert "Draft still needs review" in response.text