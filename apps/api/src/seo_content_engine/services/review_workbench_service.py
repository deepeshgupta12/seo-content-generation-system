from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

from seo_content_engine.services.content_plan_builder import ContentPlanBuilder
from seo_content_engine.services.draft_generation_service import DraftGenerationService
from seo_content_engine.services.factual_validator import FactualValidator
from seo_content_engine.services.keyword_intelligence_service import KeywordIntelligenceService
from seo_content_engine.services.markdown_renderer import MarkdownRenderer
from seo_content_engine.services.normalizer import EntityNormalizer
from seo_content_engine.services.review_session_store import ReviewSessionStore
from seo_content_engine.services.source_loader import SourceLoader


class ReviewWorkbenchService:
    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat()

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
    def _build_version_entry(
        draft: dict,
        *,
        version_number: int,
        action_type: str,
    ) -> dict:
        return {
            "version_id": f"v-{uuid4().hex[:12]}",
            "version_number": version_number,
            "action_type": action_type,
            "created_at": ReviewWorkbenchService._now_iso(),
            "publish_ready": draft.get("publish_ready", False),
            "approval_status": draft.get("quality_report", {}).get("approval_status"),
            "overall_quality_score": draft.get("quality_report", {}).get("overall_quality_score"),
            "summary": {
                "page_type": draft.get("page_type"),
                "entity_name": draft.get("entity", {}).get("entity_name"),
                "warning_reasons": draft.get("quality_report", {}).get("warning_reasons", []),
                "blocking_reasons": draft.get("debug_summary", {}).get("blocking_reasons", []),
            },
            "draft_snapshot": deepcopy(draft),
        }

    @staticmethod
    def _next_version_number(session: dict) -> int:
        version_history = session.get("version_history", [])
        if not version_history:
            return 1
        return max(item.get("version_number", 0) for item in version_history) + 1

    @staticmethod
    def _mutation_summary(session: dict, *, action_type: str, extra: dict | None = None) -> dict:
        payload = {
            "action_type": action_type,
            "session_id": session["session_id"],
            "latest_version_id": session.get("latest_version_id"),
            "approval_status": session.get("quality_report", {}).get("approval_status"),
            "overall_quality_score": session.get("quality_report", {}).get("overall_quality_score"),
            "publish_ready": session.get("draft", {}).get("publish_ready", False),
        }
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def _recompute_mutated_draft(session: dict, draft: dict) -> dict:
        recomputed_draft = deepcopy(draft)

        refreshed_content_plan = ContentPlanBuilder.build(
            normalized=session["normalized"],
            keyword_intelligence=session["keyword_intelligence"],
        )
        recomputed_draft["content_plan"] = refreshed_content_plan

        validation_report = FactualValidator.validate_draft(recomputed_draft)
        debug_summary = FactualValidator.summarize_report(validation_report)

        sanitized = FactualValidator.apply_sanitization(recomputed_draft, validation_report)
        sanitized["debug_summary"] = debug_summary
        sanitized["quality_report"] = validation_report.get("quality_report", {})
        sanitized["publish_ready"] = sanitized["quality_report"].get("approval_status") != "fail"
        sanitized["markdown_draft"] = MarkdownRenderer.render(sanitized)

        validation_history = list(draft.get("validation_history", []))
        validation_history.append(
            {
                "pass_name": "mutation_recompute",
                "pass_index": len(validation_history),
                "passed": validation_report["passed"],
                "debug_summary": debug_summary,
                "validation_report": validation_report,
            }
        )

        sanitized["validation_history"] = validation_history
        sanitized["repair_passes_used"] = draft.get("repair_passes_used", 0)
        sanitized["pre_block_draft"] = deepcopy(recomputed_draft)
        return sanitized

    @staticmethod
    def _apply_draft_to_session(session: dict, draft: dict, *, action_type: str) -> dict:
        updated = deepcopy(session)
        updated["draft"] = draft
        updated["content_plan"] = draft.get("content_plan", updated.get("content_plan", {}))
        updated["validation_report"] = draft.get("validation_report", {})
        updated["quality_report"] = draft.get("quality_report", {})
        updated["section_review"] = ReviewWorkbenchService._build_section_review_payload(draft)
        updated["updated_at"] = ReviewWorkbenchService._now_iso()

        version_entry = ReviewWorkbenchService._build_version_entry(
            draft,
            version_number=ReviewWorkbenchService._next_version_number(updated),
            action_type=action_type,
        )
        updated.setdefault("version_history", []).append(version_entry)
        updated["latest_version_id"] = version_entry["version_id"]
        return updated

    @staticmethod
    def _persist_if_needed(session: dict, persist_session: bool) -> None:
        if persist_session:
            ReviewSessionStore.save_session(session)

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
        version_entry = ReviewWorkbenchService._build_version_entry(
            draft,
            version_number=1,
            action_type="initial_generate",
        )

        review_session = {
            "session_id": session_id,
            "created_at": ReviewWorkbenchService._now_iso(),
            "updated_at": ReviewWorkbenchService._now_iso(),
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

    @staticmethod
    def regenerate_draft(
        *,
        session_id: str,
        persist_session: bool = True,
        action_label: str = "full_regenerate",
    ) -> tuple[dict, dict]:
        session = ReviewSessionStore.load_session(session_id)
        regenerated_draft = DraftGenerationService.generate(
            normalized=session["normalized"],
            keyword_intelligence=session["keyword_intelligence"],
        )
        updated_session = ReviewWorkbenchService._apply_draft_to_session(
            session,
            regenerated_draft,
            action_type=action_label,
        )
        ReviewWorkbenchService._persist_if_needed(updated_session, persist_session)
        return updated_session, ReviewWorkbenchService._mutation_summary(
            updated_session,
            action_type=action_label,
        )

    @staticmethod
    def regenerate_section(
        *,
        session_id: str,
        section_id: str,
        persist_session: bool = True,
        action_label: str = "section_regenerate",
    ) -> tuple[dict, dict]:
        session = ReviewSessionStore.load_session(session_id)
        regenerated_draft = DraftGenerationService.generate(
            normalized=session["normalized"],
            keyword_intelligence=session["keyword_intelligence"],
        )

        existing_sections = {section.get("id"): section for section in session["draft"].get("sections", [])}
        regenerated_sections = {section.get("id"): section for section in regenerated_draft.get("sections", [])}

        if section_id not in existing_sections:
            raise ValueError(f"Section not found in current draft: {section_id}")
        if section_id not in regenerated_sections:
            raise ValueError(f"Section not found in regenerated draft: {section_id}")

        merged_draft = deepcopy(session["draft"])
        merged_sections = []
        for section in merged_draft.get("sections", []):
            if section.get("id") == section_id:
                merged_sections.append(regenerated_sections[section_id])
            else:
                merged_sections.append(section)
        merged_draft["sections"] = merged_sections

        merged_draft["tables"] = regenerated_draft.get("tables", merged_draft.get("tables", []))
        merged_draft["faqs"] = regenerated_draft.get("faqs", merged_draft.get("faqs", []))
        merged_draft["internal_links"] = regenerated_draft.get(
            "internal_links",
            merged_draft.get("internal_links", {}),
        )
        merged_draft["keyword_intelligence_version"] = regenerated_draft.get(
            "keyword_intelligence_version",
            merged_draft.get("keyword_intelligence_version"),
        )

        recomputed_draft = ReviewWorkbenchService._recompute_mutated_draft(session, merged_draft)

        updated_session = ReviewWorkbenchService._apply_draft_to_session(
            session,
            recomputed_draft,
            action_type=action_label,
        )
        ReviewWorkbenchService._persist_if_needed(updated_session, persist_session)
        return updated_session, ReviewWorkbenchService._mutation_summary(
            updated_session,
            action_type=action_label,
            extra={"section_id": section_id},
        )

    @staticmethod
    def update_section_body(
        *,
        session_id: str,
        section_id: str,
        body: str,
        persist_session: bool = True,
        action_label: str = "section_edit",
    ) -> tuple[dict, dict]:
        session = ReviewSessionStore.load_session(session_id)
        updated_draft = deepcopy(session["draft"])

        found = False
        for section in updated_draft.get("sections", []):
            if section.get("id") == section_id:
                section["body"] = body
                found = True
                break

        if not found:
            raise ValueError(f"Section not found: {section_id}")

        recomputed_draft = ReviewWorkbenchService._recompute_mutated_draft(session, updated_draft)

        updated_session = ReviewWorkbenchService._apply_draft_to_session(
            session,
            recomputed_draft,
            action_type=action_label,
        )
        ReviewWorkbenchService._persist_if_needed(updated_session, persist_session)
        return updated_session, ReviewWorkbenchService._mutation_summary(
            updated_session,
            action_type=action_label,
            extra={"section_id": section_id},
        )

    @staticmethod
    def update_metadata(
        *,
        session_id: str,
        title: str,
        meta_description: str,
        h1: str,
        intro_snippet: str,
        persist_session: bool = True,
        action_label: str = "metadata_edit",
    ) -> tuple[dict, dict]:
        session = ReviewSessionStore.load_session(session_id)
        updated_draft = deepcopy(session["draft"])
        updated_draft["metadata"] = {
            **updated_draft.get("metadata", {}),
            "title": title,
            "meta_description": meta_description,
            "h1": h1,
            "intro_snippet": intro_snippet,
        }

        recomputed_draft = ReviewWorkbenchService._recompute_mutated_draft(session, updated_draft)

        updated_session = ReviewWorkbenchService._apply_draft_to_session(
            session,
            recomputed_draft,
            action_type=action_label,
        )
        ReviewWorkbenchService._persist_if_needed(updated_session, persist_session)
        return updated_session, ReviewWorkbenchService._mutation_summary(
            updated_session,
            action_type=action_label,
        )

    @staticmethod
    def restore_version(
        *,
        session_id: str,
        version_id: str,
        persist_session: bool = True,
        action_label: str = "restore_version",
    ) -> tuple[dict, dict]:
        session = ReviewSessionStore.load_session(session_id)
        version_history = session.get("version_history", [])

        matched_version = None
        for version in version_history:
            if version.get("version_id") == version_id:
                matched_version = version
                break

        if matched_version is None:
            raise ValueError(f"Version not found: {version_id}")

        restored_draft = deepcopy(matched_version["draft_snapshot"])
        recomputed_draft = ReviewWorkbenchService._recompute_mutated_draft(session, restored_draft)

        updated_session = ReviewWorkbenchService._apply_draft_to_session(
            session,
            recomputed_draft,
            action_type=action_label,
        )
        ReviewWorkbenchService._persist_if_needed(updated_session, persist_session)
        return updated_session, ReviewWorkbenchService._mutation_summary(
            updated_session,
            action_type=action_label,
            extra={"restored_from_version_id": version_id},
        )