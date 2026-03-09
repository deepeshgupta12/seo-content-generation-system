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
            "micromarket_rates": [{"name": "Mumbai Western Suburbs", "avgRate": 21180, "changePercentage": 1.25}],
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
            "faq_keyword_candidates": [
                {"keyword": "property prices in andheri west mumbai"},
                {"keyword": "resale flats in andheri west mumbai"},
                {"keyword": "2 bhk resale in andheri west mumbai"},
            ],
            "metadata_keywords": [
                "flats for sale in andheri west mumbai",
                "apartments for sale in andheri west mumbai",
            ],
            "exact_match_keywords": [{"keyword": "flats for sale in andheri west mumbai"}],
            "loose_match_keywords": [{"keyword": "andheri west resale property"}],
        },
    }

    content_plan = ContentPlanBuilder.build(normalized=normalized, keyword_intelligence=keyword_intelligence)

    assert content_plan["version"] == "v1.7"
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
    assert "nearby_alternatives" in section_ids

    table_ids = {table["id"] for table in content_plan["table_plan"]}
    assert "property_types_table" in table_ids
    assert "location_rates_table" in table_ids
    assert "property_status_table" in table_ids

    assert "section_generation_context" in content_plan
    assert "price_trends_and_rates" in content_plan["section_generation_context"]
    assert "review_and_rating_signals" in content_plan["section_generation_context"]
    assert len(content_plan["faq_plan"]["faq_intents"]) >= 5

    faq_ids = {item["id"] for item in content_plan["faq_plan"]["faq_intents"]}
    assert "pricing" in faq_ids
    assert "inventory" in faq_ids
    assert "bhk_availability" in faq_ids
    assert "ready_to_move" in faq_ids
    assert "nearby_localities" in faq_ids


def test_content_plan_builder_for_micromarket_adds_parity_sections_and_tables() -> None:
    normalized = {
        "entity": {
            "entity_type": "micromarket",
            "page_type": "resale_micromarket",
            "listing_type": "resale",
            "entity_name": "Noida Extension",
            "city_name": "Greater Noida",
            "micromarket_name": "Noida Extension",
        },
        "listing_summary": {
            "sale_count": 1420,
            "total_listings": 4200,
            "total_projects": 310,
            "sale_available": 1420,
        },
        "pricing_summary": {
            "asking_price": 8450,
            "registration_rate": 6200,
            "price_trend": [{"quarterName": "Dec 2025", "micromarketRate": 8450, "cityRate": 7900}],
            "location_rates": [{"name": "Sector 1", "avgRate": 8125, "changePercentage": 3.2}],
            "property_types": [{"propertyType": "apartment", "avgPrice": 8450, "changePercent": 5.1}],
            "property_status": [{"status": "Ready To Move", "units": 180, "avgPrice": 9025}],
            "micromarket_rates": [{"name": "Noida Extension", "avgRate": 8450, "changePercentage": 2.4}],
        },
        "distributions": {
            "sale_unit_type_distribution": [{"key": "2 BHK", "doc_count": 540}],
            "sale_property_type_distribution": [{"key": "Apartment", "doc_count": 900}],
        },
        "nearby_localities": [
            {
                "name": "Gaur City 2",
                "distance_km": 1.2,
                "sale_count": 220,
                "sale_avg_price_per_sqft": 7800,
                "url": "gaur-city-2-greater-noida",
            }
        ],
        "links": {
            "sale_unit_type_urls": [],
            "sale_property_type_urls": [],
            "sale_quick_links": [{"label": "Flats in Noida Extension", "url": "sale/property-for-sale-in-noida-extension-greater-noida"}],
        },
        "top_projects": {"byTransactions": {"projects": []}},
        "review_summary": {"overview": {"avg_rating": 4.0, "review_count": 40, "rating_count": 40}},
        "ai_summary": {"locality_summary": "Large residential belt with active resale inventory."},
        "insight_rates": {"name": "Noida Extension", "avg_rate": 8450},
        "demand_supply": {"sale": {"unitType": [{"name": "2 BHK", "listing": 540, "demandPercent": 34, "supplyPercent": 36}]}},
        "listing_ranges": {"sale_listing_range": {"doc_count": 1200, "min_price": 2500000, "max_price": 22000000}},
        "cms_faq": [],
        "featured_projects": [],
        "projects_by_status": {},
        "raw_source_meta": {
            "main_message": "micromarket Found",
            "rates_message": "Property Rates Data Found",
            "last_modified_date": "2026-03-02",
        },
    }

    keyword_intelligence = {
        "version": "v1.1",
        "keyword_clusters": {
            "primary_keyword": {"keyword": "resale properties in noida extension greater noida", "score": 88},
            "secondary_keywords": [{"keyword": "apartments for sale in noida extension greater noida"}],
            "bhk_keywords": [{"keyword": "2 bhk flats in noida extension"}],
            "price_keywords": [{"keyword": "property prices in noida extension greater noida"}],
            "ready_to_move_keywords": [{"keyword": "ready to move flats in noida extension"}],
            "faq_keyword_candidates": [{"keyword": "resale flats in noida extension"}],
            "metadata_keywords": ["resale properties in noida extension greater noida"],
            "exact_match_keywords": [{"keyword": "resale properties in noida extension greater noida"}],
            "loose_match_keywords": [],
        },
    }

    content_plan = ContentPlanBuilder.build(normalized=normalized, keyword_intelligence=keyword_intelligence)

    assert content_plan["version"] == "v1.7"
    assert content_plan["page_type"] == "resale_micromarket"

    section_ids = {section["id"] for section in content_plan["section_plan"]}
    assert "locality_coverage" in section_ids
    assert "review_and_rating_signals" in section_ids
    assert "demand_and_supply_signals" in section_ids
    assert "property_type_signals" in section_ids

    table_ids = {table["id"] for table in content_plan["table_plan"]}
    assert "coverage_summary_table" in table_ids
    assert "price_trend_table" in table_ids

    assert len(content_plan["faq_plan"]["faq_intents"]) >= 5


