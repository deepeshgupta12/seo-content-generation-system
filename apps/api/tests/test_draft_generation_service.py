from seo_content_engine.services.draft_generation_service import DraftGenerationService


class DummyOpenAIClient:
    def generate_json(self, system_prompt: str, user_prompt: str):
        if '"validation_by_field"' in user_prompt:
            return {
                "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
                "meta_description": "Explore resale properties in Andheri West, Mumbai with current price trends and BHK mix on Square Yards.",
                "h1": "Resale Properties in Andheri West, Mumbai",
                "intro_snippet": "Browse current resale property options in Andheri West, Mumbai on Square Yards.",
            }

        if '"faq"' in user_prompt and '"validator_feedback"' in user_prompt:
            return {
                "question": "What is the asking price signal for resale properties in Andheri West, Mumbai?",
                "answer": "The asking price signal is ₹40,238.",
            }

        if '"section"' in user_prompt and '"validator_feedback"' in user_prompt:
            return {
                "id": "market_snapshot",
                "title": "Resale Market Snapshot",
                "body": "The asking price signal is ₹40,238 and total listings are 6,109.",
            }

        if '"faqs"' in user_prompt:
            return {
                "faqs": [
                    {
                        "question": "What is the asking price signal for resale properties in Andheri West, Mumbai?",
                        "answer": "The asking price signal is ₹40,238.",
                    },
                    {
                        "question": "What review signals are available for this resale page?",
                        "answer": "The page includes an average rating of 4.23 based on 97 reviews.",
                    },
                    {
                        "question": "What demand and supply inputs are available on this page?",
                        "answer": "The sale-side inputs include a 2 BHK demand percent of 30 and supply percent of 32.",
                    },
                    {
                        "question": "Which property-type signals are available on this resale page?",
                        "answer": "Apartment property-type inputs are available in the grounded source data.",
                    },
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
                        "body": "The asking price signal is ₹40,238 and total listings are 6,109.",
                    },
                    {
                        "id": "price_trends_and_rates",
                        "title": "Price Trends and Rates",
                        "body": "The asking price signal is ₹40,238.",
                    },
                    {
                        "id": "review_and_rating_signals",
                        "title": "Review and Rating Signals",
                        "body": "The page includes a 4.23 average rating based on 97 reviews.",
                    },
                    {
                        "id": "demand_and_supply_signals",
                        "title": "Demand and Supply Signals",
                        "body": "The sale-side inputs include a 2 BHK demand percent of 30 and supply percent of 32.",
                    },
                    {
                        "id": "property_type_signals",
                        "title": "Property Type Signals",
                        "body": "Apartment appears in the grounded property-type inputs.",
                    },
                ]
            }

        return {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Explore resale properties in Andheri West, Mumbai with current price trends and BHK mix on Square Yards.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse current resale property options in Andheri West, Mumbai on Square Yards.",
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
            "sale_available": 2039,
        },
        "pricing_summary": {
            "asking_price": 40238,
            "registration_rate": 26616,
            "price_trend": [{"quarterName": "Dec 2025", "locationRate": 40238, "micromarketRate": 21180}],
            "location_rates": [{"name": "Yari Road", "avgRate": 32638, "changePercentage": 0}],
            "property_types": [{"propertyType": "apartment", "avgPrice": 40238, "changePercent": 4.61}],
            "property_status": [{"status": "Ready To Move", "units": 957, "avgPrice": 31639, "changePercent": -2.88}],
        },
        "distributions": {
            "sale_unit_type_distribution": [{"key": "3 BHK", "doc_count": 789}],
            "sale_property_type_distribution": [{"key": "Apartment", "doc_count": 1658}],
        },
        "nearby_localities": [
            {
                "name": "Sv Patel Nagar",
                "distance_km": 0.587,
                "sale_count": 38,
                "sale_avg_price_per_sqft": 29775.32,
                "url": "sv-patel-nagar-mumbai",
            }
        ],
        "links": {
            "sale_unit_type_urls": [[{"unitType": "2 BHK", "url": "sale/2-bhk-for-sale-in-andheri-west-mumbai"}]],
            "sale_property_type_urls": [[{"propertyType": "Apartment", "url": "sale/apartments-for-sale-in-andheri-west-mumbai"}]],
            "sale_quick_links": [{"label": "New Projects in Andheri West", "url": "projects-in-andheri-west-mumbai"}],
        },
        "top_projects": {"byTransactions": {"projects": []}},
        "review_summary": {
            "overview": {"avg_rating": 4.23, "rating_count": 97, "review_count": 97},
            "star_distribution": [{"rating": 5, "count": 40}],
            "positive_tags": ["metro connectivity"],
            "negative_tags": ["traffic"],
        },
        "ai_summary": {"locality_summary": "Established locality with mixed residential inventory."},
        "insight_rates": {"name": "Andheri West", "avg_rate": 40238},
        "demand_supply": {"sale": {"unitType": [{"name": "2 BHK", "listing": 577, "demandPercent": 30, "supplyPercent": 32}]}},
        "listing_ranges": {"sale_listing_range": {"doc_count": 1933, "min_price": 2320000, "max_price": 4900000000}},
        "cms_faq": [{"question": "Sample question", "answer": "Sample answer"}],
        "featured_projects": [{"name": "Project A", "url": "projects-in-andheri-west-mumbai/project-a"}],
        "projects_by_status": {},
        "raw_source_meta": {
            "main_message": "locality Found",
            "rates_message": "Property Rates Data Found",
            "last_modified_date": "2026-03-02",
        },
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

    assert draft["version"] == "v2.4"
    assert draft["metadata"]["h1"] == "Resale Properties in Andheri West, Mumbai"
    assert len(draft["sections"]) > 0
    assert len(draft["tables"]) > 0
    assert len(draft["faqs"]) > 0
    assert "validation_report" in draft
    assert "quality_report" in draft
    assert "repair_passes_used" in draft
    assert "validation_history" in draft
    assert "pre_block_draft" in draft
    assert "debug_summary" in draft

    review_section = next(section for section in draft["sections"] if section["id"] == "review_and_rating_signals")
    demand_section = next(section for section in draft["sections"] if section["id"] == "demand_and_supply_signals")
    property_type_section = next(section for section in draft["sections"] if section["id"] == "property_type_signals")

    assert "4.23" in review_section["body"]
    assert "demand percent" in demand_section["body"].lower()
    assert "apartment" in property_type_section["body"].lower()
    assert draft["quality_report"]["approval_status"] in {"pass", "warning"}
    assert "overall_quality_score" in draft["quality_report"]
    assert "warning_taxonomy" in draft["quality_report"]
    assert "page_uniqueness_check" in draft["quality_report"]
    assert "https://www.squareyards.com/" in draft["markdown_draft"]

