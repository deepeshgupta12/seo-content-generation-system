from __future__ import annotations

import re
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
    ]

    PRICING_SYNONYMS = {
        "asking_price": [
            "asking price",
            "current asking price",
            "price signal",
            "asking rate",
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
                rounded = round(value)
                allowed.add(str(rounded))
                allowed.add(f"{value:.2f}")
                return
            if isinstance(value, str):
                for match in re.findall(r"\b\d{4}\b", value):
                    allowed.add(match)

        walk(content_plan.get("data_context", {}))
        return allowed

    @staticmethod
    def _find_forbidden_claims(text: str) -> list[str]:
        lowered = text.lower()
        return [phrase for phrase in FactualValidator.FORBIDDEN_CLAIMS if phrase in lowered]

    @staticmethod
    def _find_unreconciled_numbers(text: str, allowed_numbers: set[str]) -> list[str]:
        findings: list[str] = []

        currency_matches = re.findall(r"₹\s?([\d,]+(?:\.\d+)?)", text)
        plain_matches = re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", text)

        candidates = currency_matches + plain_matches
        seen: set[str] = set()

        for raw in candidates:
            cleaned = raw.replace(",", "").strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)

            if re.fullmatch(r"\d{1,2}", cleaned):
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
        return sanitized.strip()

    @staticmethod
    def validate_text(text: str, allowed_numbers: set[str], canonical_metric_name: str | None = None) -> dict[str, Any]:
        forbidden_claims = FactualValidator._find_forbidden_claims(text)
        unreconciled_numbers = FactualValidator._find_unreconciled_numbers(text, allowed_numbers)
        metric_issues = FactualValidator._validate_metric_consistency(text, canonical_metric_name) if canonical_metric_name else []
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
            "passed": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def validate_draft(draft: dict) -> dict[str, Any]:
        content_plan = draft["content_plan"]
        allowed_numbers = FactualValidator._extract_allowed_numeric_strings(content_plan)
        canonical_metric_name = content_plan["metadata_plan"]["canonical_pricing_metric"]["metric_name"]

        metadata_checks = {
            "title": FactualValidator.validate_text(draft["metadata"].get("title", ""), allowed_numbers, canonical_metric_name),
            "meta_description": FactualValidator.validate_text(draft["metadata"].get("meta_description", ""), allowed_numbers, canonical_metric_name),
            "h1": FactualValidator.validate_text(draft["metadata"].get("h1", ""), allowed_numbers, canonical_metric_name),
            "intro_snippet": FactualValidator.validate_text(draft["metadata"].get("intro_snippet", ""), allowed_numbers, canonical_metric_name),
        }

        section_checks = []
        for section in draft.get("sections", []):
            body_check = FactualValidator.validate_text(section.get("body", ""), allowed_numbers, canonical_metric_name)
            section_checks.append(
                {
                    "id": section.get("id"),
                    "title": section.get("title"),
                    "validation": body_check,
                }
            )

        faq_checks = []
        for faq in draft.get("faqs", []):
            answer_check = FactualValidator.validate_text(faq.get("answer", ""), allowed_numbers, canonical_metric_name)
            faq_checks.append(
                {
                    "question": faq.get("question"),
                    "validation": answer_check,
                }
            )

        passed = all(item["passed"] for item in metadata_checks.values())
        passed = passed and all(item["validation"]["passed"] for item in section_checks)
        passed = passed and all(item["validation"]["passed"] for item in faq_checks)

        return {
            "passed": passed,
            "metadata_checks": metadata_checks,
            "section_checks": section_checks,
            "faq_checks": faq_checks,
            "canonical_metric_name": canonical_metric_name,
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
        sanitized["needs_review"] = not validation_report["passed"]
        return sanitized