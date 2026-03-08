from __future__ import annotations

from datetime import UTC, datetime

from seo_content_engine.domain.enums import PageType
from seo_content_engine.utils.formatters import slugify


class BlueprintBuilder:
    @staticmethod
    def build(normalized: dict) -> dict:
        entity = normalized["entity"]
        page_type = PageType(entity["page_type"])

        section_map = {
            PageType.RESALE_LOCALITY: [
                "hero_intro",
                "market_snapshot",
                "price_trend_summary",
                "inventory_mix",
                "nearby_localities_table",
                "faq_seed_block",
                "internal_links",
            ],
            PageType.RESALE_MICROMARKET: [
                "hero_intro",
                "market_snapshot",
                "locality_coverage",
                "price_trend_summary",
                "inventory_mix",
                "faq_seed_block",
                "internal_links",
            ],
            PageType.RESALE_CITY: [
                "hero_intro",
                "market_snapshot",
                "micromarket_coverage",
                "price_trend_summary",
                "inventory_mix",
                "faq_seed_block",
                "internal_links",
            ],
        }

        entity_name = entity["entity_name"]
        city_name = entity["city_name"]

        return {
            "version": "v0",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": entity["page_type"],
            "listing_type": entity["listing_type"],
            "entity": entity,
            "seo_stub": {
                "suggested_h1": f"Resale Properties in {entity_name}, {city_name}",
                "suggested_title_stub": f"Resale Properties in {entity_name}, {city_name} | Square Yards",
                "suggested_slug_stub": slugify(f"resale-properties-{entity_name}-{city_name}"),
            },
            "data_blocks": {
                "listing_summary": normalized["listing_summary"],
                "pricing_summary": normalized["pricing_summary"],
                "distributions": normalized["distributions"],
                "nearby_localities": normalized["nearby_localities"],
                "links": normalized["links"],
                "top_projects": normalized["top_projects"],
            },
            "sections": [{"id": section_id, "status": "planned"} for section_id in section_map[page_type]],
            "faq_seed_questions": [
                f"What is the average asking price of resale properties in {entity_name}, {city_name}?",
                f"How many resale listings are available in {entity_name}, {city_name}?",
                f"Which unit types are commonly available for sale in {entity_name}, {city_name}?",
                f"Which nearby localities can buyers also consider around {entity_name}, {city_name}?",
            ],
            "source_meta": normalized["raw_source_meta"],
        }