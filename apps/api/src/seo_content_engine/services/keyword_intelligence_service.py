from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

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
    def _normalize_site_group(
        grouped_items: list[dict[str, Any]],
        source: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        by_site: list[dict[str, Any]] = []
        all_items: list[dict[str, Any]] = []

        for group in grouped_items:
            site_domain = group["site_domain"]
            raw_items = KeywordIntelligenceService._dedupe_raw_items(group["raw_items"])

            normalized_items: list[dict[str, Any]] = []
            for item in raw_items:
                enriched_item = dict(item)
                enriched_item["source_domain"] = site_domain
                normalized_items.append(
                    KeywordProcessing.normalize_raw_item(
                        enriched_item,
                        source=source,
                        seed_keyword=site_domain,
                    )
                )

            by_site.append(
                {
                    "site_domain": site_domain,
                    "items_count": len(normalized_items),
                    "items": normalized_items,
                }
            )
            all_items.extend(normalized_items)

        return by_site, all_items

    @staticmethod
    def _safe_domain(value: str | None) -> str | None:
        if not value:
            return None

        candidate = value.strip()
        if not candidate:
            return None

        if "://" not in candidate:
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)
        domain = (parsed.netloc or parsed.path or "").lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or None

    @staticmethod
    def _extract_serp_items(raw_response: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for task in raw_response.get("tasks", []) or []:
            for result in task.get("result", []) or []:
                for item in result.get("items", []) or []:
                    items.append(item)

        return items

    @staticmethod
    def _extract_competitor_domains(
        serp_groups: list[dict[str, Any]],
        *,
        limit: int,
    ) -> list[str]:
        blocked_domains = {
            "squareyards.com",
            "google.com",
            "youtube.com",
            "facebook.com",
            "instagram.com",
            "linkedin.com",
            "x.com",
            "twitter.com",
            "reddit.com",
            "justdial.com",
        }

        ranked_domains: list[str] = []
        seen: set[str] = set()

        for group in serp_groups:
            for item in group.get("items", []):
                if (item.get("type") or "").lower() != "organic":
                    continue

                domain = KeywordIntelligenceService._safe_domain(item.get("domain") or item.get("url"))
                if not domain or domain in seen or domain in blocked_domains:
                    continue

                seen.add(domain)
                ranked_domains.append(domain)

                if len(ranked_domains) >= limit:
                    return ranked_domains

        return ranked_domains

    @staticmethod
    def _build_unique_keywords(records: list[dict[str, Any]], limit: int | None = None) -> list[str]:
        keywords: list[str] = []
        seen_keywords = set()

        for record in records:
            key = record["normalized_keyword"]
            if not key or key in seen_keywords:
                continue
            seen_keywords.add(key)
            keywords.append(record["keyword"])

            if limit is not None and len(keywords) >= limit:
                break

        return keywords

    @staticmethod
    def _apply_serp_validation(
        records: list[dict[str, Any]],
        serp_groups: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        serp_map: dict[str, list[str]] = {}

        for group in serp_groups:
            seed_keyword = KeywordProcessing.normalize_text(group["seed_keyword"])
            domains: list[str] = []

            for item in group.get("items", []):
                if (item.get("type") or "").lower() != "organic":
                    continue

                domain = KeywordIntelligenceService._safe_domain(item.get("domain") or item.get("url"))
                if domain and domain not in domains:
                    domains.append(domain)

            serp_map[seed_keyword] = domains

        updated_records: list[dict[str, Any]] = []

        for record in records:
            merged = dict(record)
            record_keyword = record["normalized_keyword"]

            if record_keyword in serp_map:
                merged["serp_validated"] = True
                merged["serp_top_domains"] = serp_map[record_keyword]
            else:
                merged["serp_validated"] = False
                merged["serp_top_domains"] = []

            updated_records.append(merged)

        return updated_records

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
        serp_validation_groups: list[dict[str, Any]] = []
        competitor_site_groups: list[dict[str, Any]] = []

        for seed in seeds:
            try:
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
            except Exception as exc:
                warnings.append(f"keyword_suggestions_failed:{seed}:{exc}")

            try:
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
            except Exception as exc:
                warnings.append(f"related_keywords_failed:{seed}:{exc}")

        serp_seed_subset = seeds[: settings.dataforseo_serp_seed_limit]
        for seed in serp_seed_subset:
            try:
                serp_raw = client.get_serp_organic_advanced(
                    keyword=seed,
                    location_name=resolved_location,
                    language_name=resolved_language,
                    depth=settings.dataforseo_serp_top_results_limit,
                )
                serp_validation_groups.append(
                    {
                        "seed_keyword": seed,
                        "items": KeywordIntelligenceService._extract_serp_items(serp_raw),
                    }
                )
            except Exception as exc:
                warnings.append(f"serp_validation_failed:{seed}:{exc}")

        competitor_domains = KeywordIntelligenceService._extract_competitor_domains(
            serp_validation_groups,
            limit=settings.dataforseo_competitor_domain_limit,
        )

        for domain in competitor_domains:
            try:
                competitor_raw = client.get_keywords_for_site(
                    target=domain,
                    location_name=resolved_location,
                    language_name=resolved_language,
                    limit=settings.dataforseo_keywords_for_site_limit,
                )
                competitor_site_groups.append(
                    {
                        "site_domain": domain,
                        "raw_items": KeywordIntelligenceService._extract_items(competitor_raw),
                    }
                )
            except Exception as exc:
                warnings.append(f"keywords_for_site_failed:{domain}:{exc}")

        suggestions_by_seed, all_suggestions = KeywordIntelligenceService._normalize_group(
            suggestions_raw_groups,
            source="suggestions",
        )
        related_by_seed, all_related = KeywordIntelligenceService._normalize_group(
            related_raw_groups,
            source="related",
        )
        competitor_by_site, all_competitor_keywords = KeywordIntelligenceService._normalize_site_group(
            competitor_site_groups,
            source="keywords_for_site",
        )

        all_records = all_suggestions + all_related + all_competitor_keywords
        all_records = KeywordIntelligenceService._apply_serp_validation(all_records, serp_validation_groups)

        unique_keywords_for_enrichment = KeywordIntelligenceService._build_unique_keywords(
            all_records,
            limit=max(
                settings.dataforseo_keyword_overview_limit,
                settings.dataforseo_google_ads_limit,
                settings.dataforseo_historical_keywords_limit,
            ),
        )

        historical_enriched = False
        historical_map: dict[str, dict[str, Any]] = {}

        if include_historical:
            try:
                historical_keywords = unique_keywords_for_enrichment[: settings.dataforseo_historical_keywords_limit]
                historical_raw = client.get_historical_search_volume(
                    keywords=historical_keywords,
                    location_name=resolved_location,
                    language_name=resolved_language,
                )
                historical_map = KeywordProcessing.extract_historical_map(historical_raw)
                all_records = KeywordProcessing.apply_historical_enrichment(all_records, historical_map)
                historical_enriched = True
            except Exception as exc:
                warnings.append(f"historical_enrichment_failed:{exc}")

        keyword_overview_enriched = False
        keyword_overview_map: dict[str, dict[str, Any]] = {}
        try:
            overview_keywords = unique_keywords_for_enrichment[: settings.dataforseo_keyword_overview_limit]
            overview_raw = client.get_keyword_overview(
                keywords=overview_keywords,
                location_name=resolved_location,
                language_name=resolved_language,
            )
            keyword_overview_map = KeywordProcessing.extract_keyword_overview_map(overview_raw)
            all_records = KeywordProcessing.apply_keyword_overview_enrichment(all_records, keyword_overview_map)
            keyword_overview_enriched = True
        except Exception as exc:
            warnings.append(f"keyword_overview_enrichment_failed:{exc}")

        google_ads_enriched = False
        google_ads_map: dict[str, dict[str, Any]] = {}
        try:
            google_ads_keywords = unique_keywords_for_enrichment[: settings.dataforseo_google_ads_limit]
            google_ads_raw = client.get_google_ads_search_volume(
                keywords=google_ads_keywords,
                location_name=resolved_location,
                language_name=resolved_language,
            )
            google_ads_map = KeywordProcessing.extract_google_ads_map(google_ads_raw)
            all_records = KeywordProcessing.apply_google_ads_enrichment(all_records, google_ads_map)
            google_ads_enriched = True
        except Exception as exc:
            warnings.append(f"google_ads_enrichment_failed:{exc}")

        evaluated_records = [
            KeywordProcessing.evaluate_record(record, entity=entity)
            for record in all_records
        ]
        consolidated_records = KeywordProcessing.consolidate_records(evaluated_records)
        clusters = KeywordProcessing.build_clusters(consolidated_records)

        included_records = [record for record in consolidated_records if record["include"]]
        excluded_records = [record for record in consolidated_records if not record["include"]]

        return {
            "version": "v1.2",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "page_type": page_type,
            "listing_type": entity["listing_type"],
            "entity": entity,
            "dataforseo_context": {
                "location_name": resolved_location,
                "language_name": resolved_language,
                "limit": resolved_limit,
                "related_depth": settings.dataforseo_related_depth,
                "historical_keywords_limit": settings.dataforseo_historical_keywords_limit,
                "keyword_overview_limit": settings.dataforseo_keyword_overview_limit,
                "google_ads_limit": settings.dataforseo_google_ads_limit,
                "serp_seed_limit": settings.dataforseo_serp_seed_limit,
                "serp_top_results_limit": settings.dataforseo_serp_top_results_limit,
                "competitor_domain_limit": settings.dataforseo_competitor_domain_limit,
                "keywords_for_site_limit": settings.dataforseo_keywords_for_site_limit,
                "historical_enriched": historical_enriched,
                "keyword_overview_enriched": keyword_overview_enriched,
                "google_ads_enriched": google_ads_enriched,
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
                "competitor_keywords": {
                    "competitor_domains": competitor_domains,
                    "total_unique_keywords": len({item["normalized_keyword"] for item in all_competitor_keywords}),
                    "by_site": competitor_by_site,
                },
                "serp_validation": {
                    "seed_keywords_checked": serp_seed_subset,
                    "checked_seed_count": len(serp_seed_subset),
                    "organic_domains": competitor_domains,
                    "by_seed": serp_validation_groups,
                },
            },
            "historical_enrichment": {
                "applied": historical_enriched,
                "historical_keywords_count": len(historical_map),
            },
            "keyword_overview_enrichment": {
                "applied": keyword_overview_enriched,
                "overview_keywords_count": len(keyword_overview_map),
            },
            "google_ads_enrichment": {
                "applied": google_ads_enriched,
                "ads_keywords_count": len(google_ads_map),
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