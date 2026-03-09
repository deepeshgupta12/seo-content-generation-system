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
                f"Resale price signals for {entity_name}, {city_name} currently centre around an asking price of ₹{asking_price:,}. "
                f"This gives a grounded starting point for understanding how the visible resale inventory on this page is positioned."
            )

        if price_trend:
            latest = price_trend[0]
            quarter = latest.get("quarterName")
            location_rate = latest.get("locationRate")
            micromarket_rate = latest.get("micromarketRate")
            city_rate = latest.get("cityRate")

            trend_parts: list[str] = []
            if quarter:
                trend_parts.append(f"the latest tracked period is {quarter}")
            if location_rate is not None:
                trend_parts.append(f"the locality-level rate is ₹{location_rate:,}")
            if micromarket_rate is not None:
                trend_parts.append(f"the micromarket-level rate is ₹{micromarket_rate:,}")
            if city_rate is not None:
                trend_parts.append(f"the city-level rate is ₹{city_rate:,}")

            if trend_parts:
                lines.append(
                    "Within the available trend inputs, "
                    + ", ".join(trend_parts)
                    + ". These values help place the current page-level asking signal in a wider local market context without introducing unsupported interpretation."
                )

        if not lines:
            return (
                f"This section summarises the grounded asking-price inputs available for {entity_name}, {city_name}. "
                f"When trend records are present, they can be used to compare the current page-level price signal with nearby market benchmarks."
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
            lines.append(
                "Grounded review inputs on this page show "
                + ", ".join(summary_parts)
                + ". These figures reflect only what is currently available in the source-backed review layer."
            )

        if positive_tags:
            lines.append(
                f"Among the positive tags currently surfaced, examples include {', '.join(positive_tags[:3])}. "
                f"These are presented as observed review signals rather than editorial judgement."
            )
        if negative_tags:
            lines.append(
                f"The available negative tags include {', '.join(negative_tags[:3])}. "
                f"This helps show the kinds of feedback labels attached to the current review dataset."
            )
        if locality_summary:
            lines.append(
                f"The page also includes an AI summary field for the locality, which currently reads: {locality_summary}"
            )

        if not lines:
            return (
                "Review and rating signals are shown only when they are present in the grounded page inputs. "
                "Where available, this section summarises counts, ratings, tags, and AI summary fields without adding interpretation beyond the data."
            )

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
            lines.append(
                "Current sale-side inventory inputs show "
                + ", ".join(count_parts)
                + ". This gives a direct view of the scale of resale supply currently represented on the page."
            )

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
                lines.append(
                    "At the unit-type level, the available grounded inputs indicate "
                    + ", ".join(unit_parts)
                    + ". This helps explain how the visible resale inventory is distributed for one of the surfaced configurations."
                )

        range_parts: list[str] = []
        if sale_range.get("doc_count") is not None:
            range_parts.append(f"listing range document count is {sale_range['doc_count']}")
        if sale_range.get("min_price") is not None:
            range_parts.append(f"minimum listed price is ₹{sale_range['min_price']:,}")
        if sale_range.get("max_price") is not None:
            range_parts.append(f"maximum listed price is ₹{sale_range['max_price']:,}")
        if range_parts:
            lines.append(
                "Listing-range inputs further show "
                + ", ".join(range_parts)
                + ". These values help frame the spread of resale listings represented in the current structured dataset."
            )

        if not lines:
            return (
                "Demand and supply signals are shown only when grounded sale-side inputs are available. "
                "Where present, this section uses explicit counts, percentages, and listing-range values from the source data."
            )

        return " ".join(lines)
    
    @staticmethod
    def _summarize_table(table: dict) -> str:
        title = table.get("title", "This table")
        rows = table.get("rows", []) or []
        columns = table.get("columns", []) or []

        if not rows:
            return (
                f"{title} currently does not contain structured rows in the grounded dataset. "
                "This table is still retained in the draft structure so reviewers can confirm when source-backed structured coverage is unavailable. "
                "Reviewers can use this table to cross-check whether a narrative should stay descriptive only, without leaning on unavailable row-level data."
            )

        row_count = len(rows)
        column_count = len(columns)
        first_row = rows[0] if rows else {}

        highlights: list[str] = []
        for column in columns[:3]:
            value = first_row.get(column)
            if value not in {None, "", "—"}:
                highlights.append(f"{column} starts with {value}")

        summary = (
            f"{title} presents {row_count} grounded row{'s' if row_count != 1 else ''} "
            f"across {column_count} column{'s' if column_count != 1 else ''}. "
            "It gives a structured snapshot of the source-backed values that support this page section. "
        )

        if highlights:
            summary += "In the first visible row, " + ", ".join(highlights) + ". "

        summary += (
            "This makes it easier to review the visible price, inventory, locality, or category signals without relying only on prose. "
            "Reviewers can use this table to cross-check whether the generated narrative stays aligned with the underlying structured inputs."
        )
        return summary
    
    @staticmethod
    def _attach_table_summaries(tables: list[dict]) -> list[dict]:
        enriched: list[dict] = []
        for table in tables:
            updated = dict(table)
            updated["summary"] = DraftGenerationService._summarize_table(updated)
            enriched.append(updated)
        return enriched

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
                lines.append(
                    "The available property-type rate inputs show "
                    + ", ".join(parts)
                    + ". This offers a grounded snapshot of how at least one property-type bucket is represented in the current resale dataset."
                )

        if sale_property_type_distribution:
            first_dist = sale_property_type_distribution[0]
            dist_parts: list[str] = []
            if first_dist.get("key"):
                dist_parts.append(f"{first_dist['key']} appears in the sale property-type mix")
            if first_dist.get("doc_count") is not None:
                dist_parts.append(f"document count is {first_dist['doc_count']}")
            if dist_parts:
                lines.append(
                    "Within the sale property-type distribution, " + ", ".join(dist_parts) + "."
                )

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
                lines.append(
                    "Status-level inputs also indicate "
                    + ", ".join(status_parts)
                    + ". This is useful where the page includes readiness or completion-state segmentation."
                )

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
                lines.append(
                    "At the local rate level, the grounded input shows " + ", ".join(location_parts) + "."
                )

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
                lines.append(
                    "Micromarket-rate inputs show " + ", ".join(micromarket_parts) + "."
                )

        if not lines:
            return (
                "Property-type and status signals are shown only when grounded source inputs are available. "
                "Where present, this section summarises property-type, status, and rate fields without recommending one type over another."
            )

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
        data_context = content_plan.get("data_context", {}) or {}
        entity = content_plan.get("entity", {}) or {}
        entity_name = entity.get("entity_name", "this location")
        city_name = entity.get("city_name", "")
        location_label = f"{entity_name}, {city_name}" if city_name and city_name != entity_name else entity_name

        listing_summary = data_context.get("listing_summary", {}) or {}
        distributions = data_context.get("distributions", {}) or {}
        nearby_localities = data_context.get("nearby_localities", []) or []
        pricing_summary = data_context.get("pricing_summary", {}) or {}
        listing_ranges = data_context.get("listing_ranges", {}) or {}

        if "review" in lowered or "rating" in lowered:
            return DraftGenerationService._build_review_signals_safe_body(content_plan)

        if "demand" in lowered or "supply" in lowered:
            return DraftGenerationService._build_demand_supply_safe_body(content_plan)

        if "property type" in lowered or "property-type" in lowered or "property types" in lowered:
            return DraftGenerationService._build_property_type_safe_body(content_plan)

        if "status" in lowered or "ready-to-move" in lowered or "ready to move" in lowered:
            return DraftGenerationService._build_property_type_safe_body(content_plan)

        if "price range" in lowered or ("range" in lowered and "price" in lowered):
            sale_range = listing_ranges.get("sale_listing_range", {}) or {}
            parts: list[str] = []
            if sale_range.get("doc_count") is not None:
                parts.append(f"the visible resale price-range dataset covers {sale_range['doc_count']} listings")
            if sale_range.get("min_price") is not None:
                parts.append(f"the minimum listed price is ₹{sale_range['min_price']:,}")
            if sale_range.get("max_price") is not None:
                parts.append(f"the maximum listed price is ₹{sale_range['max_price']:,}")

            if parts:
                return (
                    f"For {location_label}, the grounded resale listing-range inputs show that "
                    + ", ".join(parts)
                    + ". This answer is based only on the structured values available in the current page dataset."
                )

        if "price" in lowered or "asking" in lowered or "rate" in lowered:
            return DraftGenerationService._build_price_trends_safe_body(content_plan)

        if "how many" in lowered or "available" in lowered or "inventory" in lowered:
            sale_count = listing_summary.get("sale_count")
            total_listings = listing_summary.get("total_listings")
            total_projects = listing_summary.get("total_projects")

            parts: list[str] = []
            if sale_count is not None:
                parts.append(f"the visible resale listing count is {sale_count}")
            if total_listings is not None:
                parts.append(f"the total listing count is {total_listings}")
            if total_projects is not None:
                parts.append(f"the total project count is {total_projects}")

            if parts:
                return (
                    f"For {location_label}, the current page-level inventory inputs show that "
                    + ", ".join(parts)
                    + ". These figures are taken directly from the grounded listing summary available to the draft."
                )

        if "bhk" in lowered or "unit type" in lowered or "unit-type" in lowered:
            bhk_mix = distributions.get("sale_unit_type_distribution", []) or []
            if bhk_mix:
                first = bhk_mix[0]
                key = first.get("key")
                doc_count = first.get("doc_count")
                details: list[str] = []
                if key:
                    details.append(f"the first visible BHK bucket is {key}")
                if doc_count is not None:
                    details.append(f"its document count is {doc_count}")

                return (
                    f"The grounded BHK mix for {location_label} is derived from the available resale unit-type distribution. "
                    + (", ".join(details) + ". " if details else "")
                    + "This helps show which configurations are currently represented in the structured page data."
                )

        if "nearby" in lowered or "localities" in lowered or "locality" in lowered:
            if nearby_localities:
                first = nearby_localities[0]
                name = first.get("name")
                distance_km = first.get("distance_km")
                sale_count = first.get("sale_count")

                parts: list[str] = []
                if name:
                    parts.append(f"the first nearby locality listed is {name}")
                if distance_km is not None:
                    parts.append(f"it is {distance_km:.2f} km away")
                if sale_count is not None:
                    parts.append(f"it shows {sale_count} resale listings")

                return (
                    f"The nearby-locality comparison inputs for {location_label} help surface alternate areas visible in the same grounded dataset. "
                    + (", ".join(parts) + ". " if parts else "")
                    + "These nearby options are included to support comparison and exploration within the current page context."
                )

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
    def _ensure_faq_coverage(content_plan: dict, faqs: list[dict]) -> list[dict]:
        existing_questions = {item.get("question", "").strip().lower() for item in faqs if item.get("question")}
        ensured = list(faqs)

        for intent in content_plan.get("faq_plan", {}).get("faq_intents", []):
            question = intent.get("question_template")
            if not question:
                continue
            if question.strip().lower() in existing_questions:
                continue

            answer = DraftGenerationService._build_safe_faq_answer(content_plan, question)
            if answer:
                ensured.append(
                    {
                        "question": question,
                        "answer": answer,
                    }
                )
                existing_questions.add(question.strip().lower())

        return ensured

    @staticmethod
    def _build_base_draft(
        content_plan: dict,
        keyword_intelligence_version: str,
        metadata: dict,
        sections: list[dict],
        faqs: list[dict],
    ) -> dict:
        tables = TableRenderer.render_all(content_plan["table_plan"], content_plan["data_context"])
        tables = DraftGenerationService._attach_table_summaries(tables)
        internal_links = DraftGenerationService._resolve_internal_links(content_plan["internal_links_plan"])

        return {
            "version": "v2.5",
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
        faqs = DraftGenerationService._ensure_faq_coverage(content_plan, faqs)

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
            faqs = DraftGenerationService._ensure_faq_coverage(content_plan, faqs)

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