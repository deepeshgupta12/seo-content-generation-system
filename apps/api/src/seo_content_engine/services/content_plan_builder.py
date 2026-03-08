from __future__ import annotations

from datetime import UTC, datetime

from seo_content_engine.domain.enums import PageType
from seo_content_engine.utils.formatters import slugify


class ContentPlanBuilder:
    @staticmethod
    def _top_keywords(records: list[dict], limit: int = 5) -> list[str]:
        return [record["keyword"] for record in records[:limit]]

    @staticmethod
    def _build_metadata_plan(entity: dict, keyword_clusters: dict) -> dict:
        entity_name = entity["entity_name"]
        city_name = entity["city_name"]

        primary_keyword = keyword_clusters.get("primary_keyword")
        primary_keyword_text = primary_keyword["keyword"] if primary_keyword else f"resale properties in {entity_name} {city_name}"

        metadata_keywords = keyword_clusters.get("metadata_keywords", [])
        title_candidates = [
            f"Resale Properties in {entity_name}, {city_name} | Square Yards",
            f"{entity_name}, {city_name} Resale Properties for Sale | Square Yards",
            f"Flats for Sale in {entity_name}, {city_name} | Square Yards",
        ]

        description_candidates = [
            f"Explore resale properties in {entity_name}, {city_name} with prices, BHK options, nearby localities, and current market signals on Square Yards.",
            f"Find flats and resale properties in {entity_name}, {city_name} with price trends, inventory mix, and nearby area insights on Square Yards.",
            f"Browse resale listings in {entity_name}, {city_name} with rates, property mix, and key buying insights on Square Yards.",
        ]

        return {
            "primary_keyword": primary_keyword_text,
            "supporting_keywords": metadata_keywords,
            "recommended_h1": f"Resale Properties in {entity_name}, {city_name}",
            "recommended_slug": slugify(f"resale-properties-{entity_name}-{city_name}"),
            "title_candidates": title_candidates,
            "meta_description_candidates": description_candidates,
        }

    @staticmethod
    def _build_table_plan(page_type: PageType, normalized: dict) -> list[dict]:
        tables = [
            {
                "id": "price_trend_table",
                "title": "Price Trend Snapshot",
                "source_data_path": "pricing_summary.price_trend",
                "render_type": "deterministic",
                "columns": ["quarterName", "locationRate", "micromarketRate"],
            },
            {
                "id": "sale_unit_type_distribution_table",
                "title": "Available BHK Mix",
                "source_data_path": "distributions.sale_unit_type_distribution",
                "render_type": "deterministic",
                "columns": ["key", "doc_count"],
            },
            {
                "id": "nearby_localities_table",
                "title": "Nearby Localities to Explore",
                "source_data_path": "nearby_localities",
                "render_type": "deterministic",
                "columns": ["name", "distance_km", "sale_count", "sale_avg_price_per_sqft"],
            },
        ]

        top_projects = normalized.get("top_projects", {})
        if top_projects:
            tables.append(
                {
                    "id": "top_projects_table",
                    "title": "Selected Top Project Signals",
                    "source_data_path": "top_projects",
                    "render_type": "deterministic",
                    "columns": ["projectName", "currentRate", "saleRentValue", "noOfTransactions"],
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
                }
            )

        return tables

    @staticmethod
    def _build_internal_links_plan(normalized: dict) -> dict:
        links = normalized["links"]
        nearby_localities = normalized["nearby_localities"]

        return {
            "sale_unit_type_links": links.get("sale_unit_type_urls", []),
            "sale_property_type_links": links.get("sale_property_type_urls", []),
            "quick_links": links.get("sale_quick_links", []),
            "nearby_locality_links": [
                {
                    "label": item["name"],
                    "url": item.get("url"),
                }
                for item in nearby_localities
                if item.get("name") and item.get("url")
            ],
        }

    @staticmethod
    def _build_faq_plan(entity: dict, keyword_clusters: dict, normalized: dict) -> dict:
        entity_name = entity["entity_name"]
        city_name = entity["city_name"]

        faq_keywords = keyword_clusters.get("faq_keyword_candidates", [])
        faq_intents = [
            {
                "id": "pricing",
                "question_template": f"What is the average price of resale properties in {entity_name}, {city_name}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 3),
                "data_dependencies": ["pricing_summary.asking_price", "pricing_summary.price_trend"],
            },
            {
                "id": "inventory",
                "question_template": f"How many resale properties are available in {entity_name}, {city_name}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 3),
                "data_dependencies": ["listing_summary.sale_count", "listing_summary.total_listings"],
            },
            {
                "id": "bhk_availability",
                "question_template": f"Which BHK options are commonly available in {entity_name}, {city_name}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("bhk_keywords", []), 4),
                "data_dependencies": ["distributions.sale_unit_type_distribution"],
            },
            {
                "id": "ready_to_move",
                "question_template": f"Are ready-to-move resale properties available in {entity_name}, {city_name}?",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("ready_to_move_keywords", []), 3),
                "data_dependencies": ["pricing_summary.property_status"],
            },
            {
                "id": "nearby_localities",
                "question_template": f"Which nearby localities can buyers also consider around {entity_name}, {city_name}?",
                "target_keywords": ContentPlanBuilder._top_keywords(faq_keywords, 3),
                "data_dependencies": ["nearby_localities"],
            },
        ]

        return {
            "total_faq_intents": len(faq_intents),
            "faq_intents": faq_intents,
        }

    @staticmethod
    def _build_sections(page_type: PageType, entity: dict, keyword_clusters: dict) -> list[dict]:
        entity_name = entity["entity_name"]
        city_name = entity["city_name"]

        common_sections = [
            {
                "id": "hero_intro",
                "title": f"Resale Property Overview in {entity_name}, {city_name}",
                "objective": "Introduce the page clearly and establish the main sale/resale intent.",
                "render_type": "generative",
                "target_keywords": [keyword_clusters.get("primary_keyword", {}).get("keyword")] if keyword_clusters.get("primary_keyword") else [],
                "data_dependencies": ["entity", "listing_summary", "pricing_summary"],
            },
            {
                "id": "market_snapshot",
                "title": "Resale Market Snapshot",
                "objective": "Summarize inventory, listing activity, and overall resale positioning.",
                "render_type": "generative",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
                "data_dependencies": ["listing_summary", "pricing_summary"],
            },
            {
                "id": "price_trends_and_rates",
                "title": "Price Trends and Rates",
                "objective": "Explain price trends and rates using deterministic market data.",
                "render_type": "hybrid",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("price_keywords", []), 4),
                "data_dependencies": ["pricing_summary.asking_price", "pricing_summary.registration_rate", "pricing_summary.price_trend"],
            },
            {
                "id": "bhk_and_inventory_mix",
                "title": "BHK and Inventory Mix",
                "objective": "Highlight what BHK and property types are typically available for sale.",
                "render_type": "hybrid",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("bhk_keywords", []), 5),
                "data_dependencies": ["distributions.sale_unit_type_distribution", "distributions.sale_property_type_distribution"],
            },
            {
                "id": "buyer_guidance",
                "title": "What Buyers Can Explore Here",
                "objective": "Help buyers understand the type of resale options they can explore here.",
                "render_type": "generative",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 4),
                "data_dependencies": ["listing_summary", "pricing_summary", "links"],
            },
            {
                "id": "faq_section",
                "title": "Frequently Asked Questions",
                "objective": "Cover key buying and market questions with grounded answers.",
                "render_type": "generative",
                "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("faq_keyword_candidates", []), 6),
                "data_dependencies": ["pricing_summary", "listing_summary", "distributions", "nearby_localities"],
            },
            {
                "id": "internal_links",
                "title": "Explore More Property Options",
                "objective": "Guide users to relevant listing, unit-type, property-type, and nearby pages.",
                "render_type": "deterministic",
                "target_keywords": [],
                "data_dependencies": ["links", "nearby_localities"],
            },
        ]

        locality_specific = {
            "id": "nearby_alternatives",
            "title": "Nearby Localities Buyers Can Also Explore",
            "objective": "Highlight nearby alternatives around the locality using actual Square Yards locality data.",
            "render_type": "hybrid",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 3),
            "data_dependencies": ["nearby_localities"],
        }

        micromarket_specific = {
            "id": "locality_coverage",
            "title": "Localities Covered in This Micromarket",
            "objective": "Explain the micromarket coverage and local resale opportunity spread.",
            "render_type": "generative",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 3),
            "data_dependencies": ["listing_summary", "nearby_localities"],
        }

        city_specific = {
            "id": "micromarket_coverage",
            "title": "Key Resale Zones Across the City",
            "objective": "Introduce how resale opportunities are distributed across the city.",
            "render_type": "generative",
            "target_keywords": ContentPlanBuilder._top_keywords(keyword_clusters.get("secondary_keywords", []), 3),
            "data_dependencies": ["listing_summary", "links"],
        }

        if page_type == PageType.RESALE_LOCALITY:
            return common_sections[:4] + [locality_specific] + common_sections[4:]
        if page_type == PageType.RESALE_MICROMARKET:
            return common_sections[:2] + [micromarket_specific] + common_sections[2:]
        if page_type == PageType.RESALE_CITY:
            return common_sections[:2] + [city_specific] + common_sections[2:]

        return common_sections

    @staticmethod
    def build(normalized: dict, keyword_intelligence: dict) -> dict:
        entity = normalized["entity"]
        page_type = PageType(entity["page_type"])
        keyword_clusters = keyword_intelligence["keyword_clusters"]

        return {
            "version": "v1.2",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": entity["page_type"],
            "listing_type": entity["listing_type"],
            "entity": entity,
            "metadata_plan": ContentPlanBuilder._build_metadata_plan(entity, keyword_clusters),
            "keyword_strategy": {
                "primary_keyword": keyword_clusters.get("primary_keyword"),
                "secondary_keywords": keyword_clusters.get("secondary_keywords", []),
                "bhk_keywords": keyword_clusters.get("bhk_keywords", []),
                "price_keywords": keyword_clusters.get("price_keywords", []),
                "ready_to_move_keywords": keyword_clusters.get("ready_to_move_keywords", []),
                "faq_keyword_candidates": keyword_clusters.get("faq_keyword_candidates", []),
                "metadata_keywords": keyword_clusters.get("metadata_keywords", []),
            },
            "section_plan": ContentPlanBuilder._build_sections(page_type, entity, keyword_clusters),
            "table_plan": ContentPlanBuilder._build_table_plan(page_type, normalized),
            "faq_plan": ContentPlanBuilder._build_faq_plan(entity, keyword_clusters, normalized),
            "internal_links_plan": ContentPlanBuilder._build_internal_links_plan(normalized),
            "data_context": {
                "listing_summary": normalized["listing_summary"],
                "pricing_summary": normalized["pricing_summary"],
                "distributions": normalized["distributions"],
                "nearby_localities": normalized["nearby_localities"],
                "top_projects": normalized["top_projects"],
            },
            "source_meta": {
                "raw_source_meta": normalized["raw_source_meta"],
                "keyword_intelligence_version": keyword_intelligence["version"],
            },
        }