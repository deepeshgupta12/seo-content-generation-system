from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse


class CompetitorIntelligenceService:
    DEFAULT_WHITELIST = [
        "99acres.com",
        "magicbricks.com",
        "housing.com",
        "nobroker.in",
        "makaan.com",
        "commonfloor.com",
        "proptiger.com",
    ]

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
    def _normalize_text(value: str | None) -> str:
        if not value:
            return ""
        return " ".join(value.lower().strip().split())

    @staticmethod
    def _classify_keyword_themes(keyword: str) -> list[str]:
        lowered = CompetitorIntelligenceService._normalize_text(keyword)
        themes: list[str] = []

        if any(term in lowered for term in ["price", "prices", "rate", "rates", "trend", "market overview"]):
            themes.append("pricing")
        if any(term in lowered for term in ["bhk", "1 bhk", "2 bhk", "3 bhk", "studio", "1 rk"]):
            themes.append("bhk")
        if any(term in lowered for term in ["ready to move", "ready possession"]):
            themes.append("ready_to_move")
        if any(term in lowered for term in ["nearby", "locality", "localities", "area", "sector"]):
            themes.append("locality_navigation")
        if any(term in lowered for term in ["review", "reviews", "rating", "ratings"]):
            themes.append("reviews")
        if any(term in lowered for term in ["what", "how", "which", "why", "best", "good", "guide", "overview"]):
            themes.append("informational")
        if any(term in lowered for term in ["flat", "flats", "property", "properties", "apartment", "apartments", "sale", "resale"]):
            themes.append("listing_discovery")

        return themes or ["general_listing"]

    @staticmethod
    def _classify_page_family(keyword: str) -> str:
        lowered = CompetitorIntelligenceService._normalize_text(keyword)

        if any(term in lowered for term in ["price", "prices", "rate", "rates", "trend"]):
            return "price_page"
        if any(term in lowered for term in ["bhk", "studio", "1 rk"]):
            return "bhk_page"
        if any(term in lowered for term in ["ready to move", "ready possession"]):
            return "status_page"
        if any(term in lowered for term in ["nearby", "locality", "localities", "area", "sector"]):
            return "locality_page"
        if any(term in lowered for term in ["review", "reviews", "rating", "ratings"]):
            return "review_page"
        if any(term in lowered for term in ["what", "how", "which", "why", "best", "good", "guide", "overview"]):
            return "informational_page"

        return "listing_page"

    @staticmethod
    def _theme_sort_key(item: dict[str, Any]) -> tuple[int, str]:
        return (item.get("count", 0), item.get("theme", ""))

    @staticmethod
    def _family_sort_key(item: dict[str, Any]) -> tuple[int, str]:
        return (item.get("keyword_count", 0), item.get("page_family", ""))

    @staticmethod
    def _extract_competitor_records(keyword_intelligence: dict) -> list[dict[str, Any]]:
        competitor_groups = (
            keyword_intelligence.get("raw_retrieval", {})
            .get("competitor_keywords", {})
            .get("by_site", [])
            or []
        )

        records: list[dict[str, Any]] = []
        for group in competitor_groups:
            domain = group.get("site_domain")
            for item in group.get("items", []) or []:
                if not isinstance(item, dict):
                    continue
                enriched = dict(item)
                enriched["source_domain"] = domain
                records.append(enriched)

        return records

    @staticmethod
    def _extract_serp_overlap(keyword_intelligence: dict, selected_domains: list[str]) -> dict[str, Any]:
        serp_groups = (
            keyword_intelligence.get("raw_retrieval", {})
            .get("serp_validation", {})
            .get("by_seed", [])
            or []
        )

        by_competitor: list[dict[str, Any]] = []
        overlapping_domains: list[str] = []

        for domain in selected_domains:
            matched_seeds: list[str] = []

            for group in serp_groups:
                seed_keyword = group.get("seed_keyword")
                items = group.get("items", []) or []
                group_domains: list[str] = []

                for item in items:
                    if (item.get("type") or "").lower() != "organic":
                        continue
                    resolved_domain = CompetitorIntelligenceService._safe_domain(
                        item.get("domain") or item.get("url")
                    )
                    if resolved_domain:
                        group_domains.append(resolved_domain)

                if domain in group_domains and seed_keyword:
                    matched_seeds.append(seed_keyword)

            if matched_seeds:
                overlapping_domains.append(domain)

            by_competitor.append(
                {
                    "domain": domain,
                    "serp_overlap_count": len(matched_seeds),
                    "serp_overlap_keywords": matched_seeds,
                }
            )

        return {
            "overlapping_domains": overlapping_domains,
            "overlap_count": len(overlapping_domains),
            "by_competitor": by_competitor,
        }
    
    @staticmethod
    def _allowed_page_families() -> set[str]:
        return {
            "listing_page",
            "locality_page",
            "price_page",
            "bhk_page",
            "status_page",
            "review_page",
            "informational_page",
        }

    @staticmethod
    def _build_scoped_competitor_records(
        included_keywords: list[dict[str, Any]],
        selected_domains: list[str],
    ) -> list[dict[str, Any]]:
        scoped: list[dict[str, Any]] = []
        allowed_page_families = CompetitorIntelligenceService._allowed_page_families()

        for record in included_keywords:
            if not isinstance(record, dict):
                continue

            if not record.get("include", True):
                continue

            source_domains = record.get("source_domains", []) or []
            serp_top_domains = record.get("serp_top_domains", []) or []

            matched_competitor_domains = sorted(
                {
                    domain
                    for domain in source_domains + serp_top_domains
                    if domain in selected_domains
                }
            )

            if not matched_competitor_domains:
                continue

            if not (
                record.get("entity_match")
                or record.get("city_match")
                or record.get("exact_location_match")
            ):
                continue

            keyword = record.get("keyword", "")
            page_family = CompetitorIntelligenceService._classify_page_family(keyword)
            if page_family not in allowed_page_families:
                continue

            enriched = dict(record)
            enriched["page_family"] = page_family
            enriched["matched_competitor_domains"] = matched_competitor_domains
            enriched["keyword_themes"] = CompetitorIntelligenceService._classify_keyword_themes(keyword)
            scoped.append(enriched)

        scoped.sort(
            key=lambda item: (
                item.get("score", 0),
                item.get("search_volume") or item.get("ads_search_volume") or 0,
                item.get("keyword", ""),
            ),
            reverse=True,
        )
        return scoped

    @staticmethod
    def _build_relevant_keyword_views(
        scoped_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        relevant_competitor_keywords = [
            {
                "keyword": record.get("keyword"),
                "page_family": record.get("page_family"),
                "themes": record.get("keyword_themes", []),
                "matched_competitor_domains": record.get("matched_competitor_domains", []),
                "score": record.get("score"),
                "search_volume": record.get("search_volume"),
                "ads_search_volume": record.get("ads_search_volume"),
            }
            for record in scoped_records[:20]
        ]

        relevant_informational_keywords = [
            {
                "keyword": record.get("keyword"),
                "page_family": record.get("page_family"),
                "themes": record.get("keyword_themes", []),
                "matched_competitor_domains": record.get("matched_competitor_domains", []),
                "score": record.get("score"),
                "search_volume": record.get("search_volume"),
                "ads_search_volume": record.get("ads_search_volume"),
            }
            for record in scoped_records
            if (
                record.get("informational_signal")
                or "informational" in (record.get("keyword_themes", []) or [])
                or record.get("page_family") == "informational_page"
            )
        ][:20]

        relevant_overlap_keywords = [
            {
                "keyword": record.get("keyword"),
                "source_domains": record.get("source_domains", []),
                "serp_top_domains": record.get("serp_top_domains", []),
                "matched_competitor_domains": record.get("matched_competitor_domains", []),
                "page_family": record.get("page_family"),
                "score": record.get("score"),
                "search_volume": record.get("search_volume"),
                "ads_search_volume": record.get("ads_search_volume"),
            }
            for record in scoped_records
            if record.get("matched_competitor_domains")
        ][:20]

        return {
            "relevant_competitor_keywords": relevant_competitor_keywords,
            "relevant_informational_keywords": relevant_informational_keywords,
            "relevant_overlap_keywords": relevant_overlap_keywords,
        }

    @staticmethod
    def _build_competitor_breakdown(
        scoped_records: list[dict[str, Any]],
        selected_domains: list[str],
    ) -> list[dict[str, Any]]:
        breakdown: list[dict[str, Any]] = []

        for domain in selected_domains:
            domain_records = [
                item
                for item in scoped_records
                if domain in (item.get("matched_competitor_domains", []) or [])
            ]

            page_family_map: dict[str, list[str]] = {}
            theme_map: dict[str, list[str]] = {}

            for record in domain_records:
                keyword = record.get("keyword", "")
                family = record.get("page_family") or CompetitorIntelligenceService._classify_page_family(keyword)
                page_family_map.setdefault(family, []).append(keyword)

                for theme in record.get("keyword_themes", []) or CompetitorIntelligenceService._classify_keyword_themes(keyword):
                    theme_map.setdefault(theme, []).append(keyword)

            page_family_breakdown = [
                {
                    "page_family": family,
                    "keyword_count": len(keywords),
                    "sample_keywords": keywords[:4],
                }
                for family, keywords in page_family_map.items()
            ]
            page_family_breakdown.sort(key=CompetitorIntelligenceService._family_sort_key, reverse=True)

            theme_breakdown = [
                {
                    "theme": theme,
                    "count": len(keywords),
                    "sample_keywords": keywords[:4],
                }
                for theme, keywords in theme_map.items()
            ]
            theme_breakdown.sort(key=CompetitorIntelligenceService._theme_sort_key, reverse=True)

            top_keywords = sorted(
                [
                    {
                        "keyword": item.get("keyword"),
                        "page_family": item.get("page_family"),
                        "themes": item.get("keyword_themes", []),
                        "score": item.get("score"),
                        "search_volume": item.get("search_volume"),
                        "ads_search_volume": item.get("ads_search_volume"),
                        "matched_competitor_domains": item.get("matched_competitor_domains", []),
                    }
                    for item in domain_records
                ],
                key=lambda item: (
                    item.get("score", 0),
                    item.get("search_volume") or item.get("ads_search_volume") or 0,
                    item.get("keyword", ""),
                ),
                reverse=True,
            )[:8]

            breakdown.append(
                {
                    "domain": domain,
                    "keyword_count": len(domain_records),
                    "top_keywords": top_keywords,
                    "page_family_breakdown": page_family_breakdown,
                    "theme_breakdown": theme_breakdown,
                }
            )

        return breakdown

    @staticmethod
    def _build_keyword_intersection(
        scoped_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        shared_keywords = sorted(
            [
                {
                    "keyword": record.get("keyword"),
                    "sources": record.get("sources", []),
                    "source_domains": record.get("source_domains", []),
                    "matched_competitor_domains": record.get("matched_competitor_domains", []),
                    "page_family": record.get("page_family"),
                    "score": record.get("score"),
                    "search_volume": record.get("search_volume"),
                    "ads_search_volume": record.get("ads_search_volume"),
                }
                for record in scoped_records
            ],
            key=lambda item: (
                item.get("score", 0),
                item.get("search_volume") or item.get("ads_search_volume") or 0,
                item.get("keyword", ""),
            ),
            reverse=True,
        )

        return {
            "intersection_count": len(shared_keywords),
            "intersection_keywords": shared_keywords[:20],
        }

    @staticmethod
    def _build_structural_patterns(
        competitor_breakdown: list[dict[str, Any]],
    ) -> dict[str, Any]:
        aggregate_theme_counts: dict[str, int] = {}

        for competitor in competitor_breakdown:
            for item in competitor.get("theme_breakdown", []) or []:
                theme = item.get("theme")
                count = item.get("count", 0)
                if not theme:
                    continue
                aggregate_theme_counts[theme] = aggregate_theme_counts.get(theme, 0) + count

        section_patterns: list[dict[str, Any]] = []
        faq_patterns: list[dict[str, Any]] = []
        table_patterns: list[dict[str, Any]] = []
        hierarchy_patterns: list[dict[str, Any]] = []
        schema_patterns: list[dict[str, Any]] = []

        def maybe_add(theme: str, section_title: str, faq_pattern: str, table_pattern: str | None) -> None:
            evidence = aggregate_theme_counts.get(theme, 0)
            if evidence <= 0:
                return

            section_patterns.append(
                {
                    "theme": theme,
                    "recommended_section_title": section_title,
                    "evidence_count": evidence,
                    "evidence_type": "keyword_theme_heuristic",
                }
            )
            faq_patterns.append(
                {
                    "theme": theme,
                    "recommended_question_pattern": faq_pattern,
                    "evidence_count": evidence,
                    "evidence_type": "keyword_theme_heuristic",
                }
            )
            if table_pattern:
                table_patterns.append(
                    {
                        "theme": theme,
                        "recommended_table_pattern": table_pattern,
                        "evidence_count": evidence,
                        "evidence_type": "keyword_theme_heuristic",
                    }
                )

        maybe_add("pricing", "Price Trends and Rates", "What is the asking price signal for this location?", "Price Trend Snapshot")
        maybe_add("bhk", "BHK and Inventory Mix", "Which BHK options are commonly available here?", "Available BHK Mix")
        maybe_add("ready_to_move", "Status and Readiness Snapshot", "Are ready-to-move properties available here?", "Property Status Snapshot")
        maybe_add("locality_navigation", "Nearby Localities Buyers Can Also Explore", "Which nearby localities can buyers compare?", "Nearby Localities to Explore")
        maybe_add("reviews", "Review and Rating Signals", "What review and rating signals are available here?", None)
        maybe_add("listing_discovery", "Resale Market Snapshot", "How many resale properties are available here?", "Coverage Summary")
        maybe_add("informational", "Buyer Guidance", "What should buyers check before narrowing options here?", None)

        if aggregate_theme_counts.get("informational", 0) > 0:
            hierarchy_patterns.append(
                {
                    "pattern": "FAQ-rich content hierarchy",
                    "reason": "Informational competitor keywords indicate search demand beyond simple listing discovery.",
                    "evidence_type": "keyword_theme_heuristic",
                }
            )
            schema_patterns.append(
                {
                    "pattern": "FAQ-supportive schema opportunity",
                    "reason": "Informational and comparison-style queries suggest strong structured FAQ coverage.",
                    "evidence_type": "keyword_theme_heuristic",
                }
            )

        if aggregate_theme_counts.get("pricing", 0) > 0:
            hierarchy_patterns.append(
                {
                    "pattern": "Pricing block high in page hierarchy",
                    "reason": "Competitor keyword mix strongly signals price-first comparison intent.",
                    "evidence_type": "keyword_theme_heuristic",
                }
            )

        return {
            "section_patterns": section_patterns,
            "faq_patterns": faq_patterns,
            "table_patterns": table_patterns,
            "schema_patterns": schema_patterns,
            "hierarchy_patterns": hierarchy_patterns,
        }

    @staticmethod
    def _build_inspiration_signals(structural_patterns: dict[str, Any]) -> dict[str, Any]:
        recommended_sections = [
            {
                "title": item["recommended_section_title"],
                "theme": item["theme"],
                "evidence_count": item["evidence_count"],
            }
            for item in structural_patterns.get("section_patterns", [])[:8]
        ]

        recommended_faq_themes = [
            {
                "theme": item["theme"],
                "question_pattern": item["recommended_question_pattern"],
                "evidence_count": item["evidence_count"],
            }
            for item in structural_patterns.get("faq_patterns", [])[:8]
        ]

        recommended_table_themes = [
            {
                "theme": item["theme"],
                "table_pattern": item["recommended_table_pattern"],
                "evidence_count": item["evidence_count"],
            }
            for item in structural_patterns.get("table_patterns", [])[:8]
        ]

        return {
            "confidence": "heuristic",
            "usage_rule": "Use only for structural inspiration. Do not copy competitor wording or claims.",
            "recommended_sections": recommended_sections,
            "recommended_faq_themes": recommended_faq_themes,
            "recommended_table_themes": recommended_table_themes,
            "recommended_schema_hierarchy_patterns": structural_patterns.get("schema_patterns", []) + structural_patterns.get("hierarchy_patterns", []),
        }

    @staticmethod
    def build(normalized: dict[str, Any], keyword_intelligence: dict[str, Any]) -> dict[str, Any]:
        del normalized

        whitelist = list(CompetitorIntelligenceService.DEFAULT_WHITELIST)

        raw_competitor_domains = (
            keyword_intelligence.get("raw_retrieval", {})
            .get("competitor_keywords", {})
            .get("competitor_domains", [])
            or []
        )
        selected_domains = [domain for domain in raw_competitor_domains if domain in whitelist]

        if not selected_domains:
            selected_domains = whitelist[:4]

        included_keywords = (
            keyword_intelligence.get("normalized_keywords", {}).get("included_keywords", []) or []
        )

        scoped_records = CompetitorIntelligenceService._build_scoped_competitor_records(
            included_keywords,
            selected_domains,
        )

        competitor_breakdown = CompetitorIntelligenceService._build_competitor_breakdown(
            scoped_records,
            selected_domains,
        )
        keyword_intersection = CompetitorIntelligenceService._build_keyword_intersection(
            scoped_records,
        )
        serp_overlap = CompetitorIntelligenceService._extract_serp_overlap(
            keyword_intelligence,
            selected_domains,
        )
        relevant_keyword_views = CompetitorIntelligenceService._build_relevant_keyword_views(
            scoped_records,
        )
        structural_patterns = CompetitorIntelligenceService._build_structural_patterns(
            competitor_breakdown
        )
        inspiration_signals = CompetitorIntelligenceService._build_inspiration_signals(
            structural_patterns
        )

        return {
            "version": "v1.1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "whitelist_domains": whitelist,
            "selected_competitors": selected_domains,
            "competitor_breakdown": competitor_breakdown,
            "keyword_intersection": keyword_intersection,
            "serp_overlap": serp_overlap,
            "structural_patterns": structural_patterns,
            "inspiration_signals": inspiration_signals,
            "relevant_competitor_keywords": relevant_keyword_views["relevant_competitor_keywords"],
            "relevant_informational_keywords": relevant_keyword_views["relevant_informational_keywords"],
            "relevant_overlap_keywords": relevant_keyword_views["relevant_overlap_keywords"],
        }