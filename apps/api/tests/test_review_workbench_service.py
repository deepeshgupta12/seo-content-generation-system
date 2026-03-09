from seo_content_engine.domain.enums import ListingType
from seo_content_engine.services.review_workbench_service import ReviewWorkbenchService


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
                "primary_keyword": {"keyword": "flats for sale in andheri west mumbai", "score": 92},
                "secondary_keywords": [{"keyword": "apartments for sale in andheri west mumbai"}],
                "bhk_keywords": [{"keyword": "2 bhk flats for sale in andheri west mumbai"}],
                "price_keywords": [{"keyword": "property prices in andheri west mumbai"}],
                "ready_to_move_keywords": [{"keyword": "ready possession flats in andheri west"}],
                "faq_keyword_candidates": [{"keyword": "property prices in andheri west mumbai"}],
                "metadata_keywords": ["flats for sale in andheri west mumbai"],
                "exact_match_keywords": [{"keyword": "flats for sale in andheri west mumbai"}],
                "loose_match_keywords": [],
            },
        }


class DummyContentPlanBuilder:
    @staticmethod
    def build(normalized, keyword_intelligence):
        return {
            "version": "v1.6",
            "page_type": normalized["entity"]["page_type"],
            "listing_type": normalized["entity"]["listing_type"],
            "entity": normalized["entity"],
            "metadata_plan": {
                "canonical_pricing_metric": {
                    "metric_name": "asking_price",
                    "label": "asking price",
                    "value": 40238,
                }
            },
            "keyword_strategy": keyword_intelligence["keyword_clusters"],
            "section_plan": [],
            "data_context": {
                "pricing_summary": normalized["pricing_summary"],
                "listing_summary": normalized["listing_summary"],
            },
            "source_meta": {
                "raw_source_meta": normalized["raw_source_meta"],
            },
        }


class DummyDraftGenerationService:
    @staticmethod
    def generate(normalized, keyword_intelligence):
        return {
            "version": "v2.4",
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
                    "body": "Andheri West has 2,039 resale listings visible on Square Yards.",
                    "validation_passed": True,
                    "validation_issues": [],
                }
            ],
            "tables": [],
            "faqs": [],
            "internal_links": {},
            "content_plan": {
                "metadata_plan": {
                    "canonical_pricing_metric": {
                        "metric_name": "asking_price",
                        "label": "asking price",
                        "value": 40238,
                    }
                }
            },
            "keyword_intelligence_version": "v1.1",
            "validation_report": {
                "passed": True,
                "metadata_checks": {},
                "section_checks": [
                    {
                        "id": "hero_intro",
                        "title": "Resale Property Overview in Andheri West, Mumbai",
                        "validation": {"passed": True, "issues": [], "sanitized_text": "Andheri West has 2,039 resale listings visible on Square Yards."},
                    }
                ],
                "faq_checks": [],
            },
            "quality_report": {
                "approval_status": "pass",
                "overall_quality_score": 96,
                "warning_reasons": [],
                "section_quality_scores": [
                    {
                        "id": "hero_intro",
                        "title": "Resale Property Overview in Andheri West, Mumbai",
                        "score": 96,
                        "confidence": "high",
                        "warnings": [],
                        "word_count": 9,
                    }
                ],
            },
            "debug_summary": {
                "blocked": False,
                "approval_status": "pass",
                "blocking_reasons": [],
            },
            "publish_ready": True,
            "markdown_draft": "# Resale Properties in Andheri West, Mumbai\n",
        }


class DummySourceLoader:
    @staticmethod
    def load_json(path: str):
        if "rates" in path:
            return {
                "message": "ok",
                "data": {
                    "type": "locality",
                    "propertyRatesData": {
                        "details": {
                            "name": "Andheri West",
                            "cityName": "Mumbai",
                        },
                        "marketOverview": {
                            "askingPrice": 40238,
                        },
                        "priceTrend": [],
                        "locationRates": [],
                        "propertyTypes": [],
                        "propertyStatus": [],
                        "topProjects": {},
                    },
                },
            }

        return {
            "message": "ok",
            "data": {
                "lastModifiedDate": "2026-03-09",
                "localityOverviewData": {
                    "name": "Andheri West",
                    "cityName": "Mumbai",
                    "saleCount": 2039,
                    "totallistings": 6109,
                    "totalprojects": 1762,
                    "sale": {"available": 2039},
                    "rent": {"available": 0},
                    "metrics": {"sale": {}, "rent": {}},
                },
                "localityData": {
                    "subLocalityName": "Andheri West",
                    "cityName": "Mumbai",
                },
                "saleListingFooter": {},
                "nearByLocalities": [],
                "ratingReview": {},
                "localityAiData": {},
                "demandSupply": {},
                "listingCountData": [],
                "insightRates": {},
                "cmsFAQ": [],
                "featuredProjects": [],
                "projectsByStatus": {},
            },
        }


def test_review_workbench_service_build_session(monkeypatch) -> None:
    from seo_content_engine.services import review_workbench_service as module

    monkeypatch.setattr(module, "KeywordIntelligenceService", DummyKeywordService)
    monkeypatch.setattr(module, "ContentPlanBuilder", DummyContentPlanBuilder)
    monkeypatch.setattr(module, "DraftGenerationService", DummyDraftGenerationService)
    monkeypatch.setattr(module, "SourceLoader", DummySourceLoader)

    session = ReviewWorkbenchService.build_session(
        main_datacenter_json_path="main.json",
        property_rates_json_path="rates.json",
        listing_type=ListingType.RESALE,
        persist_session=False,
    )

    assert session["entity"]["entity_name"] == "Andheri West"
    assert session["draft"]["quality_report"]["approval_status"] == "pass"
    assert session["keyword_preview"]["primary_keyword"]["keyword"] == "flats for sale in andheri west mumbai"
    assert len(session["section_review"]) == 1
    assert len(session["version_history"]) == 1