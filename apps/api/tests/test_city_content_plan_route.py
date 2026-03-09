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
                "primary_keyword": {"keyword": "flats for sale in mumbai", "score": 95},
                "secondary_keywords": [{"keyword": "apartments for sale in mumbai"}],
                "bhk_keywords": [{"keyword": "2 bhk flats for sale in mumbai"}],
                "price_keywords": [{"keyword": "property prices in mumbai"}],
                "ready_to_move_keywords": [{"keyword": "ready possession flats in mumbai"}],
                "faq_keyword_candidates": [{"keyword": "property prices in mumbai"}],
                "metadata_keywords": [
                    "flats for sale in mumbai",
                    "apartments for sale in mumbai",
                ],
            },
        }


def test_city_content_plan_route(monkeypatch) -> None:
    from seo_content_engine.api.routes import generation as generation_route_module

    monkeypatch.setattr(
        generation_route_module,
        "KeywordIntelligenceService",
        DummyKeywordService,
    )

    project_root = Path(__file__).resolve().parents[3]
    main_json = project_root / "data" / "samples" / "raw" / "Mumbai city.json"
    rates_json = project_root / "data" / "samples" / "raw" / "Mumbai Property rates.json"

    response = client.post(
        "/v1/generate/content-plan",
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
    assert payload["content_plan"]["entity"]["entity_name"] == "Mumbai"
    assert payload["content_plan"]["entity"]["city_name"] == "Mumbai"
    assert payload["content_plan"]["page_type"] == "resale_city"
    assert payload["content_plan"]["metadata_plan"]["recommended_h1"] == "Resale Properties in Mumbai"