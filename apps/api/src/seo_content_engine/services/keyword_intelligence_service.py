from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from seo_content_engine.core.config import settings
from seo_content_engine.services.dataforseo_client import DataForSEOClient
from seo_content_engine.services.keyword_processing import KeywordProcessing
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
                    extracted_items.append(item)

        return extracted_items

    @staticmethod
    def _dedupe_raw_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen = set()

        for item in items:
            keyword = item.get("keyword") or item.get("keyword_data", {}).get("keyword") or ""
            key = " ".join(keyword.lower().split())
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        return deduped

    @staticmethod
    def _normalize_group(
        grouped_items: list[dict[str, Any]],
        source: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        by_seed: list[dict[str, Any]] = []
        all_items: list[dict[str, Any]] = []

        for group in grouped_items:
            seed_keyword = group["seed_keyword"]
            raw_items = KeywordIntelligenceService._dedupe_raw_items(group["raw_items"])
            normalized_items = [
                KeywordProcessing.normalize_raw_item(item, source=source, seed_keyword=seed_keyword)
                for item in raw_items
            ]

            by_seed.append(
                {
                    "seed_keyword": seed_keyword,
                    "items_count": len(normalized_items),
                    "items": normalized_items,
                }
            )
            all_items.extend(normalized_items)

        return by_seed, all_items

    @staticmethod
    def build_keyword_intelligence(
        normalized: dict[str, Any],
        location_name: str | None = None,
        language_name: str | None = None,
        limit: int | None = None,
        include_historical: bool = True,
        client: DataForSEOClient | None = None,
    ) -> dict[str, Any]:
        entity = normalized["entity"]
        page_type = entity["page_type"]

        resolved_location = location_name or settings.dataforseo_default_location_name
        resolved_language = language_name or settings.dataforseo_default_language_name
        resolved_limit = limit or settings.dataforseo_default_limit

        seeds = KeywordSeedGenerator.generate(normalized)
        client = client or DataForSEOClient()
        warnings: list[str] = []

        suggestions_raw_groups: list[dict[str, Any]] = []
        related_raw_groups: list[dict[str, Any]] = []

        for seed in seeds:
            suggestions_raw = client.get_keyword_suggestions(
                keyword=seed,
                location_name=resolved_location,
                language_name=resolved_language,
                limit=resolved_limit,
            )
            suggestions_raw_groups.append(
                {
                    "seed_keyword": seed,
                    "raw_items": KeywordIntelligenceService._extract_items(suggestions_raw),
                }
            )

            related_raw = client.get_related_keywords(
                keyword=seed,
                location_name=resolved_location,
                language_name=resolved_language,
                limit=resolved_limit,
                depth=settings.dataforseo_related_depth,
            )
            related_raw_groups.append(
                {
                    "seed_keyword": seed,
                    "raw_items": KeywordIntelligenceService._extract_items(related_raw),
                }
            )

        suggestions_by_seed, all_suggestions = KeywordIntelligenceService._normalize_group(
            suggestions_raw_groups,
            source="suggestions",
        )
        related_by_seed, all_related = KeywordIntelligenceService._normalize_group(
            related_raw_groups,
            source="related",
        )

        all_records = all_suggestions + all_related

        unique_for_historical = []
        seen_keywords = set()
        for record in all_records:
            key = record["normalized_keyword"]
            if not key or key in seen_keywords:
                continue
            seen_keywords.add(key)
            unique_for_historical.append(record["keyword"])

        historical_enriched = False
        historical_map: dict[str, dict[str, Any]] = {}

        if include_historical:
            try:
                historical_keywords = unique_for_historical[: settings.dataforseo_historical_keywords_limit]
                historical_raw = client.get_historical_search_volume(
                    keywords=historical_keywords,
                    location_name=resolved_location,
                    language_name=resolved_language,
                )
                historical_map = KeywordProcessing.extract_historical_map(historical_raw)
                all_records = KeywordProcessing.apply_historical_enrichment(all_records, historical_map)
                historical_enriched = True
            except Exception as exc:
                warnings.append(f"historical_enrichment_failed: {exc}")

        evaluated_records = [
            KeywordProcessing.evaluate_record(record, entity=entity)
            for record in all_records
        ]
        consolidated_records = KeywordProcessing.consolidate_records(evaluated_records)
        clusters = KeywordProcessing.build_clusters(consolidated_records)

        included_records = [record for record in consolidated_records if record["include"]]
        excluded_records = [record for record in consolidated_records if not record["include"]]

        return {
            "version": "v1.1",
            "generated_at": datetime.now(UTC).isoformat(),
            "page_type": page_type,
            "listing_type": entity["listing_type"],
            "entity": entity,
            "dataforseo_context": {
                "location_name": resolved_location,
                "language_name": resolved_language,
                "limit": resolved_limit,
                "related_depth": settings.dataforseo_related_depth,
                "historical_keywords_limit": settings.dataforseo_historical_keywords_limit,
                "historical_enriched": historical_enriched,
            },
            "warnings": warnings,
            "seed_keywords": seeds,
            "seed_count": len(seeds),
            "raw_retrieval": {
                "suggestions": {
                    "total_unique_keywords": len({item["normalized_keyword"] for item in all_suggestions}),
                    "by_seed": suggestions_by_seed,
                },
                "related_keywords": {
                    "total_unique_keywords": len({item["normalized_keyword"] for item in all_related}),
                    "by_seed": related_by_seed,
                },
            },
            "historical_enrichment": {
                "applied": historical_enriched,
                "historical_keywords_count": len(historical_map),
            },
            "normalized_keywords": {
                "total_records_before_consolidation": len(evaluated_records),
                "total_unique_records_after_consolidation": len(consolidated_records),
                "included_count": len(included_records),
                "excluded_count": len(excluded_records),
                "included_keywords": included_records,
                "excluded_keywords": excluded_records,
            },
            "keyword_clusters": clusters,
        }