def test_content_plan_builder_for_city_adds_city_parity_sections_and_tables() -> None:
    normalized = {
        "entity": {
            "entity_type": "city",
            "page_type": "resale_city",
            "listing_type": "resale",
            "entity_name": "Pune",
            "city_name": "Pune",
            "micromarket_name": "",
        },
        "listing_summary": {
            "sale_count": 8200,
            "total_listings": 18200,
            "total_projects": 2100,
            "sale_available": 8200,
        },
        "pricing_summary": {
            "asking_price": 11250,
            "registration_rate": 9600,
            "price_trend": [{"quarterName": "Dec 2025", "cityRate": 11250}],
            "location_rates": [{"name": "Wakad", "avgRate": 11890, "changePercentage": 4.8}],
            "property_types": [{"propertyType": "apartment", "avgPrice": 11250, "changePercent": 3.6}],
            "property_status": [{"status": "Ready To Move", "units": 1200, "avgPrice": 12440}],
            "micromarket_rates": [{"name": "Hinjewadi Belt", "avgRate": 10980, "changePercentage": 2.2}],
        },
        "distributions": {
            "sale_unit_type_distribution": [{"key": "2 BHK", "doc_count": 2200}],
            "sale_property_type_distribution": [{"key": "Apartment", "doc_count": 6400}],
        },
        "nearby_localities": [
            {
                "name": "Wakad",
                "distance_km": 0.0,
                "sale_count": 620,
                "sale_avg_price_per_sqft": 11890,
                "url": "wakad-pune",
            }
        ],
        "links": {
            "sale_unit_type_urls": [],
            "sale_property_type_urls": [],
            "sale_quick_links": [{"label": "Flats for sale in Pune", "url": "sale/property-for-sale-in-pune"}],
        },
        "top_projects": {"byTransactions": {"projects": []}},
        "review_summary": {"overview": {"avg_rating": 4.1, "review_count": 120, "rating_count": 120}},
        "ai_summary": {"locality_summary": "City-level resale coverage across multiple residential belts."},
        "insight_rates": {"name": "Pune", "avg_rate": 11250},
        "demand_supply": {"sale": {"unitType": [{"name": "2 BHK", "listing": 2200, "demandPercent": 38, "supplyPercent": 35}]}},
        "listing_ranges": {"sale_listing_range": {"doc_count": 7900, "min_price": 1800000, "max_price": 65000000}},
        "cms_faq": [],
        "featured_projects": [],
        "projects_by_status": {},
        "raw_source_meta": {
            "main_message": "city Found",
            "rates_message": "Property Rates Data Found",
            "last_modified_date": "2026-03-02",
        },
    }

    keyword_intelligence = {
        "version": "v1.1",
        "keyword_clusters": {
            "primary_keyword": {"keyword": "resale properties in pune", "score": 91},
            "secondary_keywords": [{"keyword": "apartments for sale in pune"}],
            "bhk_keywords": [{"keyword": "2 bhk flats in pune"}],
            "price_keywords": [{"keyword": "property prices in pune"}],
            "ready_to_move_keywords": [{"keyword": "ready to move flats in pune"}],
            "faq_keyword_candidates": [{"keyword": "resale property market in pune"}],
            "metadata_keywords": ["resale properties in pune"],
            "exact_match_keywords": [{"keyword": "resale properties in pune"}],
            "loose_match_keywords": [],
        },
    }

    content_plan = ContentPlanBuilder.build(normalized=normalized, keyword_intelligence=keyword_intelligence)

    assert content_plan["version"] == "v1.7"
    assert content_plan["page_type"] == "resale_city"

    section_ids = {section["id"] for section in content_plan["section_plan"]}
    assert "micromarket_coverage" in section_ids
    assert "review_and_rating_signals" in section_ids
    assert "demand_and_supply_signals" in section_ids
    assert "property_type_rate_snapshot" in section_ids

    table_ids = {table["id"] for table in content_plan["table_plan"]}
    assert "coverage_summary_table" in table_ids
    assert "location_rates_table" in table_ids

    assert len(content_plan["faq_plan"]["faq_intents"]) >= 5