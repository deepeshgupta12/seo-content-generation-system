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
            "sale_available": 2039,
            "sale_supply_count": 2039,
            "sale_visit_count": 1200,
            "sale_enquired_count": 210,
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
            },
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
        "demand_supply": {
            "sale": {
                "unitType": [{"name": "2 BHK", "listing": 577, "demandPercent": 30, "supplyPercent": 32}],
            }
        },
        "listing_ranges": {
            "sale_listing_range": {
                "doc_count": 1933,
                "min_price": 2320000,
                "max_price": 4900000000,
                "building_types": [{"key": "Residential", "doc_count": 1768}],
            }
        },
        "cms_faq": [{"question": "Is Andheri West a good place to live?", "answer": "Sample answer"}],
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

    assert content_plan["version"] == "v1.6"
    assert content_plan["page_type"] == "resale_locality"
    assert content_plan["entity"]["entity_name"] == "Andheri West"
    assert content_plan["metadata_plan"]["recommended_h1"] == "Resale Properties in Andheri West, Mumbai"
    assert "refresh_plan" in content_plan["metadata_plan"]
    assert "comparison_plan" in content_plan
    assert len(content_plan["comparison_plan"]) > 0
    assert "internal_links_plan" in content_plan
    assert "featured_project_links" in content_plan["internal_links_plan"]

    section_ids = {section["id"] for section in content_plan["section_plan"]}
    assert "review_and_rating_signals" in section_ids
    assert "demand_and_supply_signals" in section_ids
    assert "property_type_rate_snapshot" in section_ids

    table_ids = {table["id"] for table in content_plan["table_plan"]}
    assert "property_types_table" in table_ids
    assert "location_rates_table" in table_ids
    assert "property_status_table" in table_ids

    assert "section_generation_context" in content_plan
    assert "price_trends_and_rates" in content_plan["section_generation_context"]
    assert len(content_plan["faq_plan"]["faq_intents"]) > 0