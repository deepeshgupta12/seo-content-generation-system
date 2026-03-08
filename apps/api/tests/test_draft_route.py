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
        return {
            "version": "v2.0",
            "page_type": normalized["entity"]["page_type"],
            "listing_type": normalized["entity"]["listing_type"],
            "entity": normalized["entity"],
            "metadata": {
                "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
                "meta_description": "Explore resale properties in Andheri West, Mumbai on Square Yards.",
                "h1": "Resale Properties in Andheri West, Mumbai",
                "intro_snippet": "Browse resale listings in Andheri West, Mumbai.",
            },
            "sections": [
                {
                    "id": "hero_intro",
                    "title": "Resale Property Overview in Andheri West, Mumbai",
                    "body": "Andheri West has a visible resale supply on Square Yards.",
                }
            ],
            "tables": [],
            "faqs": [],
            "internal_links": {},
            "content_plan": {},
            "keyword_intelligence_version": "v1.1",
            "markdown_draft": "# Resale Properties in Andheri West, Mumbai\n",
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