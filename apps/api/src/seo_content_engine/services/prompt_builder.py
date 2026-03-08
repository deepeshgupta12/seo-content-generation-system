from __future__ import annotations

import json


class PromptBuilder:
    @staticmethod
    def metadata_prompts(content_plan: dict) -> tuple[str, str]:
        system_prompt = (
            "You generate SEO metadata for Square Yards resale listing pages. "
            "You must stay grounded in the provided data and keyword plan. "
            "Do not invent facts, amenities, connectivity claims, demand claims, popularity claims, investment claims, or numbers. "
            "Use the canonical page pricing metric only when referencing price: asking price. "
            "Avoid phrases like premium, most sought-after, excellent connectivity, strong demand, investment potential, luxury, prime destination. "
            "If a fact is not explicitly present in the input, do not mention it. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "metadata_plan": content_plan["metadata_plan"],
            "keyword_strategy": {
                "primary_keyword": content_plan["keyword_strategy"]["primary_keyword"],
                "metadata_keywords": content_plan["metadata_plan"]["supporting_keywords"],
                "exact_match_keywords": content_plan["keyword_strategy"]["exact_match_keywords"],
            },
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "requirements": {
                "brand": "Square Yards",
                "strict_grounding": True,
                "output_schema": {
                    "title": "string",
                    "meta_description": "string",
                    "h1": "string",
                    "intro_snippet": "string",
                },
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def sections_prompts(content_plan: dict) -> tuple[str, str]:
        system_prompt = (
            "You generate grounded section copy for Square Yards resale property pages. "
            "Use only the provided data context and section plan. "
            "Never invent numbers or unsupported claims. "
            "Do not mention connectivity, amenities, appreciation, investment potential, market strength, popularity, luxury positioning, or buyer suitability unless explicitly present in the input. "
            "Do not use adjectives like premium, excellent, prime, sought-after, fast-growing, high-demand. "
            "When discussing price, prefer the canonical page pricing metric: asking price. "
            "Use neutral, factual, concise language. "
            "Return only valid JSON."
        )

        sections = [
            section
            for section in content_plan["section_plan"]
            if section["render_type"] in {"generative", "hybrid"} and section["id"] != "faq_section"
        ]

        user_payload = {
            "entity": content_plan["entity"],
            "sections": sections,
            "data_context": content_plan["data_context"],
            "comparison_plan": content_plan.get("comparison_plan", []),
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "keyword_strategy": {
                "primary_keyword": content_plan["keyword_strategy"]["primary_keyword"],
                "secondary_keywords": content_plan["keyword_strategy"]["secondary_keywords"],
                "bhk_keywords": content_plan["keyword_strategy"]["bhk_keywords"],
                "price_keywords": content_plan["keyword_strategy"]["price_keywords"],
                "ready_to_move_keywords": content_plan["keyword_strategy"]["ready_to_move_keywords"],
                "exact_match_keywords": content_plan["keyword_strategy"]["exact_match_keywords"],
            },
            "requirements": {
                "strict_grounding": True,
                "output_schema": {
                    "sections": [
                        {
                            "id": "string",
                            "title": "string",
                            "body": "string",
                        }
                    ]
                },
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def faq_prompts(content_plan: dict) -> tuple[str, str]:
        system_prompt = (
            "You generate FAQ answers for Square Yards resale listing pages. "
            "Use only the provided FAQ plan and data context. "
            "Answer directly, avoid fluff, and do not invent numbers or claims. "
            "When referencing price, prefer the canonical page pricing metric: asking price. "
            "Do not add market interpretation beyond explicit data. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "faq_plan": content_plan["faq_plan"],
            "data_context": content_plan["data_context"],
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "requirements": {
                "strict_grounding": True,
                "output_schema": {
                    "faqs": [
                        {
                            "question": "string",
                            "answer": "string",
                        }
                    ]
                },
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def repair_section_prompt(content_plan: dict, section: dict, validation: dict) -> tuple[str, str]:
        system_prompt = (
            "You repair a previously generated Square Yards section. "
            "Be surgical. Keep the same section id, section purpose, and grounded meaning. "
            "Only rewrite the body. Remove unsupported claims, forbidden adjectives, and invalid numbers. "
            "If price is mentioned, use only the canonical asking price metric. "
            "Do not introduce any fact that is not present in the provided grounded data. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "section": section,
            "validator_feedback": validation,
            "suggested_safe_rewrite": validation.get("sanitized_text"),
            "data_context": content_plan["data_context"],
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "repair_rules": {
                "preserve_section_id": True,
                "preserve_section_title": True,
                "rewrite_body_only": True,
                "avoid_forbidden_claims": True,
                "avoid_non_canonical_pricing_terms": True,
            },
            "output_schema": {
                "id": "string",
                "title": "string",
                "body": "string",
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def repair_faq_prompt(content_plan: dict, faq: dict, validation: dict) -> tuple[str, str]:
        system_prompt = (
            "You repair a previously generated Square Yards FAQ answer. "
            "Be surgical. Keep the same question. Only rewrite the answer. "
            "Remove unsupported claims, forbidden adjectives, and invalid numbers. "
            "If price is mentioned, use only the canonical asking price metric. "
            "Do not introduce any fact that is not present in the grounded data. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "faq": faq,
            "validator_feedback": validation,
            "suggested_safe_rewrite": validation.get("sanitized_text"),
            "data_context": content_plan["data_context"],
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "repair_rules": {
                "preserve_question": True,
                "rewrite_answer_only": True,
                "avoid_forbidden_claims": True,
                "avoid_non_canonical_pricing_terms": True,
            },
            "output_schema": {
                "question": "string",
                "answer": "string",
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def repair_metadata_prompt(content_plan: dict, metadata: dict, issues_by_field: dict, validation_map: dict) -> tuple[str, str]:
        system_prompt = (
            "You repair previously generated Square Yards metadata. "
            "Be surgical. Preserve the field structure and rewrite only the fields that need fixing. "
            "Remove unsupported claims, forbidden adjectives, and invalid numbers. "
            "If price is mentioned, use only the canonical asking price metric. "
            "Do not introduce facts beyond the grounded data. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "metadata": metadata,
            "issues_by_field": issues_by_field,
            "validation_by_field": validation_map,
            "metadata_plan": content_plan["metadata_plan"],
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "repair_rules": {
                "preserve_output_fields": ["title", "meta_description", "h1", "intro_snippet"],
                "avoid_forbidden_claims": True,
                "avoid_non_canonical_pricing_terms": True,
            },
            "output_schema": {
                "title": "string",
                "meta_description": "string",
                "h1": "string",
                "intro_snippet": "string",
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)