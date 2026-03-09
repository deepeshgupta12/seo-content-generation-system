from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class FactualValidator:
    FORBIDDEN_CLAIMS = [
        "most sought-after",
        "premium status",
        "excellent connectivity",
        "excellent amenities",
        "growing appeal",
        "investment potential",
        "stable market with strong demand",
        "luxury lifestyle",
        "world-class amenities",
        "prime destination",
        "strong demand",
        "high demand",
        "premium",
        "excellent",
        "best property type",
        "better property type",
        "recommended property type",
        "ideal property type",
        "top property type",
    ]

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

    STALE_DATA_THRESHOLD_DAYS = 45
    PRIMARY_KEYWORD_MAX_OCCURRENCES = 3
    PRIMARY_KEYWORD_MAX_DENSITY = 0.04
    MIN_SECTION_WORD_COUNT = 8

    @staticmethod
    def _extract_allowed_numeric_strings(content_plan: dict) -> set[str]:
        allowed: set[str] = set()

        def walk(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, dict):
                for nested in value.values():
                    walk(nested)
                return
            if isinstance(value, list):
                for nested in value:
                    walk(nested)
                return
            if isinstance(value, bool):
                return
            if isinstance(value, int):
                allowed.add(str(value))
                return
            if isinstance(value, float):
                allowed.add(f"{value:.2f}")
                allowed.add(str(round(value)))
                return
            if isinstance(value, str):
                for match in re.findall(r"-?\d{4}(?:\.\d+)?", value):
                    allowed.add(match)

        walk(content_plan.get("data_context", {}))
        return allowed

    @staticmethod
    def _find_forbidden_claims(text: str) -> list[str]:
        lowered = text.lower()
        return [phrase for phrase in FactualValidator.FORBIDDEN_CLAIMS if phrase in lowered]

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
        for phrase in FactualValidator.FORBIDDEN_CLAIMS:
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
    def _word_count(text: str) -> int:
        return len(re.findall(r"\b\w+\b", text))

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
    def validate_text(text: str, allowed_numbers: set[str], canonical_metric_name: str | None = None) -> dict[str, Any]:
        forbidden_claims = FactualValidator._find_forbidden_claims(text)
        unreconciled_numbers = FactualValidator._find_unreconciled_numbers(text, allowed_numbers)
        metric_issues = (
            FactualValidator._validate_metric_consistency(text, canonical_metric_name)
            if canonical_metric_name
            else []
        )
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
            "unreconciled_numbers": unreconciled_numbers,
            "metric_issues": metric_issues,
            "word_count": FactualValidator._word_count(text),
            "passed": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def _build_repetition_check(draft: dict) -> dict[str, Any]:
        sections = draft.get("sections", [])
        normalized_bodies: dict[str, str] = {}
        repeated_section_ids: list[str] = []

        for section in sections:
            section_id = section.get("id", "")
            normalized_body = FactualValidator._normalize_text(section.get("body", ""))
            if not normalized_body:
                continue

            if normalized_body in normalized_bodies.values():
                repeated_section_ids.append(section_id)
            normalized_bodies[section_id] = normalized_body

        repeated_sentences: list[str] = []
        sentence_counter: dict[str, int] = {}

        for section in sections:
            body = section.get("body", "")
            parts = re.split(r"[.!?]\s+|\n+", body)
            for part in parts:
                normalized = FactualValidator._normalize_text(part)
                if len(normalized.split()) < 6:
                    continue
                sentence_counter[normalized] = sentence_counter.get(normalized, 0) + 1

        for sentence, count in sentence_counter.items():
            if count > 1:
                repeated_sentences.append(sentence)

        warnings: list[str] = []
        if repeated_section_ids:
            warnings.append("repeated_section_body_detected")
        if repeated_sentences:
            warnings.append("repeated_sentence_pattern_detected")

        return {
            "passed": len(warnings) == 0,
            "warnings": warnings,
            "repeated_section_ids": repeated_section_ids,
            "repeated_sentences": repeated_sentences[:10],
        }

    @staticmethod
    def _count_phrase_occurrences(text: str, phrase: str) -> int:
        if not phrase:
            return 0
        pattern = re.escape(phrase.lower())
        return len(re.findall(pattern, text.lower()))

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
            if count > FactualValidator.PRIMARY_KEYWORD_MAX_OCCURRENCES + 1:
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
    def _build_stale_data_check(content_plan: dict) -> dict[str, Any]:
        raw_source_meta = content_plan.get("source_meta", {}).get("raw_source_meta", {}) or {}
        generated_at = content_plan.get("generated_at")
        last_modified_date = raw_source_meta.get("last_modified_date")

        generated_dt = FactualValidator._parse_iso_date(generated_at)
        modified_dt = FactualValidator._parse_iso_date(last_modified_date)

        if not generated_dt or not modified_dt:
            return {
                "passed": True,
                "warnings": [],
                "last_modified_date": last_modified_date,
                "days_since_last_modified": None,
            }

        delta_days = (generated_dt.date() - modified_dt.date()).days
        warnings: list[str] = []
        if delta_days > FactualValidator.STALE_DATA_THRESHOLD_DAYS:
            warnings.append("stale_source_data_detected")

        return {
            "passed": len(warnings) == 0,
            "warnings": warnings,
            "last_modified_date": last_modified_date,
            "days_since_last_modified": delta_days,
        }

    @staticmethod
    def _score_section(section: dict, validation: dict, repetition_check: dict) -> dict[str, Any]:
        score = 100
        warnings: list[str] = []

        issues = validation.get("issues", [])
        if issues:
            score -= 40
            warnings.extend(issues)

        body = section.get("body", "")
        word_count = FactualValidator._word_count(body)
        if word_count < FactualValidator.MIN_SECTION_WORD_COUNT:
            score -= 10
            warnings.append("section_too_short")

        if section.get("id") in repetition_check.get("repeated_section_ids", []):
            score -= 20
            warnings.append("repeated_section_body_detected")

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
    def _build_quality_report(draft: dict, validation_report: dict) -> dict[str, Any]:
        repetition_check = FactualValidator._build_repetition_check(draft)
        keyword_stuffing_check = FactualValidator._build_keyword_stuffing_check(draft)
        stale_data_check = FactualValidator._build_stale_data_check(draft["content_plan"])

        section_quality_scores = [
            FactualValidator._score_section(item, item_validation["validation"], repetition_check)
            for item, item_validation in zip(draft.get("sections", []), validation_report["section_checks"])
        ]

        overall_quality_score = (
            round(sum(item["score"] for item in section_quality_scores) / len(section_quality_scores))
            if section_quality_scores
            else 100
        )

        warning_reasons: list[str] = []
        warning_reasons.extend(repetition_check.get("warnings", []))
        warning_reasons.extend(keyword_stuffing_check.get("warnings", []))
        warning_reasons.extend(stale_data_check.get("warnings", []))
        warning_reasons = sorted(set(warning_reasons))

        if not validation_report["passed"]:
            approval_status = "fail"
        elif warning_reasons:
            approval_status = "warning"
        else:
            approval_status = "pass"

        return {
            "approval_status": approval_status,
            "warning_reasons": warning_reasons,
            "repetition_check": repetition_check,
            "keyword_stuffing_check": keyword_stuffing_check,
            "stale_data_check": stale_data_check,
            "section_quality_scores": section_quality_scores,
            "overall_quality_score": overall_quality_score,
        }

    @staticmethod
    def validate_draft(draft: dict) -> dict[str, Any]:
        content_plan = draft["content_plan"]
        allowed_numbers = FactualValidator._extract_allowed_numeric_strings(content_plan)
        canonical_metric_name = content_plan["metadata_plan"]["canonical_pricing_metric"]["metric_name"]

        metadata_checks = {
            "title": FactualValidator.validate_text(
                draft["metadata"].get("title", ""),
                allowed_numbers,
                canonical_metric_name,
            ),
            "meta_description": FactualValidator.validate_text(
                draft["metadata"].get("meta_description", ""),
                allowed_numbers,
                canonical_metric_name,
            ),
            "h1": FactualValidator.validate_text(
                draft["metadata"].get("h1", ""),
                allowed_numbers,
                canonical_metric_name,
            ),
            "intro_snippet": FactualValidator.validate_text(
                draft["metadata"].get("intro_snippet", ""),
                allowed_numbers,
                canonical_metric_name,
            ),
        }

        section_checks = []
        for section in draft.get("sections", []):
            body_check = FactualValidator.validate_text(
                section.get("body", ""),
                allowed_numbers,
                canonical_metric_name,
            )
            section_checks.append(
                {
                    "id": section.get("id"),
                    "title": section.get("title"),
                    "validation": body_check,
                }
            )

        faq_checks = []
        for faq in draft.get("faqs", []):
            answer_check = FactualValidator.validate_text(
                faq.get("answer", ""),
                allowed_numbers,
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
        approval_status = quality_report.get("approval_status", "fail" if not validation_report["passed"] else "pass")
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