def test_micromarket_property_type_safe_body_allows_single_decimal_grounded_value() -> None:
    normalized = {
        "entity": {
            "entity_type": "micromarket",
            "page_type": "resale_micromarket",
            "listing_type": "resale",
            "entity_name": "Chandigarh Sectors",
            "city_name": "Chandigarh",
            "micromarket_name": "Chandigarh Sectors",
        },
        "listing_summary": {
            "sale_count": 10,
            "total_listings": 10,
            "total_projects": 2,
            "sale_available": 10,
        },
        "pricing_summary": {
            "asking_price": 25000,
            "registration_rate": 20000,
            "price_trend": [{"quarterName": "Dec 2025", "micromarketRate": 25000}],
            "location_rates": [{"name": "Sector 51", "avgRate": 18543, "changePercentage": 16.47}],
            "property_types": [{"propertyType": "villa", "avgPrice": 36631, "changePercent": 8.4}],
            "property_status": [{"status": "Ready To Move", "units": 1, "avgPrice": 20047}],
        },
        "distributions": {
            "sale_unit_type_distribution": [{"key": "3 BHK", "doc_count": 4}],
            "sale_property_type_distribution": [{"key": "Villa", "doc_count": 2}],
        },
        "nearby_localities": [],
        "links": {
            "sale_unit_type_urls": [],
            "sale_property_type_urls": [],
            "sale_quick_links": [],
        },
        "top_projects": {"byTransactions": {"projects": []}},
        "review_summary": {"overview": {}},
        "ai_summary": {},
        "insight_rates": {},
        "demand_supply": {},
        "listing_ranges": {},
        "cms_faq": [],
        "featured_projects": [],
        "projects_by_status": {},
        "raw_source_meta": {
            "main_message": "micromarket Found",
            "rates_message": "Property Rates Data Found",
            "last_modified_date": "2026-03-05",
        },
    }

    keyword_intelligence = {
        "version": "v1.1",
        "keyword_clusters": {
            "primary_keyword": {"keyword": "resale properties in chandigarh sectors chandigarh", "score": 90},
            "secondary_keywords": [{"keyword": "apartments for sale in chandigarh sectors chandigarh"}],
            "bhk_keywords": [],
            "price_keywords": [{"keyword": "property prices in chandigarh sectors chandigarh"}],
            "ready_to_move_keywords": [],
            "faq_keyword_candidates": [],
            "metadata_keywords": ["resale properties in chandigarh sectors chandigarh"],
            "exact_match_keywords": [{"keyword": "resale properties in chandigarh sectors chandigarh"}],
            "loose_match_keywords": [],
        },
    }

    content_plan = DraftGenerationService.generate(
        normalized=normalized,
        keyword_intelligence=keyword_intelligence,
        openai_client=DummyOpenAIClient(),
    )["content_plan"]

    safe_body = DraftGenerationService._build_property_type_safe_body(content_plan)

    assert "8.4" in safe_body
    assert "16.47" in safe_body
