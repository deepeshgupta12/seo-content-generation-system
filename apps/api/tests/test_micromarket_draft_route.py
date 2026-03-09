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
                    "keyword": "resale properties in chandigarh tricity chandigarh",
                    "score": 88,
                },
                "secondary_keywords": [{"keyword": "apartments for sale in chandigarh tricity chandigarh"}],
                "bhk_keywords": [],
                "price_keywords": [{"keyword": "property prices in chandigarh tricity chandigarh"}],
                "ready_to_move_keywords": [],
                "faq_keyword_candidates": [{"keyword": "property prices in chandigarh tricity chandigarh"}],
                "metadata_keywords": ["resale properties in chandigarh tricity chandigarh"],
                "exact_match_keywords": [{"keyword": "resale properties in chandigarh tricity chandigarh"}],
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


def test_micromarket_draft_route(monkeypatch, tmp_path: Path) -> None:
    from seo_content_engine.api.routes import generation as generation_route_module

    monkeypatch.setattr(generation_route_module, "KeywordIntelligenceService", DummyKeywordService)
    monkeypatch.setattr(generation_route_module, "DraftGenerationService", DummyDraftService)

    main_data = {
        "message": "ok",
        "data": {
            "lastModifiedDate": "2026-03-09",
            "localityOverviewData": {
                "name": "Chandigarh Tricity",
                "cityName": "Chandigarh",
                "isMicroMarket": 1,
                "saleCount": 120,
                "totallistings": 250,
                "totalprojects": 60,
                "sale": {"available": 120},
                "rent": {"available": 0},
                "metrics": {"sale": {}, "rent": {}},
            },
            "localityData": {
                "cityName": "Chandigarh",
                "microMarketId": 22,
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
            "type": "micromarket",
            "propertyRatesData": {
                "details": {
                    "name": "Chandigarh Tricity",
                    "cityName": "Chandigarh",
                    "microMarketName": "Chandigarh Tricity",
                },
                "marketOverview": {
                    "askingPrice": 12345,
                },
                "priceTrend": [],
                "locationRates": [],
                "propertyTypes": [],
                "propertyStatus": [],
                "topProjects": {},
            },
        },
    }

    main_path = tmp_path / "chandigarh-micromarket-main.json"
    rates_path = tmp_path / "chandigarh-micromarket-rates.json"
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
    assert payload["draft"]["page_type"] == "resale_micromarket"
    assert payload["draft"]["entity"]["entity_name"] == "Chandigarh Tricity"
    assert payload["draft"]["entity"]["city_name"] == "Chandigarh"
    assert payload["draft"]["quality_report"]["approval_status"] == "pass"