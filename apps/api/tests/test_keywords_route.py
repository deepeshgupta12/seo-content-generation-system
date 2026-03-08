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
            "generated_at": "2026-03-08T00:00:00+00:00",
            "page_type": normalized["entity"]["page_type"],
            "listing_type": normalized["entity"]["listing_type"],
            "entity": normalized["entity"],
            "dataforseo_context": {
                "location_name": location_name or "India",
                "language_name": language_name or "English",
                "limit": limit or 50,
                "related_depth": 2,
                "historical_keywords_limit": 50,
                "historical_enriched": include_historical,
            },
            "warnings": [],
            "seed_keywords": ["resale properties in Andheri West Mumbai"],
            "seed_count": 1,
            "raw_retrieval": {
                "suggestions": {"total_unique_keywords": 1, "by_seed": []},
                "related_keywords": {"total_unique_keywords": 1, "by_seed": []},
            },
            "historical_enrichment": {
                "applied": include_historical,
                "historical_keywords_count": 1,
            },
            "normalized_keywords": {
                "total_records_before_consolidation": 2,
                "total_unique_records_after_consolidation": 1,
                "included_count": 1,
                "excluded_count": 0,
                "included_keywords": [],
                "excluded_keywords": [],
            },
            "keyword_clusters": {
                "primary_keyword": {
                    "keyword": "flats for sale in andheri west mumbai",
                    "score": 92,
                },
                "secondary_keywords": [],
                "bhk_keywords": [],
                "price_keywords": [],
                "ready_to_move_keywords": [],
                "long_tail_keywords": [],
                "faq_keyword_candidates": [],
                "metadata_keywords": ["flats for sale in andheri west mumbai"],
                "total_included_keywords": 1,
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
            "include_historical": True,
            "write_artifact": False,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["keyword_intelligence"]["entity"]["entity_name"] == "Andheri West"
    assert payload["keyword_intelligence"]["keyword_clusters"]["primary_keyword"]["keyword"] == (
        "flats for sale in andheri west mumbai"
    )