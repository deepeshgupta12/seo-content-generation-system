from seo_content_engine.services.draft_generation_service import DraftGenerationService


class RepairingDummyOpenAIClient:
    def __init__(self) -> None:
        self.section_repair_called = 0
        self.faq_repair_called = 0
        self.metadata_repair_called = 0

    def generate_json(self, system_prompt: str, user_prompt: str):
        if '"validation_by_field"' in user_prompt:
            self.metadata_repair_called += 1
            return {
                "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
                "meta_description": "Explore resale properties in Andheri West, Mumbai with current price trends and BHK mix on Square Yards.",
                "h1": "Resale Properties in Andheri West, Mumbai",
                "intro_snippet": "Browse current resale property options in Andheri West, Mumbai on Square Yards.",
            }

        if '"faq"' in user_prompt and '"validator_feedback"' in user_prompt:
            self.faq_repair_called += 1
            return {
                "question": "What is the asking price signal for resale properties in Andheri West, Mumbai?",
                "answer": "The asking price signal is ₹40,238 based on Square Yards data.",
            }

        if '"section"' in user_prompt and '"validator_feedback"' in user_prompt:
            self.section_repair_called += 1

            if '"id": "price_trends_and_rates"' in user_prompt:
                return {
                    "id": "price_trends_and_rates",
                    "title": "Price Trends and Rates",
                    "body": "The asking price signal is ₹40,238.",
                }

            if '"id": "market_snapshot"' in user_prompt:
                return {
                    "id": "market_snapshot",
                    "title": "Resale Market Snapshot",
                    "body": "The asking price signal is ₹40,238 and total listings are 6,109.",
                }

            return {
                "id": "hero_intro",
                "title": "Resale Property Overview in Andheri West, Mumbai",
                "body": "Andheri West has 2,039 resale listings visible on Square Yards.",
            }

        if '"faqs"' in user_prompt:
            return {
                "faqs": [
                    {
                        "question": "What is the asking price signal for resale properties in Andheri West, Mumbai?",
                        "answer": "This area has strong demand and the average price is ₹99,999.",
                    }
                ]
            }

        if '"sections"' in user_prompt:
            return {
                "sections": [
                    {
                        "id": "hero_intro",
                        "title": "Resale Property Overview in Andheri West, Mumbai",
                        "body": "Andheri West has 2,039 resale listings visible on Square Yards.",
                    },
                    {
                        "id": "market_snapshot",
                        "title": "Resale Market Snapshot",
                        "body": "This locality has strong demand and the average price is ₹99,999.",
                    },
                    {
                        "id": "price_trends_and_rates",
                        "title": "Price Trends and Rates",
                        "body": "The registration rate is ₹26,616 and the average price is ₹40,238.",
                    },
                ]
            }

        return {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Andheri West is one of the most sought-after areas.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse current resale property options in Andheri West, Mumbai.",
        }


def test_draft_repair_loop_repairs_flagged_content() -> None:
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

    client = RepairingDummyOpenAIClient()
    draft = DraftGenerationService.generate(
        normalized=normalized,
        keyword_intelligence=keyword_intelligence,
        openai_client=client,
    )

    assert draft["version"] == "v2.3"
    assert client.metadata_repair_called >= 1
    assert client.section_repair_called >= 1
    assert client.faq_repair_called >= 1
    assert draft["repair_passes_used"] >= 1
    assert "pre_block_draft" in draft
    assert "debug_summary" in draft

    price_section = next(section for section in draft["sections"] if section["id"] == "price_trends_and_rates")
    assert "registration rate" not in price_section["body"].lower()