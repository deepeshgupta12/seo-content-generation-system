from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from seo_content_engine.core.config import settings
from seo_content_engine.domain.enums import PageType
from seo_content_engine.utils.formatters import slugify


class ContentPlanBuilder:
    @staticmethod
    def _top_keywords(records: list[dict], limit: int = 5) -> list[str]:
        return [record["keyword"] for record in records[:limit] if record.get("keyword")]

    @staticmethod
    def _dedupe_metadata_keywords(keywords: list[str]) -> list[str]:
        deduped: list[str] = []
        seen_signatures: set[tuple[str, ...]] = set()

        for keyword in keywords:
            signature = tuple(sorted(set(keyword.lower().split())))
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            deduped.append(keyword)

        return deduped

    @staticmethod
    def _entity_label_parts(entity: dict) -> tuple[str, str]:
        entity_name = (entity.get("entity_name") or "").strip()
        city_name = (entity.get("city_name") or entity_name).strip()
        if not entity_name:
            entity_name = city_name
        if not city_name:
            city_name = entity_name
        return entity_name, city_name

    @staticmethod
    def _display_location(entity: dict) -> str:
        entity_name, city_name = ContentPlanBuilder._entity_label_parts(entity)
        if entity_name.lower() == city_name.lower():
            return entity_name
        return f"{entity_name}, {city_name}"

    @staticmethod
    def _metadata_whitelist_filter(keywords: list[str], entity: dict) -> list[str]:
        entity_name, city_name = ContentPlanBuilder._entity_label_parts(entity)
        entity_name = entity_name.lower()
        city_name = city_name.lower()

        allowed: list[str] = []
        for keyword in keywords:
            lowered = keyword.lower()
            if entity_name and entity_name not in lowered:
                continue
            if city_name and city_name not in lowered and f"{entity_name} {city_name}" not in lowered:
                continue
            if "rent" in lowered or "rental" in lowered or "lease" in lowered:
                continue
            allowed.append(keyword)

        return allowed

    @staticmethod
    def _select_metadata_keywords(keyword_clusters: dict, entity: dict) -> list[str]:
        selected: list[str] = []

        exact_match_keywords = keyword_clusters.get("exact_match_keywords", [])
        secondary_keywords = keyword_clusters.get("secondary_keywords", [])
        metadata_keywords = keyword_clusters.get("metadata_keywords", [])

        for record in exact_match_keywords[: settings.keyword_metadata_exact_match_max_count]:
            keyword = record.get("keyword")
            if keyword and keyword not in selected:
                selected.append(keyword)

        for record in secondary_keywords:
            keyword = record.get("keyword")
            if not keyword:
                continue
            if keyword not in selected:
                selected.append(keyword)
            if len(selected) >= settings.keyword_metadata_max_count:
                break

        for keyword in metadata_keywords:
            if keyword not in selected:
                selected.append(keyword)
            if len(selected) >= settings.keyword_metadata_max_count:
                break

        selected = ContentPlanBuilder._dedupe_metadata_keywords(selected)
        selected = ContentPlanBuilder._metadata_whitelist_filter(selected, entity)
        return selected[: settings.keyword_metadata_max_count]

    @staticmethod
    def _extract_rera_context(normalized: dict) -> dict[str, Any] | None:
        possible_sources = [
            normalized.get("rera"),
            normalized.get("rera_details"),
            normalized.get("buyer_protection"),
            normalized.get("legal"),
            normalized.get("pricing_summary", {}).get("rera"),
            normalized.get("pricing_summary", {}).get("rera_details"),
            normalized.get("raw_source_meta", {}).get("rera"),
        ]
        for item in possible_sources:
            if isinstance(item, dict) and item:
                return item
        return None

    @staticmethod
    def _build_refresh_plan(raw_source_meta: dict) -> dict:
        return {
            "enable_last_updated_note": True,
            "generated_at_source": "content_plan.generated_at",
            "raw_source_meta_available": bool(raw_source_meta),
            "raw_source_signals": raw_source_meta,
        }

    @staticmethod
    def _build_metadata_plan(entity: dict, keyword_clusters: dict, raw_source_meta: dict) -> dict:
        entity_name, city_name = ContentPlanBuilder._entity_label_parts(entity)
        location_label = ContentPlanBuilder._display_location(entity)

        primary_keyword = keyword_clusters.get("primary_keyword")
        primary_keyword_text = (
            primary_keyword["keyword"] if primary_keyword else f"resale properties in {location_label}"
        )

        metadata_keywords = ContentPlanBuilder._select_metadata_keywords(keyword_clusters, entity)
        title_candidates = [
            f"Resale Properties in {location_label} | Square Yards",
            f"{location_label} Resale Properties for Sale | Square Yards",
            f"Flats for Sale in {location_label} | Square Yards",
            f"Property for Sale in {location_label} | Resale Listings | Square Yards",
        ]

        description_candidates = [
            f"Explore resale properties in {location_label} with prices, BHK options, nearby localities, and current market signals on Square Yards.",
            f"Find flats and resale properties in {location_label} with price trends, inventory mix, and nearby area insights on Square Yards.",
            f"Browse resale listings in {location_label} with rates, property mix, and key buying insights on Square Yards.",
            f"Check resale property options in {location_label} with asking price trends, BHK availability, locality comparisons, and buyer-focused data on Square Yards.",
        ]

        canonical_pricing = {
            "metric_name": "asking_price",
            "label": "asking price",
            "value": entity.get("canonical_asking_price"),
        }

        return {
            "primary_keyword": primary_keyword_text,
            "supporting_keywords": metadata_keywords,
            "recommended_h1": f"Resale Properties in {location_label}",
            "recommended_slug": slugify(f"resale-properties-{entity_name}-{city_name}"),
            "title_candidates": title_candidates,
            "meta_description_candidates": description_candidates,
            "canonical_pricing_metric": canonical_pricing,
            "refresh_plan": ContentPlanBuilder._build_refresh_plan(raw_source_meta),
        }

    @staticmethod
    def _build_table_plan(page_type: PageType, normalized: dict) -> list[dict]:
        tables = [
            {
                "id": "price_trend_table",
                "title": "Price Trend Snapshot",
                "source_data_path": "pricing_summary.price_trend",
                "render_type": "deterministic",
                "columns": ["quarterName", "locationRate", "micromarketRate", "cityRate"],
                "summary_instruction": (
                    "Summarize what this table covers, what a reviewer can learn from it, "
                    "and mention the first visible row using grounded values only."
                ),
            },
            {
                "id": "sale_unit_type_distribution_table",
                "title": "Available BHK Mix",
                "source_data_path": "distributions.sale_unit_type_distribution",
                "render_type": "deterministic",
                "columns": ["key", "doc_count"],
                "summary_instruction": (
                    "Explain that this table helps reviewers understand the visible BHK mix "
                    "and reference the first row with grounded values only."
                ),
            },
            {
                "id": "nearby_localities_table",
                "title": "Nearby Localities to Explore",
                "source_data_path": "nearby_localities",
                "render_type": "deterministic",
                "columns": ["name", "distance_km", "sale_count", "sale_avg_price_per_sqft", "url"],
                "summary_instruction": (
                    "Explain that this table highlights nearby alternatives and mention the first row "
                    "with grounded values only."
                ),
            },
        ]

        location_rates = normalized.get("pricing_summary", {}).get("location_rates", [])
        if location_rates:
            tables.append(
                {
                    "id": "location_rates_table",
                    "title": "Location Rate Snapshot",
                    "source_data_path": "pricing_summary.location_rates",
                    "render_type": "deterministic",
                    "columns": ["name", "avgRate", "changePercentage"],
                    "summary_instruction": (
                        "Explain that this table compares rate signals across covered locations "
                        "and reference the first visible row using grounded values only."
                    ),
                }
            )

        property_types = normalized.get("pricing_summary", {}).get("property_types", [])
        if property_types:
            tables.append(
                {
                    "id": "property_types_table",
                    "title": "Property Type Rate Snapshot",
                    "source_data_path": "pricing_summary.property_types",
                    "render_type": "deterministic",
                    "columns": ["propertyType", "avgPrice", "changePercent"],
                    "summary_instruction": (
                        "Explain what property-type pricing signals are visible here and mention the first row "
                        "with grounded values only."
                    ),
                }
            )

        property_status = normalized.get("pricing_summary", {}).get("property_status", [])
        if property_status:
            tables.append(
                {
                    "id": "property_status_table",
                    "title": "Property Status Snapshot",
                    "source_data_path": "pricing_summary.property_status",
                    "render_type": "deterministic",
                    "columns": ["status", "units", "avgPrice"],
                    "summary_instruction": (
                        "Explain that this table shows visible readiness or status buckets and reference the first row "
                        "with grounded values only."
                    ),
                }
            )

        top_projects = normalized.get("top_projects", {})
        if top_projects.get("byTransactions", {}).get("projects"):
            tables.append(
                {
                    "id": "top_projects_table",
                    "title": "Top Projects by Transactions",
                    "source_data_path": "top_projects.byTransactions.projects",
                    "render_type": "deterministic",
                    "columns": ["projectName", "currentRate", "saleRentValue", "noOfTransactions", "productUrl"],
                    "summary_instruction": (
                        "Explain that this table lists visible project-level signals and mention the first project row "
                        "with grounded values only."
                    ),
                }
            )
        elif top_projects.get("byListingRates", {}).get("projects"):
            tables.append(
                {
                    "id": "top_projects_table",
                    "title": "Top Projects by Listing Rates",
                    "source_data_path": "top_projects.byListingRates.projects",
                    "render_type": "deterministic",
                    "columns": ["projectName", "currentRate", "changePercentage"],
                    "summary_instruction": (
                        "Explain that this table lists project-level rate signals and mention the first project row "
                        "with grounded values only."
                    ),
                }
            )
        elif top_projects.get("byValue", {}).get("projects"):
            tables.append(
                {
                    "id": "top_projects_table",
                    "title": "Top Projects by Value",
                    "source_data_path": "top_projects.byValue.projects",
                    "render_type": "deterministic",
                    "columns": ["projectName", "currentRate", "saleRentValue", "noOfTransactions", "productUrl"],
                    "summary_instruction": (
                        "Explain that this table highlights project-level value signals and mention the first project row "
                        "with grounded values only."
                    ),
                }
            )

        if page_type in {PageType.RESALE_CITY, PageType.RESALE_MICROMARKET}:
            tables.append(
                {
                    "id": "coverage_summary_table",
                    "title": "Coverage Summary",
                    "source_data_path": "listing_summary",
                    "render_type": "deterministic",
                    "columns": ["sale_count", "total_listings", "total_projects"],
                    "summary_instruction": (
                        "Explain that this table gives a quick coverage snapshot of the page and reference the visible values only."
                    ),
                }
            )

        return tables

    @staticmethod
    def _build_comparison_plan(normalized: dict) -> list[dict]:
        opportunities: list[dict] = []

        price_trend = normalized.get("pricing_summary", {}).get("price_trend", [])
        if price_trend:
            opportunities.append(
                {
                    "id": "location_vs_micromarket_price_trend",
                    "title": "Locality vs Micromarket Price Trend",
                    "comparison_type": "trend",
                    "enabled": True,
                    "source_paths": ["pricing_summary.price_trend"],
                }
            )

        nearby_localities = normalized.get("nearby_localities", [])
        if nearby_localities:
            opportunities.append(
                {
                    "id": "nearby_locality_comparison",
                    "title": "Nearby Locality Price and Supply Comparison",
                    "comparison_type": "tabular",
                    "enabled": True,
                    "source_paths": ["nearby_localities"],
                }
            )

        property_status = normalized.get("pricing_summary", {}).get("property_status", [])
        if property_status:
            opportunities.append(
                {
                    "id": "status_readiness_comparison",
                    "title": "Ready-to-Move and Status Comparison",
                    "comparison_type": "tabular",
                    "enabled": True,
                    "source_paths": ["pricing_summary.property_status"],
                }
            )

        return opportunities

    @staticmethod
    def _build_internal_links_plan(normalized: dict) -> dict:
        links = normalized["links"]
        nearby_localities = normalized["nearby_localities"]

        top_project_links: list[dict] = []
        for bucket_key in ["byTransactions", "byListingRates", "byValue"]:
            projects = normalized.get("top_projects", {}).get(bucket_key, {}).get("projects", [])
            for project in projects:
                if project.get("projectName") and project.get("productUrl"):
                    top_project_links.append(
                        {
                            "label": project["projectName"],
                            "url": project["productUrl"],
                        }
                    )

        featured_project_links: list[dict] = []
        for project in normalized.get("featured_projects", []) or []:
            if project.get("name") and project.get("url"):
                featured_project_links.append(
                    {
                        "label": project["name"],
                        "url": project["url"],
                    }
                )

        return {
            "sale_unit_type_links": links.get("sale_unit_type_urls", []),
            "sale_property_type_links": links.get("sale_property_type_urls", []),
            "sale_quick_links": links.get("sale_quick_links", []),
            "nearby_locality_links": [
                {
                    "label": item["name"],
                    "url": item.get("url"),
                }
                for item in nearby_localities
                if item.get("name") and item.get("url")
            ],
            "top_project_links": top_project_links,
            "featured_project_links": featured_project_links,
        }

    @staticmethod
    def _build_faq_plan(entity: dict, keyword_clusters: dict, normalized: dict) -> dict:
        location_label = ContentPlanBuilder._display_location(entity)
        faq_keywords = keyword_clusters.get("faq_keyword_candidates", [])

        faq_intents = [
            {
                "id": "pricing",
                "question_template": f"What is the asking price signal for resale properties in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                "data_dependencies": ["pricing_summary.asking_price", "pricing_summary.price_trend"],
            },
            {
                "id": "inventory",
                "question_template": f"How many resale properties are available in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
                "data_dependencies": ["listing_summary.sale_count", "listing_summary.total_listings"],
            },
            {
                "id": "bhk_availability",
                "question_template": f"Which BHK options are commonly available in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("bhk_keywords", []), 5),
                "data_dependencies": ["distributions.sale_unit_type_distribution"],
            },
            {
                "id": "ready_to_move",
                "question_template": f"Are ready-to-move resale properties available in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("ready_to_move_keywords", []), 4),
                "data_dependencies": ["pricing_summary.property_status"],
            },
            {
                "id": "nearby_localities",
                "question_template": f"Which nearby localities can buyers also consider around {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["nearby_localities"],
            },
            {
                "id": "review_signals",
                "question_template": f"What review and rating signals are available for {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["review_summary", "ai_summary"],
            },
            {
                "id": "demand_supply",
                "question_template": f"What demand and supply signals are available for resale listings in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["demand_supply", "listing_ranges", "listing_summary"],
            },
            {
                "id": "property_type_signals",
                "question_template": f"What property-type signals are visible for resale listings in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["pricing_summary.property_types", "distributions.sale_property_type_distribution"],
            },
            {
                "id": "price_range",
                "question_template": f"What price range is visible for resale listings in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                "data_dependencies": ["listing_ranges.sale_listing_range"],
            },
        ]

        rera_context = ContentPlanBuilder._extract_rera_context(normalized)
        if rera_context:
            faq_intents.append(
                {
                    "id": "rera_buyer_protection",
                    "question_template": f"What RERA or buyer-protection details are available for {location_label} on this page?",
                    "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                    "data_dependencies": ["rera_context"],
                }
            )

        return {
            "total_faq_intents": len(faq_intents),
            "faq_intents": faq_intents,
        }

    @staticmethod
    def _build_sections(page_type: PageType, entity: dict, keyword_clusters: dict, normalized: dict) -> list[dict]:
        location_label = ContentPlanBuilder._display_location(entity)
        property_status = normalized.get("pricing_summary", {}).get("property_status", [])

        common_sections = [
            {
                "id": "hero_intro",
                "title": f"Resale Property Overview in {location_label}",
                "objective": "Write a human, descriptive opening that establishes resale intent, location context, and visible inventory without overclaiming.",
                "render_type": "generative",
                "target_keywords": [keyword_clusters.get("primary_keyword", {}).get("keyword")]
                if keyword_clusters.get("primary_keyword")
                else [],
                "data_dependencies": ["entity", "listing_summary", "pricing_summary"],
            },
            {
                "id": "market_snapshot",
                "title": "Resale Market Snapshot",
                "objective": "Summarize visible resale inventory, listing activity, and current on-page market context in a grounded but readable way.",
                "render_type": "generative",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 5),
                "data_dependencies": ["listing_summary", "pricing_summary"],
            },
            {
                "id": "price_trends_and_rates",
                "title": "Price Trends and Rates",
                "objective": "Explain visible asking price direction and trend context using grounded inputs only, in a more descriptive and SEO-friendly format.",
                "render_type": "hybrid",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 5),
                "data_dependencies": ["pricing_summary.asking_price", "pricing_summary.price_trend"],
                "narrative_rules": {
                    "allowed_pricing_metrics": ["asking_price"],
                    "disallowed_pricing_metrics": ["registration_rate", "sale_avg_price_per_sqft"],
                },
            },
            {
                "id": "bhk_and_inventory_mix",
                "title": "BHK and Inventory Mix",
                "objective": "Describe the visible mix of BHK formats and inventory composition in a buyer-friendly but fully grounded way.",
                "render_type": "hybrid",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("bhk_keywords", []), 6),
                "data_dependencies": [
                    "distributions.sale_unit_type_distribution",
                    "distributions.sale_property_type_distribution",
                ],
            },
            {
                "id": "buyer_guidance",
                "title": "What Buyers Can Explore Here",
                "objective": "Give grounded exploratory guidance using only visible inventory, page links, and pricing context.",
                "render_type": "generative",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 5),
                "data_dependencies": ["listing_summary", "pricing_summary", "links"],
            },
            {
                "id": "faq_section",
                "title": "Frequently Asked Questions",
                "objective": "Answer a broader set of grounded buying, inventory, price, supply, and nearby-location questions.",
                "render_type": "generative",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("faq_keyword_candidates", []), 8),
                "data_dependencies": [
                    "pricing_summary",
                    "listing_summary",
                    "distributions",
                    "nearby_localities",
                    "review_summary",
                    "ai_summary",
                    "demand_supply",
                    "listing_ranges",
                    "rera_context",
                ],
            },
            {
                "id": "internal_links",
                "title": "Explore More Property Options",
                "objective": "Guide users to relevant listing, unit-type, property-type, project, and nearby-area pages.",
                "render_type": "deterministic",
                "target_keywords": [],
                "data_dependencies": ["links", "nearby_localities", "top_projects", "featured_projects"],
            },
        ]

        locality_specific = {
            "id": "nearby_alternatives",
            "title": "Nearby Localities Buyers Can Also Explore",
            "objective": "Describe nearby resale alternatives around the locality using actual nearby locality data and grounded comparisons.",
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["nearby_localities"],
        }

        review_signals_section = {
            "id": "review_and_rating_signals",
            "title": "Review and Rating Signals",
            "objective": "Summarize explicit review counts, rating inputs, visible tags, and AI summary text in a descriptive but grounded way.",
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["review_summary", "ai_summary"],
        }

        demand_supply_section = {
            "id": "demand_and_supply_signals",
            "title": "Demand and Supply Signals",
            "objective": "Describe visible demand, supply, range, and availability inputs without adding unsupported market interpretation.",
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["demand_supply", "listing_ranges", "listing_summary"],
        }

        property_type_signals_section = {
            "id": "property_type_signals",
            "title": "Property Type Signals",
            "objective": "Describe visible property-type and mix inputs without ranking or recommending any property type.",
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": [
                "pricing_summary.property_types",
                "pricing_summary.property_status",
                "distributions.sale_property_type_distribution",
            ],
        }

        property_type_rate_snapshot_section = {
            "id": "property_type_rate_snapshot",
            "title": "Property Type Rate Snapshot",
            "objective": "Explain visible property-type and location-level rate inputs in a descriptive, grounded format.",
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": [
                "pricing_summary.property_types",
                "pricing_summary.location_rates",
            ],
        }

        micromarket_specific = {
            "id": "locality_coverage",
            "title": "Localities Covered in This Micromarket",
            "objective": "Describe how resale options are distributed across the micromarket using grounded listing and nearby-locality signals.",
            "render_type": "generative",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["listing_summary", "nearby_localities", "pricing_summary.location_rates"],
        }

        city_specific = {
            "id": "micromarket_coverage",
            "title": "Key Resale Zones Across the City",
            "objective": "Describe how visible resale opportunities are distributed across city-level zones using grounded city coverage signals.",
            "render_type": "generative",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["listing_summary", "links", "pricing_summary.location_rates", "nearby_localities"],
        }

        readiness_section = {
            "id": "status_and_readiness",
            "title": "Status and Readiness Snapshot",
            "objective": "Summarize visible status buckets such as ready-to-move using grounded property-status inputs only.",
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("ready_to_move_keywords", []), 5),
            "data_dependencies": ["pricing_summary.property_status"],
        }

        sections = list(common_sections)
        sections.insert(4, review_signals_section)
        sections.insert(5, demand_supply_section)
        sections.insert(6, property_type_signals_section)
        sections.insert(7, property_type_rate_snapshot_section)

        if property_status:
            sections.insert(4, readiness_section)

        if page_type == PageType.RESALE_LOCALITY:
            return sections[:4] + [locality_specific] + sections[4:]
        if page_type == PageType.RESALE_MICROMARKET:
            return sections[:2] + [micromarket_specific] + sections[2:]
        if page_type == PageType.RESALE_CITY:
            return sections[:2] + [city_specific] + sections[2:]

        return sections

    @staticmethod
    def _resolve_dependency_value(normalized: dict, path: str) -> Any:
        current: Any = normalized
        for key in path.split("."):
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    @staticmethod
    def _build_section_generation_context(section_plan: list[dict], normalized: dict, entity: dict) -> dict[str, dict]:
        context_map: dict[str, dict] = {}

        for section in section_plan:
            section_context: dict[str, Any] = {"entity": entity}

            for dependency in section.get("data_dependencies", []):
                value = ContentPlanBuilder._resolve_dependency_value(normalized, dependency)
                if value is None:
                    continue
                section_context[dependency] = value

            section_context["writing_style"] = {
                "target_tone": "human, descriptive, grounded, SEO-friendly",
                "min_paragraphs": 2,
                "prefer_paragraphs_over_bullets": True,
                "avoid_template_like_phrasing": True,
                "avoid_repetition": True,
            }

            if section["id"] == "price_trends_and_rates":
                section_context["narrative_guardrails"] = {
                    "allowed_pricing_metrics": ["asking_price"],
                    "disallowed_pricing_metrics": ["registration_rate", "sale_avg_price_per_sqft"],
                    "instruction": "Use only asking_price and price_trend in prose. Do not mention registration_rate or any non-canonical pricing metric.",
                }

            if section["id"] == "review_and_rating_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["review_summary", "ai_summary"],
                    "instruction": "Use only explicit review counts, rating values, tags, and ai_summary inputs. Do not infer sentiment or desirability.",
                }

            if section["id"] == "demand_and_supply_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["demand_supply", "listing_ranges", "listing_summary"],
                    "instruction": "Use only explicit counts, percentages, availability, and listing-range values. Do not interpret market strength.",
                }

            if section["id"] in {"property_type_signals", "property_type_rate_snapshot"}:
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": [
                        "pricing_summary.property_types",
                        "pricing_summary.property_status",
                        "pricing_summary.location_rates",
                        "distributions.sale_property_type_distribution",
                    ],
                    "instruction": "Use only explicit property-type, location-rate, status, price, and mix inputs. Do not recommend or rank property types.",
                }

            context_map[section["id"]] = section_context

        return context_map

    @staticmethod
    def build(normalized: dict, keyword_intelligence: dict) -> dict:
        entity = dict(normalized["entity"])
        entity["canonical_asking_price"] = normalized["pricing_summary"].get("asking_price")
        page_type = PageType(entity["page_type"])
        keyword_clusters = keyword_intelligence["keyword_clusters"]
        raw_source_meta = normalized["raw_source_meta"]
        rera_context = ContentPlanBuilder._extract_rera_context(normalized)

        section_plan = ContentPlanBuilder._build_sections(page_type, entity, keyword_clusters, normalized)

        return {
            "version": "v1.7",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": entity["page_type"],
            "listing_type": entity["listing_type"],
            "entity": entity,
            "metadata_plan": ContentPlanBuilder._build_metadata_plan(entity, keyword_clusters, raw_source_meta),
            "keyword_strategy": {
                "primary_keyword": keyword_clusters.get("primary_keyword"),
                "secondary_keywords": keyword_clusters.get("secondary_keywords", []),
                "bhk_keywords": keyword_clusters.get("bhk_keywords", []),
                "price_keywords": keyword_clusters.get("price_keywords", []),
                "ready_to_move_keywords": keyword_clusters.get("ready_to_move_keywords", []),
                "faq_keyword_candidates": keyword_clusters.get("faq_keyword_candidates", []),
                "metadata_keywords": keyword_clusters.get("metadata_keywords", []),
                "exact_match_keywords": keyword_clusters.get("exact_match_keywords", []),
                "loose_match_keywords": keyword_clusters.get("loose_match_keywords", []),
            },
            "section_plan": section_plan,
            "section_generation_context": ContentPlanBuilder._build_section_generation_context(
                section_plan,
                normalized,
                entity,
            ),
            "table_plan": ContentPlanBuilder._build_table_plan(page_type, normalized),
            "comparison_plan": ContentPlanBuilder._build_comparison_plan(normalized),
            "faq_plan": ContentPlanBuilder._build_faq_plan(entity, keyword_clusters, normalized),
            "internal_links_plan": ContentPlanBuilder._build_internal_links_plan(normalized),
            "data_context": {
                "listing_summary": normalized["listing_summary"],
                "pricing_summary": normalized["pricing_summary"],
                "distributions": normalized["distributions"],
                "nearby_localities": normalized["nearby_localities"],
                "top_projects": normalized["top_projects"],
                "review_summary": normalized.get("review_summary"),
                "ai_summary": normalized.get("ai_summary"),
                "insight_rates": normalized.get("insight_rates"),
                "demand_supply": normalized.get("demand_supply"),
                "listing_ranges": normalized.get("listing_ranges"),
                "cms_faq": normalized.get("cms_faq"),
                "featured_projects": normalized.get("featured_projects"),
                "projects_by_status": normalized.get("projects_by_status"),
                "rera_context": rera_context,
            },
            "source_meta": {
                "raw_source_meta": raw_source_meta,
                "keyword_intelligence_version": keyword_intelligence["version"],
            },
        }