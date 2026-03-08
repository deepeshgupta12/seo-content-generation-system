from __future__ import annotations

import json


class PromptBuilder:
    @staticmethod
    def metadata_prompts(content_plan: dict) -> tuple[str, str]:
        system_prompt = (
            "You generate SEO metadata for Square Yards resale listing pages. "
            "You must stay grounded in the provided data and keyword plan. "
            "Do not invent facts, amenities, connectivity claims, demand claims, popularity claims, investment claims, or numbers. "
            "Avoid phrases like premium, most sought-after, excellent connectivity, strong demand, investment potential, luxury, prime destination. "
            "If a fact is not explicitly present in the input, do not mention it. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "metadata_plan": content_plan["metadata_plan"],
            "keyword_strategy": {
                "primary_keyword": content_plan["keyword_strategy"]["primary_keyword"],
                "metadata_keywords": content_plan["keyword_strategy"]["metadata_keywords"],
                "exact_match_keywords": content_plan["keyword_strategy"]["exact_match_keywords"],
            },
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
                }
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def faq_prompts(content_plan: dict) -> tuple[str, str]:
        system_prompt = (
            "You generate FAQ answers for Square Yards resale listing pages. "
            "Use only the provided FAQ plan and data context. "
            "Answer directly, avoid fluff, and do not invent numbers or claims. "
            "Do not add market interpretation beyond explicit data. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "faq_plan": content_plan["faq_plan"],
            "data_context": content_plan["data_context"],
            "requirements": {
                "strict_grounding": True,
                "output_schema": {
                    "faqs": [
                        {
                            "question": "string",
                            "answer": "string",
                        }
                    ]
                }
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)