from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from seo_content_engine.services.content_plan_builder import ContentPlanBuilder
from seo_content_engine.services.draft_generation_service import DraftGenerationService
from seo_content_engine.services.keyword_intelligence_service import KeywordIntelligenceService
from seo_content_engine.services.normalizer import EntityNormalizer
from seo_content_engine.services.review_session_store import ReviewSessionStore
from seo_content_engine.services.source_loader import SourceLoader


class ReviewWorkbenchService:
    @staticmethod
    def _build_source_preview(normalized: dict) -> dict:
        entity = normalized.get("entity", {})
        return {
            "entity": entity,
            "listing_summary": normalized.get("listing_summary", {}),
            "pricing_summary": normalized.get("pricing_summary", {}),
            "distributions": normalized.get("distributions", {}),
            "nearby_localities": normalized.get("nearby_localities", []),
            "review_summary": normalized.get("review_summary", {}),
            "ai_summary": normalized.get("ai_summary", {}),
            "demand_supply": normalized.get("demand_supply", {}),
            "listing_ranges": normalized.get("listing_ranges", {}),
            "featured_projects": normalized.get("featured_projects", []),
            "projects_by_status": normalized.get("projects_by_status", {}),
            "raw_source_meta": normalized.get("raw_source_meta", {}),
        }

    @staticmethod
    def _build_keyword_preview(keyword_intelligence: dict) -> dict:
        clusters = keyword_intelligence.get("keyword_clusters", {})
        return {
            "version": keyword_intelligence.get("version"),
            "primary_keyword": clusters.get("primary_keyword"),
            "secondary_keywords": clusters.get("secondary_keywords", []),
            "bhk_keywords": clusters.get("bhk_keywords", []),
            "price_keywords": clusters.get("price_keywords", []),
            "ready_to_move_keywords": clusters.get("ready_to_move_keywords", []),
            "faq_keyword_candidates": clusters.get("faq_keyword_candidates", []),
            "metadata_keywords": clusters.get("metadata_keywords", []),
            "exact_match_keywords": clusters.get("exact_match_keywords", []),
            "loose_match_keywords": clusters.get("loose_match_keywords", []),
        }

    @staticmethod
    def _build_section_review_payload(draft: dict) -> list[dict]:
        validation_report = draft.get("validation_report", {})
        section_checks = {
            item.get("id"): item.get("validation", {})
            for item in validation_report.get("section_checks", [])
        }
        section_quality_scores = {
            item.get("id"): item
            for item in draft.get("quality_report", {}).get("section_quality_scores", [])
        }

        section_review_items: list[dict] = []
        for section in draft.get("sections", []):
            section_id = section.get("id")
            section_review_items.append(
                {
                    "id": section_id,
                    "title": section.get("title"),
                    "body": section.get("body"),
                    "validation": section_checks.get(section_id, {}),
                    "quality": section_quality_scores.get(section_id, {}),
                    "validation_passed": section.get("validation_passed"),
                    "validation_issues": section.get("validation_issues", []),
                }
            )

        return section_review_items

    @staticmethod
    def _build_version_entry(draft: dict) -> dict:
        return {
            "version_id": f"v-{uuid4().hex[:12]}",
            "version_number": 1,
            "action_type": "initial_generate",
            "created_at": datetime.now(UTC).isoformat(),
            "publish_ready": draft.get("publish_ready", False),
            "approval_status": draft.get("quality_report", {}).get("approval_status"),
            "overall_quality_score": draft.get("quality_report", {}).get("overall_quality_score"),
            "summary": {
                "page_type": draft.get("page_type"),
                "entity_name": draft.get("entity", {}).get("entity_name"),
                "warning_reasons": draft.get("quality_report", {}).get("warning_reasons", []),
                "blocking_reasons": draft.get("debug_summary", {}).get("blocking_reasons", []),
            },
            "draft_snapshot": draft,
        }

    @staticmethod
    def build_session(
        *,
        main_datacenter_json_path: str,
        property_rates_json_path: str,
        listing_type,
        location_name: str | None = None,
        language_name: str | None = None,
        limit: int | None = None,
        include_historical: bool = True,
        persist_session: bool = True,
    ) -> dict:
        normalized = EntityNormalizer.normalize_from_paths(
            main_datacenter_json_path=main_datacenter_json_path,
            property_rates_json_path=property_rates_json_path,
            listing_type=listing_type,
            source_loader=SourceLoader,
        )

        keyword_intelligence = KeywordIntelligenceService.build_keyword_intelligence(
            normalized=normalized,
            location_name=location_name,
            language_name=language_name,
            limit=limit,
            include_historical=include_historical,
        )

        content_plan = ContentPlanBuilder.build(
            normalized=normalized,
            keyword_intelligence=keyword_intelligence,
        )

        draft = DraftGenerationService.generate(
            normalized=normalized,
            keyword_intelligence=keyword_intelligence,
        )

        session_id = f"review-{uuid4().hex}"
        version_entry = ReviewWorkbenchService._build_version_entry(draft)

        review_session = {
            "session_id": session_id,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "inputs": {
                "main_datacenter_json_path": main_datacenter_json_path,
                "property_rates_json_path": property_rates_json_path,
                "listing_type": getattr(listing_type, "value", str(listing_type)),
                "location_name": location_name,
                "language_name": language_name,
                "limit": limit,
                "include_historical": include_historical,
            },
            "entity": normalized.get("entity", {}),
            "source_preview": ReviewWorkbenchService._build_source_preview(normalized),
            "keyword_preview": ReviewWorkbenchService._build_keyword_preview(keyword_intelligence),
            "normalized": normalized,
            "keyword_intelligence": keyword_intelligence,
            "content_plan": content_plan,
            "draft": draft,
            "validation_report": draft.get("validation_report", {}),
            "quality_report": draft.get("quality_report", {}),
            "section_review": ReviewWorkbenchService._build_section_review_payload(draft),
            "version_history": [version_entry],
            "latest_version_id": version_entry["version_id"],
        }

        if persist_session:
            ReviewSessionStore.save_session(review_session)

        return review_session

    @staticmethod
    def get_session(session_id: str) -> dict:
        return ReviewSessionStore.load_session(session_id)