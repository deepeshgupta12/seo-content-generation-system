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

    def get_keywords_for_site(self, target, location_name, language_name, limit):
        if target == "housing.com":
            return {
                "tasks": [
                    {
                        "result": [
                            {
                                "items": [
                                    {
                                        "keyword": "best flats for sale in andheri west mumbai",
                                        "keyword_info": {
                                            "search_volume": 70,
                                            "competition": 0.44,
                                            "competition_level": "MEDIUM",
                                            "cpc": 0.35,
                                        },
                                        "keyword_properties": {
                                            "core_keyword": None,
                                            "detected_language": "en",
                                            "words_count": 8,
                                        },
                                        "search_intent_info": {
                                            "main_intent": "informational",
                                            "foreign_intent": [],
                                        },
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        return {"tasks": [{"result": [{"items": []}]}]}

    def get_keyword_overview(self, keywords, location_name, language_name):
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
                        "search_intent_info": {
                            "main_intent": "informational",
                            "foreign_intent": [],
                        },
                    }
                )
        return {"tasks": [{"result": [{"items": items}]}]}

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

    def get_google_ads_search_volume(self, keywords, location_name, language_name):
        items = []
        for keyword in keywords:
            if keyword == "best flats for sale in andheri west mumbai":
                items.append(
                    {
                        "keyword": keyword,
                        "search_volume": 55,
                        "competition": 0.41,
                        "cpc": 0.31,
                        "monthly_searches": [{"year": 2025, "month": 12, "search_volume": 55}],
                    }
                )
        return {"tasks": [{"result": [{"items": items}]}]}

    def get_serp_organic_advanced(self, keyword, location_name, language_name, depth):
        if "flats for sale" in keyword.lower():
            return {
                "tasks": [
                    {
                        "result": [
                            {
                                "items": [
                                    {"type": "organic", "domain": "housing.com", "url": "https://housing.com"},
                                    {"type": "organic", "domain": "99acres.com", "url": "https://99acres.com"},
                                    {"type": "organic", "domain": "squareyards.com", "url": "https://squareyards.com"},
                                ]
                            }
                        ]
                    }
                ]
            }
        return {"tasks": [{"result": [{"items": []}]}]}

def test_keyword_intelligence_filters_and_clusters() -> None:
    from seo_content_engine.core.config import settings

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

    original_serp_seed_limit = settings.dataforseo_serp_seed_limit
    settings.dataforseo_serp_seed_limit = 10

    try:
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

        assert output["version"] == "v1.2"
        assert primary_keyword is not None
        assert primary_keyword["keyword"] == "flats for sale in andheri west mumbai"

        included_keyword_values = {item["keyword"] for item in included_keywords}
        excluded_keyword_values = {item["keyword"] for item in excluded_keywords}

        assert "flats for sale in andheri west mumbai" in included_keyword_values
        assert "2 bhk flats for sale in andheri west mumbai" in included_keyword_values
        assert "property prices in andheri west mumbai" in included_keyword_values
        assert "best flats for sale in andheri west mumbai" in included_keyword_values
        assert "flats in andheri for rent" in excluded_keyword_values
        assert "1 bhk flat in mumbai" in excluded_keyword_values

        competitor_domains = output["raw_retrieval"]["competitor_keywords"]["competitor_domains"]
        assert "housing.com" in competitor_domains

        competitor_keywords = output["keyword_clusters"]["competitor_keywords"]
        informational_keywords = output["keyword_clusters"]["informational_keywords"]
        serp_validated_keywords = output["keyword_clusters"]["serp_validated_keywords"]

        assert len(competitor_keywords) > 0
        assert len(informational_keywords) > 0
        assert len(serp_validated_keywords) > 0

        assert output["keyword_overview_enrichment"]["applied"] is True
        assert output["google_ads_enrichment"]["applied"] is True
        assert output["historical_enrichment"]["applied"] is True
    finally:
        settings.dataforseo_serp_seed_limit = original_serp_seed_limit