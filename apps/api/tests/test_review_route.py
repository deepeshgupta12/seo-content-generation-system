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
                "listing_type": "resale",
            },
            "source_preview": {"listing_summary": {"sale_count": 2039}},
            "keyword_preview": {"primary_keyword": {"keyword": "flats for sale in andheri west mumbai"}},
            "normalized": {},
            "keyword_intelligence": {},
            "content_plan": {},
            "draft": {
                "entity": {"entity_name": "Andheri West"},
                "quality_report": {"approval_status": "pass", "overall_quality_score": 96},
                "sections": [
                    {
                        "id": "hero_intro",
                        "title": "Hero Intro",
                        "body": "Initial body with grounded resale context.",
                    }
                ],
                "tables": [
                    {
                        "id": "price_trend_table",
                        "title": "Price Trend Snapshot",
                        "columns": ["quarterName", "locationRate"],
                        "rows": [{"quarterName": "Dec 2025", "locationRate": "₹40,238"}],
                        "summary": "Price Trend Snapshot presents structured price inputs for draft review.",
                    }
                ],
                "faqs": [
                    {
                        "question": "What is the asking price signal for resale properties in Andheri West, Mumbai?",
                        "answer": "The asking price signal is ₹40,238 based on the grounded inputs.",
                        "validation_passed": True,
                        "validation_issues": [],
                    }
                ],
                "metadata": {
                    "title": "Initial Title",
                    "meta_description": "Initial Description",
                    "h1": "Initial H1",
                    "intro_snippet": "Initial intro",
                },
                "publish_ready": True,
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
                "listing_type": "resale",
            },
            "source_preview": {"listing_summary": {"sale_count": 2039}},
            "keyword_preview": {"primary_keyword": {"keyword": "flats for sale in andheri west mumbai"}},
            "normalized": {},
            "keyword_intelligence": {},
            "content_plan": {},
            "draft": {
                "entity": {"entity_name": "Andheri West"},
                "quality_report": {"approval_status": "pass", "overall_quality_score": 96},
                "tables": [],
                "faqs": [],
                "publish_ready": True,
            },
            "validation_report": {"passed": True},
            "quality_report": {"approval_status": "pass", "overall_quality_score": 96},
            "section_review": [],
            "version_history": [],
            "latest_version_id": "v-test",
        }

    @staticmethod
    def regenerate_draft(*, session_id, persist_session=True, action_label="full_regenerate"):
        return (
            {
                "session_id": session_id,
                "latest_version_id": "v-regenerated",
                "draft": {
                    "metadata": {"title": "Regenerated Title"},
                    "sections": [],
                    "tables": [
                        {
                            "id": "price_trend_table",
                            "title": "Price Trend Snapshot",
                            "columns": ["quarterName", "locationRate"],
                            "rows": [{"quarterName": "Dec 2025", "locationRate": "₹40,238"}],
                            "summary": "Regenerated table summary for structured price review.",
                        }
                    ],
                    "faqs": [
                        {
                            "question": "What is the asking price signal for resale properties in Andheri West, Mumbai?",
                            "answer": "The asking price signal remains ₹40,238 in the regenerated draft.",
                        }
                    ],
                    "publish_ready": True,
                },
                "quality_report": {"approval_status": "pass", "overall_quality_score": 97},
            },
            {
                "action_type": action_label,
                "session_id": session_id,
                "latest_version_id": "v-regenerated",
                "approval_status": "pass",
                "overall_quality_score": 97,
                "publish_ready": True,
            },
        )

    @staticmethod
    def regenerate_section(*, session_id, section_id, persist_session=True, action_label="section_regenerate"):
        return (
            {
                "session_id": session_id,
                "latest_version_id": "v-section-regenerated",
                "draft": {
                    "sections": [
                        {
                            "id": section_id,
                            "title": "Hero Intro",
                            "body": "Regenerated section body with more descriptive grounded resale context.",
                        }
                    ],
                    "publish_ready": True,
                },
                "quality_report": {"approval_status": "pass", "overall_quality_score": 95},
            },
            {
                "action_type": action_label,
                "session_id": session_id,
                "section_id": section_id,
                "latest_version_id": "v-section-regenerated",
                "approval_status": "pass",
                "overall_quality_score": 95,
                "publish_ready": True,
            },
        )

    @staticmethod
    def update_section_body(*, session_id, section_id, body, persist_session=True, action_label="section_edit"):
        return (
            {
                "session_id": session_id,
                "latest_version_id": "v-section-updated",
                "draft": {
                    "sections": [
                        {
                            "id": section_id,
                            "title": "Hero Intro",
                            "body": body,
                        }
                    ],
                    "publish_ready": True,
                },
                "quality_report": {"approval_status": "pass", "overall_quality_score": 94},
            },
            {
                "action_type": action_label,
                "session_id": session_id,
                "section_id": section_id,
                "latest_version_id": "v-section-updated",
                "approval_status": "pass",
                "overall_quality_score": 94,
                "publish_ready": True,
            },
        )

    @staticmethod
    def update_metadata(
        *,
        session_id,
        title,
        meta_description,
        h1,
        intro_snippet,
        persist_session=True,
        action_label="metadata_edit",
    ):
        return (
            {
                "session_id": session_id,
                "latest_version_id": "v-metadata-updated",
                "draft": {
                    "metadata": {
                        "title": title,
                        "meta_description": meta_description,
                        "h1": h1,
                        "intro_snippet": intro_snippet,
                    },
                    "publish_ready": True,
                },
                "quality_report": {"approval_status": "pass", "overall_quality_score": 93},
            },
            {
                "action_type": action_label,
                "session_id": session_id,
                "latest_version_id": "v-metadata-updated",
                "approval_status": "pass",
                "overall_quality_score": 93,
                "publish_ready": True,
            },
        )

    @staticmethod
    def restore_version(*, session_id, version_id, persist_session=True, action_label="restore_version"):
        return (
            {
                "session_id": session_id,
                "latest_version_id": "v-restored",
                "draft": {
                    "metadata": {"title": "Restored Title"},
                    "publish_ready": True,
                },
                "quality_report": {"approval_status": "pass", "overall_quality_score": 98},
            },
            {
                "action_type": action_label,
                "session_id": session_id,
                "restored_from_version_id": version_id,
                "latest_version_id": "v-restored",
                "approval_status": "pass",
                "overall_quality_score": 98,
                "publish_ready": True,
            },
        )


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
    assert len(payload["review_session"]["draft"]["tables"]) == 1
    assert len(payload["review_session"]["draft"]["faqs"]) == 1


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


