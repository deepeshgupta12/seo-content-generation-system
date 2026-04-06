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
    def _page_property_type_context(content_plan: dict) -> dict:
        return content_plan.get("data_context", {}).get("page_property_type_context", {}) or {}

    @staticmethod
    def _is_residential_property_type(name: str | None) -> bool:
        lowered = str(name or "").strip().lower()
        if not lowered:
            return False

        blocked = {
            "shop",
            "office space",
            "co-working space",
            "co working space",
            "warehouse",
            "showroom",
            "industrial",
            "commercial",
        }
        return lowered not in blocked

    @staticmethod
    def _normalize_property_type_alias(name: str | None) -> str:
        lowered = str(name or "").strip().lower()

        if lowered in {"flat", "flats", "apartment", "apartments"}:
            return "Apartment"
        if lowered in {"builder floor", "builder floors", "builder-floor", "builder-floors"}:
            return "Builder Floor"
        if lowered in {"villa", "villas"}:
            return "Villa"
        if lowered in {"plot", "plots"}:
            return "Plot"
        if lowered in {"house", "houses", "independent house", "independent-house"}:
            return "House"
        if lowered in {"penthouse", "penthouses"}:
            return "Penthouse"
        if lowered in {"studio", "studios"}:
            return "Studio"
        if lowered in {"office space", "office spaces", "office-space", "office-spaces"}:
            return "Office Space"
        if lowered in {"shop", "shops"}:
            return "Shop"
        if lowered in {"warehouse", "warehouses"}:
            return "Warehouse"
        if lowered in {"showroom", "showrooms"}:
            return "Showroom"

        return str(name or "").strip()

    @staticmethod
    def _filter_residential_property_types(records: list[dict]) -> list[dict]:
        filtered: list[dict] = []
        for item in records or []:
            if not isinstance(item, dict):
                continue
            property_type = DraftGenerationService._normalize_property_type_alias(item.get("propertyType"))
            if not DraftGenerationService._is_residential_property_type(property_type):
                continue
            filtered.append({**item, "propertyType": property_type})
        return filtered

    @staticmethod
    def _find_property_type_record(records: list[dict], target_property_type: str | None) -> dict | None:
        if not target_property_type:
            return None

        target = DraftGenerationService._normalize_property_type_alias(target_property_type).lower()
        for item in records or []:
            property_type = DraftGenerationService._normalize_property_type_alias(item.get("propertyType"))
            if property_type.lower() == target:
                return {**item, "propertyType": property_type}

        return None

    @staticmethod
    def _property_type_distribution_count(
        distribution_rows: list[dict],
        target_property_type: str | None,
    ) -> int | None:
        if not target_property_type:
            return None

        target = DraftGenerationService._normalize_property_type_alias(target_property_type).lower()

        for item in distribution_rows or []:
            key = str(item.get("key") or "").lower()
            if not key:
                continue
            if target == "apartment" and ("flat" in key or "apartment" in key):
                return item.get("doc_count")
            if target in key:
                return item.get("doc_count")

        return None

    @staticmethod
    def _clean_market_signal_items(items: list[str], limit: int = 4) -> list[str]:
        cleaned: list[str] = []

        for item in items or []:
            text = str(item or "").strip()
            if not text:
                continue

            text = " ".join(text.split())
            text = text.rstrip(" .;,:")
            if not text:
                continue

            cleaned.append(text)
            if len(cleaned) >= limit:
                break

        return cleaned

    @staticmethod
    def _location_label(content_plan: dict) -> str:
        entity = content_plan.get("entity", {}) or {}
        entity_name = entity.get("entity_name", "this location")
        city_name = entity.get("city_name", "")
        return f"{entity_name}, {city_name}" if city_name and city_name != entity_name else entity_name

    @staticmethod
    def _build_price_trends_safe_body(content_plan: dict) -> str:
        pricing_summary = content_plan["data_context"].get("pricing_summary", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        asking_price = pricing_summary.get("asking_price")
        price_trend = pricing_summary.get("price_trend", []) or []

        lines: list[str] = []

        if asking_price is not None:
            lines.append(
                f"The current asking price signal for resale properties in {location_label} is ₹{asking_price:,}."
            )

        if price_trend:
            latest = price_trend[0]
            trend_parts: list[str] = []
            if latest.get("quarterName"):
                trend_parts.append(f"the latest tracked quarter is {latest.get('quarterName')}")
            if latest.get("locationRate") is not None:
                trend_parts.append(f"the locality-level rate in that entry is ₹{latest.get('locationRate'):,}")
            if latest.get("micromarketRate") is not None:
                trend_parts.append(f"the micromarket-level rate is ₹{latest.get('micromarketRate'):,}")
            if latest.get("cityRate") is not None:
                trend_parts.append(f"the city-level rate is ₹{latest.get('cityRate'):,}")
            if trend_parts:
                lines.append("In the available trend view, " + ", ".join(trend_parts) + ".")

        if not lines:
            return (
                f"This section covers the available asking-price view for resale properties in {location_label}. "
                "When trend data is present, it can be used to compare the current asking signal with the broader local context."
            )

        return "\n\n".join(lines)

    @staticmethod
    def _build_review_signals_safe_body(content_plan: dict) -> str:
        review_summary = content_plan["data_context"].get("review_summary", {}) or {}
        ai_summary = content_plan["data_context"].get("ai_summary", {}) or {}
        overview = review_summary.get("overview", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        avg_rating = overview.get("avg_rating")
        review_count = overview.get("review_count")
        positive_tags = review_summary.get("positive_tags", []) or []
        negative_tags = review_summary.get("negative_tags", []) or []
        locality_summary = ai_summary.get("locality_summary")

        lines: list[str] = []

        summary_bits: list[str] = []
        if avg_rating is not None:
            summary_bits.append(f"an average rating of {avg_rating}")
        if review_count is not None:
            summary_bits.append(f"{review_count} reviews")

        if summary_bits:
            lines.append(
                f"For {location_label}, the available review view shows " + " and ".join(summary_bits) + "."
            )

        if positive_tags:
            lines.append(f"Some of the visible positive review tags include {', '.join(positive_tags[:3])}.")
        if negative_tags:
            lines.append(f"Some of the visible negative review tags include {', '.join(negative_tags[:3])}.")
        if locality_summary:
            lines.append(locality_summary)

        if not lines:
            return (
                f"This section covers the review and rating signals available for {location_label}. "
                "When review data is present, it helps add buyer context beyond pricing and inventory."
            )

        return "\n\n".join(lines)

    @staticmethod
    def _build_demand_supply_safe_body(content_plan: dict) -> str:
        listing_summary = content_plan["data_context"].get("listing_summary", {}) or {}
        demand_supply = content_plan["data_context"].get("demand_supply", {}) or {}
        listing_ranges = content_plan["data_context"].get("listing_ranges", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        sale_summary = demand_supply.get("sale", {}) or {}
        unit_types = sale_summary.get("unitType", []) or []
        sale_available = listing_summary.get("sale_available")
        sale_count = listing_summary.get("sale_count")
        sale_range = listing_ranges.get("sale_listing_range", {}) or {}

        lines: list[str] = []

        count_parts: list[str] = []
        if sale_available is not None:
            count_parts.append(f"{sale_available} available resale listings")
        if sale_count is not None and sale_count != sale_available:
            count_parts.append(f"{sale_count} total resale listings")

        if count_parts:
            lines.append(
                f"For {location_label}, the current resale view includes " + " and ".join(count_parts) + "."
            )

        if unit_types:
            primary = unit_types[0]
            unit_name = primary.get("name")
            listing = primary.get("listing")
            demand_percent = primary.get("demandPercent")
            supply_percent = primary.get("supplyPercent")

            unit_parts: list[str] = []
            if unit_name:
                unit_parts.append(f"{unit_name}")
            if listing is not None:
                unit_parts.append(f"{listing} listings")
            if demand_percent is not None:
                unit_parts.append(f"demand share of {demand_percent}")
            if supply_percent is not None:
                unit_parts.append(f"supply share of {supply_percent}")

            if unit_parts:
                lines.append("At the unit-type level, one visible configuration shows " + ", ".join(unit_parts) + ".")

        range_parts: list[str] = []
        if sale_range.get("min_price") is not None:
            range_parts.append(f"a minimum listed price of ₹{sale_range['min_price']:,}")
        if sale_range.get("max_price") is not None:
            range_parts.append(f"a maximum listed price of ₹{sale_range['max_price']:,}")
        if sale_range.get("doc_count") is not None:
            range_parts.append(f"{sale_range['doc_count']} rows in the listing-range view")

        if range_parts:
            lines.append("The available price-range view shows " + ", ".join(range_parts) + ".")

        if not lines:
            return (
                f"This section explains the demand, supply, and listing-range signals available for {location_label}. "
                "When those inputs are present, they help clarify how the visible resale stock is distributed."
            )

        return "\n\n".join(lines)

    @staticmethod
    def _build_property_rates_ai_safe_body(content_plan: dict) -> str:
        location_label = DraftGenerationService._location_label(content_plan)
        property_rates_ai_summary = (
            content_plan.get("data_context", {}).get("property_rates_ai_summary", {}) or {}
        )

        market_snapshot = str(property_rates_ai_summary.get("market_snapshot") or "").strip()
        market_strengths = DraftGenerationService._clean_market_signal_items(
            property_rates_ai_summary.get("market_strengths", []) or [],
            limit=4,
        )
        market_challenges = DraftGenerationService._clean_market_signal_items(
            property_rates_ai_summary.get("market_challenges", []) or [],
            limit=4,
        )
        investment_opportunities = DraftGenerationService._clean_market_signal_items(
            property_rates_ai_summary.get("investment_opportunities", []) or [],
            limit=4,
        )

        if (
            not market_snapshot
            and not market_strengths
            and not market_challenges
            and not investment_opportunities
        ):
            return f"No market-summary notes are currently available for {location_label}."

        paragraphs: list[str] = []

        if market_snapshot:
            paragraphs.append(market_snapshot)

        if market_strengths:
            paragraphs.append("Strengths: " + "; ".join(market_strengths) + ".")

        if market_challenges:
            paragraphs.append("Challenges: " + "; ".join(market_challenges) + ".")

        if investment_opportunities:
            paragraphs.append("Opportunities: " + "; ".join(investment_opportunities) + ".")

        return "\n\n".join(paragraphs)

    @staticmethod
    def _build_market_snapshot_safe_body(content_plan: dict) -> str:
        location_label = DraftGenerationService._location_label(content_plan)
        listing_summary = content_plan.get("data_context", {}).get("listing_summary", {}) or {}
        pricing_summary = content_plan.get("data_context", {}).get("pricing_summary", {}) or {}
        distributions = content_plan.get("data_context", {}).get("distributions", {}) or {}
        page_property_type_context = DraftGenerationService._page_property_type_context(content_plan)

        sale_count = listing_summary.get("sale_count")
        residential_property_types = DraftGenerationService._filter_residential_property_types(
            pricing_summary.get("property_types", []) or []
        )
        property_mix = distributions.get("sale_property_type_distribution", []) or []

        if page_property_type_context.get("scope") == "specific" and page_property_type_context.get("property_type"):
            property_type = page_property_type_context.get("property_type")
            property_record = DraftGenerationService._find_property_type_record(
                residential_property_types,
                property_type,
            )
            property_count = DraftGenerationService._property_type_distribution_count(
                property_mix,
                property_type,
            )

            lines: list[str] = [
                f"This page is focused on resale {property_type.lower()} options in {location_label}."
            ]

            detail_parts: list[str] = []
            if sale_count is not None:
                detail_parts.append(f"{sale_count} resale listings are currently visible")
            if property_count is not None:
                detail_parts.append(f"{property_count} rows in the property-type mix align to this category")
            if detail_parts:
                lines.append("At a page level, " + " and ".join(detail_parts) + ".")

            if property_record:
                rate_parts: list[str] = []
                if property_record.get("avgPrice") is not None:
                    rate_parts.append(f"the asking-rate signal for this category is ₹{property_record['avgPrice']:,}")
                if property_record.get("changePercent") is not None:
                    rate_parts.append(f"the visible change signal is {property_record['changePercent']}")
                if rate_parts:
                    lines.append("In the available rate view, " + " and ".join(rate_parts) + ".")

            return "\n\n".join(lines)

        visible_residential_types = [
            item.get("propertyType") for item in residential_property_types[:4] if item.get("propertyType")
        ]

        if not visible_residential_types and sale_count is None:
            return (
                f"This section gives a grounded overview of the resale market visible for {location_label}. "
                "When inventory and property-type data is available, it helps explain what kinds of options are showing up here."
            )

        lines: list[str] = []
        if visible_residential_types:
            lines.append(
                f"The visible resale mix in {location_label} includes residential categories such as {', '.join(visible_residential_types)}."
            )
        if sale_count is not None:
            lines.append(f"The page currently shows {sale_count} resale listings.")

        return "\n\n".join(lines)

    @staticmethod
    def _build_property_type_signals_safe_body(content_plan: dict) -> str:
        pricing_summary = content_plan["data_context"].get("pricing_summary", {}) or {}
        distributions = content_plan["data_context"].get("distributions", {}) or {}
        page_property_type_context = DraftGenerationService._page_property_type_context(content_plan)
        location_label = DraftGenerationService._location_label(content_plan)

        residential_property_types = DraftGenerationService._filter_residential_property_types(
            pricing_summary.get("property_types", []) or []
        )
        property_mix = distributions.get("sale_property_type_distribution", []) or []

        if page_property_type_context.get("scope") == "specific" and page_property_type_context.get("property_type"):
            property_type = page_property_type_context.get("property_type")
            property_record = DraftGenerationService._find_property_type_record(
                residential_property_types,
                property_type,
            )
            property_count = DraftGenerationService._property_type_distribution_count(
                property_mix,
                property_type,
            )

            lines: list[str] = [
                f"For {location_label}, this page stays focused on resale {property_type.lower()} inventory."
            ]

            if property_count is not None:
                lines.append(f"The available property-type mix shows {property_count} rows for this category.")

            if property_record:
                record_parts: list[str] = []
                if property_record.get("avgPrice") is not None:
                    record_parts.append(f"an asking-rate signal of ₹{property_record['avgPrice']:,}")
                if property_record.get("changePercent") is not None:
                    record_parts.append(f"a visible change signal of {property_record['changePercent']}")
                if record_parts:
                    lines.append("The current rate view shows " + " and ".join(record_parts) + ".")

            return "\n\n".join(lines)

        if not residential_property_types and not property_mix:
            return (
                f"This section covers the residential property-type mix visible for {location_label}. "
                "When that data is available, it helps explain how the current resale options are distributed."
            )

        visible_names = [item.get("propertyType") for item in residential_property_types[:4] if item.get("propertyType")]
        lines: list[str] = []

        if visible_names:
            lines.append(
                f"For {location_label}, the visible residential mix includes categories such as {', '.join(visible_names)}."
            )

        if property_mix:
            first_match = None
            for item in property_mix:
                key = str(item.get("key") or "")
                if "flat" in key.lower() or "apartment" in key.lower() or "villa" in key.lower() or "builder" in key.lower():
                    first_match = item
                    break
            if first_match and first_match.get("doc_count") is not None:
                lines.append(f"One visible property-type bucket is {first_match.get('key')} with {first_match.get('doc_count')} rows.")

        return "\n\n".join(lines)

    @staticmethod
    def _build_property_type_rate_snapshot_safe_body(content_plan: dict) -> str:
        pricing_summary = content_plan["data_context"].get("pricing_summary", {}) or {}
        page_property_type_context = DraftGenerationService._page_property_type_context(content_plan)
        location_label = DraftGenerationService._location_label(content_plan)

        residential_property_types = DraftGenerationService._filter_residential_property_types(
            pricing_summary.get("property_types", []) or []
        )
        location_rates = pricing_summary.get("location_rates", []) or []
        micromarket_rates = pricing_summary.get("micromarket_rates", []) or []

        lines: list[str] = []

        if page_property_type_context.get("scope") == "specific" and page_property_type_context.get("property_type"):
            property_type = page_property_type_context.get("property_type")
            property_record = DraftGenerationService._find_property_type_record(
                residential_property_types,
                property_type,
            )

            if property_record:
                parts: list[str] = [
                    f"For {location_label}, this rate view stays focused on resale {property_type.lower()}s."
                ]
                if property_record.get("avgPrice") is not None:
                    parts.append(f"The asking-rate signal for this category is ₹{property_record['avgPrice']:,}.")
                if property_record.get("changePercent") is not None:
                    parts.append(f"The visible change signal for this category is {property_record['changePercent']}.")
                lines.append(" ".join(parts))

            comparison_row = None
            if location_rates and isinstance(location_rates[0], dict):
                comparison_row = location_rates[0]
            elif micromarket_rates and isinstance(micromarket_rates[0], dict):
                comparison_row = micromarket_rates[0]

            if comparison_row and comparison_row.get("name") and comparison_row.get("avgRate") is not None:
                lines.append(
                    f"For broader location context, {comparison_row.get('name')} is shown at ₹{comparison_row.get('avgRate'):,}."
                )

            if lines:
                return "\n\n".join(lines)

        if residential_property_types:
            visible_types = [item.get("propertyType") for item in residential_property_types[:3] if item.get("propertyType")]
            if visible_types:
                lines.append(
                    f"The current rate view for {location_label} covers residential categories such as {', '.join(visible_types)}."
                )

        comparison_row = None
        if location_rates and isinstance(location_rates[0], dict):
            comparison_row = location_rates[0]
        elif micromarket_rates and isinstance(micromarket_rates[0], dict):
            comparison_row = micromarket_rates[0]

        if comparison_row and comparison_row.get("name") and comparison_row.get("avgRate") is not None:
            row_bits = [f"{comparison_row.get('name')} is shown at ₹{comparison_row.get('avgRate'):,}"]
            if comparison_row.get("changePercentage") is not None:
                row_bits.append(f"with a change signal of {comparison_row.get('changePercentage')}")
            lines.append("For broader context, " + " and ".join(row_bits) + ".")

        if not lines:
            return (
                f"This section explains the property-type and location-rate view available for {location_label}. "
                "When those values are present, they help add context to the current asking-price picture."
            )

        return "\n\n".join(lines)

    @staticmethod
    def _build_micromarket_coverage_safe_body(content_plan: dict) -> str:
        pricing_summary = content_plan.get("data_context", {}).get("pricing_summary", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)
        location_rates = pricing_summary.get("location_rates", []) or []

        valid_rows = [
            item for item in location_rates if isinstance(item, dict) and item.get("name") and item.get("avgRate") is not None
        ]
        if not valid_rows:
            return (
                f"This section covers the city-level zone view available for {location_label}. "
                "When zone-level rates are present, they help show how asking-rate signals differ across the city."
            )

        sorted_rows = sorted(valid_rows, key=lambda item: item.get("avgRate") or 0, reverse=True)
        top_rows = sorted_rows[:4]
        top_bits = [f"{item.get('name')} at ₹{item.get('avgRate'):,}" for item in top_rows]

        premium_zone = sorted_rows[0]
        value_zone = sorted_rows[-1]

        lines: list[str] = []
        if top_bits:
            lines.append(
                f"The visible city-rate view for {location_label} includes zones such as " + ", ".join(top_bits) + "."
            )

        lines.append(
            f"Within this view, {premium_zone.get('name')} is at the higher end at ₹{premium_zone.get('avgRate'):,}, while {value_zone.get('name')} appears at the lower end at ₹{value_zone.get('avgRate'):,}."
        )

        return "\n\n".join(lines)

    @staticmethod
    def _build_safe_section_body(content_plan: dict, section_id: str) -> str | None:
        if section_id == "market_snapshot":
            return DraftGenerationService._build_market_snapshot_safe_body(content_plan)

        if section_id == "price_trends_and_rates":
            return DraftGenerationService._build_price_trends_safe_body(content_plan)

        if section_id == "review_and_rating_signals":
            return DraftGenerationService._build_review_signals_safe_body(content_plan)

        if section_id == "property_rates_ai_signals":
            return DraftGenerationService._build_property_rates_ai_safe_body(content_plan)

        if section_id == "demand_and_supply_signals":
            return DraftGenerationService._build_demand_supply_safe_body(content_plan)

        if section_id == "property_type_signals":
            return DraftGenerationService._build_property_type_signals_safe_body(content_plan)

        if section_id == "property_type_rate_snapshot":
            return DraftGenerationService._build_property_type_rate_snapshot_safe_body(content_plan)

        if section_id == "micromarket_coverage":
            return DraftGenerationService._build_micromarket_coverage_safe_body(content_plan)

        return None

    @staticmethod
    def _enforce_strict_section_bodies(
        content_plan: dict,
        sections: list[dict],
    ) -> list[dict]:
        strict_section_ids = set(settings.editorial_force_safe_sections or [])
        updated_sections: list[dict] = []

        for section in sections:
            updated = dict(section)
            section_id = updated.get("id")

            if section_id in strict_section_ids:
                safe_body = DraftGenerationService._build_safe_section_body(
                    content_plan,
                    section_id,
                )
                if safe_body is not None:
                    updated["body"] = safe_body

            updated_sections.append(updated)

        return updated_sections

    @staticmethod
    def _fallback_section_if_needed(content_plan: dict, section: dict, validation: dict) -> dict:
        section_id = section.get("id", "")
        issues = validation.get("issues", [])

        if section_id in set(settings.editorial_force_safe_sections or []):
            safe_body = DraftGenerationService._build_safe_section_body(content_plan, section_id)
            if safe_body is None:
                return section

            updated = dict(section)
            updated["body"] = safe_body
            return updated

        if not issues:
            return section

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
    def _faq_answer_for_pricing(content_plan: dict) -> str | None:
        pricing_summary = content_plan.get("data_context", {}).get("pricing_summary", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)
        asking_price = pricing_summary.get("asking_price")
        price_trend = pricing_summary.get("price_trend", []) or []

        if asking_price is None and not price_trend:
            return None

        parts: list[str] = []
        if asking_price is not None:
            parts.append(
                f"The current asking price signal for resale properties in {location_label} is ₹{asking_price:,}."
            )

        if price_trend:
            latest = price_trend[0]
            trend_bits: list[str] = []
            if latest.get("quarterName"):
                trend_bits.append(f"the latest tracked quarter is {latest['quarterName']}")
            if latest.get("locationRate") is not None:
                trend_bits.append(f"the locality-level rate in that entry is ₹{latest['locationRate']:,}")
            if latest.get("micromarketRate") is not None:
                trend_bits.append(f"the micromarket-level rate is ₹{latest['micromarketRate']:,}")
            if latest.get("cityRate") is not None:
                trend_bits.append(f"the city-level rate is ₹{latest['cityRate']:,}")
            if trend_bits:
                parts.append("The available trend view shows " + ", ".join(trend_bits) + ".")

        return " ".join(parts)

    @staticmethod
    def _faq_answer_for_inventory(content_plan: dict) -> str | None:
        listing_summary = content_plan.get("data_context", {}).get("listing_summary", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        sale_count = listing_summary.get("sale_count")
        total_listings = listing_summary.get("total_listings")
        total_projects = listing_summary.get("total_projects")

        if sale_count is None and total_listings is None and total_projects is None:
            return None

        metrics: list[str] = []
        if sale_count is not None:
            metrics.append(f"{sale_count} resale listings")
        if total_listings is not None:
            metrics.append(f"{total_listings} total listings")
        if total_projects is not None:
            metrics.append(f"{total_projects} projects")

        return (
            f"For {location_label}, the current page-level summary shows " + ", ".join(metrics) + "."
        )

    @staticmethod
    def _faq_answer_for_bhk_availability(content_plan: dict) -> str | None:
        bhk_mix = (
            content_plan.get("data_context", {}).get("distributions", {}).get("sale_unit_type_distribution", [])
            or []
        )
        location_label = DraftGenerationService._location_label(content_plan)

        if not bhk_mix:
            return None

        top_rows = bhk_mix[:4]
        pieces: list[str] = []
        for item in top_rows:
            key = item.get("key")
            doc_count = item.get("doc_count")
            if key and doc_count is not None:
                pieces.append(f"{key} with {doc_count} listings")
            elif key:
                pieces.append(str(key))

        if not pieces:
            return None

        return (
            f"The available BHK mix for resale properties in {location_label} includes {', '.join(pieces)}."
        )

    @staticmethod
    def _faq_answer_for_ready_to_move(content_plan: dict) -> str | None:
        property_status = (
            content_plan.get("data_context", {}).get("pricing_summary", {}).get("property_status", [])
            or []
        )
        location_label = DraftGenerationService._location_label(content_plan)

        if not property_status:
            return None

        ready_bucket = None
        for item in property_status:
            status = (item.get("status") or "").lower()
            if "ready" in status:
                ready_bucket = item
                break

        target = ready_bucket or property_status[0]
        status_label = target.get("status")
        units = target.get("units")
        avg_price = target.get("avgPrice")

        parts: list[str] = []
        if status_label:
            parts.append(status_label)
        if units is not None:
            parts.append(f"{units} units")
        if avg_price is not None:
            parts.append(f"average listed value of ₹{avg_price:,}")

        return (
            f"For {location_label}, one visible property-status bucket shows " + ", ".join(parts) + "."
        )

    @staticmethod
    def _faq_answer_for_nearby_localities(content_plan: dict) -> str | None:
        nearby_localities = content_plan.get("data_context", {}).get("nearby_localities", []) or []
        location_label = DraftGenerationService._location_label(content_plan)

        if not nearby_localities:
            return None

        top_rows = nearby_localities[:5]
        names = [item.get("name") for item in top_rows if item.get("name")]
        first = top_rows[0]

        parts: list[str] = []
        if names:
            parts.append(f"nearby localities such as {', '.join(names)}")
        if first.get("distance_km") is not None:
            parts.append(f"the closest visible option is {first['distance_km']:.2f} km away")
        if first.get("sale_count") is not None:
            parts.append(f"that row shows {first['sale_count']} resale listings")

        return f"Around {location_label}, the current nearby-locality view includes " + ", ".join(parts) + "."

    @staticmethod
    def _faq_answer_for_review_signals(content_plan: dict) -> str | None:
        review_summary = content_plan.get("data_context", {}).get("review_summary", {}) or {}
        ai_summary = content_plan.get("data_context", {}).get("ai_summary", {}) or {}
        overview = review_summary.get("overview", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        avg_rating = overview.get("avg_rating")
        review_count = overview.get("review_count")
        positive_tags = review_summary.get("positive_tags", []) or []
        negative_tags = review_summary.get("negative_tags", []) or []
        locality_summary = ai_summary.get("locality_summary")

        if (
            avg_rating is None
            and review_count is None
            and not positive_tags
            and not negative_tags
            and not locality_summary
        ):
            return None

        parts: list[str] = []
        if avg_rating is not None:
            parts.append(f"an average rating of {avg_rating}")
        if review_count is not None:
            parts.append(f"{review_count} reviews")
        if positive_tags:
            parts.append(f"positive tags such as {', '.join(positive_tags[:3])}")
        if negative_tags:
            parts.append(f"negative tags such as {', '.join(negative_tags[:3])}")

        answer = f"For {location_label}, the available review view shows " + ", ".join(parts) + "."
        if locality_summary:
            answer += " " + locality_summary
        return answer

    @staticmethod
    def _faq_answer_for_property_rates_ai_signals(content_plan: dict) -> str | None:
        property_rates_ai_summary = content_plan.get("data_context", {}).get("property_rates_ai_summary", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        market_snapshot = (property_rates_ai_summary.get("market_snapshot") or "").strip()
        market_strengths = property_rates_ai_summary.get("market_strengths", []) or []
        market_challenges = property_rates_ai_summary.get("market_challenges", []) or []
        investment_opportunities = property_rates_ai_summary.get("investment_opportunities", []) or []

        if (
            not market_snapshot
            and not market_strengths
            and not market_challenges
            and not investment_opportunities
        ):
            return None

        parts: list[str] = []
        if market_snapshot:
            parts.append(market_snapshot)
        if market_strengths:
            parts.append("Strengths include " + ", ".join(market_strengths[:3]) + ".")
        if market_challenges:
            parts.append("Challenges include " + ", ".join(market_challenges[:3]) + ".")
        if investment_opportunities:
            parts.append("Opportunities noted here include " + ", ".join(investment_opportunities[:3]) + ".")

        return f"For {location_label}, the market-summary notes say: " + " ".join(parts)

    @staticmethod
    def _faq_answer_for_demand_supply(content_plan: dict) -> str | None:
        demand_supply = content_plan.get("data_context", {}).get("demand_supply", {}) or {}
        listing_ranges = content_plan.get("data_context", {}).get("listing_ranges", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        unit_types = demand_supply.get("sale", {}).get("unitType", []) or []
        sale_range = listing_ranges.get("sale_listing_range", {}) or {}

        if not unit_types and not sale_range:
            return None

        details: list[str] = []
        if unit_types:
            first = unit_types[0]
            unit_name = first.get("name")
            listing = first.get("listing")
            demand_percent = first.get("demandPercent")
            supply_percent = first.get("supplyPercent")

            unit_bits: list[str] = []
            if unit_name:
                unit_bits.append(f"{unit_name}")
            if listing is not None:
                unit_bits.append(f"{listing} listings")
            if demand_percent is not None:
                unit_bits.append(f"demand share of {demand_percent}")
            if supply_percent is not None:
                unit_bits.append(f"supply share of {supply_percent}")

            if unit_bits:
                details.append(", ".join(unit_bits))

        if sale_range.get("doc_count") is not None:
            details.append(f"{sale_range['doc_count']} rows in the listing-range view")
        if sale_range.get("min_price") is not None and sale_range.get("max_price") is not None:
            details.append(
                f"a visible price span from ₹{sale_range['min_price']:,} to ₹{sale_range['max_price']:,}"
            )

        return f"For resale listings in {location_label}, the available demand and supply view shows " + ", ".join(details) + "."

    @staticmethod
    def _faq_answer_for_property_type_signals(content_plan: dict) -> str | None:
        pricing_summary = content_plan.get("data_context", {}).get("pricing_summary", {}) or {}
        distributions = content_plan.get("data_context", {}).get("distributions", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        property_types = pricing_summary.get("property_types", []) or []
        property_mix = distributions.get("sale_property_type_distribution", []) or []

        if not property_types and not property_mix:
            return None

        details: list[str] = []
        if property_types:
            first = property_types[0]
            prop = first.get("propertyType")
            avg_price = first.get("avgPrice")
            change = first.get("changePercent")

            prop_bits: list[str] = []
            if prop:
                prop_bits.append(str(prop))
            if avg_price is not None:
                prop_bits.append(f"₹{avg_price:,}")
            if change is not None:
                prop_bits.append(f"change signal of {change}")

            if prop_bits:
                details.append(", ".join(prop_bits))

        if property_mix:
            first_mix = property_mix[0]
            if first_mix.get("key") and first_mix.get("doc_count") is not None:
                details.append(f"{first_mix['key']} with {first_mix['doc_count']} rows")

        return f"For {location_label}, the current property-type view includes " + " and ".join(details) + "."

    @staticmethod
    def _faq_answer_for_price_range(content_plan: dict) -> str | None:
        listing_ranges = content_plan.get("data_context", {}).get("listing_ranges", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)
        sale_range = listing_ranges.get("sale_listing_range", {}) or {}

        if not sale_range:
            return None

        parts: list[str] = []
        if sale_range.get("doc_count") is not None:
            parts.append(f"{sale_range['doc_count']} listings in the range view")
        if sale_range.get("min_price") is not None:
            parts.append(f"a minimum listed price of ₹{sale_range['min_price']:,}")
        if sale_range.get("max_price") is not None:
            parts.append(f"a maximum listed price of ₹{sale_range['max_price']:,}")

        if not parts:
            return None

        return f"For {location_label}, the visible resale price range includes " + ", ".join(parts) + "."

    @staticmethod
    def _faq_answer_for_rera(content_plan: dict) -> str | None:
        rera_context = content_plan.get("data_context", {}).get("rera_context")
        location_label = DraftGenerationService._location_label(content_plan)

        if not isinstance(rera_context, dict) or not rera_context:
            return None

        visible_keys = [key for key, value in rera_context.items() if value not in {None, "", [], {}}]
        if not visible_keys:
            return None

        preview = ", ".join(visible_keys[:4])
        return (
            f"For {location_label}, the page includes RERA or buyer-protection related fields such as {preview}."
        )

    @staticmethod
    def _build_safe_faq_answer_for_intent(content_plan: dict, intent_id: str) -> str | None:
        mapping = {
            "pricing": DraftGenerationService._faq_answer_for_pricing,
            "inventory": DraftGenerationService._faq_answer_for_inventory,
            "bhk_availability": DraftGenerationService._faq_answer_for_bhk_availability,
            "ready_to_move": DraftGenerationService._faq_answer_for_ready_to_move,
            "nearby_localities": DraftGenerationService._faq_answer_for_nearby_localities,
            "review_signals": DraftGenerationService._faq_answer_for_review_signals,
            "property_rates_ai_signals": DraftGenerationService._faq_answer_for_property_rates_ai_signals,
            "demand_supply": DraftGenerationService._faq_answer_for_demand_supply,
            "property_type_signals": DraftGenerationService._faq_answer_for_property_type_signals,
            "price_range": DraftGenerationService._faq_answer_for_price_range,
            "rera_buyer_protection": DraftGenerationService._faq_answer_for_rera,
        }
        builder = mapping.get(intent_id)
        return builder(content_plan) if builder else None

    @staticmethod
    def _build_safe_faq_answer(content_plan: dict, question: str) -> str | None:
        lowered = question.lower()

        if "review" in lowered or "rating" in lowered:
            return DraftGenerationService._faq_answer_for_review_signals(content_plan)

        if (
            "market strengths" in lowered
            or "market challenges" in lowered
            or "opportunities" in lowered
            or "investment opportunities" in lowered
            or "property rates ai" in lowered
            or "ai market" in lowered
            or "market signals" in lowered
        ):
            return DraftGenerationService._faq_answer_for_property_rates_ai_signals(content_plan)

        if "demand" in lowered or "supply" in lowered:
            return DraftGenerationService._faq_answer_for_demand_supply(content_plan)

        if "property type" in lowered or "property-type" in lowered or "property types" in lowered:
            return DraftGenerationService._faq_answer_for_property_type_signals(content_plan)

        if "status" in lowered or "ready-to-move" in lowered or "ready to move" in lowered:
            return DraftGenerationService._faq_answer_for_ready_to_move(content_plan)

        if "price range" in lowered or ("range" in lowered and "price" in lowered):
            return DraftGenerationService._faq_answer_for_price_range(content_plan)

        if "price" in lowered or "asking" in lowered or "rate" in lowered:
            return DraftGenerationService._faq_answer_for_pricing(content_plan)

        if "how many" in lowered or "available" in lowered or "inventory" in lowered:
            return DraftGenerationService._faq_answer_for_inventory(content_plan)

        if "bhk" in lowered or "unit type" in lowered or "unit-type" in lowered:
            return DraftGenerationService._faq_answer_for_bhk_availability(content_plan)

        if "nearby" in lowered or "localities" in lowered or "locality" in lowered:
            return DraftGenerationService._faq_answer_for_nearby_localities(content_plan)

        if "rera" in lowered or "buyer-protection" in lowered or "buyer protection" in lowered:
            return DraftGenerationService._faq_answer_for_rera(content_plan)

        return None

    @staticmethod
    def _normalize_generated_faqs(content_plan: dict, faqs: list[dict]) -> list[dict]:
        del content_plan

        normalized: list[dict] = []
        seen_questions: set[str] = set()

        for faq in faqs:
            question = (faq.get("question") or "").strip()
            answer = (faq.get("answer") or "").strip()

            if not question or not answer:
                continue

            lowered = question.lower()
            if lowered in seen_questions:
                continue

            normalized.append(
                {
                    "question": question,
                    "answer": answer,
                }
            )
            seen_questions.add(lowered)

        return normalized

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
                repaired_faqs.append(
                    {
                        "question": faq.get("question"),
                        "answer": repaired["answer"],
                    }
                )
                continue

            safe_answer = DraftGenerationService._build_safe_faq_answer(
                content_plan,
                faq.get("question", ""),
            )

            if safe_answer:
                repaired_faqs.append(
                    {
                        "question": faq.get("question"),
                        "answer": safe_answer,
                    }
                )
                continue

            repaired_faqs.append(
                {
                    "question": faq.get("question"),
                    "answer": validation.get("sanitized_text") or faq.get("answer", ""),
                }
            )

        return repaired_faqs

    @staticmethod
    def _ensure_faq_coverage(content_plan: dict, faqs: list[dict]) -> list[dict]:
        normalized_faqs = DraftGenerationService._normalize_generated_faqs(content_plan, faqs)
        existing_questions = {
            item.get("question", "").strip().lower()
            for item in normalized_faqs
            if item.get("question")
        }
        ensured = list(normalized_faqs)

        for intent in content_plan.get("faq_plan", {}).get("faq_intents", []):
            question = intent.get("question_template")
            intent_id = intent.get("id", "")
            if not question:
                continue

            lowered = question.strip().lower()
            if lowered in existing_questions:
                continue

            answer = DraftGenerationService._build_safe_faq_answer_for_intent(content_plan, intent_id)
            if answer:
                ensured.append(
                    {
                        "question": question,
                        "answer": answer,
                    }
                )
                existing_questions.add(lowered)

        return ensured

    @staticmethod
    def _summarize_price_trend_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return "This table will show the latest asking-price trend when data is available."

        first = rows[0]
        parts: list[str] = []
        if first.get("quarterName") not in {None, "", "—"}:
            parts.append(f"{first['quarterName']}")
        if first.get("locationRate") not in {None, "", "—"}:
            parts.append(f"locality rate {first['locationRate']}")
        if first.get("micromarketRate") not in {None, "", "—"}:
            parts.append(f"micromarket rate {first['micromarketRate']}")
        if first.get("cityRate") not in {None, "", "—"}:
            parts.append(f"city rate {first['cityRate']}")

        return (
            "This table helps compare the latest asking-price trend with the broader local context. "
            + (f"One visible entry includes {', '.join(parts)}." if parts else "")
        )

    @staticmethod
    def _summarize_bhk_mix_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return "This table will show the BHK mix when inventory data is available."

        first = rows[0]
        lead = []
        if first.get("key") not in {None, "", "—"}:
            lead.append(str(first["key"]))
        if first.get("doc_count") not in {None, "", "—"}:
            lead.append(f"{first['doc_count']} listings")

        return (
            "This table makes it easier to see which home configurations are showing up most often. "
            + (f"For example, the first visible row shows {' with '.join(lead)}." if lead else "")
        )

    @staticmethod
    def _summarize_nearby_localities_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return "This table will show nearby localities when comparison data is available."

        first = rows[0]
        bits: list[str] = []
        if first.get("name") not in {None, "", "—"}:
            bits.append(f"{first['name']}")
        if first.get("distance_km") not in {None, "", "—"}:
            bits.append(f"{first['distance_km']} away")
        if first.get("sale_count") not in {None, "", "—"}:
            bits.append(f"with {first['sale_count']} resale listings")

        return (
            "This table helps compare nearby alternatives around the current location. "
            + (f"The first option shown is {' '.join(bits)}." if bits else "")
        )

    @staticmethod
    def _summarize_location_rates_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return "This table will show location-level asking-rate signals when data is available."

        first = rows[0]
        bits: list[str] = []
        if first.get("name") not in {None, "", "—"}:
            bits.append(f"{first['name']}")
        if first.get("avgRate") not in {None, "", "—"}:
            bits.append(f"at {first['avgRate']}")
        if first.get("changePercentage") not in {None, "", "—"}:
            bits.append(f"with a change signal of {first['changePercentage']}")

        return (
            "This table helps compare asking-rate signals across the covered locations. "
            + (f"One visible entry shows {' '.join(bits)}." if bits else "")
        )

    @staticmethod
    def _summarize_property_types_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return "This table will show property-type pricing signals when data is available."

        first = rows[0]
        bits: list[str] = []
        if first.get("propertyType") not in {None, "", "—"}:
            bits.append(str(first["propertyType"]))
        if first.get("avgPrice") not in {None, "", "—"}:
            bits.append(f"at {first['avgPrice']}")
        if first.get("changePercent") not in {None, "", "—"}:
            bits.append(f"with a change signal of {first['changePercent']}")

        return (
            "This table helps compare how different residential property types appear in the pricing view. "
            + (f"The first row shown is {' '.join(bits)}." if bits else "")
        )

    @staticmethod
    def _summarize_property_status_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return "This table will show property-status buckets when data is available."

        first = rows[0]
        bits: list[str] = []
        if first.get("status") not in {None, "", "—"}:
            bits.append(str(first["status"]))
        if first.get("units") not in {None, "", "—"}:
            bits.append(f"with {first['units']} units")
        if first.get("avgPrice") not in {None, "", "—"}:
            bits.append(f"and an average listed value of {first['avgPrice']}")

        return (
            "This table helps explain which status buckets are visible in the resale inventory. "
            + (f"One visible row shows {' '.join(bits)}." if bits else "")
        )

    @staticmethod
    def _summarize_coverage_summary_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return "This table will show the page-level coverage summary when data is available."

        first = rows[0]
        bits: list[str] = []
        if first.get("sale_count") not in {None, "", "—"}:
            bits.append(f"{first['sale_count']} resale listings")
        if first.get("total_listings") not in {None, "", "—"}:
            bits.append(f"{first['total_listings']} total listings")
        if first.get("total_projects") not in {None, "", "—"}:
            bits.append(f"{first['total_projects']} total projects")

        return (
            "This table gives a quick view of the page scale. "
            + (f"The current summary includes {', '.join(bits)}." if bits else "")
        )

    @staticmethod
    def _summarize_table(table: dict) -> str:
        table_id = table.get("id")

        mapping = {
            "price_trend_table": DraftGenerationService._summarize_price_trend_table,
            "sale_unit_type_distribution_table": DraftGenerationService._summarize_bhk_mix_table,
            "nearby_localities_table": DraftGenerationService._summarize_nearby_localities_table,
            "location_rates_table": DraftGenerationService._summarize_location_rates_table,
            "property_types_table": DraftGenerationService._summarize_property_types_table,
            "property_status_table": DraftGenerationService._summarize_property_status_table,
            "coverage_summary_table": DraftGenerationService._summarize_coverage_summary_table,
        }

        builder = mapping.get(table_id)
        if builder:
            return builder(table)

        rows = table.get("rows", []) or []
        title = table.get("title", "This table")
        if not rows:
            return f"{title} will display additional page data when available."

        return f"{title} gives a compact view of the values behind this page."

    @staticmethod
    def _generate_table_summary(table: dict, content_plan: dict, client: OpenAIClient) -> str:
        system_prompt, user_prompt = PromptBuilder.table_summary_prompt(
            table,
            content_plan["entity"],
            content_plan.get("planning_signals", {}),
        )
        response = client.generate_json(system_prompt, user_prompt)
        if isinstance(response, dict):
            summary = response.get("summary")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()
        return DraftGenerationService._summarize_table(table)

    @staticmethod
    def _attach_table_summaries(
        tables: list[dict],
        content_plan: dict,
        client: OpenAIClient,
    ) -> list[dict]:
        enriched: list[dict] = []
        for table in tables:
            updated = dict(table)
            updated["summary"] = DraftGenerationService._generate_table_summary(
                updated,
                content_plan,
                client,
            )
            enriched.append(updated)
        return enriched

    @staticmethod
    def _build_base_draft(
        content_plan: dict,
        keyword_intelligence_version: str,
        metadata: dict,
        sections: list[dict],
        faqs: list[dict],
        client: OpenAIClient,
    ) -> dict:
        tables = TableRenderer.render_all(content_plan["table_plan"], content_plan["data_context"])
        tables = DraftGenerationService._attach_table_summaries(tables, content_plan, client)
        internal_links = DraftGenerationService._resolve_internal_links(content_plan["internal_links_plan"])

        return {
            "version": "v2.6",
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
        sections = DraftGenerationService._enforce_strict_section_bodies(content_plan, sections)

        faqs = DraftGenerationService._generate_faqs(content_plan, client)
        faqs = DraftGenerationService._ensure_faq_coverage(content_plan, faqs)

        draft = DraftGenerationService._build_base_draft(
            content_plan=content_plan,
            keyword_intelligence_version=keyword_intelligence["version"],
            metadata=metadata,
            sections=sections,
            faqs=faqs,
            client=client,
        )

        validation_report = FactualValidator.validate_draft(draft)
        validation_history = [
            DraftGenerationService._build_validation_history_entry("initial_generation", 0, validation_report)
        ]

        repair_passes = 0
        while not validation_report["passed"] and repair_passes < settings.draft_repair_max_passes:
            metadata = DraftGenerationService._repair_metadata(content_plan, draft["metadata"], validation_report, client)
            sections = DraftGenerationService._repair_sections(
                content_plan,
                draft["sections"],
                validation_report,
                client,
            )
            sections = DraftGenerationService._ensure_planned_sections_present(content_plan, sections)
            sections = DraftGenerationService._enforce_strict_section_bodies(content_plan, sections)
            faqs = DraftGenerationService._repair_faqs(content_plan, draft["faqs"], validation_report, client)
            faqs = DraftGenerationService._ensure_faq_coverage(content_plan, faqs)

            draft = DraftGenerationService._build_base_draft(
                content_plan=content_plan,
                keyword_intelligence_version=keyword_intelligence["version"],
                metadata=metadata,
                sections=sections,
                faqs=faqs,
                client=client,
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
        sanitized["needs_review"] = not bool(validation_report.get("passed"))
        sanitized["markdown_draft"] = MarkdownRenderer.render(sanitized)
        return sanitized