from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from seo_content_engine.core.config import settings
from seo_content_engine.domain.enums import PageType
from seo_content_engine.services.competitor_intelligence_service import CompetitorIntelligenceService
from seo_content_engine.utils.formatters import slugify


class ContentPlanBuilder:
    COMMERCIAL_PROPERTY_TERMS = {
        "shop",
        "office space",
        "office spaces",
        "co-working space",
        "co working space",
        "warehouse",
        "showroom",
        "commercial",
    }

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
    def _has_landmarks_data(normalized: dict) -> bool:
        """D6: Returns True when at least one landmark category is present."""
        landmarks = normalized.get("landmarks", {}) or {}
        categories = landmarks.get("categories", []) or []
        return bool(categories)

    @staticmethod
    def _has_registration_data(normalized: dict) -> bool:
        """D7: Returns True when govt_registration or top_developers data is present."""
        govt_reg = normalized.get("govt_registration", {}) or {}
        top_devs = normalized.get("top_developers", []) or []
        return bool(govt_reg.get("transaction_count") or govt_reg.get("gross_value") or top_devs)

    @staticmethod
    def _has_demand_supply_data(normalized: dict) -> bool:
        demand_supply = normalized.get("demand_supply", {}) or {}
        listing_ranges = normalized.get("listing_ranges", {}) or {}

        sale = demand_supply.get("sale", {}) or {}
        sale_unit_type = sale.get("unitType", []) or []
        sale_listing_range = listing_ranges.get("sale_listing_range", {}) or {}

        return bool(sale_unit_type or sale_listing_range)

    @staticmethod
    def _has_price_range_data(normalized: dict) -> bool:
        sale_listing_range = (normalized.get("listing_ranges", {}) or {}).get("sale_listing_range", {}) or {}
        return bool(sale_listing_range)

    @staticmethod
    def _filter_residential_property_types(records: list[dict]) -> list[dict]:
        filtered: list[dict] = []
        for item in records or []:
            if not isinstance(item, dict):
                continue
            property_type = str(item.get("propertyType") or "").strip().lower()
            if not property_type:
                continue
            if any(term in property_type for term in ContentPlanBuilder.COMMERCIAL_PROPERTY_TERMS):
                continue
            filtered.append(item)
        return filtered

    @staticmethod
    def _filter_residential_distribution(records: list[dict]) -> list[dict]:
        filtered: list[dict] = []
        for item in records or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip().lower()
            if not key:
                continue
            if any(term in key for term in ContentPlanBuilder.COMMERCIAL_PROPERTY_TERMS):
                continue
            filtered.append(item)
        return filtered

    @staticmethod
    def _has_residential_property_type_data(normalized: dict) -> bool:
        pricing_summary = normalized.get("pricing_summary", {}) or {}
        distributions = normalized.get("distributions", {}) or {}

        property_types = ContentPlanBuilder._filter_residential_property_types(
            pricing_summary.get("property_types", []) or []
        )
        property_mix = ContentPlanBuilder._filter_residential_distribution(
            distributions.get("sale_property_type_distribution", []) or []
        )

        return bool(property_types or property_mix)

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
    def _keyword_limits_by_type(page_type: PageType | None) -> dict[str, int]:
        """B1 — Return per-cluster keyword limits based on entity type.

        LOCALITY pages emphasise BHK and price keywords (buyers search by BHK and budget).
        CITY pages emphasise secondary/area keywords for zone comparison.
        MICROMARKET pages balance BHK and area keywords.
        """
        if page_type == PageType.RESALE_LOCALITY:
            return {"bhk_limit": 8, "price_limit": 6, "secondary_limit": 4}
        if page_type == PageType.RESALE_CITY:
            return {"bhk_limit": 4, "price_limit": 8, "secondary_limit": 6}
        # MICROMARKET (default)
        return {"bhk_limit": 6, "price_limit": 5, "secondary_limit": 5}

    @staticmethod
    def _body_keyword_priority(
        keyword_clusters: dict,
        entity: dict,
        page_type: PageType | None = None,
    ) -> list[str]:
        limits = ContentPlanBuilder._keyword_limits_by_type(page_type)
        prioritized: list[str] = []
        seen: set[str] = set()

        for keyword in ContentPlanBuilder._primary_keyword_variants(keyword_clusters, entity):
            signature = keyword.lower()
            if signature in seen:
                continue
            seen.add(signature)
            prioritized.append(keyword)

        secondary_count = 0
        for record in keyword_clusters.get("secondary_keywords", []) or []:
            keyword = ContentPlanBuilder._extract_keyword_text(record)
            if not keyword:
                continue
            signature = keyword.lower()
            if signature in seen:
                continue
            seen.add(signature)
            prioritized.append(keyword)
            secondary_count += 1
            if secondary_count >= limits["secondary_limit"]:
                break

        # B1: Inject BHK keywords into body priority based on type-specific limit.
        bhk_count = 0
        for record in keyword_clusters.get("bhk_keywords", []) or []:
            keyword = ContentPlanBuilder._extract_keyword_text(record)
            if not keyword:
                continue
            signature = keyword.lower()
            if signature in seen:
                continue
            seen.add(signature)
            prioritized.append(keyword)
            bhk_count += 1
            if bhk_count >= limits["bhk_limit"]:
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
            "ready_to_move": ["ready_to_move"],
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
            "ready_to_move": ["property_status_table"],
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
            f"Explore {primary_keyword_text.lower()} with sale price details, BHK options, nearby localities, and resale market context on Square Yards.",
            f"Find {secondary_primary_keyword.lower()} with sale price trends, inventory mix, and nearby area insights on Square Yards.",
            f"Browse {tertiary_primary_keyword.lower()} with rates, property mix, and grounded resale information on Square Yards.",
            f"Check resale property options in {location_label} with sale price trends, BHK availability, locality comparisons, and source-backed data on Square Yards.",
        ]

        canonical_pricing = {
            "metric_name": "asking_price",
            "label": "sale price",
            "value": entity.get("canonical_asking_price"),
        }

        # Bug-fix: when the page is scoped to a specific property type (e.g. "flats",
        # "villas"), the H1 and slug should reflect that filter instead of the generic
        # "Resale Properties in ..." fallback.
        _pt_scope = entity.get("page_property_type_scope") or "all"
        _pt_type = entity.get("page_property_type")  # canonical, e.g. "Apartment"

        # Map canonical property types → buyer-friendly plural label used in H1/slug
        _pt_h1_labels: dict[str, str] = {
            "Apartment": "Flats",
            "Villa": "Villas",
            "Builder Floor": "Builder Floors",
            "Plot": "Plots",
            "House": "Houses",
            "Penthouse": "Penthouses",
            "Studio": "Studio Apartments",
            "Office Space": "Office Spaces",
            "Shop": "Shops",
            "Warehouse": "Warehouses",
            "Showroom": "Showrooms",
        }

        if _pt_scope == "specific" and _pt_type and _pt_type in _pt_h1_labels:
            _friendly = _pt_h1_labels[_pt_type]
            recommended_h1 = f"{_friendly} for Sale in {location_label}"[:120]
            recommended_slug = slugify(f"{_friendly.lower()}-for-sale-{entity_name}-{city_name}")
        else:
            recommended_h1 = f"Resale Properties in {location_label}"[:120]
            recommended_slug = slugify(f"resale-properties-{entity_name}-{city_name}")

        return {
            "primary_keyword": primary_keyword_text,
            "primary_keyword_variants": primary_keyword_variants,
            "supporting_keywords": metadata_keywords,
            "metadata_keyword_priority": metadata_keywords,
            "recommended_h1": recommended_h1,
            "recommended_slug": recommended_slug,
            "title_candidates": title_candidates,
            "meta_description_candidates": description_candidates,
            "canonical_pricing_metric": canonical_pricing,
            "refresh_plan": ContentPlanBuilder._build_refresh_plan(raw_source_meta),
        }

    # Table IDs that must never appear on resale pages — they carry new-project or
    # status-level data that is irrelevant (and misleading) for a resale listing page.
    RESALE_BLOCKED_TABLE_IDS: frozenset[str] = frozenset(
        {"property_status_table", "coverage_summary_table"}
    )

    @staticmethod
    def _build_table_plan(page_type: PageType, normalized: dict, entity: dict | None = None) -> list[dict]:
        _entity_name, _city_name = ContentPlanBuilder._entity_label_parts(entity or {})
        _eloc = _entity_name if _entity_name.lower() != _city_name.lower() else _city_name

        tables = [
            {
                "id": "price_trend_table",
                "title": f"Resale Price Trend — {_eloc}" if _eloc else "Price Trend Snapshot",
                "source_data_path": "pricing_summary.price_trend",
                "render_type": "deterministic",
                "columns": ["quarterName", "locationRate", "micromarketRate", "cityRate"],
                "summary_instruction": "Explain what this table helps the user compare and mention one visible row naturally.",
            },
            {
                "id": "sale_unit_type_distribution_table",
                "title": f"BHK Options in {_eloc}" if _eloc else "Available BHK Mix",
                "source_data_path": "distributions.sale_unit_type_distribution",
                "render_type": "deterministic",
                "columns": ["key", "doc_count"],
                "summary_instruction": "Explain what this table says about the available BHK mix and mention one visible row naturally.",
            },
        ]

        # nearby_localities_table is excluded for CITY pages: city-level pages use
        # location_rates_table (micromarket rate snapshot) for area comparison. The
        # nearby_localities data on a city page refers to the same micromarkets already
        # covered there and has missing distance/sale_count fields, creating duplicate noise.
        if page_type != PageType.RESALE_CITY:
            tables.append(
                {
                    "id": "nearby_localities_table",
                    "title": f"Localities Near {_eloc}" if _eloc else "Nearby Localities to Explore",
                    "source_data_path": "nearby_localities",
                    "render_type": "deterministic",
                    "columns": ["name", "distance_km", "sale_count", "sale_avg_price_per_sqft", "url"],
                    "summary_instruction": "Explain how this table helps compare nearby alternatives and mention one visible row naturally.",
                }
            )

        location_rates = normalized.get("pricing_summary", {}).get("location_rates", [])
        if location_rates:
            # D2: Type-aware table title and summary so the table label reflects what "name" means.
            _location_rates_title = {
                PageType.RESALE_CITY: f"Micromarket Rates in {_city_name}" if _city_name else "Micromarket Rate Snapshot",
                PageType.RESALE_MICROMARKET: f"Locality Rates in {_eloc}" if _eloc else "Locality Rate Snapshot",
                PageType.RESALE_LOCALITY: f"Sub-Locality Rates in {_eloc}" if _eloc else "Sub-Locality Rate Snapshot",
            }.get(page_type, f"Location Rates — {_eloc}" if _eloc else "Location Rate Snapshot")
            _location_rates_summary_instruction = {
                PageType.RESALE_CITY: (
                    "Each row represents a micromarket or zone within the city. "
                    "Explain how the sale price signals vary across zones and mention one visible row naturally."
                ),
                PageType.RESALE_MICROMARKET: (
                    "Each row represents a locality within this micromarket. "
                    "Explain how rates differ across localities and mention one visible row naturally."
                ),
                PageType.RESALE_LOCALITY: (
                    "Each row represents a sub-locality or cluster within this locality. "
                    "Explain what the rate signals show and mention one visible row naturally."
                ),
            }.get(page_type, "Explain what these location-rate signals show and mention one visible row naturally.")
            tables.append(
                {
                    "id": "location_rates_table",
                    "title": _location_rates_title,
                    "source_data_path": "pricing_summary.location_rates",
                    "render_type": "deterministic",
                    "columns": ["name", "avgRate", "changePercentage"],
                    "summary_instruction": _location_rates_summary_instruction,
                }
            )

        property_types = ContentPlanBuilder._filter_residential_property_types(
            normalized.get("pricing_summary", {}).get("property_types", []) or []
        )
        if property_types:
            tables.append(
                {
                    "id": "property_types_table",
                    "title": f"Property Type Rates in {_eloc}" if _eloc else "Property Type Rate Snapshot",
                    "source_data_path": "pricing_summary.property_types",
                    "render_type": "deterministic",
                    "columns": ["propertyType", "avgPrice", "changePercent"],
                    "summary_instruction": "Explain the visible residential property-type pricing signals and mention one visible row naturally.",
                }
            )

        # property_status_table and coverage_summary_table are intentionally excluded:
        # - property_status_table carries New Launch / Under Construction data which is
        #   new-project data, not resale data, and is misleading on a resale page.
        # - coverage_summary_table adds no actionable buyer value on a resale page.
        # Both are listed in RESALE_BLOCKED_TABLE_IDS for downstream enforcement.

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
        entity_name, city_name = ContentPlanBuilder._entity_label_parts(entity)
        page_type_str = str(entity.get("page_type") or "").lower()
        faq_keywords = keyword_clusters.get("faq_keyword_candidates", [])

        faq_intents = [
            {
                "id": "pricing",
                "question_template": f"What is the sale price for resale properties in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                "data_dependencies": ["pricing_summary.asking_price", "pricing_summary.price_trend"],
            },
            {
                "id": "price_range",
                "question_template": f"What is the price range for resale flats in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                "data_dependencies": ["listing_ranges.sale_listing_range", "pricing_summary.asking_price"],
            },
            {
                "id": "inventory",
                "question_template": f"How many resale properties are currently available in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
                "data_dependencies": ["listing_summary.sale_count", "listing_summary.total_listings"],
            },
            {
                "id": "bhk_availability",
                "question_template": f"Which BHK configurations are available in resale properties in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("bhk_keywords", []), 5),
                "data_dependencies": ["distributions.sale_unit_type_distribution"],
            },
            {
                "id": "price_trend",
                "question_template": f"How have resale property prices changed in {location_label} recently?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                "data_dependencies": ["pricing_summary.price_trend"],
            },
            {
                "id": "nearby_localities",
                "question_template": f"Which areas near {location_label} can buyers also explore for resale properties?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["nearby_localities"],
            },
            {
                "id": "property_type_signals",
                "question_template": f"What types of residential properties are available for resale in {location_label}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                "data_dependencies": ["pricing_summary.property_types", "distributions.sale_property_type_distribution"],
            },
        ]

        property_status = (normalized.get("pricing_summary", {}) or {}).get("property_status", []) or []
        if property_status:
            faq_intents.append(
                {
                    "id": "ready_to_move",
                    "question_template": f"Are ready-to-move resale properties visible in {location_label}?",
                    "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("ready_to_move_keywords", []), 4),
                    "data_dependencies": ["pricing_summary.property_status"],
                }
            )

        if ContentPlanBuilder._has_review_signals(normalized):
            faq_intents.append(
                {
                    "id": "review_signals",
                    "question_template": f"What review and rating signals are available for {location_label}?",
                    "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                    "data_dependencies": ["review_summary", "ai_summary"],
                }
            )

        property_rates_ai_summary = normalized.get("property_rates_ai_summary", {}) or {}
        if property_rates_ai_summary:
            faq_intents.append(
                {
                    "id": "property_rates_ai_signals",
                    "question_template": f"What market strengths, challenges, and opportunities are highlighted for {location_label}?",
                    "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                    "data_dependencies": ["property_rates_ai_summary"],
                }
            )

        if ContentPlanBuilder._has_demand_supply_data(normalized):
            faq_intents.append(
                {
                    "id": "demand_supply",
                    "question_template": f"What does the supply picture look like for resale listings in {location_label}?",
                    "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                    "data_dependencies": ["demand_supply", "listing_ranges", "listing_summary"],
                }
            )
            # Add a BHK-split demand intent if unit-type demand data is available
            demand_data = normalized.get("demand_supply", {}) or {}
            if demand_data.get("unit_type_splits") or demand_data.get("bhk_split"):
                faq_intents.append(
                    {
                        "id": "demand_supply_bhk_split",
                        "question_template": f"Which BHK sizes are in higher supply in {location_label} resale market?",
                        "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("bhk_keywords", []), 4),
                        "data_dependencies": ["demand_supply.unit_type_splits", "demand_supply.bhk_split"],
                    }
                )

        rera_context = ContentPlanBuilder._extract_rera_context(normalized)
        if rera_context:
            faq_intents.append(
                {
                    "id": "rera_buyer_protection",
                    "question_template": f"Are resale properties in {location_label} RERA-registered?",
                    "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                    "data_dependencies": ["rera_context"],
                }
            )

        # D8: FAQ — neighbourhood essentials (landmarks) for LOCALITY/MICROMARKET pages
        if ContentPlanBuilder._has_landmarks_data(normalized) and "city" not in page_type_str:
            faq_intents.append(
                {
                    "id": "neighbourhood_essentials_faq",
                    "question_template": f"What essential facilities and landmarks are accessible from {location_label}?",
                    "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                    "data_dependencies": ["landmarks"],
                }
            )

        # D8: FAQ — registration activity and developer trust signals
        if ContentPlanBuilder._has_registration_data(normalized):
            faq_intents.append(
                {
                    "id": "registration_activity_faq",
                    "question_template": f"How active is the property registration market in {location_label}?",
                    "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                    "data_dependencies": ["govt_registration", "top_developers"],
                }
            )

        # D8: FAQ — hot-selling localities for CITY pages
        if "city" in page_type_str:
            city_insights = normalized.get("city_insights", {}) or {}
            hot_selling = city_insights.get("hot_selling_localities", []) or []
            if hot_selling:
                faq_intents.append(
                    {
                        "id": "hot_selling_localities_faq",
                        "question_template": f"Which localities in {city_name} have the highest resale listing activity?",
                        "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
                        "data_dependencies": ["city_insights.hot_selling_localities"],
                    }
                )

        # Location comparison: how does this location compare to the broader city/micromarket?
        price_trend = normalized.get("pricing_summary", {}).get("price_trend", [])
        if price_trend and len(price_trend) > 0:
            faq_intents.append(
                {
                    "id": "location_vs_benchmark",
                    "question_template": (
                        f"How do resale property prices in {location_label} compare to the broader {city_name} market?"
                    ),
                    "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                    "data_dependencies": ["pricing_summary.price_trend"],
                }
            )

        # City-page specific: coverage of micromarkets
        if "city" in page_type_str:
            listing_summary = normalized.get("listing_summary", {}) or {}
            if listing_summary.get("total_listings") or listing_summary.get("sale_count"):
                faq_intents.append(
                    {
                        "id": "city_market_coverage",
                        "question_template": f"How much of the {city_name} resale market does this page cover?",
                        "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
                        "data_dependencies": ["listing_summary"],
                    }
                )

        # Micromarket-page specific: locality coverage
        if "micromarket" in page_type_str:
            listing_summary = normalized.get("listing_summary", {}) or {}
            if listing_summary.get("total_listings") or listing_summary.get("sale_count"):
                faq_intents.append(
                    {
                        "id": "micromarket_locality_coverage",
                        "question_template": f"Which localities in {entity_name} have resale properties available?",
                        "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 4),
                        "data_dependencies": ["listing_summary", "nearby_localities"],
                    }
                )

        return {
            "total_faq_intents": len(faq_intents),
            "faq_intents": faq_intents,
        }

    @staticmethod
    def _build_sections(page_type: PageType, entity: dict, keyword_clusters: dict, normalized: dict) -> list[dict]:
        entity_name, city_name = ContentPlanBuilder._entity_label_parts(entity)
        # Use city_name as fallback if entity_name equals city_name (CITY pages)
        _loc = entity_name if entity_name.lower() != city_name.lower() else city_name
        _loc_with_city = f"{entity_name}, {city_name}" if entity_name.lower() != city_name.lower() else city_name

        has_review_signals = ContentPlanBuilder._has_review_signals(normalized)
        has_demand_supply = ContentPlanBuilder._has_demand_supply_data(normalized)
        has_residential_property_signals = ContentPlanBuilder._has_residential_property_type_data(normalized)
        has_property_rates_ai = bool(normalized.get("property_rates_ai_summary", {}) or {})
        has_landmarks = ContentPlanBuilder._has_landmarks_data(normalized)
        has_registration = ContentPlanBuilder._has_registration_data(normalized)

        common_sections = [
            {
                "id": "market_snapshot",
                "title": f"Resale Market Overview — {_loc}",
                "objective": (
                    "What is a buyer actually looking at on this page right now? "
                    "Open with a grounded overview of the visible resale market, and keep it residential-first."
                ),
                "render_type": "generative",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 5),
                "data_dependencies": ["listing_summary", "pricing_summary", "distributions", "page_property_type_context"],
            },
            {
                "id": "price_trends_and_rates",
                "title": f"Resale Price Trends in {_loc}",
                "objective": (
                    "What does the current sale price view look like, and what does the trend table help a buyer compare?"
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
                "title": f"BHK Options and Inventory in {_loc}",
                "objective": (
                    "Which home sizes and visible inventory buckets are showing up here, and how should a buyer read that mix?"
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
            "title": f"Localities Near {_loc} to Explore",
            "objective": (
                "Which nearby areas can a buyer compare without leaving the resale context, and what does the nearby view help with?"
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["nearby_localities"],
        }

        review_signals_section = {
            "id": "review_and_rating_signals",
            "title": f"Resident Reviews and Ratings — {_loc}",
            "objective": (
                "What do the available review counts, ratings, and tags say about the feedback visible on this page?"
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["review_summary", "ai_summary"],
        }

        property_rates_ai_section = {
            "id": "property_rates_ai_signals",
            "title": f"Market Insights for {_loc_with_city}",
            "objective": (
                "Present the property-rates AI notes exactly as a restrained summary of the supplied snapshot and lists, without interpreting them."
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["property_rates_ai_summary"],
        }

        demand_supply_section = {
            "id": "demand_and_supply_signals",
            "title": f"Resale Supply Signals — {_loc}",
            "objective": (
                "What resale breadth, configuration split, or listing-range cues are actually visible in this sample?"
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["demand_supply", "listing_ranges", "listing_summary"],
        }

        property_type_signals_section = {
            "id": "property_type_signals",
            "title": f"Property Types in {_loc}",
            "objective": (
                "Which residential property formats are visible here, and how do they appear in the current resale mix?"
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
            "title": f"Property Type Rates in {_loc_with_city}",
            "objective": (
                "How should a buyer read the residential property-type and location-rate view without turning it into a generic market recap?"
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
            "title": f"Localities in {_loc_with_city}",
            "objective": (
                "Which localities are visible inside this micromarket view, and what does that help a buyer compare?"
            ),
            "render_type": "generative",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["listing_summary", "nearby_localities", "pricing_summary.location_rates"],
        }

        city_specific = {
            "id": "micromarket_coverage",
            "title": f"Key Resale Zones Across {city_name}",
            "objective": (
                "How are visible resale rate signals distributed across the city, and where do the higher and lower visible bands sit?"
            ),
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["listing_summary", "pricing_summary.location_rates", "nearby_localities"],
        }

        # D6: Neighbourhood essentials — landmarks summary for LOCALITY/MICROMARKET pages
        neighbourhood_essentials_section = {
            "id": "neighbourhood_essentials",
            "title": f"Neighbourhood Essentials Near {_loc}",
            "objective": (
                "What day-to-day infrastructure is visible near this location? "
                "Describe the landmark categories present (hospitals, schools, banks, etc.) "
                "and what they signal about everyday livability."
            ),
            "render_type": "generative",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["landmarks"],
        }

        # D7: Market registration activity — govt registration + top developers for all entity types
        market_registration_section = {
            "id": "market_registration_activity",
            "title": f"Property Registrations in {_loc_with_city}",
            "objective": (
                "What do the government registration transaction count and gross value say about buyer activity? "
                "Which developers have a visible presence in this market?"
            ),
            "render_type": "generative",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
            "data_dependencies": ["govt_registration", "top_developers"],
        }

        sections = list(common_sections)

        if has_review_signals:
            sections.insert(3, review_signals_section)

        if has_property_rates_ai:
            sections.insert(4 if has_review_signals else 3, property_rates_ai_section)

        if has_demand_supply:
            insert_index = 5 if has_review_signals and has_property_rates_ai else 4 if (has_review_signals or has_property_rates_ai) else 3
            sections.insert(insert_index, demand_supply_section)

        if has_residential_property_signals:
            sections.insert(len(sections) - 2, property_type_signals_section)
            sections.insert(len(sections) - 2, property_type_rate_snapshot_section)

        # D6: Add neighbourhood_essentials for LOCALITY/MICROMARKET pages (before faq and internal_links)
        if has_landmarks and page_type in {PageType.RESALE_LOCALITY, PageType.RESALE_MICROMARKET}:
            sections.insert(len(sections) - 2, neighbourhood_essentials_section)

        # D7: Add market_registration_activity for all entity types when data is present
        if has_registration:
            sections.insert(len(sections) - 2, market_registration_section)

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
        page_type: PageType | None = None,
    ) -> dict[str, dict]:
        context_map: dict[str, dict] = {}

        primary_keyword_variants = ContentPlanBuilder._primary_keyword_variants(
            keyword_clusters,
            entity,
        )
        body_keyword_priority = ContentPlanBuilder._body_keyword_priority(
            keyword_clusters,
            entity,
            page_type=page_type,
        )
        page_property_type_context = ContentPlanBuilder._page_property_type_context(
            normalized,
            entity,
        )
        buyer_segmentation = ContentPlanBuilder._build_city_zone_segmentation(
            normalized.get("pricing_summary", {}) or {}
        )

        # Build entity-type framing notes once, used per-section below.
        page_type_value = page_type.value if page_type else entity.get("page_type", "")
        _entity_type_framing: dict[str, str] = {
            "resale_city": (
                "This is a city-level page. The reader is comparing broad zones or micromarkets within the city. "
                "Frame all data in terms of which zones offer which price bands. Avoid hyper-local detail."
            ),
            "resale_micromarket": (
                "This is a micromarket-level page. The reader has shortlisted this area and is comparing "
                "localities within it. Frame data to help them navigate sub-areas and price tiers inside the micromarket."
            ),
            "resale_locality": (
                "This is a locality-level page. The reader is actively evaluating a specific neighbourhood. "
                "Lead with what the locality offers: BHK mix, sale price, nearby alternatives, and walkability signals."
            ),
        }
        entity_type_context: dict[str, Any] = {
            "page_type": page_type_value,
            "framing_note": _entity_type_framing.get(page_type_value, "Frame data in terms of what a resale buyer needs."),
        }
        # Inject locality ai_summary for LOCALITY pages (D1 — locality character into entity_type_context)
        if page_type == PageType.RESALE_LOCALITY:
            ai_summary = normalized.get("ai_summary") or {}
            locality_summary = ai_summary.get("locality_summary") or ""
            if locality_summary:
                entity_type_context["locality_character_summary"] = locality_summary

        for section in section_plan:
            section_context: dict[str, Any] = {"entity": entity}

            for dependency in section.get("data_dependencies", []):
                # D1: For LOCALITY market_snapshot, also resolve ai_summary so the
                # locality character summary is available to the LLM without changing section_plan.
                if (
                    dependency == "listing_summary"
                    and section.get("id") == "market_snapshot"
                    and page_type == PageType.RESALE_LOCALITY
                ):
                    ai_summary = normalized.get("ai_summary")
                    if ai_summary:
                        section_context["ai_summary"] = ai_summary

                value = ContentPlanBuilder._resolve_dependency_value(normalized, dependency)
                if value is None:
                    continue
                section_context[dependency] = value

            # Inject the entity_type_context into every section so the LLM understands
            # the page scope and frames content accordingly (A2).
            section_context["entity_type_context"] = entity_type_context

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
                        "Open with what a buyer is actually seeing here. "
                        "CRITICAL: If page_property_type_context.scope is 'specific', you MUST write ONLY about that one property type "
                        "(e.g. only apartments/flats, only villas, only plots). Do NOT mention other property types at all. "
                        "If the page scope is 'all', summarize only relevant residential property types visible in source data. "
                        "Do not mix residential and commercial types."
                    ),
                }

            if section["id"] == "price_trends_and_rates":
                section_context["narrative_guardrails"] = {
                    "allowed_pricing_metrics": ["asking_price"],
                    "disallowed_pricing_metrics": ["registration_rate", "sale_avg_price_per_sqft"],
                    "instruction": (
                        "Use only sale price and price_trend in prose. "
                        "Explain what the sale price signal is and what the trend comparison helps a buyer understand."
                    ),
                }

            if section["id"] == "review_and_rating_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["review_summary", "ai_summary"],
                    "instruction": (
                        "Use only explicit review counts, rating values, tags, and ai_summary inputs. "
                        "Do not infer trust, desirability, or sentiment beyond the source."
                    ),
                }

            if section["id"] == "property_rates_ai_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["property_rates_ai_summary"],
                    "instruction": (
                        "Use only explicit property_rates_ai_summary fields. "
                        "Break the response into a short snapshot followed by Strengths, Challenges, and Opportunities. "
                        "Do not add advice, forecasts, or market interpretation."
                    ),
                }

            if section["id"] == "demand_and_supply_signals":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["demand_supply", "listing_ranges", "listing_summary"],
                    "instruction": (
                        "Use only explicit counts, percentages, availability, and listing-range values. "
                        "If the source block is absent or thin, keep the section narrow and factual."
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
                        "CRITICAL: If page_property_type_context.scope is 'specific', write ONLY about that single property type. "
                        "Do not mention any other property types. Focus entirely on inventory count, price, and BHK breakdown for that type. "
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
                        "CRITICAL: If page_property_type_context.scope is 'specific', discuss rates only for that property type. "
                        "Do not mention other property types. "
                        "Avoid technical field language and avoid repeating the market snapshot section."
                    ),
                }

            if section["id"] == "micromarket_coverage":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["pricing_summary.location_rates", "buyer_segmentation"],
                    "instruction": (
                        "For city pages, explain covered zones using the visible location-rate rows. "
                        "Where clear tiers exist, explain them simply as pricing bands. "
                        "If buyer_segmentation is absent, fall back to framing by sale price tier from location_rates. "
                        "Do not add unsupported investment or growth claims."
                    ),
                }

            # A2: Locality_coverage guardrails for MICROMARKET pages — previously had no framing.
            if section["id"] == "locality_coverage":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["pricing_summary.location_rates", "nearby_localities", "listing_summary"],
                    "instruction": (
                        "Explain which localities are visible inside this micromarket. "
                        "Mention the count of localities covered if visible. "
                        "Highlight the top-priced and lowest-priced localities if data allows. "
                        "Help the buyer understand how to navigate across the localities — what each sub-area is known for in pricing terms. "
                        "Avoid repeating the market_snapshot section. Do not add investment advice."
                    ),
                }

            # D6: Guardrails for neighbourhood_essentials (landmarks section)
            if section["id"] == "neighbourhood_essentials":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["landmarks"],
                    "instruction": (
                        "Use only the landmark category names, counts, and top landmark names from the landmarks data. "
                        "Group by category (hospitals, schools, banks, etc.). "
                        "Describe what the visible infrastructure suggests about everyday livability. "
                        "Do not fabricate landmark names or distances not present in the data. "
                        "Keep the section factual and scannable."
                    ),
                }

            # D7: Guardrails for market_registration_activity section
            if section["id"] == "market_registration_activity":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["govt_registration", "top_developers"],
                    "instruction": (
                        "Use only govt_registration fields (transaction_count, gross_value, registered_rate, date_range) "
                        "and top_developers names and counts to describe market activity. "
                        "Frame registration data as a signal of buyer demand in the specified time period. "
                        "Name up to 5 top developers when present. "
                        "Do not add growth forecasts or investment advice."
                    ),
                }

            # A3: Narrative rules for nearby_alternatives section (LOCALITY pages).
            if section["id"] == "nearby_alternatives":
                section_context["narrative_guardrails"] = {
                    "allowed_inputs": ["nearby_localities"],
                    "instruction": (
                        "Highlight at most 4–5 nearby locality alternatives. "
                        "For each, frame by distance from current locality and sale price comparison where data allows. "
                        "Note which alternatives have more inventory visible. "
                        "The table already lists all options — prose should highlight only the most relevant alternatives, not list all rows."
                    ),
                }

            # B2: Inject BHK keyword phrases into bhk_and_inventory_mix so the LLM
            # has both the data distribution AND the exact keyword forms to use.
            if section["id"] == "bhk_and_inventory_mix":
                bhk_phrases = ContentPlanBuilder._top_keywords(
                    keyword_clusters.get("bhk_keywords", []), 6
                )
                if bhk_phrases:
                    section_context["target_bhk_phrases"] = bhk_phrases

            context_map[section["id"]] = section_context

        return context_map

    @staticmethod
    def build(normalized: dict, keyword_intelligence: dict) -> dict:
        entity = dict(normalized["entity"])
        pricing_summary = normalized.get("pricing_summary", {}) or {}
        entity["canonical_asking_price"] = pricing_summary.get("asking_price")
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
            ContentPlanBuilder._build_table_plan(page_type, normalized, entity),
            competitor_intelligence,
        )

        planning_signals = ContentPlanBuilder._build_planning_signals(
            competitor_intelligence,
            page_type,
        )

        return {
            "version": "v1.9",
            "generated_at": datetime.now(timezone.utc).isoformat(),
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
                    page_type=page_type,
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
                page_type=page_type,
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
                # D5: New data fields from enhanced normalizer
                "landmarks": normalized.get("landmarks"),
                "govt_registration": normalized.get("govt_registration"),
                "top_developers": normalized.get("top_developers"),
                "city_insights": normalized.get("city_insights"),
            },
            "source_meta": {
                "raw_source_meta": raw_source_meta,
                "keyword_intelligence_version": keyword_intelligence["version"],
                "competitor_intelligence_version": competitor_intelligence["version"],
            },
        }