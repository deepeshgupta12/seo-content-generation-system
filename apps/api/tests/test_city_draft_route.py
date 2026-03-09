import json
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
                    "keyword": "resale properties in mumbai",
                    "score": 90,
                },
                "secondary_keywords": [{"keyword": "apartments for sale in mumbai"}],
                "bhk_keywords": [],
                "price_keywords": [{"keyword": "property prices in mumbai"}],
                "ready_to_move_keywords": [],
                "faq_keyword_candidates": [{"keyword": "property prices in mumbai"}],
                "metadata_keywords": ["resale properties in mumbai"],
                "exact_match_keywords": [{"keyword": "resale properties in mumbai"}],
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
            "sections": [],
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


def test_city_draft_route(monkeypatch, tmp_path: Path) -> None:
    from seo_content_engine.api.routes import generation as generation_route_module

    monkeypatch.setattr(generation_route_module, "KeywordIntelligenceService", DummyKeywordService)
    monkeypatch.setattr(generation_route_module, "DraftGenerationService", DummyDraftService)

    main_data = {
        "message": "ok",
        "data": {
            "lastModifiedDate": "2026-03-09",
            "localityOverviewData": {
                "name": "Mumbai",
                "cityName": "Mumbai",
                "saleCount": 1000,
                "totallistings": 1800,
                "totalprojects": 300,
                "sale": {"available": 1000},
                "rent": {"available": 0},
                "metrics": {"sale": {}, "rent": {}},
            },
            "localityData": {
                "cityName": "Mumbai",
                "beatsCityId": 1,
            },
            "saleListingFooter": {},
            "nearByLocalities": [],
            "ratingReview": {},
            "localityAiData": {},
            "demandSupply": {},
            "listingCountData": [],
            "insightRates": {},
            "cmsFAQ": [],
            "featuredProjects": [],
            "projectsByStatus": {},
        },
    }

    rates_data = {
        "message": "ok",
        "data": {
            "type": "city",
            "propertyRatesData": {
                "details": {
                    "name": "Mumbai",
                    "cityName": "Mumbai",
                    "cityId": 1,
                },
                "marketOverview": {
                    "askingPrice": 45000,
                },
                "priceTrend": [],
                "locationRates": [],
                "propertyTypes": [],
                "propertyStatus": [],
                "topProjects": {},
            },
        },
    }

    main_path = tmp_path / "mumbai-city-main.json"
    rates_path = tmp_path / "mumbai-city-rates.json"
    main_path.write_text(json.dumps(main_data), encoding="utf-8")
    rates_path.write_text(json.dumps(rates_data), encoding="utf-8")

    response = client.post(
        "/v1/generate/draft",
        json={
            "main_datacenter_json_path": str(main_path),
            "property_rates_json_path": str(rates_path),
            "listing_type": "resale",
            "include_historical": True,
            "write_artifact": False,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["draft"]["page_type"] == "resale_city"
    assert payload["draft"]["entity"]["entity_name"] == "Mumbai"
    assert payload["draft"]["entity"]["city_name"] == "Mumbai"
    assert payload["draft"]["quality_report"]["approval_status"] == "pass"