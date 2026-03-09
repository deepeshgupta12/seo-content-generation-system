from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from seo_content_engine.core.config import settings
from seo_content_engine.services.content_plan_builder import ContentPlanBuilder
from seo_content_engine.services.factual_validator import FactualValidator
from seo_content_engine.services.markdown_renderer import MarkdownRenderer
from seo_content_engine.services.openai_client import OpenAIClient
from seo_content_engine.services.prompt_builder import PromptBuilder
from seo_content_engine.services.table_renderer import TableRenderer


class DraftGenerationService:
    @staticmethod
    def _generate_metadata(content_plan: dict, client: OpenAIClient) -> dict:
        system_prompt, user_prompt = PromptBuilder.metadata_prompts(content_plan)
        return client.generate_json(system_prompt, user_prompt)

    @staticmethod
    def _generate_sections(content_plan: dict, client: OpenAIClient) -> list[dict]:
        system_prompt, user_prompt = PromptBuilder.sections_prompts(content_plan)
        response = client.generate_json(system_prompt, user_prompt)
        return response.get("sections", [])

    @staticmethod
    def _generate_faqs(content_plan: dict, client: OpenAIClient) -> list[dict]:
        system_prompt, user_prompt = PromptBuilder.faq_prompts(content_plan)
        response = client.generate_json(system_prompt, user_prompt)
        return response.get("faqs", [])

    @staticmethod
    def _resolve_internal_links(internal_links: dict) -> dict:
        from seo_content_engine.services.output_formatter import OutputFormatter

        resolved: dict = {}
        for group_name, group_links in internal_links.items():
            if not isinstance(group_links, list):
                resolved[group_name] = group_links
                continue

            resolved_group = []
            for item in group_links:
                if isinstance(item, list):
                    nested_group = []
                    for nested in item:
                        updated = dict(nested)
                        if "url" in updated:
                            updated["url"] = OutputFormatter.resolve_url(updated.get("url"))
                        nested_group.append(updated)
                    resolved_group.append(nested_group)
                elif isinstance(item, dict):
                    updated = dict(item)
                    if "url" in updated:
                        updated["url"] = OutputFormatter.resolve_url(updated.get("url"))
                    resolved_group.append(updated)

            resolved[group_name] = resolved_group

        return resolved

    @staticmethod
    def _repair_metadata(
        content_plan: dict,
        metadata: dict,
        validation_report: dict,
        client: OpenAIClient,
    ) -> dict:
        issues_by_field = {
            field_name: report["issues"]
            for field_name, report in validation_report["metadata_checks"].items()
            if report["issues"]
        }
        if not issues_by_field:
            return metadata

        validation_map = {
            field_name: report
            for field_name, report in validation_report["metadata_checks"].items()
            if report["issues"]
        }

        system_prompt, user_prompt = PromptBuilder.repair_metadata_prompt(
            content_plan,
            metadata,
            issues_by_field,
            validation_map,
        )
        repaired = client.generate_json(system_prompt, user_prompt)
        return repaired if isinstance(repaired, dict) else metadata

    @staticmethod
    def _build_price_trends_safe_body(content_plan: dict) -> str:
        entity = content_plan["entity"]
        entity_name = entity["entity_name"]
        city_name = entity["city_name"]

        pricing_summary = content_plan["data_context"].get("pricing_summary", {}) or {}
        asking_price = pricing_summary.get("asking_price")
        price_trend = pricing_summary.get("price_trend", []) or []

        lines: list[str] = []
        if asking_price is not None:
            lines.append(
                f"The asking price signal for resale properties in {entity_name}, {city_name} is ₹{asking_price:,}."
            )

        if price_trend:
            latest = price_trend[0]
            quarter = latest.get("quarterName")
            location_rate = latest.get("locationRate")
            micromarket_rate = latest.get("micromarketRate")
            city_rate = latest.get("cityRate")

            trend_parts: list[str] = []
            if quarter:
                trend_parts.append(f"The latest available trend entry is for {quarter}")
            if location_rate is not None:
                trend_parts.append(f"the locality rate is ₹{location_rate:,}")
            if micromarket_rate is not None:
                trend_parts.append(f"the micromarket rate is ₹{micromarket_rate:,}")
            if city_rate is not None:
                trend_parts.append(f"the city rate is ₹{city_rate:,}")

            if trend_parts:
                lines.append(", ".join(trend_parts) + ".")

        if not lines:
            return (
                f"This section uses the asking price signal and available price-trend entries "
                f"for {entity_name}, {city_name}."
            )

        return " ".join(lines)

    @staticmethod
    def _build_review_signals_safe_body(content_plan: dict) -> str:
        review_summary = content_plan["data_context"].get("review_summary", {}) or {}
        ai_summary = content_plan["data_context"].get("ai_summary", {}) or {}
        overview = review_summary.get("overview", {}) or {}

        avg_rating = overview.get("avg_rating")
        review_count = overview.get("review_count")
        rating_count = overview.get("rating_count")
        positive_tags = review_summary.get("positive_tags", []) or []
        negative_tags = review_summary.get("negative_tags", []) or []
        locality_summary = ai_summary.get("locality_summary")

        lines: list[str] = []

        summary_parts: list[str] = []
        if avg_rating is not None:
            summary_parts.append(f"the average rating is {avg_rating}")
        if review_count is not None:
            summary_parts.append(f"review count is {review_count}")
        if rating_count is not None and rating_count != review_count:
            summary_parts.append(f"rating count is {rating_count}")

        if summary_parts:
            lines.append("Available review signals show " + ", ".join(summary_parts) + ".")

        if positive_tags:
            lines.append(f"Positive review tags include {', '.join(positive_tags[:3])}.")
        if negative_tags:
            lines.append(f"Negative review tags include {', '.join(negative_tags[:3])}.")
        if locality_summary:
            lines.append(f"AI summary available for this page: {locality_summary}")

        if not lines:
            return "Review and rating signals are available on this page when present in the source data."

        return " ".join(lines)

    @staticmethod
    def _build_demand_supply_safe_body(content_plan: dict) -> str:
        listing_summary = content_plan["data_context"].get("listing_summary", {}) or {}
        demand_supply = content_plan["data_context"].get("demand_supply", {}) or {}
        listing_ranges = content_plan["data_context"].get("listing_ranges", {}) or {}

        sale_summary = demand_supply.get("sale", {}) or {}
        unit_types = sale_summary.get("unitType", []) or []
        sale_available = listing_summary.get("sale_available")
        sale_count = listing_summary.get("sale_count")
        sale_range = listing_ranges.get("sale_listing_range", {}) or {}

        lines: list[str] = []

        count_parts: list[str] = []
        if sale_available is not None:
            count_parts.append(f"sale available count is {sale_available}")
        if sale_count is not None and sale_count != sale_available:
            count_parts.append(f"sale count is {sale_count}")
        if count_parts:
            lines.append("Available sale-side signals show " + ", ".join(count_parts) + ".")

        if unit_types:
            primary = unit_types[0]
            unit_name = primary.get("name")
            listing = primary.get("listing")
            demand_percent = primary.get("demandPercent")
            supply_percent = primary.get("supplyPercent")

            unit_parts: list[str] = []
            if unit_name:
                unit_parts.append(f"for {unit_name}")
            if listing is not None:
                unit_parts.append(f"listing count is {listing}")
            if demand_percent is not None:
                unit_parts.append(f"demand percent is {demand_percent}")
            if supply_percent is not None:
                unit_parts.append(f"supply percent is {supply_percent}")

            if unit_parts:
                lines.append("Unit-type demand and supply inputs indicate " + ", ".join(unit_parts) + ".")

        range_parts: list[str] = []
        if sale_range.get("doc_count") is not None:
            range_parts.append(f"listing range document count is {sale_range['doc_count']}")
        if sale_range.get("min_price") is not None:
            range_parts.append(f"minimum listed price is ₹{sale_range['min_price']:,}")
        if sale_range.get("max_price") is not None:
            range_parts.append(f"maximum listed price is ₹{sale_range['max_price']:,}")
        if range_parts:
            lines.append("Listing-range inputs show " + ", ".join(range_parts) + ".")

        if not lines:
            return "Demand and supply signals are shown only when grounded sale-side inputs are available."

        return " ".join(lines)

    @staticmethod
    def _build_property_type_safe_body(content_plan: dict) -> str:
        pricing_summary = content_plan["data_context"].get("pricing_summary", {}) or {}
        distributions = content_plan["data_context"].get("distributions", {}) or {}

        property_types = pricing_summary.get("property_types", []) or []
        property_status = pricing_summary.get("property_status", []) or []
        location_rates = pricing_summary.get("location_rates", []) or []
        micromarket_rates = pricing_summary.get("micromarket_rates", []) or []
        sale_property_type_distribution = distributions.get("sale_property_type_distribution", []) or []

        lines: list[str] = []

        if property_types:
            first = property_types[0]
            parts: list[str] = []
            if first.get("propertyType"):
                parts.append(f"property type is {first['propertyType']}")
            if first.get("avgPrice") is not None:
                parts.append(f"average listed value in this input is ₹{first['avgPrice']:,}")
            if first.get("changePercent") is not None:
                parts.append(f"change percent is {first['changePercent']}")
            if parts:
                lines.append("Property-type rate inputs show " + ", ".join(parts) + ".")

        if sale_property_type_distribution:
            first_dist = sale_property_type_distribution[0]
            dist_parts: list[str] = []
            if first_dist.get("key"):
                dist_parts.append(f"{first_dist['key']} appears in the sale property-type mix")
            if first_dist.get("doc_count") is not None:
                dist_parts.append(f"document count is {first_dist['doc_count']}")
            if dist_parts:
                lines.append(", ".join(dist_parts) + ".")

        if property_status:
            first_status = property_status[0]
            status_parts: list[str] = []
            if first_status.get("status"):
                status_parts.append(f"status bucket is {first_status['status']}")
            if first_status.get("units") is not None:
                status_parts.append(f"units are {first_status['units']}")
            if first_status.get("avgPrice") is not None:
                status_parts.append(f"average price is ₹{first_status['avgPrice']:,}")
            if status_parts:
                lines.append("Status inputs indicate " + ", ".join(status_parts) + ".")

        if location_rates:
            first_location = location_rates[0]
            location_parts: list[str] = []
            if first_location.get("name"):
                location_parts.append(f"location name is {first_location['name']}")
            if first_location.get("avgRate") is not None:
                location_parts.append(f"average rate is ₹{first_location['avgRate']:,}")
            if first_location.get("changePercentage") is not None:
                location_parts.append(f"change percentage is {first_location['changePercentage']}")
            if location_parts:
                lines.append("Location-rate inputs show " + ", ".join(location_parts) + ".")

        if micromarket_rates:
            first_micromarket = micromarket_rates[0]
            micromarket_parts: list[str] = []
            if first_micromarket.get("name"):
                micromarket_parts.append(f"micromarket name is {first_micromarket['name']}")
            if first_micromarket.get("avgRate") is not None:
                micromarket_parts.append(f"average rate is ₹{first_micromarket['avgRate']:,}")
            if first_micromarket.get("changePercentage") is not None:
                micromarket_parts.append(f"change percentage is {first_micromarket['changePercentage']}")
            if micromarket_parts:
                lines.append("Micromarket-rate inputs show " + ", ".join(micromarket_parts) + ".")

        if not lines:
            return "Property-type and status signals are shown only when grounded source inputs are available."

        return " ".join(lines)

    @staticmethod
    def _build_safe_section_body(content_plan: dict, section_id: str) -> str | None:
        if section_id == "price_trends_and_rates":
            return DraftGenerationService._build_price_trends_safe_body(content_plan)

        if section_id == "review_and_rating_signals":
            return DraftGenerationService._build_review_signals_safe_body(content_plan)

        if section_id == "demand_and_supply_signals":
            return DraftGenerationService._build_demand_supply_safe_body(content_plan)

        if section_id in {"property_type_signals", "property_type_rate_snapshot"}:
            return DraftGenerationService._build_property_type_safe_body(content_plan)

        return None

    @staticmethod
    def _fallback_section_if_needed(content_plan: dict, section: dict, validation: dict) -> dict:
        issues = validation.get("issues", [])
        if not issues:
            return section

        section_id = section.get("id", "")
        safe_body = DraftGenerationService._build_safe_section_body(content_plan, section_id)
        if safe_body is None:
            return section

        updated = dict(section)
        updated["body"] = safe_body
        return updated

    @staticmethod
    def _ensure_planned_sections_present(content_plan: dict, sections: list[dict]) -> list[dict]:
        section_map = {section.get("id"): dict(section) for section in sections if section.get("id")}
        completed_sections: list[dict] = []

        for planned in content_plan.get("section_plan", []):
            if planned.get("render_type") not in {"generative", "hybrid"} or planned.get("id") == "faq_section":
                continue

            existing = section_map.get(planned["id"])
            if existing:
                completed_sections.append(existing)
                continue

            safe_body = DraftGenerationService._build_safe_section_body(content_plan, planned["id"])
            if safe_body is None:
                continue

            completed_sections.append(
                {
                    "id": planned["id"],
                    "title": planned["title"],
                    "body": safe_body,
                }
            )

        return completed_sections

    @staticmethod
    def _build_safe_faq_answer(content_plan: dict, question: str) -> str | None:
        lowered = question.lower()

        if "review" in lowered or "rating" in lowered:
            return DraftGenerationService._build_review_signals_safe_body(content_plan)

        if "demand" in lowered or "supply" in lowered or "listing range" in lowered:
            return DraftGenerationService._build_demand_supply_safe_body(content_plan)

        if "property type" in lowered or "property types" in lowered or "status" in lowered:
            return DraftGenerationService._build_property_type_safe_body(content_plan)

        if "price" in lowered or "rate" in lowered:
            return DraftGenerationService._build_price_trends_safe_body(content_plan)

        return None

    @staticmethod
    def _repair_sections(
        content_plan: dict,
        sections: list[dict],
        validation_report: dict,
        client: OpenAIClient,
    ) -> list[dict]:
        check_map = {item["id"]: item["validation"] for item in validation_report["section_checks"]}
        repaired_sections: list[dict] = []

        for section in sections:
            validation = check_map.get(section.get("id"), {})
            issues = validation.get("issues", [])
            if not issues:
                repaired_sections.append(section)
                continue

            system_prompt, user_prompt = PromptBuilder.repair_section_prompt(content_plan, section, validation)
            repaired = client.generate_json(system_prompt, user_prompt)

            if isinstance(repaired, dict) and repaired.get("body"):
                repaired_section = dict(section)
                repaired_section["body"] = repaired["body"]
                repaired_section = DraftGenerationService._fallback_section_if_needed(
                    content_plan,
                    repaired_section,
                    validation,
                )
                repaired_sections.append(repaired_section)
            else:
                fallback = DraftGenerationService._fallback_section_if_needed(content_plan, section, validation)
                repaired_sections.append(fallback)

        return repaired_sections

    @staticmethod
    def _repair_faqs(
        content_plan: dict,
        faqs: list[dict],
        validation_report: dict,
        client: OpenAIClient,
    ) -> list[dict]:
        check_map = {item["question"]: item["validation"] for item in validation_report["faq_checks"]}
        repaired_faqs: list[dict] = []

        for faq in faqs:
            validation = check_map.get(faq.get("question"), {})
            issues = validation.get("issues", [])
            if not issues:
                repaired_faqs.append(faq)
                continue

            system_prompt, user_prompt = PromptBuilder.repair_faq_prompt(content_plan, faq, validation)
            repaired = client.generate_json(system_prompt, user_prompt)
            if isinstance(repaired, dict) and repaired.get("answer"):
                repaired_faqs.append(repaired)
            else:
                fallback_answer = DraftGenerationService._build_safe_faq_answer(
                    content_plan,
                    faq.get("question", ""),
                )
                if fallback_answer:
                    repaired_faqs.append(
                        {
                            "question": faq.get("question"),
                            "answer": fallback_answer,
                        }
                    )
                else:
                    repaired_faqs.append(faq)

        return repaired_faqs

    @staticmethod
    def _build_base_draft(
        content_plan: dict,
        keyword_intelligence_version: str,
        metadata: dict,
        sections: list[dict],
        faqs: list[dict],
    ) -> dict:
        tables = TableRenderer.render_all(content_plan["table_plan"], content_plan["data_context"])
        internal_links = DraftGenerationService._resolve_internal_links(content_plan["internal_links_plan"])

        return {
            "version": "v2.4",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": content_plan["page_type"],
            "listing_type": content_plan["listing_type"],
            "entity": content_plan["entity"],
            "metadata": metadata,
            "sections": sections,
            "tables": tables,
            "faqs": faqs,
            "internal_links": internal_links,
            "content_plan": content_plan,
            "keyword_intelligence_version": keyword_intelligence_version,
        }

    @staticmethod
    def _build_validation_history_entry(pass_name: str, pass_index: int, validation_report: dict) -> dict[str, Any]:
        return {
            "pass_name": pass_name,
            "pass_index": pass_index,
            "passed": validation_report["passed"],
            "debug_summary": FactualValidator.summarize_report(validation_report),
            "validation_report": validation_report,
        }

    @staticmethod
    def generate(
        normalized: dict,
        keyword_intelligence: dict,
        openai_client: OpenAIClient | None = None,
    ) -> dict:
        content_plan = ContentPlanBuilder.build(
            normalized=normalized,
            keyword_intelligence=keyword_intelligence,
        )

        client = openai_client or OpenAIClient()

        metadata = DraftGenerationService._generate_metadata(content_plan, client)
        sections = DraftGenerationService._generate_sections(content_plan, client)
        sections = DraftGenerationService._ensure_planned_sections_present(content_plan, sections)
        faqs = DraftGenerationService._generate_faqs(content_plan, client)

        draft = DraftGenerationService._build_base_draft(
            content_plan=content_plan,
            keyword_intelligence_version=keyword_intelligence["version"],
            metadata=metadata,
            sections=sections,
            faqs=faqs,
        )

        validation_report = FactualValidator.validate_draft(draft)
        validation_history = [
            DraftGenerationService._build_validation_history_entry("initial_generation", 0, validation_report)
        ]

        repair_passes = 0
        while not validation_report["passed"] and repair_passes < settings.draft_repair_max_passes:
            metadata = DraftGenerationService._repair_metadata(content_plan, draft["metadata"], validation_report, client)
            sections = DraftGenerationService._repair_sections(content_plan, draft["sections"], validation_report, client)
            sections = DraftGenerationService._ensure_planned_sections_present(content_plan, sections)
            faqs = DraftGenerationService._repair_faqs(content_plan, draft["faqs"], validation_report, client)

            draft = DraftGenerationService._build_base_draft(
                content_plan=content_plan,
                keyword_intelligence_version=keyword_intelligence["version"],
                metadata=metadata,
                sections=sections,
                faqs=faqs,
            )

            repair_passes += 1
            validation_report = FactualValidator.validate_draft(draft)
            validation_history.append(
                DraftGenerationService._build_validation_history_entry(
                    "repair_pass",
                    repair_passes,
                    validation_report,
                )
            )

        pre_block_draft = deepcopy(draft)
        final_debug_summary = FactualValidator.summarize_report(validation_report)

        sanitized = FactualValidator.apply_sanitization(draft, validation_report)
        sanitized["repair_passes_used"] = repair_passes
        sanitized["validation_history"] = validation_history
        sanitized["pre_block_draft"] = pre_block_draft
        sanitized["debug_summary"] = final_debug_summary
        sanitized["quality_report"] = sanitized.get("quality_report", final_debug_summary)
        sanitized["publish_ready"] = sanitized["quality_report"].get("approval_status") != "fail"
        sanitized["markdown_draft"] = MarkdownRenderer.render(sanitized)
        return sanitized