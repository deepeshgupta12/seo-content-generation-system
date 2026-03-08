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
    ]

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
    def _sanitize_text(text: str) -> str:
        sanitized = text
        for phrase in FactualValidator.FORBIDDEN_CLAIMS:
            sanitized = re.sub(re.escape(phrase), "", sanitized, flags=re.IGNORECASE)

        sanitized = re.sub(r"\s{2,}", " ", sanitized)
        sanitized = re.sub(r"\s+([,.])", r"\1", sanitized)
        return sanitized.strip()

    @staticmethod
    def validate_text(text: str, allowed_numbers: set[str]) -> dict[str, Any]:
        forbidden_claims = FactualValidator._find_forbidden_claims(text)
        unreconciled_numbers = FactualValidator._find_unreconciled_numbers(text, allowed_numbers)
        sanitized_text = FactualValidator._sanitize_text(text)

        issues: list[str] = []
        if forbidden_claims:
            issues.append("forbidden_claims_detected")
        if unreconciled_numbers:
            issues.append("unreconciled_numbers_detected")

        return {
            "original_text": text,
            "sanitized_text": sanitized_text,
            "forbidden_claims": forbidden_claims,
            "unreconciled_numbers": unreconciled_numbers,
            "passed": len(issues) == 0,
            "issues": issues,
        }

    @staticmethod
    def validate_draft(draft: dict) -> dict[str, Any]:
        content_plan = draft["content_plan"]
        allowed_numbers = FactualValidator._extract_allowed_numeric_strings(content_plan)

        metadata_checks = {
            "title": FactualValidator.validate_text(draft["metadata"].get("title", ""), allowed_numbers),
            "meta_description": FactualValidator.validate_text(draft["metadata"].get("meta_description", ""), allowed_numbers),
            "h1": FactualValidator.validate_text(draft["metadata"].get("h1", ""), allowed_numbers),
            "intro_snippet": FactualValidator.validate_text(draft["metadata"].get("intro_snippet", ""), allowed_numbers),
        }

        section_checks = []
        for section in draft.get("sections", []):
            body_check = FactualValidator.validate_text(section.get("body", ""), allowed_numbers)
            section_checks.append(
                {
                    "id": section.get("id"),
                    "title": section.get("title"),
                    "validation": body_check,
                }
            )

        faq_checks = []
        for faq in draft.get("faqs", []):
            answer_check = FactualValidator.validate_text(faq.get("answer", ""), allowed_numbers)
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