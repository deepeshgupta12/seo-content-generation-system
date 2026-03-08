from pathlib import Path

from fastapi.testclient import TestClient
from seo_content_engine.main import app

client = TestClient(app)


class DummyKeywordService:
    @staticmethod
    def build_keyword_intelligence(normalized, location_name=None, language_name=None, limit=None):
        return {
            "version": "v1",
            "generated_at": "2026-03-08T00:00:00+00:00",
            "page_type": normalized["entity"]["page_type"],
            "listing_type": normalized["entity"]["listing_type"],
            "entity": normalized["entity"],
            "dataforseo_context": {
                "location_name": location_name or "India",
                "language_name": language_name or "English",
                "limit": limit or 50,
                "related_depth": 2,
            },
            "seed_keywords": ["resale properties in Andheri West Mumbai"],
            "seed_count": 1,
            "suggestions": {
                "total_unique_keywords": 1,
                "by_seed": [],
                "all_unique_items": [{"keyword": "resale properties in andheri west mumbai", "search_volume": 100}],
            },
            "related_keywords": {
                "total_unique_keywords": 1,
                "by_seed": [],
                "all_unique_items": [{"keyword": "flats for sale in andheri west mumbai", "search_volume": 90}],
            },
        }


def test_keywords_intelligence_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import keywords as keywords_route_module

    monkeypatch.setattr(
        keywords_route_module,
        "KeywordIntelligenceService",
        DummyKeywordService,
    )

    project_root = Path(__file__).resolve().parents[3]
    main_json = project_root / "data" / "samples" / "raw" / "andheri-west-locality.json"
    rates_json = project_root / "data" / "samples" / "raw" / "andheri-west-property-rates.json"

    response = client.post(
        "/v1/keywords/intelligence",
        json={
            "main_datacenter_json_path": str(main_json),
            "property_rates_json_path": str(rates_json),
            "listing_type": "resale",
            "write_artifact": False,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["keyword_intelligence"]["entity"]["entity_name"] == "Andheri West"
    assert payload["keyword_intelligence"]["seed_count"] == 1