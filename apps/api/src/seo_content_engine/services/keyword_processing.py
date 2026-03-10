from __future__ import annotations

import re
from typing import Any

from seo_content_engine.core.config import settings
from seo_content_engine.domain.enums import PageType


class KeywordProcessing:
    HARD_EXCLUDE_TERMS = {
        "rent",
        "rental",
        "lease",
        "leased",
        "pg",
    }

    SOFT_DEMOTE_TERMS = {
        "cheap",
        "without brokerage",
        "brokerage",
    }

    SALE_SIGNAL_TERMS = {
        "sale",
        "resale",
        "buy",
        "property",
        "properties",
        "flat",
        "flats",
        "apartment",
        "apartments",
        "home",
        "homes",
        "price",
        "prices",
        "ready to move",
        "ready possession",
        "bhk",
    }

    PRICE_TERMS = {
        "price",
        "prices",
        "rate",
        "rates",
        "cost",
        "value",
    }

    READY_TO_MOVE_TERMS = {
        "ready to move",
        "ready possession",
        "ready possession flats",
    }

    QUESTION_TERMS = {
        "price",
        "prices",
        "ready to move",
        "bhk",
        "sale",
        "resale",
        "property",
        "properties",
        "apartment",
        "flat",
        "how",
        "what",
        "which",
        "best",
        "good",
        "why",
        "where",
    }

    INFORMATIONAL_TERMS = {
        "how",
        "what",
        "which",
        "best",
        "good",
        "guide",
        "market",
        "price trend",
        "rates",
        "overview",
        "comparison",
    }

    BHK_REGEX = re.compile(r"\b\d+(\.\d+)?\s*bhk\b|\b1\s*rk\b|\bstudio\b", re.IGNORECASE)

    @staticmethod
    def normalize_text(value: str | None) -> str:
        if not value:
            return ""
        return " ".join(value.strip().lower().split())

    @staticmethod
    def _contains_any(text: str, phrases: set[str]) -> bool:
        return any(phrase in text for phrase in phrases)

    @staticmethod
    def _extract_search_volume(raw_item: dict[str, Any]) -> int | None:
        direct_volume = raw_item.get("search_volume")
        keyword_info = raw_item.get("keyword_info") or {}
        nested_volume = keyword_info.get("search_volume")

        if isinstance(direct_volume, (int, float)):
            return int(direct_volume)
        if isinstance(nested_volume, (int, float)):
            return int(nested_volume)
        return None

    @staticmethod
    def _extract_monthly_searches(raw_item: dict[str, Any]) -> list[dict[str, Any]]:
        keyword_info = raw_item.get("keyword_info") or {}
        return keyword_info.get("monthly_searches") or raw_item.get("monthly_searches") or []

    @staticmethod
    def _extract_search_volume_trend(raw_item: dict[str, Any]) -> dict[str, Any]:
        keyword_info = raw_item.get("keyword_info") or {}
        return keyword_info.get("search_volume_trend") or raw_item.get("search_volume_trend") or {}

    @staticmethod
    def normalize_raw_item(raw_item: dict[str, Any], source: str, seed_keyword: str) -> dict[str, Any]:
        keyword_info = raw_item.get("keyword_info") or {}
        keyword_properties = raw_item.get("keyword_properties") or {}
        search_intent_info = raw_item.get("search_intent_info") or {}

        keyword = raw_item.get("keyword") or raw_item.get("keyword_data", {}).get("keyword") or ""
        normalized_keyword = KeywordProcessing.normalize_text(keyword)
        core_keyword = keyword_properties.get("core_keyword") or keyword
        normalized_core_keyword = KeywordProcessing.normalize_text(core_keyword)

        return {
            "keyword": keyword,
            "normalized_keyword": normalized_keyword,
            "core_keyword": core_keyword,
            "normalized_core_keyword": normalized_core_keyword,
            "source": source,
            "source_seed": seed_keyword,
            "source_domain": raw_item.get("source_domain"),
            "search_volume": KeywordProcessing._extract_search_volume(raw_item),
            "competition": keyword_info.get("competition") or raw_item.get("competition"),
            "competition_level": keyword_info.get("competition_level") or raw_item.get("competition_level"),
            "cpc": keyword_info.get("cpc") or raw_item.get("cpc"),
            "monthly_searches": KeywordProcessing._extract_monthly_searches(raw_item),
            "search_volume_trend": KeywordProcessing._extract_search_volume_trend(raw_item),
            "keyword_difficulty": keyword_properties.get("keyword_difficulty") or raw_item.get("keyword_difficulty"),
            "detected_language": keyword_properties.get("detected_language") or raw_item.get("detected_language"),
            "words_count": keyword_properties.get("words_count") or raw_item.get("words_count"),
            "main_intent": search_intent_info.get("main_intent") or raw_item.get("main_intent"),
            "foreign_intent": search_intent_info.get("foreign_intent") or raw_item.get("foreign_intent") or [],
            "clickstream_search_volume": raw_item.get("clickstream_search_volume"),
            "serp_top_domains": raw_item.get("serp_top_domains") or [],
            "serp_validated": raw_item.get("serp_validated", False),
            "raw": raw_item,
        }

    @staticmethod
    def extract_historical_map(raw_response: dict[str, Any]) -> dict[str, dict[str, Any]]:
        historical_map: dict[str, dict[str, Any]] = {}

        for task in raw_response.get("tasks", []) or []:
            for result in task.get("result", []) or []:
                for item in result.get("items", []) or []:
                    keyword = item.get("keyword")
                    if not keyword:
                        continue

                    keyword_info = item.get("keyword_info") or {}
                    historical_map[KeywordProcessing.normalize_text(keyword)] = {
                        "search_volume": keyword_info.get("search_volume"),
                        "competition": keyword_info.get("competition"),
                        "competition_level": keyword_info.get("competition_level"),
                        "cpc": keyword_info.get("cpc"),
                        "monthly_searches": keyword_info.get("monthly_searches") or [],
                        "search_volume_trend": keyword_info.get("search_volume_trend") or {},
                    }

        return historical_map

    @staticmethod
    def extract_keyword_overview_map(raw_response: dict[str, Any]) -> dict[str, dict[str, Any]]:
        overview_map: dict[str, dict[str, Any]] = {}

        for task in raw_response.get("tasks", []) or []:
            for result in task.get("result", []) or []:
                for item in result.get("items", []) or []:
                    keyword = item.get("keyword") or item.get("keyword_data", {}).get("keyword")
                    if not keyword:
                        continue

                    keyword_info = item.get("keyword_info") or {}
                    search_intent_info = item.get("search_intent_info") or {}

                    overview_map[KeywordProcessing.normalize_text(keyword)] = {
                        "search_volume": keyword_info.get("search_volume"),
                        "competition": keyword_info.get("competition"),
                        "competition_level": keyword_info.get("competition_level"),
                        "cpc": keyword_info.get("cpc"),
                        "monthly_searches": keyword_info.get("monthly_searches") or [],
                        "search_volume_trend": keyword_info.get("search_volume_trend") or {},
                        "main_intent": search_intent_info.get("main_intent"),
                        "foreign_intent": search_intent_info.get("foreign_intent") or [],
                    }

        return overview_map

    @staticmethod
    def extract_google_ads_map(raw_response: dict[str, Any]) -> dict[str, dict[str, Any]]:
        ads_map: dict[str, dict[str, Any]] = {}

        for task in raw_response.get("tasks", []) or []:
            for result in task.get("result", []) or []:
                for item in result.get("items", []) or []:
                    keyword = item.get("keyword")
                    if not keyword:
                        continue

                    ads_map[KeywordProcessing.normalize_text(keyword)] = {
                        "ads_search_volume": item.get("search_volume"),
                        "ads_cpc": item.get("cpc"),
                        "ads_competition": item.get("competition"),
                        "ads_monthly_searches": item.get("monthly_searches") or [],
                    }

        return ads_map

    @staticmethod
    def apply_historical_enrichment(
        records: list[dict[str, Any]],
        historical_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched_records: list[dict[str, Any]] = []

        for record in records:
            key = record["normalized_keyword"]
            historical = historical_map.get(key)

            if not historical:
                enriched_records.append(record)
                continue

            merged = dict(record)

            if merged.get("search_volume") is None and historical.get("search_volume") is not None:
                merged["search_volume"] = historical["search_volume"]

            if merged.get("competition") is None and historical.get("competition") is not None:
                merged["competition"] = historical["competition"]

            if merged.get("competition_level") is None and historical.get("competition_level") is not None:
                merged["competition_level"] = historical["competition_level"]

            if merged.get("cpc") is None and historical.get("cpc") is not None:
                merged["cpc"] = historical["cpc"]

            if not merged.get("monthly_searches") and historical.get("monthly_searches"):
                merged["monthly_searches"] = historical["monthly_searches"]

            if not merged.get("search_volume_trend") and historical.get("search_volume_trend"):
                merged["search_volume_trend"] = historical["search_volume_trend"]

            merged["historical_enriched"] = True
            enriched_records.append(merged)

        return enriched_records

    @staticmethod
    def apply_keyword_overview_enrichment(
        records: list[dict[str, Any]],
        overview_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched_records: list[dict[str, Any]] = []

        for record in records:
            key = record["normalized_keyword"]
            overview = overview_map.get(key)

            if not overview:
                enriched_records.append(record)
                continue

            merged = dict(record)

            if merged.get("search_volume") is None and overview.get("search_volume") is not None:
                merged["search_volume"] = overview["search_volume"]

            if merged.get("competition") is None and overview.get("competition") is not None:
                merged["competition"] = overview["competition"]

            if merged.get("competition_level") is None and overview.get("competition_level") is not None:
                merged["competition_level"] = overview["competition_level"]

            if merged.get("cpc") is None and overview.get("cpc") is not None:
                merged["cpc"] = overview["cpc"]

            if not merged.get("monthly_searches") and overview.get("monthly_searches"):
                merged["monthly_searches"] = overview["monthly_searches"]

            if not merged.get("search_volume_trend") and overview.get("search_volume_trend"):
                merged["search_volume_trend"] = overview["search_volume_trend"]

            if not merged.get("main_intent") and overview.get("main_intent"):
                merged["main_intent"] = overview["main_intent"]

            if not merged.get("foreign_intent") and overview.get("foreign_intent"):
                merged["foreign_intent"] = overview["foreign_intent"]

            merged["keyword_overview_enriched"] = True
            enriched_records.append(merged)

        return enriched_records

    @staticmethod
    def apply_google_ads_enrichment(
        records: list[dict[str, Any]],
        ads_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched_records: list[dict[str, Any]] = []

        for record in records:
            key = record["normalized_keyword"]
            ads = ads_map.get(key)

            if not ads:
                enriched_records.append(record)
                continue

            merged = dict(record)

            merged["ads_search_volume"] = ads.get("ads_search_volume")
            merged["ads_cpc"] = ads.get("ads_cpc")
            merged["ads_competition"] = ads.get("ads_competition")

            if not merged.get("monthly_searches") and ads.get("ads_monthly_searches"):
                merged["monthly_searches"] = ads["ads_monthly_searches"]

            merged["google_ads_enriched"] = True
            enriched_records.append(merged)

        return enriched_records

    @staticmethod
    def _token_signature(text: str) -> tuple[str, ...]:
        tokens = re.findall(r"[a-z0-9\.]+", KeywordProcessing.normalize_text(text))
        return tuple(sorted(set(tokens)))

    @staticmethod
    def evaluate_record(record: dict[str, Any], entity: dict[str, Any]) -> dict[str, Any]:
        keyword_text = record["normalized_keyword"]
        core_keyword_text = record["normalized_core_keyword"]
        combined_text = f"{keyword_text} {core_keyword_text}".strip()

        page_type = PageType(entity["page_type"])
        entity_name = KeywordProcessing.normalize_text(entity.get("entity_name"))
        city_name = KeywordProcessing.normalize_text(entity.get("city_name"))

        exact_location_phrase = f"{entity_name} {city_name}".strip()
        reversed_location_phrase = f"{city_name} {entity_name}".strip()

        entity_match = entity_name in combined_text if entity_name else False
        city_match = city_name in combined_text if city_name else False
        exact_location_match = exact_location_phrase in combined_text if exact_location_phrase else False
        reversed_location_match = reversed_location_phrase in combined_text if reversed_location_phrase else False

        has_sale_signal = KeywordProcessing._contains_any(combined_text, KeywordProcessing.SALE_SIGNAL_TERMS)
        has_rent_noise = KeywordProcessing._contains_any(combined_text, KeywordProcessing.HARD_EXCLUDE_TERMS)
        has_soft_demote = KeywordProcessing._contains_any(combined_text, KeywordProcessing.SOFT_DEMOTE_TERMS)
        has_bhk_signal = bool(KeywordProcessing.BHK_REGEX.search(combined_text))
        has_price_signal = KeywordProcessing._contains_any(combined_text, KeywordProcessing.PRICE_TERMS)
        has_ready_signal = KeywordProcessing._contains_any(combined_text, KeywordProcessing.READY_TO_MOVE_TERMS)
        faq_support_signal = KeywordProcessing._contains_any(combined_text, KeywordProcessing.QUESTION_TERMS)
        informational_signal = KeywordProcessing._contains_any(combined_text, KeywordProcessing.INFORMATIONAL_TERMS)

        filter_reasons: list[str] = []

        if page_type in {PageType.RESALE_LOCALITY, PageType.RESALE_MICROMARKET} and not entity_match:
            filter_reasons.append("missing_entity_match")

        if page_type == PageType.RESALE_CITY and not city_match:
            filter_reasons.append("missing_city_match")

        if not has_sale_signal:
            filter_reasons.append("missing_sale_signal")

        if has_rent_noise:
            filter_reasons.append("rent_noise")

        source_priority_map = {
            "suggestions": 30,
            "related": 18,
            "keywords_for_site": 24,
            "keyword_overview": 20,
            "google_ads": 16,
        }
        source_priority = source_priority_map.get(record["source"], 12)

        score = source_priority

        if entity_match:
            score += 35

        if city_match:
            score += 10

        if exact_location_match:
            score += 18
        elif reversed_location_match:
            score += 8

        main_intent = (record.get("main_intent") or "").lower()
        if main_intent == "transactional":
            score += 15
        elif main_intent == "commercial":
            score += 12
        elif main_intent == "informational":
            score += 8

        search_volume = record.get("search_volume")
        ads_search_volume = record.get("ads_search_volume")

        effective_volume = None
        if isinstance(search_volume, (int, float)):
            effective_volume = int(search_volume)
        elif isinstance(ads_search_volume, (int, float)):
            effective_volume = int(ads_search_volume)

        if isinstance(effective_volume, int):
            if effective_volume >= 500:
                score += 20
            elif effective_volume >= 100:
                score += 15
            elif effective_volume >= 20:
                score += 10
            elif effective_volume > 0:
                score += 5

        if has_bhk_signal:
            score += 8

        if has_price_signal:
            score += 8

        if has_ready_signal:
            score += 6

        if informational_signal:
            score += 4

        if record.get("serp_validated"):
            score += 10

        if record.get("source_domain"):
            score += 6

        words_count = record.get("words_count")
        if isinstance(words_count, int) and words_count >= 6:
            score += 4

        if has_soft_demote:
            score -= 10

        if "missing_entity_match" in filter_reasons or "missing_city_match" in filter_reasons:
            score -= 100

        if "missing_sale_signal" in filter_reasons:
            score -= 60

        if "rent_noise" in filter_reasons:
            score -= 100

        if exact_location_match:
            location_tier = "exact_location_match"
        elif entity_match and city_match:
            location_tier = "loose_location_match"
        elif entity_match:
            location_tier = "entity_only_match"
        else:
            location_tier = "weak_match"

        include = not filter_reasons

        evaluated = dict(record)
        evaluated.update(
            {
                "entity_match": entity_match,
                "city_match": city_match,
                "exact_location_match": exact_location_match,
                "reversed_location_match": reversed_location_match,
                "location_tier": location_tier,
                "has_sale_signal": has_sale_signal,
                "has_rent_noise": has_rent_noise,
                "has_soft_demote": has_soft_demote,
                "has_bhk_signal": has_bhk_signal,
                "has_price_signal": has_price_signal,
                "has_ready_signal": has_ready_signal,
                "faq_support_signal": faq_support_signal,
                "informational_signal": informational_signal,
                "filter_reasons": filter_reasons,
                "include": include,
                "score": score,
                "semantic_signature": KeywordProcessing._token_signature(record["keyword"]),
            }
        )
        return evaluated

    @staticmethod
    def consolidate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        consolidated: dict[str, dict[str, Any]] = {}

        for record in records:
            key = record["normalized_keyword"]
            existing = consolidated.get(key)

            if existing is None:
                merged = dict(record)
                merged["sources"] = [record["source"]]
                merged["source_seeds"] = [record["source_seed"]]
                merged["source_domains"] = [record["source_domain"]] if record.get("source_domain") else []
                consolidated[key] = merged
                continue

            if record["score"] > existing["score"]:
                merged = dict(record)
                merged["sources"] = sorted(set(existing.get("sources", []) + [record["source"]]))
                merged["source_seeds"] = sorted(set(existing.get("source_seeds", []) + [record["source_seed"]]))
                merged["source_domains"] = sorted(
                    set(existing.get("source_domains", []) + ([record["source_domain"]] if record.get("source_domain") else []))
                )
                consolidated[key] = merged
            else:
                existing["sources"] = sorted(set(existing.get("sources", []) + [record["source"]]))
                existing["source_seeds"] = sorted(set(existing.get("source_seeds", []) + [record["source_seed"]]))
                existing["source_domains"] = sorted(
                    set(existing.get("source_domains", []) + ([record["source_domain"]] if record.get("source_domain") else []))
                )

                if record.get("serp_validated"):
                    existing["serp_validated"] = True

                if not existing.get("ads_search_volume") and record.get("ads_search_volume") is not None:
                    existing["ads_search_volume"] = record["ads_search_volume"]

        ordered = list(consolidated.values())
        ordered.sort(
            key=lambda item: (
                item["include"],
                item["exact_location_match"],
                item["score"],
                item.get("search_volume") or item.get("ads_search_volume") or 0,
                item["keyword"],
            ),
            reverse=True,
        )
        return ordered

    @staticmethod
    def _top_keywords(records: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        return records[:limit]

    @staticmethod
    def _dedupe_semantic_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}

        for record in records:
            grouped.setdefault(record["semantic_signature"], []).append(record)

        canonical_records: list[dict[str, Any]] = []

        for group in grouped.values():
            group.sort(
                key=lambda item: (
                    item["exact_location_match"],
                    item["location_tier"] == "exact_location_match",
                    item["score"],
                    item.get("search_volume") or item.get("ads_search_volume") or 0,
                    -len(item["keyword"]),
                ),
                reverse=True,
            )
            canonical_records.append(group[0])

        canonical_records.sort(
            key=lambda item: (
                item["exact_location_match"],
                item["score"],
                item.get("search_volume") or item.get("ads_search_volume") or 0,
                item["keyword"],
            ),
            reverse=True,
        )
        return canonical_records

    @staticmethod
    def build_clusters(records: list[dict[str, Any]]) -> dict[str, Any]:
        included = [record for record in records if record["include"]]
        canonical_included = KeywordProcessing._dedupe_semantic_records(included)

        general_candidates = [
            record
            for record in canonical_included
            if not record["has_bhk_signal"] and not record["has_price_signal"] and not record["has_ready_signal"]
        ]
        primary_keyword = general_candidates[0] if general_candidates else (canonical_included[0] if canonical_included else None)

        secondary_keywords = [
            record
            for record in canonical_included
            if primary_keyword is None or record["semantic_signature"] != primary_keyword["semantic_signature"]
        ][: settings.keyword_secondary_max_count]

        bhk_keywords = KeywordProcessing._top_keywords(
            KeywordProcessing._dedupe_semantic_records([record for record in included if record["has_bhk_signal"]]),
            settings.keyword_bhk_max_count,
        )

        price_keywords = KeywordProcessing._top_keywords(
            KeywordProcessing._dedupe_semantic_records([record for record in included if record["has_price_signal"]]),
            settings.keyword_price_max_count,
        )

        ready_to_move_keywords = KeywordProcessing._top_keywords(
            KeywordProcessing._dedupe_semantic_records([record for record in included if record["has_ready_signal"]]),
            settings.keyword_ready_to_move_max_count,
        )

        long_tail_keywords = KeywordProcessing._top_keywords(
            KeywordProcessing._dedupe_semantic_records([record for record in included if (record.get("words_count") or 0) >= 6]),
            settings.keyword_long_tail_max_count,
        )

        faq_keyword_candidates = KeywordProcessing._top_keywords(
            KeywordProcessing._dedupe_semantic_records(
                [
                    record
                    for record in included
                    if record["faq_support_signal"] or (record.get("main_intent") or "").lower() == "informational"
                ]
            ),
            settings.keyword_faq_max_count,
        )

        competitor_keywords = KeywordProcessing._top_keywords(
            KeywordProcessing._dedupe_semantic_records(
                [record for record in included if "keywords_for_site" in record.get("sources", [])]
            ),
            settings.keyword_competitor_max_count,
        )

        informational_keywords = KeywordProcessing._top_keywords(
            KeywordProcessing._dedupe_semantic_records(
                [record for record in included if record.get("informational_signal")]
            ),
            settings.keyword_informational_max_count,
        )

        serp_validated_keywords = KeywordProcessing._top_keywords(
            KeywordProcessing._dedupe_semantic_records(
                [record for record in included if record.get("serp_validated")]
            ),
            settings.keyword_serp_validated_max_count,
        )

        metadata_keywords: list[str] = []
        if primary_keyword:
            metadata_keywords.append(primary_keyword["keyword"])

        for record in secondary_keywords:
            if len(metadata_keywords) >= settings.keyword_metadata_max_count:
                break
            if record["keyword"] not in metadata_keywords:
                metadata_keywords.append(record["keyword"])

        for record in competitor_keywords:
            if len(metadata_keywords) >= settings.keyword_metadata_max_count:
                break
            if record["keyword"] not in metadata_keywords:
                metadata_keywords.append(record["keyword"])

        exact_match_keywords = [record for record in canonical_included if record["location_tier"] == "exact_location_match"]
        loose_match_keywords = [record for record in canonical_included if record["location_tier"] != "exact_location_match"]

        return {
            "primary_keyword": primary_keyword,
            "secondary_keywords": secondary_keywords,
            "bhk_keywords": bhk_keywords,
            "price_keywords": price_keywords,
            "ready_to_move_keywords": ready_to_move_keywords,
            "long_tail_keywords": long_tail_keywords,
            "faq_keyword_candidates": faq_keyword_candidates,
            "competitor_keywords": competitor_keywords,
            "informational_keywords": informational_keywords,
            "serp_validated_keywords": serp_validated_keywords,
            "metadata_keywords": metadata_keywords,
            "exact_match_keywords": exact_match_keywords,
            "loose_match_keywords": loose_match_keywords,
            "total_included_keywords": len(included),
        }