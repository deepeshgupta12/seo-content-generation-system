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
    def _build_property_rates_ai_safe_body(content_plan: dict) -> str:
        entity = content_plan.get("entity", {}) or {}
        entity_name = entity.get("entity_name", "this location")
        city_name = entity.get("city_name", "")
        location_label = (
            f"{entity_name}, {city_name}"
            if city_name and city_name != entity_name
            else entity_name
        )

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
            return (
                f"No structured market-summary inputs are currently available for {location_label} "
                f"in the property-rates source block for this page."
            )

        paragraphs: list[str] = []

        if market_snapshot:
            paragraphs.append(market_snapshot)

        if market_strengths:
            paragraphs.append("**Strengths:** " + "; ".join(market_strengths) + ".")

        if market_challenges:
            paragraphs.append("**Challenges:** " + "; ".join(market_challenges) + ".")

        if investment_opportunities:
            paragraphs.append("**Opportunities:** " + "; ".join(investment_opportunities) + ".")

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
                f"This page is focused on resale {property_type.lower()} options in {location_label}, so the visible market context should be read through that residential category rather than across unrelated property types."
            ]

            detail_parts: list[str] = []
            if sale_count is not None:
                detail_parts.append(f"{sale_count} visible resale listings are currently represented on the page")
            if property_count is not None:
                detail_parts.append(f"the structured property-type mix shows {property_count} rows aligned to this category")
            if detail_parts:
                lines.append("At a page level, " + ", ".join(detail_parts) + ".")

            if property_record:
                rate_parts: list[str] = []
                if property_record.get("avgPrice") is not None:
                    rate_parts.append(f"the visible asking-rate signal for this category is ₹{property_record['avgPrice']:,}")
                if property_record.get("changePercent") is not None:
                    rate_parts.append(f"the current rate-change signal is {property_record['changePercent']}")
                if rate_parts:
                    lines.append("Within the available structured rate snapshot, " + ", ".join(rate_parts) + ".")

            return " ".join(lines)

        visible_residential_types = [item.get("propertyType") for item in residential_property_types[:4] if item.get("propertyType")]
        if not visible_residential_types and sale_count is None:
            return (
                f"This section summarises the grounded resale market inputs available for {location_label}. "
                f"When structured residential property-type rows are available, they can be used to explain how the visible inventory is distributed."
            )

        lines: list[str] = []
        if visible_residential_types:
            lines.append(
                f"The visible resale market in {location_label} currently spans residential categories such as {', '.join(visible_residential_types)}."
            )
        if sale_count is not None:
            lines.append(
                f"The page-level listing summary currently shows {sale_count} visible resale listings, giving a grounded sense of the inventory currently represented here."
            )

        return " ".join(lines)

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
                f"For {location_label}, the visible property-type narrative on this page should stay focused on resale {property_type.lower()} inventory."
            ]

            if property_count is not None:
                lines.append(
                    f"The structured property-type mix currently shows {property_count} rows tied to this category in the visible resale dataset."
                )

            if property_record:
                record_parts: list[str] = []
                if property_record.get("avgPrice") is not None:
                    record_parts.append(f"the asking-rate signal currently visible for this category is ₹{property_record['avgPrice']:,}")
                if property_record.get("changePercent") is not None:
                    record_parts.append(f"the current rate-change signal is {property_record['changePercent']}")
                if record_parts:
                    lines.append("In the available rate snapshot, " + ", ".join(record_parts) + ".")

            return " ".join(lines)

        if not residential_property_types and not property_mix:
            return (
                "Property-type signals are shown only when grounded residential source inputs are available. "
                "Where present, this section summarises residential categories and mix without ranking one type over another."
            )

        visible_names = [item.get("propertyType") for item in residential_property_types[:4] if item.get("propertyType")]
        lines: list[str] = []

        if visible_names:
            lines.append(
                f"For {location_label}, the visible residential property mix currently includes categories such as {', '.join(visible_names)}."
            )

        if property_mix:
            first_match = None
            for item in property_mix:
                key = str(item.get("key") or "")
                if "flat" in key.lower() or "apartment" in key.lower() or "villa" in key.lower() or "builder" in key.lower():
                    first_match = item
                    break
            if first_match and first_match.get("doc_count") is not None:
                lines.append(
                    f"Within the structured mix, {first_match.get('key')} currently shows {first_match.get('doc_count')} visible rows."
                )

        return " ".join(lines)

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
                    f"For {location_label}, this page keeps the rate snapshot focused on resale {property_type.lower()}s."
                ]
                if property_record.get("avgPrice") is not None:
                    parts.append(
                        f"The visible asking-rate signal for this category is currently ₹{property_record['avgPrice']:,}."
                    )
                if property_record.get("changePercent") is not None:
                    parts.append(
                        f"The current rate-change signal for this category is {property_record['changePercent']}."
                    )
                lines.append(" ".join(parts))

            comparison_row = None
            if location_rates and isinstance(location_rates[0], dict):
                comparison_row = location_rates[0]
            elif micromarket_rates and isinstance(micromarket_rates[0], dict):
                comparison_row = micromarket_rates[0]

            if comparison_row and comparison_row.get("name") and comparison_row.get("avgRate") is not None:
                lines.append(
                    f"For broader location context, {comparison_row.get('name')} is currently shown at ₹{comparison_row.get('avgRate'):,} in the visible rate table."
                )

            if lines:
                return " ".join(lines)

        if residential_property_types:
            visible_types = [item.get("propertyType") for item in residential_property_types[:3] if item.get("propertyType")]
            if visible_types:
                lines.append(
                    f"The visible residential rate snapshot for {location_label} currently covers categories such as {', '.join(visible_types)}."
                )

        comparison_row = None
        if location_rates and isinstance(location_rates[0], dict):
            comparison_row = location_rates[0]
        elif micromarket_rates and isinstance(micromarket_rates[0], dict):
            comparison_row = micromarket_rates[0]

        if comparison_row and comparison_row.get("name") and comparison_row.get("avgRate") is not None:
            row_bits = [f"{comparison_row.get('name')} is shown at ₹{comparison_row.get('avgRate'):,}"]
            if comparison_row.get("changePercentage") is not None:
                row_bits.append(f"with a visible change signal of {comparison_row.get('changePercentage')}")
            lines.append("For broader rate context, " + ", ".join(row_bits) + ".")

        if not lines:
            return (
                "Property-type rate snapshot signals are shown only when grounded residential source inputs are available. "
                "Where present, this section summarises relevant property-type and location-rate fields in a more readable format."
            )

        return " ".join(lines)
    
    @staticmethod
    def _build_micromarket_coverage_safe_body(content_plan: dict) -> str:
        pricing_summary = content_plan.get("data_context", {}).get("pricing_summary", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)
        location_rates = pricing_summary.get("location_rates", []) or []

        valid_rows = [item for item in location_rates if isinstance(item, dict) and item.get("name") and item.get("avgRate") is not None]
        if not valid_rows:
            return (
                f"This section summarises the visible city-level zone coverage currently available for {location_label}. "
                f"When grounded zone-level rate rows are present, they can be used to explain how pricing varies across the city."
            )

        sorted_rows = sorted(valid_rows, key=lambda item: item.get("avgRate") or 0, reverse=True)
        top_rows = sorted_rows[:4]
        top_bits = [f"{item.get('name')} at ₹{item.get('avgRate'):,}" for item in top_rows if item.get("name") and item.get("avgRate") is not None]

        premium_zone = sorted_rows[0]
        value_zone = sorted_rows[-1]

        lines: list[str] = []
        if top_bits:
            lines.append(
                f"Resale activity across {location_label} is currently represented through visible city zones such as "
                + ", ".join(top_bits)
                + "."
            )

        lines.append(
            f"At the higher visible end of the city-rate snapshot, {premium_zone.get('name')} sits at ₹{premium_zone.get('avgRate'):,}, "
            f"while {value_zone.get('name')} is currently shown at ₹{value_zone.get('avgRate'):,} on the relatively lower side of the visible range."
        )

        lines.append(
            f"This creates a simple buyer segmentation layer within the current dataset: higher-budget buyers may start with {premium_zone.get('name')}, "
            f"while buyers comparing relatively lower visible rate bands may also look at {value_zone.get('name')}."
        )

        return " ".join(lines)

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
        strict_section_ids = {
            "market_snapshot",
            "property_rates_ai_signals",
            "property_type_signals",
            "property_type_rate_snapshot",
            "micromarket_coverage",
        }
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

        if section_id == "property_rates_ai_signals":
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
    def _location_label(content_plan: dict) -> str:
        entity = content_plan.get("entity", {}) or {}
        entity_name = entity.get("entity_name", "this location")
        city_name = entity.get("city_name", "")
        return f"{entity_name}, {city_name}" if city_name and city_name != entity_name else entity_name

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
                f"The grounded asking price signal for resale properties in {location_label} is ₹{asking_price:,}."
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
                parts.append("In the available trend inputs, " + ", ".join(trend_bits) + ".")

        parts.append(
            "This answer stays limited to the asking-price and price-trend fields available in the current structured dataset."
        )
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

        parts: list[str] = [f"For {location_label}, the grounded listing summary shows"]

        metrics: list[str] = []
        if sale_count is not None:
            metrics.append(f"{sale_count} visible resale listings")
        if total_listings is not None:
            metrics.append(f"{total_listings} total listings in the broader visible page inventory")
        if total_projects is not None:
            metrics.append(f"{total_projects} total projects")

        parts.append(", ".join(metrics) + ".")
        parts.append(
            "This helps users distinguish the active resale count from the wider page-level coverage available in the current dataset."
        )
        return " ".join(parts)

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
            f"The visible BHK mix for resale properties in {location_label} is derived from the structured unit-type distribution on this page. "
            f"The leading configurations currently shown include {', '.join(pieces)}. "
            "This gives buyers a clearer view of which home formats are most visibly represented in the current resale dataset."
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
            parts.append(f"the visible status bucket includes {status_label}")
        if units is not None:
            parts.append(f"with {units} units")
        if avg_price is not None:
            parts.append(f"and an average listed value of ₹{avg_price:,}")

        return (
            f"For {location_label}, the grounded property-status inputs show that "
            + ", ".join(parts)
            + ". This helps users understand whether ready-to-move or similar status buckets are visible in the current resale dataset."
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
            parts.append(f"the nearby localities currently surfaced include {', '.join(names)}")
        if first.get("distance_km") is not None:
            parts.append(f"the closest visible entry is {first['distance_km']:.2f} km away")
        if first.get("sale_count") is not None:
            parts.append(f"and the first nearby row shows {first['sale_count']} resale listings")

        return (
            f"For buyers exploring alternatives around {location_label}, the grounded nearby-locality dataset shows that "
            + ", ".join(parts)
            + ". These nearby references are useful for comparing resale options in adjacent micro-areas without leaving the page context."
        )

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

        parts: list[str] = [f"The grounded review layer for {location_label} currently shows"]
        details: list[str] = []

        if avg_rating is not None:
            details.append(f"an average rating of {avg_rating}")
        if review_count is not None:
            details.append(f"{review_count} reviews")

        if details:
            parts.append(", ".join(details) + ".")

        if positive_tags:
            parts.append(f"Visible positive tags include {', '.join(positive_tags[:3])}.")
        if negative_tags:
            parts.append(f"Visible negative tags include {', '.join(negative_tags[:3])}.")
        if locality_summary:
            parts.append("The page also includes an AI summary field for the locality.")

        parts.append(
            "These inputs are presented as review and tag signals only, without converting them into unsupported editorial claims."
        )
        return " ".join(parts)
    
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
            parts.append(
                f"For {location_label}, the structured market-summary layer includes a snapshot that reads: {market_snapshot}"
            )

        detail_parts: list[str] = []
        if market_strengths:
            detail_parts.append(f"strengths such as {', '.join(market_strengths[:3])}")
        if market_challenges:
            detail_parts.append(f"challenges such as {', '.join(market_challenges[:3])}")
        if investment_opportunities:
            detail_parts.append(f"opportunity cues such as {', '.join(investment_opportunities[:3])}")

        if detail_parts:
            parts.append("It also highlights " + ", ".join(detail_parts) + ".")

        parts.append(
            "These signals are presented as grounded market-summary notes only, so they should be read as descriptive inputs rather than promotional promises."
        )

        return " ".join(parts)

    @staticmethod
    def _faq_answer_for_demand_supply(content_plan: dict) -> str | None:
        demand_supply = content_plan.get("data_context", {}).get("demand_supply", {}) or {}
        listing_ranges = content_plan.get("data_context", {}).get("listing_ranges", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        unit_types = demand_supply.get("sale", {}).get("unitType", []) or []
        sale_range = listing_ranges.get("sale_listing_range", {}) or {}

        if not unit_types and not sale_range:
            return None

        parts: list[str] = [f"For resale listings in {location_label}, the visible demand-supply inputs show"]

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
                unit_bits.append(f"demand percent of {demand_percent}")
            if supply_percent is not None:
                unit_bits.append(f"supply percent of {supply_percent}")

            if unit_bits:
                details.append(", ".join(unit_bits))

        if sale_range.get("doc_count") is not None:
            details.append(f"a listing-range dataset covering {sale_range['doc_count']} records")
        if sale_range.get("min_price") is not None and sale_range.get("max_price") is not None:
            details.append(
                f"a visible price span from ₹{sale_range['min_price']:,} to ₹{sale_range['max_price']:,}"
            )

        parts.append(", ".join(details) + ".")
        parts.append(
            "This helps explain how supply, unit-type mix, and listing spread are represented in the current structured resale dataset."
        )
        return " ".join(parts)

    @staticmethod
    def _faq_answer_for_property_type_signals(content_plan: dict) -> str | None:
        pricing_summary = content_plan.get("data_context", {}).get("pricing_summary", {}) or {}
        distributions = content_plan.get("data_context", {}).get("distributions", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)

        property_types = pricing_summary.get("property_types", []) or []
        property_mix = distributions.get("sale_property_type_distribution", []) or []

        if not property_types and not property_mix:
            return None

        parts: list[str] = [f"For {location_label}, the grounded property-type layer shows"]

        details: list[str] = []
        if property_types:
            first = property_types[0]
            prop = first.get("propertyType")
            avg_price = first.get("avgPrice")
            change = first.get("changePercent")

            prop_bits: list[str] = []
            if prop:
                prop_bits.append(f"{prop} in the visible property-type rate inputs")
            if avg_price is not None:
                prop_bits.append(f"average listed value of ₹{avg_price:,}")
            if change is not None:
                prop_bits.append(f"change percent of {change}")

            if prop_bits:
                details.append(", ".join(prop_bits))

        if property_mix:
            first_mix = property_mix[0]
            if first_mix.get("key") and first_mix.get("doc_count") is not None:
                details.append(
                    f"{first_mix['key']} with a document count of {first_mix['doc_count']} in the visible property-type mix"
                )

        parts.append(", ".join(details) + ".")
        parts.append(
            "These fields help explain how the current resale stock is distributed across available property formats without ranking one type over another."
        )
        return " ".join(parts)

    @staticmethod
    def _faq_answer_for_price_range(content_plan: dict) -> str | None:
        listing_ranges = content_plan.get("data_context", {}).get("listing_ranges", {}) or {}
        location_label = DraftGenerationService._location_label(content_plan)
        sale_range = listing_ranges.get("sale_listing_range", {}) or {}

        if not sale_range:
            return None

        parts: list[str] = []
        if sale_range.get("doc_count") is not None:
            parts.append(f"the visible resale price-range dataset covers {sale_range['doc_count']} listings")
        if sale_range.get("min_price") is not None:
            parts.append(f"the minimum listed price is ₹{sale_range['min_price']:,}")
        if sale_range.get("max_price") is not None:
            parts.append(f"the maximum listed price is ₹{sale_range['max_price']:,}")

        if not parts:
            return None

        return (
            f"For {location_label}, the grounded listing-range inputs show that "
            + ", ".join(parts)
            + ". This answer is based only on the structured price-range values available in the current resale dataset."
        )

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
            f"The page for {location_label} includes grounded buyer-protection or RERA-related fields in its structured source layer. "
            f"Visible field groups currently include {preview}. "
            "These details are surfaced only when present in the input data and should be read as source-backed reference information."
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
            return (
                "This table is reserved for the recent resale price trend visible on the page. "
                "When trend rows are available, it helps explain how the current asking-price signal compares with the surrounding market context over time."
            )

        first = rows[0]
        parts: list[str] = []
        if first.get("quarterName") not in {None, "", "—"}:
            parts.append(f"in the latest visible quarter, {first['quarterName']}")
        if first.get("locationRate") not in {None, "", "—"}:
            parts.append(f"the locality rate is {first['locationRate']}")
        if first.get("micromarketRate") not in {None, "", "—"}:
            parts.append(f"the micromarket rate is {first['micromarketRate']}")
        if first.get("cityRate") not in {None, "", "—"}:
            parts.append(f"the city rate is {first['cityRate']}")

        return (
            "This table shows the recent resale price trend captured for the page and helps place the current asking-price signal in a broader local context. "
            + ("Currently, " + ", ".join(parts) + ". " if parts else "")
            + "It is useful for comparing the visible locality-level pricing signal with micromarket or city-level benchmarks where those fields are available."
        )

    @staticmethod
    def _summarize_bhk_mix_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return (
                "This table is intended to show the visible BHK mix for resale listings on the page. "
                "When rows are available, it helps explain which home configurations appear most prominently in the current inventory."
            )

        first = rows[0]
        lead = []
        if first.get("key") not in {None, "", "—"}:
            lead.append(str(first["key"]))
        if first.get("doc_count") not in {None, "", "—"}:
            lead.append(f"{first['doc_count']} listings")

        return (
            "This table breaks down the visible resale inventory by BHK type so users can quickly understand which configurations are most strongly represented. "
            + (f"The leading visible row currently shows {' with '.join(lead)}. " if lead else "")
            + "That makes the inventory mix easier to scan before moving deeper into individual listings."
        )

    @staticmethod
    def _summarize_nearby_localities_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return (
                "This table is designed to highlight nearby localities that can be compared alongside the current page location. "
                "When rows are available, it helps users review alternate areas, distance, visible resale counts, and pricing signals together."
            )

        first = rows[0]
        bits: list[str] = []
        if first.get("name") not in {None, "", "—"}:
            bits.append(f"{first['name']}")
        if first.get("distance_km") not in {None, "", "—"}:
            bits.append(f"{first['distance_km']} away")
        if first.get("sale_count") not in {None, "", "—"}:
            bits.append(f"with {first['sale_count']} resale listings")

        return (
            "This table highlights nearby localities that buyers can compare with the current page location when exploring alternate resale options. "
            + (f"The first visible nearby option is {' '.join(bits)}. " if bits else "")
            + "It is especially useful for checking whether nearby areas offer different inventory depth or pricing signals within a short distance."
        )

    @staticmethod
    def _summarize_location_rates_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return (
                "This table is meant to show location-level rate signals within the broader resale context. "
                "When available, it helps compare how visible rate inputs differ across covered sub-areas."
            )

        first = rows[0]
        bits: list[str] = []
        if first.get("name") not in {None, "", "—"}:
            bits.append(f"{first['name']}")
        if first.get("avgRate") not in {None, "", "—"}:
            bits.append(f"at {first['avgRate']}")
        if first.get("changePercentage") not in {None, "", "—"}:
            bits.append(f"with a change signal of {first['changePercentage']}")

        return (
            "This table compares visible rate signals across covered local pockets, making it easier to review how sub-area pricing inputs are distributed. "
            + (f"The first visible row shows {' '.join(bits)}. " if bits else "")
            + "That gives additional context beyond the main page-level asking-price signal."
        )

    @staticmethod
    def _summarize_property_types_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return (
                "This table is intended to show property-type level pricing signals for the current resale page. "
                "When rows are present, it helps explain how different formats are represented in the structured dataset."
            )

        first = rows[0]
        bits: list[str] = []
        if first.get("propertyType") not in {None, "", "—"}:
            bits.append(str(first["propertyType"]))
        if first.get("avgPrice") not in {None, "", "—"}:
            bits.append(f"at {first['avgPrice']}")
        if first.get("changePercent") not in {None, "", "—"}:
            bits.append(f"with a change signal of {first['changePercent']}")

        return (
            "This table shows the visible pricing snapshot by property type, which helps explain how different inventory formats appear in the resale dataset. "
            + (f"The leading row currently shows {' '.join(bits)}. " if bits else "")
            + "It is useful for understanding property-format representation without turning those signals into ranking or recommendation."
        )

    @staticmethod
    def _summarize_property_status_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return (
                "This table is meant to show visible resale inventory by status or readiness bucket. "
                "When available, it helps users understand whether ready-to-move and other status groupings are present in the structured source inputs."
            )

        first = rows[0]
        bits: list[str] = []
        if first.get("status") not in {None, "", "—"}:
            bits.append(str(first["status"]))
        if first.get("units") not in {None, "", "—"}:
            bits.append(f"with {first['units']} units")
        if first.get("avgPrice") not in {None, "", "—"}:
            bits.append(f"and an average listed value of {first['avgPrice']}")

        return (
            "This table summarises the visible property-status buckets captured for the page, which helps explain readiness-level distribution in the resale inventory. "
            + (f"The first visible status row shows {' '.join(bits)}. " if bits else "")
            + "That provides a quick way to inspect how status and pricing signals appear together in the current dataset."
        )

    @staticmethod
    def _summarize_coverage_summary_table(table: dict) -> str:
        rows = table.get("rows", []) or []
        if not rows:
            return (
                "This table is designed to provide a compact coverage snapshot for the page. "
                "When values are available, it helps users review listing and project scale at a glance."
            )

        first = rows[0]
        bits: list[str] = []
        if first.get("sale_count") not in {None, "", "—"}:
            bits.append(f"{first['sale_count']} resale listings")
        if first.get("total_listings") not in {None, "", "—"}:
            bits.append(f"{first['total_listings']} total listings")
        if first.get("total_projects") not in {None, "", "—"}:
            bits.append(f"{first['total_projects']} total projects")

        return (
            "This table gives a compact view of page-level coverage, making it easier to understand how much resale inventory is represented overall. "
            + (f"The visible summary currently shows {', '.join(bits)}. " if bits else "")
            + "It works as a quick reference point before moving into detailed sections and listing-level exploration."
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
            return (
                f"{title} is included as a structured reference block for this page. "
                "When source-backed rows are available, it helps explain the visible inventory or pricing context in a more scannable format."
            )

        return (
            f"{title} provides a structured snapshot of source-backed values used in the draft. "
            "It is included to make the visible inventory, pricing, or locality signals easier to review alongside the narrative sections."
        )

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