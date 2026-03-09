from pathlib import Path

from fastapi.testclient import TestClient
from seo_content_engine.main import app

client = TestClient(app)


class DummyKeywordService:
    @staticmethod
    def build_keyword_intelligence(
        normalized,
        location_name=None,
        language_name=None,
        limit=None,
        include_historical=True,
    ):
        return {
            "version": "v1.1",
            "keyword_clusters": {
                "primary_keyword": {
                    "keyword": "flats for sale in andheri west mumbai",
                    "score": 92,
                    "semantic_signature": ("andheri", "flats", "for", "in", "mumbai", "sale", "west"),
                },
                "secondary_keywords": [{"keyword": "apartments for sale in andheri west mumbai"}],
                "bhk_keywords": [{"keyword": "2 bhk flats for sale in andheri west mumbai"}],
                "price_keywords": [{"keyword": "property prices in andheri west mumbai"}],
                "ready_to_move_keywords": [{"keyword": "ready possession flats in andheri west"}],
                "faq_keyword_candidates": [{"keyword": "property prices in andheri west mumbai"}],
                "metadata_keywords": [
                    "flats for sale in andheri west mumbai",
                    "apartments for sale in andheri west mumbai",
                ],
                "exact_match_keywords": [{"keyword": "flats for sale in andheri west mumbai"}],
                "loose_match_keywords": [],
            },
        }


class DummyDraftService:
    @staticmethod
    def generate(normalized, keyword_intelligence):
        entity_name = normalized["entity"]["entity_name"]
        city_name = normalized["entity"]["city_name"]

        return {
            "version": "v2.4",
            "page_type": normalized["entity"]["page_type"],
            "listing_type": normalized["entity"]["listing_type"],
            "entity": normalized["entity"],
            "metadata": {
                "title": f"Resale Properties in {entity_name}, {city_name} | Square Yards",
                "meta_description": f"Explore resale properties in {entity_name}, {city_name} on Square Yards.",
                "h1": f"Resale Properties in {entity_name}, {city_name}",
                "intro_snippet": f"Browse resale listings in {entity_name}, {city_name}.",
            },
            "sections": [
                {
                    "id": "hero_intro",
                    "title": f"Resale Property Overview in {entity_name}, {city_name}",
                    "body": f"{entity_name} has a visible resale supply on Square Yards.",
                }
            ],
            "tables": [],
            "faqs": [],
            "internal_links": {},
            "content_plan": {},
            "keyword_intelligence_version": "v1.1",
            "validation_report": {"passed": True},
            "quality_report": {"approval_status": "pass", "overall_score": 1.0, "warnings": []},
            "validation_history": [],
            "pre_block_draft": {},
            "debug_summary": {"blocked": False, "blocking_reasons": [], "approval_status": "pass"},
            "publish_ready": True,
            "markdown_draft": f"# Resale Properties in {entity_name}, {city_name}\n",
        }


def test_draft_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import generation as generation_route_module

    monkeypatch.setattr(
        generation_route_module,
        "KeywordIntelligenceService",
        DummyKeywordService,
    )
    monkeypatch.setattr(
        generation_route_module,
        "DraftGenerationService",
        DummyDraftService,
    )

    project_root = Path(__file__).resolve().parents[3]
    main_json = project_root / "data" / "samples" / "raw" / "andheri-west-locality.json"
    rates_json = project_root / "data" / "samples" / "raw" / "andheri-west-property-rates.json"

    response = client.post(
        "/v1/generate/draft",
        json={
            "main_datacenter_json_path": str(main_json),
            "property_rates_json_path": str(rates_json),
            "listing_type": "resale",
            "include_historical": True,
            "write_artifact": False,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["draft"]["entity"]["entity_name"] == "Andheri West"
    assert payload["draft"]["metadata"]["h1"] == "Resale Properties in Andheri West, Mumbai"
    assert payload["draft"]["quality_report"]["approval_status"] == "pass"
    assert payload["artifact_paths"] is None