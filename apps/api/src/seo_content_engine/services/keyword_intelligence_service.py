from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from seo_content_engine.core.config import settings
from seo_content_engine.services.dataforseo_client import DataForSEOClient
from seo_content_engine.services.keyword_seed_generator import KeywordSeedGenerator


class KeywordIntelligenceService:
    @staticmethod
    def _extract_items(raw_response: dict[str, Any]) -> list[dict[str, Any]]:
        tasks = raw_response.get("tasks", [])
        extracted_items: list[dict[str, Any]] = []

        for task in tasks:
            for result in task.get("result", []) or []:
                for item in result.get("items", []) or []:
                    keyword_value = item.get("keyword") or item.get("keyword_data", {}).get("keyword")
                    if not keyword_value:
                        continue

                    extracted_items.append(
                        {
                            "keyword": keyword_value,
                            "search_volume": item.get("search_volume"),
                            "keyword_info": item.get("keyword_info"),
                            "keyword_properties": item.get("keyword_properties"),
                            "avg_backlinks_info": item.get("avg_backlinks_info"),
                            "search_intent_info": item.get("search_intent_info"),
                        }
                    )

        return extracted_items

    @staticmethod
    def _dedupe_keywords(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen = set()

        for item in items:
            key = " ".join(item["keyword"].lower().split())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        return deduped

    @staticmethod
    def build_keyword_intelligence(
        normalized: dict[str, Any],
        location_name: str | None = None,
        language_name: str | None = None,
        limit: int | None = None,
        client: DataForSEOClient | None = None,
    ) -> dict[str, Any]:
        entity = normalized["entity"]
        page_type = entity["page_type"]

        resolved_location = location_name or settings.dataforseo_default_location_name
        resolved_language = language_name or settings.dataforseo_default_language_name
        resolved_limit = limit or settings.dataforseo_default_limit

        seeds = KeywordSeedGenerator.generate(normalized)
        client = client or DataForSEOClient()

        suggestions_by_seed: list[dict[str, Any]] = []
        related_by_seed: list[dict[str, Any]] = []
        all_suggestions: list[dict[str, Any]] = []
        all_related: list[dict[str, Any]] = []

        for seed in seeds:
            suggestions_raw = client.get_keyword_suggestions(
                keyword=seed,
                location_name=resolved_location,
                language_name=resolved_language,
                limit=resolved_limit,
            )
            suggestions_items = KeywordIntelligenceService._extract_items(suggestions_raw)
            suggestions_items = KeywordIntelligenceService._dedupe_keywords(suggestions_items)

            related_raw = client.get_related_keywords(
                keyword=seed,
                location_name=resolved_location,
                language_name=resolved_language,
                limit=resolved_limit,
                depth=settings.dataforseo_related_depth,
            )
            related_items = KeywordIntelligenceService._extract_items(related_raw)
            related_items = KeywordIntelligenceService._dedupe_keywords(related_items)

            suggestions_by_seed.append(
                {
                    "seed_keyword": seed,
                    "items_count": len(suggestions_items),
                    "items": suggestions_items,
                }
            )
            related_by_seed.append(
                {
                    "seed_keyword": seed,
                    "items_count": len(related_items),
                    "items": related_items,
                }
            )

            all_suggestions.extend(suggestions_items)
            all_related.extend(related_items)

        deduped_suggestions = KeywordIntelligenceService._dedupe_keywords(all_suggestions)
        deduped_related = KeywordIntelligenceService._dedupe_keywords(all_related)

        return {
            "version": "v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": page_type,
            "listing_type": entity["listing_type"],
            "entity": entity,
            "dataforseo_context": {
                "location_name": resolved_location,
                "language_name": resolved_language,
                "limit": resolved_limit,
                "related_depth": settings.dataforseo_related_depth,
            },
            "seed_keywords": seeds,
            "seed_count": len(seeds),
            "suggestions": {
                "total_unique_keywords": len(deduped_suggestions),
                "by_seed": suggestions_by_seed,
                "all_unique_items": deduped_suggestions,
            },
            "related_keywords": {
                "total_unique_keywords": len(deduped_related),
                "by_seed": related_by_seed,
                "all_unique_items": deduped_related,
            },
        }