def test_regenerate_review_draft_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import review as review_route_module

    monkeypatch.setattr(
        review_route_module,
        "ReviewWorkbenchService",
        DummyReviewWorkbenchService,
    )

    response = client.post(
        "/v1/review/session/regenerate",
        json={
            "session_id": "review-test-123",
            "persist_session": False,
            "action_label": "full_regenerate",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["mutation_summary"]["action_type"] == "full_regenerate"
    assert payload["review_session"]["latest_version_id"] == "v-regenerated"
    assert payload["review_session"]["draft"]["tables"][0]["summary"] == "Regenerated table summary for structured price review."


def test_regenerate_review_section_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import review as review_route_module

    monkeypatch.setattr(
        review_route_module,
        "ReviewWorkbenchService",
        DummyReviewWorkbenchService,
    )

    response = client.post(
        "/v1/review/section/regenerate",
        json={
            "session_id": "review-test-123",
            "section_id": "hero_intro",
            "persist_session": False,
            "action_label": "section_regenerate",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["mutation_summary"]["action_type"] == "section_regenerate"
    assert payload["mutation_summary"]["section_id"] == "hero_intro"


def test_update_review_section_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import review as review_route_module

    monkeypatch.setattr(
        review_route_module,
        "ReviewWorkbenchService",
        DummyReviewWorkbenchService,
    )

    response = client.post(
        "/v1/review/section/update",
        json={
            "session_id": "review-test-123",
            "section_id": "hero_intro",
            "body": "Updated section body from route test.",
            "persist_session": False,
            "action_label": "section_edit",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["mutation_summary"]["action_type"] == "section_edit"
    assert payload["review_session"]["draft"]["sections"][0]["body"] == "Updated section body from route test."


def test_update_review_metadata_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import review as review_route_module

    monkeypatch.setattr(
        review_route_module,
        "ReviewWorkbenchService",
        DummyReviewWorkbenchService,
    )

    response = client.post(
        "/v1/review/metadata/update",
        json={
            "session_id": "review-test-123",
            "title": "Updated Title",
            "meta_description": "Updated Description",
            "h1": "Updated H1",
            "intro_snippet": "Updated intro",
            "persist_session": False,
            "action_label": "metadata_edit",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["mutation_summary"]["action_type"] == "metadata_edit"
    assert payload["review_session"]["draft"]["metadata"]["title"] == "Updated Title"


def test_restore_review_version_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import review as review_route_module

    monkeypatch.setattr(
        review_route_module,
        "ReviewWorkbenchService",
        DummyReviewWorkbenchService,
    )

    response = client.post(
        "/v1/review/version/restore",
        json={
            "session_id": "review-test-123",
            "version_id": "v-initial",
            "persist_session": False,
            "action_label": "restore_version",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["mutation_summary"]["action_type"] == "restore_version"
    assert payload["mutation_summary"]["restored_from_version_id"] == "v-initial"