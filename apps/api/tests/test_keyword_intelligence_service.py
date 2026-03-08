from seo_content_engine.services.keyword_intelligence_service import KeywordIntelligenceService


class DummyClient:
    def get_keyword_suggestions(self, keyword, location_name, language_name, limit):
        if "flats for sale" in keyword.lower():
            return {
                "tasks": [
                    {
                        "result": [
                            {
                                "items": [
                                    {
                                        "keyword": "flats for sale in andheri west mumbai",
                                        "keyword_info": {
                                            "search_volume": 390,
                                            "competition": 0.59,
                                            "competition_level": "MEDIUM",
                                            "cpc": 0.68,
                                            "monthly_searches": [{"year": 2025, "month": 12, "search_volume": 390}],
                                            "search_volume_trend": {"monthly": 23, "quarterly": 23, "yearly": 23},
                                        },
                                        "keyword_properties": {
                                            "core_keyword": None,
                                            "keyword_difficulty": 0,
                                            "detected_language": "en",
                                            "words_count": 7,
                                        },
                                        "search_intent_info": {
                                            "main_intent": "commercial",
                                            "foreign_intent": ["transactional"],
                                        },
                                    },
                                    {
                                        "keyword": "2 bhk flats for sale in andheri west mumbai",
                                        "keyword_info": {
                                            "search_volume": 110,
                                            "competition": 0.62,
                                            "competition_level": "MEDIUM",
                                            "cpc": 0.58,
                                            "monthly_searches": [{"year": 2025, "month": 12, "search_volume": 110}],
                                            "search_volume_trend": {"monthly": 0, "quarterly": 22, "yearly": 22},
                                        },
                                        "keyword_properties": {
                                            "core_keyword": "2 bhk flat for sale in andheri west mumbai",
                                            "keyword_difficulty": None,
                                            "detected_language": "en",
                                            "words_count": 9,
                                        },
                                        "search_intent_info": {
                                            "main_intent": "transactional",
                                            "foreign_intent": ["commercial"],
                                        },
                                    },
                                ]
                            }
                        ]
                    }
                ]
            }
        return {"tasks": [{"result": [{"items": []}]}]}

    def get_related_keywords(self, keyword, location_name, language_name, limit, depth):
        if "flats for sale" in keyword.lower():
            return {
                "tasks": [
                    {
                        "result": [
                            {
                                "items": [
                                    {"keyword": "flats in andheri for rent"},
                                    {"keyword": "1 bhk flat in mumbai"},
                                    {"keyword": "property prices in andheri west mumbai"},
                                ]
                            }
                        ]
                    }
                ]
            }
        return {"tasks": [{"result": [{"items": []}]}]}

    def get_historical_search_volume(self, keywords, location_name, language_name):
        items = []
        for keyword in keywords:
            if keyword == "property prices in andheri west mumbai":
                items.append(
                    {
                        "keyword": keyword,
                        "keyword_info": {
                            "search_volume": 30,
                            "competition": 0.2,
                            "competition_level": "LOW",
                            "cpc": 0.25,
                            "monthly_searches": [{"year": 2025, "month": 12, "search_volume": 30}],
                            "search_volume_trend": {"monthly": 0, "quarterly": 0, "yearly": 0},
                        },
                    }
                )
        return {"tasks": [{"result": [{"items": items}]}]}


def test_keyword_intelligence_filters_and_clusters() -> None:
    normalized = {
        "entity": {
            "entity_type": "locality",
            "page_type": "resale_locality",
            "listing_type": "resale",
            "entity_name": "Andheri West",
            "city_name": "Mumbai",
            "micromarket_name": "Mumbai Western Suburbs",
        }
    }

    output = KeywordIntelligenceService.build_keyword_intelligence(
        normalized=normalized,
        location_name="India",
        language_name="English",
        limit=20,
        include_historical=True,
        client=DummyClient(),
    )

    included_keywords = output["normalized_keywords"]["included_keywords"]
    excluded_keywords = output["normalized_keywords"]["excluded_keywords"]
    primary_keyword = output["keyword_clusters"]["primary_keyword"]

    assert primary_keyword is not None
    assert primary_keyword["keyword"] == "flats for sale in andheri west mumbai"

    included_keyword_values = {item["keyword"] for item in included_keywords}
    excluded_keyword_values = {item["keyword"] for item in excluded_keywords}

    assert "flats for sale in andheri west mumbai" in included_keyword_values
    assert "2 bhk flats for sale in andheri west mumbai" in included_keyword_values
    assert "property prices in andheri west mumbai" in included_keyword_values
    assert "flats in andheri for rent" in excluded_keyword_values
    assert "1 bhk flat in mumbai" in excluded_keyword_values