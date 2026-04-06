from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from seo_content_engine.core.config import settings
from seo_content_engine.domain.enums import PageType
from seo_content_engine.services.competitor_intelligence_service import CompetitorIntelligenceService
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
    def _page_property_type_context(normalized: dict, entity: dict) -> dict[str, Any]:
        context = normalized.get("page_property_type_context", {}) or {}
        return {
            "scope": context.get("scope") or entity.get("page_property_type_scope") or "all",
            "property_type": context.get("property_type") or entity.get("page_property_type"),
            "source_url": context.get("source_url"),
        }

    @staticmethod
    def _has_review_signals(normalized: dict) -> bool:
        review_summary = normalized.get("review_summary", {}) or {}
        ai_summary = normalized.get("ai_summary", {}) or {}
        overview = review_summary.get("overview", {}) or {}

        return bool(
            overview.get("avg_rating") is not None
            or overview.get("review_count") is not None
            or overview.get("rating_count") is not None
            or (review_summary.get("positive_tags") or [])
            or (review_summary.get("negative_tags") or [])
            or ai_summary.get("locality_summary")
        )

    @staticmethod
    def _build_city_zone_segmentation(pricing_summary: dict) -> dict[str, Any]:
        location_rates = pricing_summary.get("location_rates", []) or []
        valid_rows = [
            item
            for item in location_rates
            if isinstance(item, dict) and item.get("name") and item.get("avgRate") is not None
        ]

        if len(valid_rows) < 2:
            return {}

        sorted_rows = sorted(valid_rows, key=lambda item: item.get("avgRate") or 0, reverse=True)
        premium_zone = sorted_rows[0]
        value_zone = sorted_rows[-1]

        return {
            "premium_zone": premium_zone.get("name"),
            "premium_zone_rate": premium_zone.get("avgRate"),
            "value_zone": value_zone.get("name"),
            "value_zone_rate": value_zone.get("avgRate"),
        }

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
    def _extract_keyword_text(record: dict | None) -> str | None:
        if not isinstance(record, dict):
            return None

        keyword = str(record.get("keyword") or "").strip()
        return keyword or None

    @staticmethod
    def _primary_keyword_variants(keyword_clusters: dict, entity: dict) -> list[str]:
        location_label = ContentPlanBuilder._display_location(entity)

        variants: list[str] = []
        seen: set[str] = set()

        primary_keyword = ContentPlanBuilder._extract_keyword_text(
            keyword_clusters.get("primary_keyword")
        )
        override_keywords = keyword_clusters.get("primary_keyword_overrides", []) or []
        exact_match_keywords = keyword_clusters.get("exact_match_keywords", []) or []

        candidates: list[str] = []
        if primary_keyword:
            candidates.append(primary_keyword)

        for item in override_keywords:
            cleaned = str(item or "").strip()
            if cleaned:
                candidates.append(cleaned)

        for record in exact_match_keywords:
            keyword = ContentPlanBuilder._extract_keyword_text(record)
            if keyword:
                candidates.append(keyword)

        for keyword in candidates:
            signature = keyword.lower()
            if signature in seen:
                continue
            seen.add(signature)
            variants.append(keyword)

        if not variants:
            variants.append(f"resale properties in {location_label}")

        return variants[:5]

    @staticmethod
    def _body_keyword_priority(keyword_clusters: dict, entity: dict) -> list[str]:
        prioritized: list[str] = []
        seen: set[str] = set()

        for keyword in ContentPlanBuilder._primary_keyword_variants(keyword_clusters, entity):
            signature = keyword.lower()
            if signature in seen:
                continue
            seen.add(signature)
            prioritized.append(keyword)

        for record in keyword_clusters.get("secondary_keywords", []) or []:
            keyword = ContentPlanBuilder._extract_keyword_text(record)
            if not keyword:
                continue
            signature = keyword.lower()
            if signature in seen:
                continue
            seen.add(signature)
            prioritized.append(keyword)
            if len(prioritized) >= 8:
                break

        return prioritized

    @staticmethod
    def _metadata_keyword_priority(keyword_clusters: dict, entity: dict) -> list[str]:
        prioritized: list[str] = []
        seen: set[str] = set()

        for keyword in ContentPlanBuilder._primary_keyword_variants(keyword_clusters, entity):
            signature = keyword.lower()
            if signature in seen:
                continue
            seen.add(signature)
            prioritized.append(keyword)

        for keyword in ContentPlanBuilder._select_metadata_keywords(keyword_clusters, entity):
            signature = keyword.lower()
            if signature in seen:
                continue
            seen.add(signature)
            prioritized.append(keyword)

        return prioritized[: settings.keyword_metadata_max_count]

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
    def _apply_priority_order(items: list[dict], priority_ids: list[str], id_key: str = "id") -> list[dict]:
        priority_map = {value: index for index, value in enumerate(priority_ids)}
        return sorted(
            items,
            key=lambda item: (
                priority_map.get(item.get(id_key), 10_000),
                item.get(id_key, ""),
            ),
        )

    @staticmethod
    def _section_ids_for_theme(page_type: PageType, theme: str) -> list[str]:
        mapping = {
            "pricing": ["price_trends_and_rates"],
            "bhk": ["bhk_and_inventory_mix"],
            "ready_to_move": [],
            "locality_navigation": (
                ["nearby_alternatives"]
                if page_type == PageType.RESALE_LOCALITY
                else ["locality_coverage"]
                if page_type == PageType.RESALE_MICROMARKET
                else ["micromarket_coverage"]
            ),
            "reviews": ["review_and_rating_signals"],
            "listing_discovery": ["market_snapshot", "property_type_signals"],
            "informational": ["faq_section"],
        }
        return mapping.get(theme, [])

    @staticmethod
    def _faq_ids_for_theme(theme: str) -> list[str]:
        mapping = {
            "pricing": ["pricing", "price_range"],
            "bhk": ["bhk_availability"],
            "ready_to_move": [],
            "locality_navigation": ["nearby_localities"],
            "reviews": ["review_signals"],
            "listing_discovery": ["inventory", "property_type_signals"],
            "informational": ["property_rates_ai_signals"],
        }
        return mapping.get(theme, [])

    @staticmethod
    def _table_ids_for_theme(theme: str) -> list[str]:
        mapping = {
            "pricing": ["price_trend_table", "location_rates_table"],
            "bhk": ["sale_unit_type_distribution_table"],
            "ready_to_move": [],
            "locality_navigation": ["nearby_localities_table"],
            "listing_discovery": ["property_types_table", "coverage_summary_table"],
        }
        return mapping.get(theme, [])

    @staticmethod
    def _apply_competitor_section_priority(
        section_plan: list[dict],
        competitor_intelligence: dict[str, Any],
        page_type: PageType,
    ) -> list[dict]:
        recommended_sections = (
            competitor_intelligence.get("inspiration_signals", {}).get("recommended_sections", []) or []
        )

        priority_ids: list[str] = []
        for item in recommended_sections:
            theme = item.get("theme")
            priority_ids.extend(ContentPlanBuilder._section_ids_for_theme(page_type, theme))

        if not priority_ids:
            return section_plan

        return ContentPlanBuilder._apply_priority_order(section_plan, priority_ids)

    @staticmethod
    def _apply_competitor_faq_priority(
        faq_plan: dict[str, Any],
        competitor_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        faq_intents = list(faq_plan.get("faq_intents", []) or [])
        recommended_faq_themes = (
            competitor_intelligence.get("inspiration_signals", {}).get("recommended_faq_themes", []) or []
        )

        priority_ids: list[str] = []
        for item in recommended_faq_themes:
            theme = item.get("theme")
            priority_ids.extend(ContentPlanBuilder._faq_ids_for_theme(theme))

        if not priority_ids:
            return faq_plan

        updated = dict(faq_plan)
        updated["faq_intents"] = ContentPlanBuilder._apply_priority_order(faq_intents, priority_ids)
        return updated

    @staticmethod
    def _apply_competitor_table_priority(
        table_plan: list[dict],
        competitor_intelligence: dict[str, Any],
    ) -> list[dict]:
        recommended_table_themes = (
            competitor_intelligence.get("inspiration_signals", {}).get("recommended_table_themes", []) or []
        )

        priority_ids: list[str] = []
        for item in recommended_table_themes:
            theme = item.get("theme")
            priority_ids.extend(ContentPlanBuilder._table_ids_for_theme(theme))

        if not priority_ids:
            return table_plan

        return ContentPlanBuilder._apply_priority_order(table_plan, priority_ids)

    @staticmethod
    def _build_planning_signals(
        competitor_intelligence: dict[str, Any],
        page_type: PageType,
    ) -> dict[str, Any]:
        recommended_sections = (
            competitor_intelligence.get("inspiration_signals", {}).get("recommended_sections", []) or []
        )
        recommended_faq_themes = (
            competitor_intelligence.get("inspiration_signals", {}).get("recommended_faq_themes", []) or []
        )
        recommended_table_themes = (
            competitor_intelligence.get("inspiration_signals", {}).get("recommended_table_themes", []) or []
        )

        return {
            "label": "Planning signals from competitor patterns",
            "usage_rule": "Structural inspiration only. Never copy competitor phrasing, claims, or FAQ wording.",
            "section_priority_signals": [
                {
                    "theme": item.get("theme"),
                    "suggested_section_ids": ContentPlanBuilder._section_ids_for_theme(page_type, item.get("theme", "")),
                    "evidence_count": item.get("evidence_count"),
                }
                for item in recommended_sections
            ],
            "faq_priority_signals": [
                {
                    "theme": item.get("theme"),
                    "suggested_faq_ids": ContentPlanBuilder._faq_ids_for_theme(item.get("theme", "")),
                    "evidence_count": item.get("evidence_count"),
                }
                for item in recommended_faq_themes
            ],
            "table_priority_signals": [
                {
                    "theme": item.get("theme"),
                    "suggested_table_ids": ContentPlanBuilder._table_ids_for_theme(item.get("theme", "")),
                    "evidence_count": item.get("evidence_count"),
                }
                for item in recommended_table_themes
            ],
            "schema_hierarchy_patterns": competitor_intelligence.get("inspiration_signals", {}).get(
                "recommended_schema_hierarchy_patterns",
                [],
            ),
        }

    @staticmethod
    def _build_metadata_plan(entity: dict, keyword_clusters: dict, raw_source_meta: dict) -> dict:
        entity_name, city_name = ContentPlanBuilder._entity_label_parts(entity)
        location_label = ContentPlanBuilder._display_location(entity)

        primary_keyword_variants = ContentPlanBuilder._primary_keyword_variants(
            keyword_clusters,
            entity,
        )
        primary_keyword_text = primary_keyword_variants[0]
        secondary_primary_keyword = (
            primary_keyword_variants[1]
            if len(primary_keyword_variants) > 1
            else f"resale properties in {location_label}"
        )
        tertiary_primary_keyword = (
            primary_keyword_variants[2]
            if len(primary_keyword_variants) > 2
            else f"flats for sale in {location_label}"
        )

        metadata_keywords = ContentPlanBuilder._metadata_keyword_priority(keyword_clusters, entity)

        title_candidates = [
            f"{primary_keyword_text} | Square Yards",
            f"{secondary_primary_keyword} | Square Yards",
            f"{location_label} Resale Properties for Sale | Square Yards",
            f"{tertiary_primary_keyword} | Square Yards",
            f"Property for Sale in {location_label} | Resale Listings | Square Yards",
        ]

        description_candidates = [
            f"Explore {primary_keyword_text.lower()} with asking price details, BHK options, nearby localities, and resale market context on Square Yards.",
            f"Find {secondary_primary_keyword.lower()} with asking price trends, inventory mix, and nearby area insights on Square Yards.",
            f"Browse {tertiary_primary_keyword.lower()} with rates, property mix, and grounded resale information on Square Yards.",
            f"Check resale property options in {location_label} with asking price trends, BHK availability, locality comparisons, and source-backed data on Square Yards.",
        ]

        canonical_pricing = {
            "metric_name": "asking_price",
            "label": "asking price",
            "value": entity.get("canonical_asking_price"),
        }

        return {
            "primary_keyword": primary_keyword_text,
            "primary_keyword_variants": primary_keyword_variants,
            "supporting_keywords": metadata_keywords,
            "metadata_keyword_priority": metadata_keywords,
            "recommended_h1": primary_keyword_text[:120],
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
                    "Explain what this table helps the user compare and mention one visible row naturally."
                ),
            },
            {
                "id": "sale_unit_type_distribution_table",
                "title": "Available BHK Mix",
                "source_data_path": "distributions.sale_unit_type_distribution",
                "render_type": "deterministic",
                "columns": ["key", "doc_count"],
                "summary_instruction": (
                    "Explain what this table says about the available BHK mix and mention one visible row naturally."
                ),
            },
            {
                "id": "nearby_localities_table",
                "title": "Nearby Localities to Explore",
                "source_data_path": "nearby_localities",
                "render_type": "deterministic",
                "columns": ["name", "distance_km", "sale_count", "sale_avg_price_per_sqft", "url"],
                "summary_instruction": (
                    "Explain how this table helps compare nearby alternatives and mention one visible row naturally."
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
                        "For city pages, treat these as city zones or micromarkets rather than locality rows."
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
                        "Explain the visible residential property-type pricing signals and mention one visible row naturally."
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
                        "Explain that this table gives a quick scale view of the page using only visible values."
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

        return opportunities

    @staticmethod
    def _build_internal_links_plan(normalized: dict) -> dict:
        links = normalized["links"]
        nearby_localities = normalized["nearby_localities"]

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
            "featured_project_links": featured_project_links,
        }

    @staticmethod
    def _build_faq_plan(entity: dict, keyword_clusters: dict, normalized: dict) -> dict:
        location_label = ContentPlanBuilder._display_location(entity)
        faq_keywords = keyword_clusters.get("faq_keyword_candidates", [])

        faq_intents = [
            {
                "id": "pricing",
                "question_template": f"What is the current asking price for resale properties in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                "data_dependencies": ["pricing_summary.asking_price", "pricing_summary.price_trend"],
            },
            {
                "id": "inventory",
                "question_template": f"How much resale inventory is currently visible in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
                "data_dependencies": ["listing_summary.sale_count", "listing_summary.total_listings", "listing_summary.total_projects"],
            },
            {
                "id": "bhk_availability",
                "question_template": f"Which home sizes are showing up most often in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("bhk_keywords", []), 5),
                "data_dependencies": ["distributions.sale_unit_type_distribution"],
            },
            {
                "id": "nearby_localities",
                "question_template": f"Which nearby areas can buyers compare with {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["nearby_localities"],
            },
            {
                "id": "property_rates_ai_signals",
                "question_template": f"What does the market-summary note say about {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["property_rates_ai_summary"],
            },
            {
                "id": "demand_supply",
                "question_template": f"What do the current demand and supply numbers show for resale listings in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["demand_supply", "listing_ranges", "listing_summary"],
            },
            {
                "id": "property_type_signals",
                "question_template": f"Which residential property types are showing up in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["pricing_summary.property_types", "distributions.sale_property_type_distribution"],
            },
            {
                "id": "price_range",
                "question_template": f"What price range is currently visible for resale properties in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                "data_dependencies": ["listing_ranges.sale_listing_range"],
            },
        ]

        if ContentPlanBuilder._has_review_signals(normalized):
            faq_intents.insert(
                4,
                {
                    "id": "review_signals",
                    "question_template": f"What do the available reviews and ratings say about {location_label}?",
                    "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                    "data_dependencies": ["review_summary", "ai_summary"],
                },
            )

        rera_context = ContentPlanBuilder._extract_rera_context(normalized)
        if rera_context:
            faq_intents.append(
                {
                    "id": "rera_buyer_protection",
                    "question_template": f"What RERA or buyer-protection details are available for {location_label}?",
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
        has_review_signals = ContentPlanBuilder._has_review_signals(normalized)

        common_sections = [
            {
                "id": "market_snapshot",
                "title": "Resale Market Snapshot",
                "objective": (
                    "Answer the buyer question: what kind of resale market am I looking at on this page? "
                    "Open with a grounded overview of the visible resale picture, not with a raw data dump. "
                    "If this page is for a specific residential property type, stay focused on that type only."
                ),
                "render_type": "generative",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 5),
                "data_dependencies": ["listing_summary", "pricing_summary", "distributions", "page_property_type_context"],
            },
            {
                "id": "price_trends_and_rates",
                "title": "Price Trends and Rates",
                "objective": (
                    "Answer the buyer question: what does the current asking price look like here, and how does the trend view help compare it? "
                    "Keep the explanation grounded, readable, and non-technical."
                ),
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
                "objective": (
                    "Answer the buyer question: what kinds of home sizes are actually showing up here? "
                    "Explain the visible BHK spread and inventory composition without repeating the market snapshot section."
                ),
                "render_type": "hybrid",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("bhk_keywords", []), 6),
                "data_dependencies": [
                    "distributions.sale_unit_type_distribution",
                    "distributions.sale_property_type_distribution",
                ],
            },
            {
                "id": "faq_section",
                "title": "Frequently Asked Questions",
                "objective": "Answer realistic buyer questions using grounded data only.",
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
                "data_dependencies": ["links", "nearby_localities", "featured_projects"],
            },
        ]

        locality_specific = {
            "id": "nearby_alternatives",
            "title": "Nearby Localities Buyers Can Also Explore",
            "objective": (
                "Answer the buyer question: where else nearby can I compare resale options? "
                "Use only actual nearby-locality data."
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["nearby_localities"],
        }

        review_signals_section = {
            "id": "review_and_rating_signals",
            "title": "Review and Rating Signals",
            "objective": (
                "Answer the buyer question: what do the available reviews and ratings show here? "
                "Summarize explicit review counts, ratings, visible tags, and locality summary text in a restrained way."
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["review_summary", "ai_summary"],
        }

        property_rates_ai_section = {
            "id": "property_rates_ai_signals",
            "title": "Market Strengths, Challenges, and Opportunities",
            "objective": (
                "Answer the buyer question: what does the structured market-summary note say here? "
                "Present the structured property-rates AI fields exactly as a restrained editorial summary. "
                "Do not add interpretation beyond the provided snapshot and lists."
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["property_rates_ai_summary"],
        }

        demand_supply_section = {
            "id": "demand_and_supply_signals",
            "title": "Demand and Supply Signals",
            "objective": (
                "Answer the buyer question: how broad does the currently visible resale stock look? "
                "Explain counts, percentages, and listing ranges without adding unsupported interpretation."
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["demand_supply", "listing_ranges", "listing_summary"],
        }

        property_type_signals_section = {
            "id": "property_type_signals",
            "title": "Property Type Signals",
            "objective": (
                "Answer the buyer question: which residential property formats are showing up here? "
                "Explain the visible residential mix only. "
                "If the page is for a specific type, stay tightly focused on that type."
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": [
                "pricing_summary.property_types",
                "distributions.sale_property_type_distribution",
                "page_property_type_context",
            ],
        }

        property_type_rate_snapshot_section = {
            "id": "property_type_rate_snapshot",
            "title": "Property Type Rate Snapshot",
            "objective": (
                "Answer the buyer question: how are the visible property-type rates distributed here? "
                "Translate property-type and location-level rate inputs into buyer-readable prose without repeating the market snapshot section."
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": [
                "pricing_summary.property_types",
                "pricing_summary.location_rates",
                "pricing_summary.micromarket_rates",
                "page_property_type_context",
            ],
        }

        micromarket_specific = {
            "id": "locality_coverage",
            "title": "Localities Covered in This Micromarket",
            "objective": (
                "Answer the buyer question: how does the resale picture vary across localities inside this micromarket? "
                "Use grounded locality and rate inputs only."
            ),
            "render_type": "generative",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["listing_summary", "nearby_localities", "pricing_summary.location_rates"],
        }

        city_specific = {
            "id": "micromarket_coverage",
            "title": "Key Resale Zones Across the City",
            "objective": (
                "Answer the buyer question: which city zones are visible in the current resale picture, and how do their rate bands compare? "
                "If clear pricing tiers exist, explain them simply without making investment claims."
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["listing_summary", "pricing_summary.location_rates", "nearby_localities"],
        }

        sections = list(common_sections)
        sections.insert(3, property_rates_ai_section)
        sections.insert(4, demand_supply_section)
        sections.insert(5, property_type_signals_section)
        sections.insert(6, property_type_rate_snapshot_section)

        if has_review_signals:
            sections.insert(3, review_signals_section)

        if page_type == PageType.RESALE_LOCALITY:
            return sections[:3] + [locality_specific] + sections[3:]
        if page_type == PageType.RESALE_MICROMARKET:
            return sections[:1] + [micromarket_specific] + sections[1:]
        if page_type == PageType.RESALE_CITY:
            return sections[:1] + [city_specific] + sections[1:]

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
    def _build_section_generation_context(
        section_plan: list[dict],
        normalized: dict,
        entity: dict,
        keyword_clusters: dict,
    ) -> dict[str, dict]:
        context_map: dict[str, dict] = {}

        primary_keyword_variants = ContentPlanBuilder._primary_keyword_variants(
            keyword_clusters,
            entity,
        )
        body_keyword_priority = ContentPlanBuilder._body_keyword_priority(
            keyword_clusters,
            entity,
        )
        page_property_type_context = ContentPlanBuilder._page_property_type_context(
            normalized,
            entity,
        )
        buyer_segmentation = ContentPlanBuilder._build_city_zone_segmentation(
            normalized.get("pricing_summary", {}) or {}
        )

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
                "avoid_internal_language": True,
                "write_for_real_buyers_not_reviewers": True,
            }

            section_context["keyword_usage_plan"] = {
                "primary_keyword": primary_keyword_variants[0] if primary_keyword_variants else None,
                "primary_keyword_variants": primary_keyword_variants,
                "body_keyword_priority": body_keyword_priority,
                "instruction": (
                    "Use the main primary keyword naturally in an early section. "
                    "Where suitable, use one alternate primary keyword variant naturally in one other section. "
                    "Do not stuff keywords or repeat the same phrase across every section."
                ),
            }

            section_context["page_property_type_context"] = page_property_type_context

            if buyer_segmentation:
                section_context["buyer_segmentation"] = buyer_segmentation

            if section["id"] == "market_snapshot":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["listing_summary", "pricing_summary", "distributions", "page_property_type_context"],
                    "instruction": (
                        "Open with what a buyer is actually looking at here. "
                        "If page_property_type_context.scope is specific, talk only about that residential property type. "
                        "If the page scope is all, summarize only the relevant residential property types visible in source data. "
                        "Do not mix residential and commercial types."
                    ),
                }

            if section["id"] == "price_trends_and_rates":
                section_context["narrative_guardrails"] = {
                    "allowed_pricing_metrics": ["asking_price"],
                    "disallowed_pricing_metrics": ["registration_rate", "sale_avg_price_per_sqft"],
                    "instruction": (
                        "Use only asking_price and price_trend in prose. "
                        "Explain the number and the trend view in plain English."
                    ),
                }

            if section["id"] == "review_and_rating_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["review_summary", "ai_summary"],
                    "instruction": (
                        "Use only explicit review counts, rating values, tags, and ai_summary inputs. "
                        "Do not infer sentiment, trust, desirability, or quality."
                    ),
                }

            if section["id"] == "property_rates_ai_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["property_rates_ai_summary"],
                    "instruction": (
                        "Use only explicit property_rates_ai_summary fields. "
                        "Break the response into a short snapshot followed by Strengths, Challenges, and Opportunities. "
                        "Keep the wording concise, readable, and source-bound. "
                        "Do not add advice, forecast, or interpretation."
                    ),
                }

            if section["id"] == "demand_and_supply_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["demand_supply", "listing_ranges", "listing_summary"],
                    "instruction": (
                        "Use only explicit counts, percentages, availability, and listing-range values. "
                        "Explain what is visible without overstating what it means."
                    ),
                }

            if section["id"] == "property_type_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": [
                        "pricing_summary.property_types",
                        "distributions.sale_property_type_distribution",
                        "page_property_type_context",
                    ],
                    "instruction": (
                        "Use only explicit residential property-type, rate, and mix inputs. "
                        "If the page is specific to one residential property type, stay focused on that type only. "
                        "Do not mix in commercial categories. "
                        "Do not use status commentary here."
                    ),
                }

            if section["id"] == "property_type_rate_snapshot":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": [
                        "pricing_summary.property_types",
                        "pricing_summary.location_rates",
                        "pricing_summary.micromarket_rates",
                        "page_property_type_context",
                    ],
                    "instruction": (
                        "Use only explicit residential property-type and location-rate inputs. "
                        "Avoid technical field language and avoid sounding like a data dump."
                    ),
                }

            if section["id"] == "micromarket_coverage":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["pricing_summary.location_rates", "buyer_segmentation"],
                    "instruction": (
                        "For city pages, explain covered zones using the visible location-rate rows. "
                        "Where clear tiers exist, explain them simply as pricing bands. "
                        "Do not add unsupported investment or growth claims."
                    ),
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

        competitor_intelligence = CompetitorIntelligenceService.build(
            normalized=normalized,
            keyword_intelligence=keyword_intelligence,
        )

        section_plan = ContentPlanBuilder._apply_competitor_section_priority(
            section_plan,
            competitor_intelligence,
            page_type,
        )

        faq_plan = ContentPlanBuilder._apply_competitor_faq_priority(
            ContentPlanBuilder._build_faq_plan(entity, keyword_clusters, normalized),
            competitor_intelligence,
        )

        table_plan = ContentPlanBuilder._apply_competitor_table_priority(
            ContentPlanBuilder._build_table_plan(page_type, normalized),
            competitor_intelligence,
        )

        planning_signals = ContentPlanBuilder._build_planning_signals(
            competitor_intelligence,
            page_type,
        )

        return {
            "version": "v2.1",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": entity["page_type"],
            "listing_type": entity["listing_type"],
            "entity": entity,
            "metadata_plan": ContentPlanBuilder._build_metadata_plan(entity, keyword_clusters, raw_source_meta),
            "keyword_strategy": {
                "primary_keyword": keyword_clusters.get("primary_keyword"),
                "primary_keyword_overrides": keyword_clusters.get("primary_keyword_overrides", []),
                "primary_keyword_variants": ContentPlanBuilder._primary_keyword_variants(
                    keyword_clusters,
                    entity,
                ),
                "metadata_keyword_priority": ContentPlanBuilder._metadata_keyword_priority(
                    keyword_clusters,
                    entity,
                ),
                "body_keyword_priority": ContentPlanBuilder._body_keyword_priority(
                    keyword_clusters,
                    entity,
                ),
                "secondary_keywords": keyword_clusters.get("secondary_keywords", []),
                "bhk_keywords": keyword_clusters.get("bhk_keywords", []),
                "price_keywords": keyword_clusters.get("price_keywords", []),
                "ready_to_move_keywords": keyword_clusters.get("ready_to_move_keywords", []),
                "faq_keyword_candidates": keyword_clusters.get("faq_keyword_candidates", []),
                "competitor_keywords": keyword_clusters.get("competitor_keywords", []),
                "informational_keywords": keyword_clusters.get("informational_keywords", []),
                "serp_validated_keywords": keyword_clusters.get("serp_validated_keywords", []),
                "metadata_keywords": keyword_clusters.get("metadata_keywords", []),
                "exact_match_keywords": keyword_clusters.get("exact_match_keywords", []),
                "loose_match_keywords": keyword_clusters.get("loose_match_keywords", []),
            },
            "section_plan": section_plan,
            "section_generation_context": ContentPlanBuilder._build_section_generation_context(
                section_plan,
                normalized,
                entity,
                keyword_clusters,
            ),
            "table_plan": table_plan,
            "comparison_plan": ContentPlanBuilder._build_comparison_plan(normalized),
            "faq_plan": faq_plan,
            "internal_links_plan": ContentPlanBuilder._build_internal_links_plan(normalized),
            "competitor_intelligence": competitor_intelligence,
            "competitor_inspiration": competitor_intelligence.get("inspiration_signals", {}),
            "planning_signals": planning_signals,
            "data_context": {
                "listing_summary": normalized["listing_summary"],
                "pricing_summary": normalized["pricing_summary"],
                "distributions": normalized["distributions"],
                "nearby_localities": normalized["nearby_localities"],
                "top_projects": normalized["top_projects"],
                "review_summary": normalized.get("review_summary"),
                "ai_summary": normalized.get("ai_summary"),
                "property_rates_ai_summary": normalized.get("property_rates_ai_summary"),
                "insight_rates": normalized.get("insight_rates"),
                "demand_supply": normalized.get("demand_supply"),
                "listing_ranges": normalized.get("listing_ranges"),
                "cms_faq": normalized.get("cms_faq"),
                "featured_projects": normalized.get("featured_projects"),
                "projects_by_status": normalized.get("projects_by_status"),
                "page_property_type_context": normalized.get("page_property_type_context", {}),
                "rera_context": rera_context,
            },
            "source_meta": {
                "raw_source_meta": raw_source_meta,
                "keyword_intelligence_version": keyword_intelligence["version"],
                "competitor_intelligence_version": competitor_intelligence["version"],
            },
        }