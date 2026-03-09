from copy import deepcopy

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
                        "validation": {
                            "passed": True,
                            "issues": [],
                            "sanitized_text": "Andheri West has 2,039 resale listings visible on Square Yards.",
                        },
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


def test_review_workbench_service_update_section_body(monkeypatch) -> None:
    from seo_content_engine.services import review_workbench_service as module

    base_session = {
        "session_id": "review-test-123",
        "entity": {"entity_name": "Andheri West", "city_name": "Mumbai"},
        "normalized": {"entity": {"entity_name": "Andheri West", "city_name": "Mumbai"}},
        "keyword_intelligence": {"version": "v1.1", "keyword_clusters": {}},
        "draft": DummyDraftGenerationService.generate(
            normalized={"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
            keyword_intelligence={"version": "v1.1"},
        ),
        "validation_report": {},
        "quality_report": {},
        "section_review": [],
        "version_history": [
            {
                "version_id": "v-initial",
                "version_number": 1,
                "action_type": "initial_generate",
                "draft_snapshot": DummyDraftGenerationService.generate(
                    normalized={"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
                    keyword_intelligence={"version": "v1.1"},
                ),
            }
        ],
        "latest_version_id": "v-initial",
    }

    monkeypatch.setattr(module.ReviewSessionStore, "load_session", lambda session_id: deepcopy(base_session))
    monkeypatch.setattr(module.ReviewSessionStore, "save_session", lambda session_payload: "/tmp/review-session.json")

    updated_session, mutation_summary = ReviewWorkbenchService.update_section_body(
        session_id="review-test-123",
        section_id="hero_intro",
        body="Updated grounded section body.",
        persist_session=True,
        action_label="section_edit",
    )

    assert updated_session["draft"]["sections"][0]["body"] == "Updated grounded section body."
    assert mutation_summary["action_type"] == "section_edit"
    assert mutation_summary["section_id"] == "hero_intro"
    assert len(updated_session["version_history"]) == 2


def test_review_workbench_service_update_metadata(monkeypatch) -> None:
    from seo_content_engine.services import review_workbench_service as module

    base_session = {
        "session_id": "review-test-123",
        "entity": {"entity_name": "Andheri West", "city_name": "Mumbai"},
        "normalized": {"entity": {"entity_name": "Andheri West", "city_name": "Mumbai"}},
        "keyword_intelligence": {"version": "v1.1", "keyword_clusters": {}},
        "draft": DummyDraftGenerationService.generate(
            normalized={"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
            keyword_intelligence={"version": "v1.1"},
        ),
        "validation_report": {},
        "quality_report": {},
        "section_review": [],
        "version_history": [
            {
                "version_id": "v-initial",
                "version_number": 1,
                "action_type": "initial_generate",
                "draft_snapshot": DummyDraftGenerationService.generate(
                    normalized={"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
                    keyword_intelligence={"version": "v1.1"},
                ),
            }
        ],
        "latest_version_id": "v-initial",
    }

    monkeypatch.setattr(module.ReviewSessionStore, "load_session", lambda session_id: deepcopy(base_session))
    monkeypatch.setattr(module.ReviewSessionStore, "save_session", lambda session_payload: "/tmp/review-session.json")

    updated_session, mutation_summary = ReviewWorkbenchService.update_metadata(
        session_id="review-test-123",
        title="Updated Title",
        meta_description="Updated Description",
        h1="Updated H1",
        intro_snippet="Updated intro snippet",
        persist_session=True,
        action_label="metadata_edit",
    )

    assert updated_session["draft"]["metadata"]["title"] == "Updated Title"
    assert updated_session["draft"]["metadata"]["meta_description"] == "Updated Description"
    assert mutation_summary["action_type"] == "metadata_edit"
    assert len(updated_session["version_history"]) == 2


def test_review_workbench_service_regenerate_draft(monkeypatch) -> None:
    from seo_content_engine.services import review_workbench_service as module

    base_session = {
        "session_id": "review-test-123",
        "entity": {"entity_name": "Andheri West", "city_name": "Mumbai"},
        "normalized": {"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
        "keyword_intelligence": {"version": "v1.1", "keyword_clusters": {}},
        "draft": DummyDraftGenerationService.generate(
            normalized={"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
            keyword_intelligence={"version": "v1.1"},
        ),
        "validation_report": {},
        "quality_report": {},
        "section_review": [],
        "version_history": [
            {
                "version_id": "v-initial",
                "version_number": 1,
                "action_type": "initial_generate",
                "draft_snapshot": DummyDraftGenerationService.generate(
                    normalized={"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
                    keyword_intelligence={"version": "v1.1"},
                ),
            }
        ],
        "latest_version_id": "v-initial",
    }

    class RegeneratedDraftService(DummyDraftGenerationService):
        @staticmethod
        def generate(normalized, keyword_intelligence):
            draft = DummyDraftGenerationService.generate(normalized, keyword_intelligence)
            draft["metadata"]["title"] = "Regenerated Title"
            return draft

    monkeypatch.setattr(module.ReviewSessionStore, "load_session", lambda session_id: deepcopy(base_session))
    monkeypatch.setattr(module.ReviewSessionStore, "save_session", lambda session_payload: "/tmp/review-session.json")
    monkeypatch.setattr(module, "DraftGenerationService", RegeneratedDraftService)

    updated_session, mutation_summary = ReviewWorkbenchService.regenerate_draft(
        session_id="review-test-123",
        persist_session=True,
        action_label="full_regenerate",
    )

    assert updated_session["draft"]["metadata"]["title"] == "Regenerated Title"
    assert mutation_summary["action_type"] == "full_regenerate"
    assert len(updated_session["version_history"]) == 2


def test_review_workbench_service_restore_version(monkeypatch) -> None:
    from seo_content_engine.services import review_workbench_service as module

    initial_draft = DummyDraftGenerationService.generate(
        normalized={"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
        keyword_intelligence={"version": "v1.1"},
    )
    modified_draft = deepcopy(initial_draft)
    modified_draft["metadata"]["title"] = "Modified Title"

    base_session = {
        "session_id": "review-test-123",
        "entity": {"entity_name": "Andheri West", "city_name": "Mumbai"},
        "normalized": {"entity": {"entity_name": "Andheri West", "city_name": "Mumbai", "page_type": "resale_locality", "listing_type": "resale"}},
        "keyword_intelligence": {"version": "v1.1", "keyword_clusters": {}},
        "draft": modified_draft,
        "validation_report": {},
        "quality_report": {},
        "section_review": [],
        "version_history": [
            {
                "version_id": "v-initial",
                "version_number": 1,
                "action_type": "initial_generate",
                "draft_snapshot": initial_draft,
            },
            {
                "version_id": "v-second",
                "version_number": 2,
                "action_type": "metadata_edit",
                "draft_snapshot": modified_draft,
            },
        ],
        "latest_version_id": "v-second",
    }

    monkeypatch.setattr(module.ReviewSessionStore, "load_session", lambda session_id: deepcopy(base_session))
    monkeypatch.setattr(module.ReviewSessionStore, "save_session", lambda session_payload: "/tmp/review-session.json")

    updated_session, mutation_summary = ReviewWorkbenchService.restore_version(
        session_id="review-test-123",
        version_id="v-initial",
        persist_session=True,
        action_label="restore_version",
    )

    assert updated_session["draft"]["metadata"]["title"] == "Resale Properties in Andheri West, Mumbai | Square Yards"
    assert mutation_summary["action_type"] == "restore_version"
    assert mutation_summary["restored_from_version_id"] == "v-initial"
    assert len(updated_session["version_history"]) == 3