from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from seo_content_engine.core.config import settings


class FactualValidator:
    # Tier 1 — Hard-block: invented superlatives and investment language that are NEVER
    # factually grounded in resale listing data. Always stripped and always trigger
    # forbidden_claims_detected.
    HARD_BLOCK_CLAIMS = [
        "most sought-after",
        "prime destination",
        "luxury lifestyle",
        "world-class amenities",
        "investment potential",
        "growth potential",
        "healthy appreciation",
        "indicating healthy appreciation",
        "active buyer engagement",
        "stable market with strong demand",
        "robust demand",
        "healthy demand",
        "healthy supply",
        "steady demand",
        "high demand",
        "strong demand",
        "active market participation",
        "reliability and market acceptance",
        "luxury interest",
        "stands out",
        "diverse offering",
        "highly liquid",
        "offers potential",
        "could provide entry",
        "growing appeal",
        "premium status",
        "best property type",
        "better property type",
        "recommended property type",
        "ideal property type",
        "top property type",
        "healthy 5.72% price increase",
        "excellent connectivity",
        "excellent amenities",
    ]

    # Tier 2 — Conditional: factually valid only when data-backed (a number appears within
    # 40 characters in the text). If no nearby number is found, treat as a hard block.
    # Examples: "2 BHK is the largest category" is fine; "largest category" alone is not.
    CONDITIONAL_CLAIMS = [
        "largest category",
        "most numerous",
        "highest average price",
        "lowest average price",
    ]

    # Tier 3 — Soft-demote: over-broad terms that are sometimes valid. These are flagged
    # in the validation report as soft_demote_warnings but are NOT stripped and do NOT
    # trigger forbidden_claims_detected (so they never cause a safe-body fallback).
    SOFT_DEMOTE_CLAIMS = [
        "premium",
        "excellent",
    ]

    # Backwards-compat alias — used by _sanitize_text and _find_forbidden_claims.
    # Populated from HARD_BLOCK_CLAIMS + conditional phrases that failed the data-backed check.
    FORBIDDEN_CLAIMS = HARD_BLOCK_CLAIMS + CONDITIONAL_CLAIMS

    ROBOTIC_PHRASES = [
        "visible dataset",
        "structured inputs",
        "source-backed layer",
        "source-backed values",
        "current structured data",
        "currently represented on the page",
        "visible row",
        "visible rows",
        "grounded layer",
        "structured snapshot",
        "structured source data",
        "visible resale dataset",
        "structured market-summary layer",
    ]

    GENERIC_FILLER_PHRASES = [
        "helps buyers understand",
        "helps users understand",
        "helps set expectations",
        "gives a clear picture",
        "provides useful insights",
        "offers a wide selection",
        "offers a wide range",
        "adds context",
        "makes it easier to understand",
        "gives a grounded sense",
        "this helps explain",
        "this helps show",
        "this can help",
        "this section explains",
        "this section covers",
    ]

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

    RESIDENTIAL_PROPERTY_TERMS = {
        "apartment",
        "apartments",
        "flat",
        "flats",
        "builder floor",
        "builder floors",
        "villa",
        "villas",
        "plot",
        "plots",
        "house",
        "houses",
        "independent house",
        "penthouse",
        "penthouses",
        "studio",
        "studios",
    }

    PRICING_SYNONYMS = {
        "asking_price": [
            "asking price",
            "current asking price",
            "price signal",
            "asking rate",
            "average price",
            "avg price",
        ],
        "registration_rate": [
            "registration rate",
            "registered rate",
            "registration price",
        ],
        "sale_avg_price_per_sqft": [
            "average resale price",
            "average price per sq ft",
            "avg price per sq ft",
        ],
    }

    WARNING_TAXONOMY = {
        "repeated_section_body_detected": {"category": "repetition", "severity": "medium"},
        "repeated_sentence_pattern_detected": {"category": "repetition", "severity": "low"},
        "duplicate_faq_answer_detected": {"category": "repetition", "severity": "medium"},
        "high_cross_section_similarity_detected": {"category": "uniqueness", "severity": "medium"},
        "repeated_section_opening_pattern_detected": {"category": "uniqueness", "severity": "low"},
        "low_distinct_term_ratio_detected": {"category": "uniqueness", "severity": "low"},
        "primary_keyword_stuffing_detected": {"category": "keyword", "severity": "high"},
        "exact_match_keyword_overused": {"category": "keyword", "severity": "medium"},
        "stale_source_data_detected": {"category": "freshness", "severity": "medium"},
        "severely_stale_source_data_detected": {"category": "freshness", "severity": "high"},
        "section_too_short": {"category": "structure", "severity": "low"},
        "faq_too_short": {"category": "structure", "severity": "low"},
        "robotic_phrase_detected": {"category": "editorial", "severity": "medium"},
        "generic_filler_detected": {"category": "editorial", "severity": "medium"},
    }

    STALE_DATA_WARNING_DAYS = 45
    STALE_DATA_FAIL_DAYS = 90

    PRIMARY_KEYWORD_MAX_OCCURRENCES = 4
    PRIMARY_KEYWORD_MAX_DENSITY = 0.05
    EXACT_KEYWORD_MAX_OCCURRENCES = 6

    MIN_SECTION_WORD_COUNT = 12
    MIN_SIGNIFICANT_SENTENCE_WORDS = 7
    MIN_SIMILARITY_WORDS = 18
    SECTION_SIMILARITY_THRESHOLD = 0.86
    LOW_DISTINCT_TERM_RATIO_THRESHOLD = 0.45
    REPEATED_OPENING_WORDS = 8

    PASS_SCORE_THRESHOLD = 85
    WARNING_SCORE_THRESHOLD = 70
    FAIL_SCORE_THRESHOLD = 50

    @staticmethod
    def _float_string_variants(value: float) -> set[str]:
        variants: set[str] = set()
        variants.add(str(value))

        fixed_2 = f"{value:.2f}"
        variants.add(fixed_2)

        trimmed = fixed_2.rstrip("0").rstrip(".")
        if trimmed:
            variants.add(trimmed)

        if float(value).is_integer():
            variants.add(str(int(value)))
        else:
            variants.add(str(round(value)))

        return variants

    @staticmethod
    def _extract_allowed_numeric_strings_from_value(value: Any) -> set[str]:
        allowed: set[str] = set()

        def walk(node: Any) -> None:
            if node is None:
                return
            if isinstance(node, dict):
                for nested in node.values():
                    walk(nested)
                return
            if isinstance(node, list):
                for nested in node:
                    walk(nested)
                return
            if isinstance(node, bool):
                return
            if isinstance(node, int):
                allowed.add(str(node))
                return
            if isinstance(node, float):
                allowed.update(FactualValidator._float_string_variants(node))
                return
            if isinstance(node, str):
                for match in re.findall(r"-?\d+(?:\.\d+)?", node):
                    allowed.add(match)

        walk(value)
        return allowed

    @staticmethod
    def _extract_allowed_numeric_strings(content_plan: dict) -> set[str]:
        return FactualValidator._extract_allowed_numeric_strings_from_value(
            content_plan.get("data_context", {})
        )

    @staticmethod
    def _resolve_content_plan_dependency(content_plan: dict, path: str) -> Any:
        root: dict[str, Any] = {
            "entity": content_plan.get("entity", {}),
            **(content_plan.get("data_context", {}) or {}),
        }

        current: Any = root
        for key in path.split("."):
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    @staticmethod
    def _build_dependency_scoped_allowed_numbers(
        content_plan: dict,
        dependency_paths: list[str] | None,
    ) -> set[str]:
        if not dependency_paths:
            return FactualValidator._extract_allowed_numeric_strings(content_plan)

        allowed: set[str] = set()
        for path in dependency_paths:
            value = FactualValidator._resolve_content_plan_dependency(content_plan, path)
            allowed.update(FactualValidator._extract_allowed_numeric_strings_from_value(value))

        return allowed or FactualValidator._extract_allowed_numeric_strings(content_plan)

    @staticmethod
    def _get_section_dependency_paths(content_plan: dict, section_id: str | None) -> list[str]:
        if not section_id:
            return []

        for section in content_plan.get("section_plan", []) or []:
            if section.get("id") == section_id:
                return list(section.get("data_dependencies", []) or [])

        return []

    @staticmethod
    def _get_faq_dependency_paths(content_plan: dict, question: str | None) -> list[str]:
        if not question:
            return []

        for item in content_plan.get("faq_plan", {}).get("faq_intents", []) or []:
            if item.get("question_template") == question:
                return list(item.get("data_dependencies", []) or [])

        return []

    @staticmethod
    def _is_data_backed(text: str, phrase: str, window: int = 40) -> bool:
        """Return True if a number appears within `window` characters of `phrase` in text."""
        lowered = text.lower()
        idx = lowered.find(phrase)
        if idx == -1:
            return False
        region = text[max(0, idx - window): idx + len(phrase) + window]
        return bool(re.search(r"[\d,]+(?:\.\d+)?", region))

    @staticmethod
    def _find_soft_demote_warnings(text: str) -> list[str]:
        """Return soft-demote phrases present in text (flagged but not stripped)."""
        lowered = text.lower()
        return [phrase for phrase in FactualValidator.SOFT_DEMOTE_CLAIMS if phrase in lowered]

    @staticmethod
    def _find_forbidden_claims(text: str) -> list[str]:
        lowered = text.lower()
        found: list[str] = []

        # Tier 1: Hard blocks — always forbidden.
        for phrase in FactualValidator.HARD_BLOCK_CLAIMS:
            if phrase in lowered:
                found.append(phrase)

        # Tier 2: Conditional — only forbidden when NOT data-backed.
        for phrase in FactualValidator.CONDITIONAL_CLAIMS:
            if phrase in lowered and not FactualValidator._is_data_backed(text, phrase):
                found.append(phrase)

        return found

    @staticmethod
    def _find_robotic_phrases(text: str) -> list[str]:
        lowered = text.lower()
        return [phrase for phrase in FactualValidator.ROBOTIC_PHRASES if phrase in lowered]

    @staticmethod
    def _find_generic_filler(text: str) -> list[str]:
        lowered = text.lower()
        return [phrase for phrase in FactualValidator.GENERIC_FILLER_PHRASES if phrase in lowered]

    @staticmethod
    def _normalize_numeric_token(raw: str) -> str:
        cleaned = raw.replace(",", "").strip()
        if cleaned.startswith("+"):
            cleaned = cleaned[1:]

        if cleaned in {"-0", "-0.0", "-0.00"}:
            return "0"

        return cleaned

    @staticmethod
    def _find_unreconciled_numbers(text: str, allowed_numbers: set[str]) -> list[str]:
        findings: list[str] = []

        currency_matches = re.findall(r"₹\s?(-?[\d,]+(?:\.\d+)?)", text)
        plain_matches = re.findall(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?", text)

        candidates = currency_matches + plain_matches
        seen: set[str] = set()

        for raw in candidates:
            cleaned = FactualValidator._normalize_numeric_token(raw)
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)

            if re.fullmatch(r"-?\d{1,2}", cleaned):
                continue

            if cleaned not in allowed_numbers:
                findings.append(cleaned)

        return findings

    @staticmethod
    def _detect_metric_mentions(text: str) -> set[str]:
        lowered = text.lower()
        found: set[str] = set()

        for metric_name, phrases in FactualValidator.PRICING_SYNONYMS.items():
            for phrase in phrases:
                if phrase in lowered:
                    found.add(metric_name)
                    break

        return found

    @staticmethod
    def _validate_metric_consistency(text: str, canonical_metric_name: str) -> list[str]:
        metric_mentions = FactualValidator._detect_metric_mentions(text)
        if not metric_mentions:
            return []

        issues: list[str] = []
        non_canonical = [metric for metric in metric_mentions if metric != canonical_metric_name]
        if non_canonical:
            issues.append("non_canonical_pricing_metric_detected")
        return issues

    @staticmethod
    def _sanitize_text(text: str) -> str:
        sanitized = text

        # Strip Tier 1 hard blocks unconditionally.
        for phrase in FactualValidator.HARD_BLOCK_CLAIMS:
            sanitized = re.sub(re.escape(phrase), "", sanitized, flags=re.IGNORECASE)

        # Strip Tier 2 conditional claims only when they are NOT data-backed.
        for phrase in FactualValidator.CONDITIONAL_CLAIMS:
            if not FactualValidator._is_data_backed(sanitized, phrase):
                sanitized = re.sub(re.escape(phrase), "", sanitized, flags=re.IGNORECASE)

        # Tier 3 (soft-demote) phrases are NOT stripped — they are surfaced as warnings only.

        for phrase in FactualValidator.ROBOTIC_PHRASES:
            sanitized = re.sub(re.escape(phrase), "", sanitized, flags=re.IGNORECASE)

        sanitized = re.sub(r"\s{2,}", " ", sanitized)
        sanitized = re.sub(r"\s+([,.])", r"\1", sanitized)
        sanitized = re.sub(r"\s+([)])", r"\1", sanitized)
        sanitized = re.sub(r"([(])\s+", r"\1", sanitized)
        return sanitized.strip()

    @staticmethod
    def _normalize_text(text: str) -> str:
        lowered = text.lower()
        lowered = re.sub(r"\s+", " ", lowered)
        lowered = re.sub(r"[^\w\s]", "", lowered)
        return lowered.strip()

    @staticmethod
    def _tokenize_words(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    @staticmethod
    def _word_count(text: str) -> int:
        return len(FactualValidator._tokenize_words(text))

    @staticmethod
    def _parse_iso_date(value: str | None) -> datetime | None:
        if not value or not isinstance(value, str):
            return None

        raw = value.strip()
        if not raw:
            return None

        try:
            if raw.endswith("Z"):
                raw = raw.replace("Z", "+00:00")
            return datetime.fromisoformat(raw)
        except ValueError:
            pass

        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def _count_phrase_occurrences(text: str, phrase: str) -> int:
        if not phrase:
            return 0
        pattern = re.escape(phrase.lower())
        return len(re.findall(pattern, text.lower()))

    @staticmethod
    def _jaccard_similarity(text_a: str, text_b: str) -> float:
        words_a = set(FactualValidator._tokenize_words(text_a))
        words_b = set(FactualValidator._tokenize_words(text_b))

        if not words_a or not words_b:
            return 0.0

        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        return len(intersection) / max(len(union), 1)

    @staticmethod
    def _build_repetition_check(draft: dict) -> dict[str, Any]:
        sections = draft.get("sections", [])
        normalized_body_map: dict[str, str] = {}
        repeated_section_ids: list[str] = []

        for section in sections:
            section_id = section.get("id", "")
            normalized_body = FactualValidator._normalize_text(section.get("body", ""))
            if not normalized_body:
                continue

            if normalized_body in normalized_body_map.values():
                repeated_section_ids.append(section_id)

            normalized_body_map[section_id] = normalized_body

        repeated_sentences: list[str] = []
        sentence_counter: dict[str, int] = {}

        for section in sections:
            body = section.get("body", "")
            parts = re.split(r"[.!?]\s+|\n+", body)
            for part in parts:
                normalized = FactualValidator._normalize_text(part)
                if len(normalized.split()) < FactualValidator.MIN_SIGNIFICANT_SENTENCE_WORDS:
                    continue
                sentence_counter[normalized] = sentence_counter.get(normalized, 0) + 1

        for sentence, count in sentence_counter.items():
            if count > 2:
                repeated_sentences.append(sentence)

        faq_answers = [FactualValidator._normalize_text(item.get("answer", "")) for item in draft.get("faqs", [])]
        duplicate_faq_answer_detected = len([item for item in faq_answers if item]) != len(
            {item for item in faq_answers if item}
        )

        warnings: list[str] = []
        if repeated_section_ids:
            warnings.append("repeated_section_body_detected")
        if repeated_sentences:
            warnings.append("repeated_sentence_pattern_detected")
        if duplicate_faq_answer_detected:
            warnings.append("duplicate_faq_answer_detected")

        return {
            "passed": len(warnings) == 0,
            "warnings": warnings,
            "repeated_section_ids": repeated_section_ids,
            "repeated_sentences": repeated_sentences[:10],
            "duplicate_faq_answer_detected": duplicate_faq_answer_detected,
        }

    @staticmethod
    def _build_page_uniqueness_check(draft: dict) -> dict[str, Any]:
        sections = draft.get("sections", [])
        high_similarity_pairs: list[dict[str, Any]] = []
        high_similarity_section_ids: set[str] = set()

        for left_index in range(len(sections)):
            left = sections[left_index]
            left_body = left.get("body", "")
            if FactualValidator._word_count(left_body) < FactualValidator.MIN_SIMILARITY_WORDS:
                continue

            for right_index in range(left_index + 1, len(sections)):
                right = sections[right_index]
                right_body = right.get("body", "")
                if FactualValidator._word_count(right_body) < FactualValidator.MIN_SIMILARITY_WORDS:
                    continue

                similarity = FactualValidator._jaccard_similarity(left_body, right_body)
                if similarity >= FactualValidator.SECTION_SIMILARITY_THRESHOLD:
                    high_similarity_pairs.append(
                        {
                            "left_section_id": left.get("id"),
                            "right_section_id": right.get("id"),
                            "similarity": round(similarity, 3),
                        }
                    )
                    high_similarity_section_ids.add(left.get("id", ""))
                    high_similarity_section_ids.add(right.get("id", ""))

        opening_counter: dict[str, int] = {}
        opening_section_ids: dict[str, list[str]] = {}

        for section in sections:
            words = FactualValidator._tokenize_words(section.get("body", ""))
            if len(words) < FactualValidator.REPEATED_OPENING_WORDS:
                continue
            opening = " ".join(words[: FactualValidator.REPEATED_OPENING_WORDS])
            opening_counter[opening] = opening_counter.get(opening, 0) + 1
            opening_section_ids.setdefault(opening, []).append(section.get("id", ""))

        repeated_openings = [
            {"opening": opening, "count": count, "section_ids": opening_section_ids[opening]}
            for opening, count in opening_counter.items()
            if count > 2
        ]

        repeated_opening_section_ids = sorted(
            {
                section_id
                for item in repeated_openings
                for section_id in item["section_ids"]
                if section_id
            }
        )

        full_text = " ".join(
            [
                draft.get("metadata", {}).get("intro_snippet", ""),
                *[section.get("body", "") for section in sections],
                *[faq.get("answer", "") for faq in draft.get("faqs", [])],
            ]
        )
        words = FactualValidator._tokenize_words(full_text)
        distinct_term_ratio = (len(set(words)) / len(words)) if words else 1.0

        warnings: list[str] = []
        if high_similarity_pairs:
            warnings.append("high_cross_section_similarity_detected")
        if repeated_openings:
            warnings.append("repeated_section_opening_pattern_detected")
        if words and distinct_term_ratio < FactualValidator.LOW_DISTINCT_TERM_RATIO_THRESHOLD:
            warnings.append("low_distinct_term_ratio_detected")

        return {
            "passed": len(warnings) == 0,
            "warnings": warnings,
            "high_similarity_pairs": high_similarity_pairs[:10],
            "high_similarity_section_ids": sorted([item for item in high_similarity_section_ids if item]),
            "repeated_openings": repeated_openings[:10],
            "repeated_opening_section_ids": repeated_opening_section_ids,
            "distinct_term_ratio": round(distinct_term_ratio, 4),
        }

    @staticmethod
    def _build_keyword_stuffing_check(draft: dict) -> dict[str, Any]:
        keyword_strategy = draft["content_plan"].get("keyword_strategy", {})
        full_text = "\n".join(
            [
                draft.get("metadata", {}).get("title", ""),
                draft.get("metadata", {}).get("meta_description", ""),
                draft.get("metadata", {}).get("h1", ""),
                draft.get("metadata", {}).get("intro_snippet", ""),
                *[section.get("body", "") for section in draft.get("sections", [])],
                *[faq.get("answer", "") for faq in draft.get("faqs", [])],
            ]
        )

        total_words = max(FactualValidator._word_count(full_text), 1)
        primary_keyword_record = keyword_strategy.get("primary_keyword") or {}
        primary_keyword = primary_keyword_record.get("keyword", "") if isinstance(primary_keyword_record, dict) else ""

        exact_matches = keyword_strategy.get("exact_match_keywords", []) or []
        exact_keywords = [record.get("keyword") for record in exact_matches if isinstance(record, dict) and record.get("keyword")]

        warnings: list[str] = []
        exact_counts: dict[str, int] = {}

        primary_count = FactualValidator._count_phrase_occurrences(full_text, primary_keyword) if primary_keyword else 0
        primary_density = primary_count / total_words if primary_keyword else 0.0

        if primary_keyword and (
            primary_count > FactualValidator.PRIMARY_KEYWORD_MAX_OCCURRENCES
            or primary_density > FactualValidator.PRIMARY_KEYWORD_MAX_DENSITY
        ):
            warnings.append("primary_keyword_stuffing_detected")

        for keyword in exact_keywords:
            count = FactualValidator._count_phrase_occurrences(full_text, keyword)
            exact_counts[keyword] = count
            if count > FactualValidator.EXACT_KEYWORD_MAX_OCCURRENCES:
                warnings.append("exact_match_keyword_overused")

        return {
            "passed": len(warnings) == 0,
            "warnings": sorted(set(warnings)),
            "primary_keyword": primary_keyword,
            "primary_keyword_count": primary_count,
            "primary_keyword_density": round(primary_density, 4),
            "exact_keyword_counts": exact_counts,
            "total_words": total_words,
        }

    @staticmethod
    def _build_robotic_language_check(draft: dict) -> dict[str, Any]:
        warnings: list[str] = []
        phrase_hits: dict[str, int] = {}

        texts = [
            draft.get("metadata", {}).get("title", ""),
            draft.get("metadata", {}).get("meta_description", ""),
            draft.get("metadata", {}).get("h1", ""),
            draft.get("metadata", {}).get("intro_snippet", ""),
            *[section.get("body", "") for section in draft.get("sections", [])],
            *[faq.get("answer", "") for faq in draft.get("faqs", [])],
            *[table.get("summary", "") for table in draft.get("tables", [])],
        ]
        full_text = "\n".join(texts).lower()

        for phrase in FactualValidator.ROBOTIC_PHRASES:
            count = full_text.count(phrase)
            if count:
                phrase_hits[phrase] = count

        total_hits = sum(phrase_hits.values())
        if total_hits >= settings.editorial_robotic_phrase_threshold:
            warnings.append("robotic_phrase_detected")

        filler_hits = {}
        filler_total = 0
        for phrase in FactualValidator.GENERIC_FILLER_PHRASES:
            count = full_text.count(phrase)
            if count:
                filler_hits[phrase] = count
                filler_total += count
        if filler_total >= 2:
            warnings.append("generic_filler_detected")

        return {
            "passed": len(warnings) == 0,
            "warnings": warnings,
            "phrase_hits": phrase_hits,
            "total_hits": total_hits,
            "filler_hits": filler_hits,
            "filler_total_hits": filler_total,
        }

    @staticmethod
    def _build_stale_data_check(content_plan: dict) -> dict[str, Any]:
        raw_source_meta = content_plan.get("source_meta", {}).get("raw_source_meta", {}) or {}
        generated_at = content_plan.get("generated_at")
        last_modified_date = raw_source_meta.get("last_modified_date")

        generated_dt = FactualValidator._parse_iso_date(generated_at)
        modified_dt = FactualValidator._parse_iso_date(last_modified_date)

        if not generated_dt or not modified_dt:
            return {
                "passed": True,
                "severity": "none",
                "warnings": [],
                "blocking": False,
                "last_modified_date": last_modified_date,
                "days_since_last_modified": None,
            }

        delta_days = (generated_dt.date() - modified_dt.date()).days
        warnings: list[str] = []
        severity = "none"
        blocking = False

        if delta_days > FactualValidator.STALE_DATA_FAIL_DAYS:
            warnings.append("severely_stale_source_data_detected")
            severity = "high"
            blocking = True
        elif delta_days > FactualValidator.STALE_DATA_WARNING_DAYS:
            warnings.append("stale_source_data_detected")
            severity = "medium"

        return {
            "passed": not blocking,
            "severity": severity,
            "warnings": warnings,
            "blocking": blocking,
            "last_modified_date": last_modified_date,
            "days_since_last_modified": delta_days,
        }

    @staticmethod
    def _score_section(
        section: dict,
        validation: dict,
        repetition_check: dict,
        uniqueness_check: dict,
        editorial_min_words: int,
    ) -> dict[str, Any]:
        score = 100
        warnings: list[str] = []

        issues = validation.get("issues", [])
        if issues:
            score -= 40
            warnings.extend(issues)

        body = section.get("body", "")
        word_count = FactualValidator._word_count(body)
        if word_count < editorial_min_words:
            score -= 8
            warnings.append("section_too_short")

        if section.get("id") in repetition_check.get("repeated_section_ids", []):
            score -= 12
            warnings.append("repeated_section_body_detected")

        if section.get("id") in uniqueness_check.get("high_similarity_section_ids", []):
            score -= 8
            warnings.append("high_cross_section_similarity_detected")

        if section.get("id") in uniqueness_check.get("repeated_opening_section_ids", []):
            score -= 3
            warnings.append("repeated_section_opening_pattern_detected")

        score = max(0, min(100, score))

        if score >= 85:
            confidence = "high"
        elif score >= 70:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "id": section.get("id"),
            "title": section.get("title"),
            "score": score,
            "confidence": confidence,
            "warnings": sorted(set(warnings)),
            "word_count": word_count,
        }

    @staticmethod
    def _build_warning_taxonomy(warning_reasons: list[str]) -> dict[str, Any]:
        categorized: dict[str, list[str]] = {}
        severity_counts = {"low": 0, "medium": 0, "high": 0}
        entries: list[dict[str, str]] = []

        for warning in warning_reasons:
            taxonomy = FactualValidator.WARNING_TAXONOMY.get(
                warning,
                {"category": "other", "severity": "medium"},
            )
            category = taxonomy["category"]
            severity = taxonomy["severity"]

            categorized.setdefault(category, []).append(warning)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            entries.append(
                {
                    "warning": warning,
                    "category": category,
                    "severity": severity,
                }
            )

        return {
            "categorized_warnings": categorized,
            "severity_counts": severity_counts,
            "warning_entries": entries,
        }

    @staticmethod
    def _section_has_mixed_scope(section_id: str | None, text: str) -> bool:
        if section_id not in {"market_snapshot", "property_type_signals", "property_type_rate_snapshot"}:
            return False

        lowered = text.lower()
        has_commercial = any(term in lowered for term in FactualValidator.COMMERCIAL_PROPERTY_TERMS)
        has_residential = any(term in lowered for term in FactualValidator.RESIDENTIAL_PROPERTY_TERMS)
        return has_commercial and has_residential

    @staticmethod
    # ------------------------------------------------------------------ #
    # H3 — Cross-Section Coherence Check                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_price_per_sqft_values(text: str) -> list[float]:
        """Extract price-per-sqft numeric values from a text string.

        Recognises patterns like "₹40,238 per sq ft", "40238 per sqft",
        "Rs 1,25,000/sq ft", etc.  Only returns values in the realistic
        INR range for per-sqft pricing (2,000 – 2,00,000).
        """
        pattern = re.compile(
            r"(?:₹|rs\.?\s*)?(\d[\d,]*(?:\.\d+)?)\s*"
            r"(?:per\s+sq(?:\.?\s*ft|uare\s*feet?)|per\s*sqft|/sq\.?\s*ft|per\s+square\s+foot)",
            re.I,
        )
        results: list[float] = []
        for match in pattern.finditer(text):
            try:
                val = float(match.group(1).replace(",", ""))
                if 2_000 <= val <= 2_00_000:  # realistic INR range
                    results.append(val)
            except ValueError:
                pass
        return results

    @staticmethod
    def _build_cross_section_coherence_check(draft: dict) -> dict[str, Any]:
        """H3 — Detect price-per-sqft contradictions across sections and FAQs.

        If the spread of all detected price-per-sqft values across sections and
        FAQs exceeds 15% of the mean, ``cross_section_incoherence_detected`` is
        raised as a warning.  The check is additive and does **not** trigger a
        hard-fail; it penalises the quality score instead.
        """
        all_values: list[float] = []
        source_map: dict[str, list[float]] = {}

        for section in draft.get("sections", []):
            section_id = str(section.get("id") or "unknown_section")
            text = str(section.get("body") or "")
            values = FactualValidator._extract_price_per_sqft_values(text)
            if values:
                all_values.extend(values)
                source_map[section_id] = values

        for faq in draft.get("faqs", []):
            question_key = "faq:" + str(faq.get("question") or "")[:60]
            text = str(faq.get("answer") or "")
            values = FactualValidator._extract_price_per_sqft_values(text)
            if values:
                all_values.extend(values)
                source_map[question_key] = values

        if len(all_values) < 2:
            return {
                "warnings": [],
                "checked_value_count": len(all_values),
                "incoherent_sources": [],
            }

        min_val = min(all_values)
        max_val = max(all_values)
        mean_val = sum(all_values) / len(all_values)
        relative_range = (max_val - min_val) / mean_val if mean_val > 0 else 0.0

        warnings: list[str] = []
        incoherent_sources: list[str] = []

        if relative_range > 0.15:  # >15% spread suggests incoherence
            warnings.append("cross_section_incoherence_detected")
            for source, values in source_map.items():
                if any(mean_val > 0 and abs(v - mean_val) / mean_val > 0.15 for v in values):
                    incoherent_sources.append(source)

        return {
            "warnings": warnings,
            "checked_value_count": len(all_values),
            "value_range": {
                "min": min_val,
                "max": max_val,
                "relative_range_pct": round(relative_range * 100, 1),
            },
            "incoherent_sources": incoherent_sources,
        }

    @staticmethod
    def _build_quality_report(draft: dict, validation_report: dict) -> dict[str, Any]:
        repetition_check = FactualValidator._build_repetition_check(draft)
        uniqueness_check = FactualValidator._build_page_uniqueness_check(draft)
        keyword_stuffing_check = FactualValidator._build_keyword_stuffing_check(draft)
        stale_data_check = FactualValidator._build_stale_data_check(draft["content_plan"])
        robotic_language_check = FactualValidator._build_robotic_language_check(draft)
        coherence_check = FactualValidator._build_cross_section_coherence_check(draft)  # H3

        section_quality_scores = [
            FactualValidator._score_section(
                section=item,
                validation=item_validation["validation"],
                repetition_check=repetition_check,
                uniqueness_check=uniqueness_check,
                editorial_min_words=settings.editorial_min_section_words,
            )
            for item, item_validation in zip(draft.get("sections", []), validation_report["section_checks"])
        ]

        base_score = (
            sum(item["score"] for item in section_quality_scores) / len(section_quality_scores)
            if section_quality_scores
            else 100.0
        )

        faq_short_count = 0
        for faq in draft.get("faqs", []):
            if FactualValidator._word_count(faq.get("answer", "")) < settings.editorial_min_faq_words:
                faq_short_count += 1

        warning_reasons: list[str] = []
        warning_reasons.extend(repetition_check.get("warnings", []))
        warning_reasons.extend(uniqueness_check.get("warnings", []))
        warning_reasons.extend(keyword_stuffing_check.get("warnings", []))
        warning_reasons.extend(stale_data_check.get("warnings", []))
        warning_reasons.extend(robotic_language_check.get("warnings", []))
        warning_reasons.extend(coherence_check.get("warnings", []))  # H3
        if faq_short_count:
            warning_reasons.append("faq_too_short")
        warning_reasons = sorted(set(warning_reasons))

        score_penalty = 0
        penalty_map = {
            "repeated_section_body_detected": 6,
            "repeated_sentence_pattern_detected": 2,
            "duplicate_faq_answer_detected": 5,
            "high_cross_section_similarity_detected": 6,
            "repeated_section_opening_pattern_detected": 1,
            "low_distinct_term_ratio_detected": 3,
            "primary_keyword_stuffing_detected": 12,
            "exact_match_keyword_overused": 5,
            "stale_source_data_detected": 8,
            "severely_stale_source_data_detected": 25,
            "faq_too_short": 5,
            "robotic_phrase_detected": 8,
            "generic_filler_detected": 6,
            "cross_section_incoherence_detected": 8,  # H3
        }
        for warning in warning_reasons:
            score_penalty += penalty_map.get(warning, 0)

        overall_quality_score = round(max(0, min(100, base_score - score_penalty)))

        warning_taxonomy = FactualValidator._build_warning_taxonomy(warning_reasons)

        if not validation_report["passed"] or stale_data_check.get("blocking"):
            approval_status = "fail"
        elif overall_quality_score < FactualValidator.FAIL_SCORE_THRESHOLD:
            approval_status = "fail"
        elif warning_reasons or overall_quality_score < FactualValidator.PASS_SCORE_THRESHOLD:
            approval_status = "warning"
        else:
            approval_status = "pass"

        return {
            "approval_status": approval_status,
            "overall_quality_score": overall_quality_score,
            "warning_reasons": warning_reasons,
            "warning_taxonomy": warning_taxonomy,
            "repetition_check": repetition_check,
            "page_uniqueness_check": uniqueness_check,
            "keyword_stuffing_check": keyword_stuffing_check,
            "stale_data_check": stale_data_check,
            "robotic_language_check": robotic_language_check,
            "coherence_check": coherence_check,  # H3
            "faq_short_count": faq_short_count,
            "section_quality_scores": section_quality_scores,
        }

    @staticmethod
    def validate_text(text: str, allowed_numbers: set[str], canonical_metric_name: str | None = None) -> dict[str, Any]:
        forbidden_claims = FactualValidator._find_forbidden_claims(text)
        unreconciled_numbers = FactualValidator._find_unreconciled_numbers(text, allowed_numbers)
        metric_issues = (
            FactualValidator._validate_metric_consistency(text, canonical_metric_name)
            if canonical_metric_name
            else []
        )
        robotic_phrases = FactualValidator._find_robotic_phrases(text)
        generic_filler = FactualValidator._find_generic_filler(text)
        # Tier 3: soft-demote warnings — flagged but NOT stripped, do NOT trigger issues.
        soft_demote_warnings = FactualValidator._find_soft_demote_warnings(text)
        sanitized_text = FactualValidator._sanitize_text(text)

        issues: list[str] = []
        if forbidden_claims:
            issues.append("forbidden_claims_detected")
        if unreconciled_numbers:
            issues.append("unreconciled_numbers_detected")
        issues.extend(metric_issues)

        return {
            "original_text": text,
            "sanitized_text": sanitized_text,
            "forbidden_claims": forbidden_claims,
            "soft_demote_warnings": soft_demote_warnings,
            "robotic_phrases": robotic_phrases,
            "generic_filler": generic_filler,
            "unreconciled_numbers": unreconciled_numbers,
            "metric_issues": metric_issues,
            "word_count": FactualValidator._word_count(text),
            "passed": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def validate_draft(draft: dict) -> dict[str, Any]:
        content_plan = draft["content_plan"]
        full_allowed_numbers = FactualValidator._extract_allowed_numeric_strings(content_plan)
        canonical_metric_name = content_plan["metadata_plan"]["canonical_pricing_metric"]["metric_name"]

        metadata_checks = {
            "title": FactualValidator.validate_text(
                draft["metadata"].get("title", ""),
                full_allowed_numbers,
                canonical_metric_name,
            ),
            "meta_description": FactualValidator.validate_text(
                draft["metadata"].get("meta_description", ""),
                full_allowed_numbers,
                canonical_metric_name,
            ),
            "h1": FactualValidator.validate_text(
                draft["metadata"].get("h1", ""),
                full_allowed_numbers,
                canonical_metric_name,
            ),
            "intro_snippet": FactualValidator.validate_text(
                draft["metadata"].get("intro_snippet", ""),
                full_allowed_numbers,
                canonical_metric_name,
            ),
        }

        section_checks = []
        for section in draft.get("sections", []):
            section_dependencies = FactualValidator._get_section_dependency_paths(
                content_plan,
                section.get("id"),
            )
            section_allowed_numbers = FactualValidator._build_dependency_scoped_allowed_numbers(
                content_plan,
                section_dependencies,
            )
            body_check = FactualValidator.validate_text(
                section.get("body", ""),
                section_allowed_numbers,
                canonical_metric_name,
            )

            if FactualValidator._section_has_mixed_scope(section.get("id"), section.get("body", "")):
                body_check["issues"] = sorted(set(body_check["issues"] + ["mixed_property_scope_detected"]))
                body_check["passed"] = False

            section_checks.append(
                {
                    "id": section.get("id"),
                    "title": section.get("title"),
                    "validation": body_check,
                }
            )

        faq_checks = []
        for faq in draft.get("faqs", []):
            faq_dependencies = FactualValidator._get_faq_dependency_paths(
                content_plan,
                faq.get("question"),
            )
            faq_allowed_numbers = FactualValidator._build_dependency_scoped_allowed_numbers(
                content_plan,
                faq_dependencies,
            )
            answer_check = FactualValidator.validate_text(
                faq.get("answer", ""),
                faq_allowed_numbers,
                canonical_metric_name,
            )
            faq_checks.append(
                {
                    "question": faq.get("question"),
                    "validation": answer_check,
                }
            )

        passed = all(item["passed"] for item in metadata_checks.values())
        passed = passed and all(item["validation"]["passed"] for item in section_checks)
        passed = passed and all(item["validation"]["passed"] for item in faq_checks)

        report = {
            "passed": passed,
            "metadata_checks": metadata_checks,
            "section_checks": section_checks,
            "faq_checks": faq_checks,
            "canonical_metric_name": canonical_metric_name,
        }

        report["quality_report"] = FactualValidator._build_quality_report(draft, report)
        return report

    @staticmethod
    def summarize_report(validation_report: dict) -> dict[str, Any]:
        failing_metadata_fields = [
            field_name
            for field_name, report in validation_report["metadata_checks"].items()
            if report["issues"]
        ]
        failing_section_ids = [
            item["id"]
            for item in validation_report["section_checks"]
            if item["validation"]["issues"]
        ]
        failing_faq_questions = [
            item["question"]
            for item in validation_report["faq_checks"]
            if item["validation"]["issues"]
        ]

        quality_report = validation_report.get("quality_report", {})
        approval_status = quality_report.get(
            "approval_status",
            "fail" if not validation_report["passed"] else "pass",
        )
        warning_reasons = quality_report.get("warning_reasons", [])

        blocking_reasons: list[str] = []
        if failing_metadata_fields:
            blocking_reasons.append("metadata_validation_failed")
        if failing_section_ids:
            blocking_reasons.append("section_validation_failed")
        if failing_faq_questions:
            blocking_reasons.append("faq_validation_failed")

        return {
            "blocked": approval_status == "fail",
            "approval_status": approval_status,
            "blocking_reasons": blocking_reasons,
            "warning_reasons": warning_reasons,
            "failing_metadata_fields": failing_metadata_fields,
            "failing_section_ids": failing_section_ids,
            "failing_faq_questions": failing_faq_questions,
            "overall_quality_score": quality_report.get("overall_quality_score"),
        }

    @staticmethod
    def apply_sanitization(draft: dict, validation_report: dict) -> dict:
        sanitized = dict(draft)
        sanitized_metadata = dict(sanitized["metadata"])

        for field_name, report in validation_report["metadata_checks"].items():
            sanitized_metadata[field_name] = report["sanitized_text"]

        sanitized["metadata"] = sanitized_metadata

        sanitized_sections = []
        for section, check in zip(sanitized.get("sections", []), validation_report["section_checks"]):
            updated = dict(section)
            updated["body"] = check["validation"]["sanitized_text"]
            updated["validation_passed"] = check["validation"]["passed"]
            updated["validation_issues"] = check["validation"]["issues"]
            sanitized_sections.append(updated)

        sanitized["sections"] = sanitized_sections

        sanitized_faqs = []
        for faq, check in zip(sanitized.get("faqs", []), validation_report["faq_checks"]):
            updated = dict(faq)
            updated["answer"] = check["validation"]["sanitized_text"]
            updated["validation_passed"] = check["validation"]["passed"]
            updated["validation_issues"] = check["validation"]["issues"]
            sanitized_faqs.append(updated)

        sanitized["faqs"] = sanitized_faqs
        sanitized["validation_report"] = validation_report
        sanitized["quality_report"] = validation_report.get("quality_report", {})
        sanitized["debug_summary"] = FactualValidator.summarize_report(validation_report)
        sanitized["needs_review"] = sanitized["debug_summary"]["approval_status"] == "fail"
        return sanitized