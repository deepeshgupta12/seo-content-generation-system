from fastapi.testclient import TestClient
from seo_content_engine.main import app

client = TestClient(app)


class DummyReviewWorkbenchService:
    @staticmethod
    def build_session(
        *,
        main_datacenter_json_path,
        property_rates_json_path,
        listing_type,
        location_name=None,
        language_name=None,
        limit=None,
        include_historical=True,
        persist_session=True,
    ):
        return {
            "session_id": "review-test-123",
            "entity": {
                "entity_name": "Andheri West",
                "city_name": "Mumbai",
                "page_type": "resale_locality",
            },
            "source_preview": {"listing_summary": {"sale_count": 2039}},
            "keyword_preview": {"primary_keyword": {"keyword": "flats for sale in andheri west mumbai"}},
            "normalized": {},
            "keyword_intelligence": {},
            "content_plan": {},
            "draft": {
                "entity": {"entity_name": "Andheri West"},
                "quality_report": {"approval_status": "pass", "overall_quality_score": 96},
            },
            "validation_report": {"passed": True},
            "quality_report": {"approval_status": "pass", "overall_quality_score": 96},
            "section_review": [],
            "version_history": [],
            "latest_version_id": "v-test",
        }

    @staticmethod
    def get_session(session_id: str):
        return {
            "session_id": session_id,
            "entity": {
                "entity_name": "Andheri West",
                "city_name": "Mumbai",
                "page_type": "resale_locality",
            },
            "source_preview": {"listing_summary": {"sale_count": 2039}},
            "keyword_preview": {"primary_keyword": {"keyword": "flats for sale in andheri west mumbai"}},
            "normalized": {},
            "keyword_intelligence": {},
            "content_plan": {},
            "draft": {
                "entity": {"entity_name": "Andheri West"},
                "quality_report": {"approval_status": "pass", "overall_quality_score": 96},
            },
            "validation_report": {"passed": True},
            "quality_report": {"approval_status": "pass", "overall_quality_score": 96},
            "section_review": [],
            "version_history": [],
            "latest_version_id": "v-test",
        }


def test_create_review_session_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import review as review_route_module

    monkeypatch.setattr(
        review_route_module,
        "ReviewWorkbenchService",
        DummyReviewWorkbenchService,
    )

    response = client.post(
        "/v1/review/session",
        json={
            "main_datacenter_json_path": "main.json",
            "property_rates_json_path": "rates.json",
            "listing_type": "resale",
            "include_historical": True,
            "persist_session": False,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["review_session"]["session_id"] == "review-test-123"
    assert payload["review_session"]["entity"]["entity_name"] == "Andheri West"


def test_get_review_session_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import review as review_route_module

    monkeypatch.setattr(
        review_route_module,
        "ReviewWorkbenchService",
        DummyReviewWorkbenchService,
    )

    response = client.get("/v1/review/session/review-test-123")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["review_session"]["session_id"] == "review-test-123"