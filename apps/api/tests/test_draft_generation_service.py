from seo_content_engine.services.draft_generation_service import DraftGenerationService


class DummyOpenAIClient:
    def generate_json(self, system_prompt: str, user_prompt: str):
        if '"faqs"' in user_prompt:
            return {
                "faqs": [
                    {
                        "question": "What is the average price of resale properties in Andheri West, Mumbai?",
                        "answer": "The current asking price signal for Andheri West can be reviewed from Square Yards market data on this page.",
                    }
                ]
            }

        if '"sections"' in user_prompt:
            return {
                "sections": [
                    {
                        "id": "hero_intro",
                        "title": "Resale Property Overview in Andheri West, Mumbai",
                        "body": "Andheri West has an active resale market with a broad mix of inventory, price points, and buyer options visible on Square Yards.",
                    },
                    {
                        "id": "market_snapshot",
                        "title": "Resale Market Snapshot",
                        "body": "The resale supply in Andheri West spans multiple BHK formats and property types, giving buyers a wider comparison set within the locality.",
                    },
                ]
            }

        return {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Explore resale properties in Andheri West, Mumbai with prices, BHK mix, and nearby locality insights on Square Yards.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse current resale property options in Andheri West, Mumbai with real market signals from Square Yards.",
        }


def test_draft_generation_service() -> None:
    normalized = {
        "entity": {
            "entity_type": "locality",
            "page_type": "resale_locality",
            "listing_type": "resale",
            "entity_name": "Andheri West",
            "city_name": "Mumbai",
            "micromarket_name": "Mumbai Western Suburbs",
        },
        "listing_summary": {
            "sale_count": 2039,
            "total_listings": 6109,
            "total_projects": 1762,
        },
        "pricing_summary": {
            "asking_price": 40238,
            "registration_rate": 26616,
            "price_trend": [{"quarterName": "Dec 2025", "locationRate": 40238, "micromarketRate": 21180}],
            "property_status": [{"status": "Ready To Move", "units": 957, "avgPrice": 31639}],
        },
        "distributions": {
            "sale_unit_type_distribution": [{"key": "3 BHK", "doc_count": 789}],
            "sale_property_type_distribution": [{"key": "Apartment", "doc_count": 1658}],
        },
        "nearby_localities": [
            {"name": "Sv Patel Nagar", "distance_km": 0.587, "sale_count": 38, "sale_avg_price_per_sqft": 29775.32, "url": "sv-patel-nagar-mumbai"},
        ],
        "links": {
            "sale_unit_type_urls": [[{"unitType": "2 BHK", "url": "sale/2-bhk-for-sale-in-andheri-west-mumbai"}]],
            "sale_property_type_urls": [[{"propertyType": "Apartment", "url": "sale/apartments-for-sale-in-andheri-west-mumbai"}]],
            "sale_quick_links": [{"label": "New Projects in Andheri West", "url": "projects-in-andheri-west-mumbai"}],
        },
        "top_projects": {"byTransactions": {"projects": []}},
        "raw_source_meta": {"main_message": "locality Found", "rates_message": "Property Rates Data Found"},
    }

    keyword_intelligence = {
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

    draft = DraftGenerationService.generate(
        normalized=normalized,
        keyword_intelligence=keyword_intelligence,
        openai_client=DummyOpenAIClient(),
    )

    assert draft["version"] == "v2.0"
    assert draft["metadata"]["h1"] == "Resale Properties in Andheri West, Mumbai"
    assert len(draft["sections"]) > 0
    assert len(draft["tables"]) > 0
    assert len(draft["faqs"]) > 0
    assert "# Resale Properties in Andheri West, Mumbai" in draft["markdown_draft"]