from seo_content_engine.services.content_plan_builder import ContentPlanBuilder


def test_content_plan_builder_for_locality() -> None:
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
            "primary_keyword": {"keyword": "flats for sale in andheri west mumbai", "score": 92},
            "secondary_keywords": [{"keyword": "apartments for sale in andheri west mumbai"}],
            "bhk_keywords": [{"keyword": "2 bhk flats for sale in andheri west mumbai"}],
            "price_keywords": [{"keyword": "property prices in andheri west mumbai"}],
            "ready_to_move_keywords": [{"keyword": "ready possession flats in andheri west"}],
            "faq_keyword_candidates": [{"keyword": "property prices in andheri west mumbai"}],
            "metadata_keywords": [
                "flats for sale in andheri west mumbai",
                "apartments for sale in andheri west mumbai",
            ],
        },
    }

    content_plan = ContentPlanBuilder.build(normalized=normalized, keyword_intelligence=keyword_intelligence)

    assert content_plan["version"] == "v1.4"
    assert content_plan["metadata_plan"]["recommended_h1"] == "Resale Properties in Andheri West, Mumbai"
    assert content_plan["keyword_strategy"]["primary_keyword"]["keyword"] == "flats for sale in andheri west mumbai"
    assert len(content_plan["section_plan"]) > 0
    assert len(content_plan["table_plan"]) > 0
    assert content_plan["faq_plan"]["total_faq_intents"] > 0