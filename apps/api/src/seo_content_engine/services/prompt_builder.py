from __future__ import annotations

import json


class PromptBuilder:
    @staticmethod
    def metadata_prompts(content_plan: dict) -> tuple[str, str]:
        system_prompt = (
            "You generate SEO metadata for Square Yards resale listing pages. "
            "Stay fully grounded in the provided data and keyword plan. "
            "Do not invent facts, amenities, demand claims, popularity claims, investment claims, or numbers. "
            "If price is mentioned, use only the canonical page pricing metric: asking price. "
            "Write like a strong human editor, not like an SEO template engine. "
            "Avoid unsupported phrases such as premium, most sought-after, excellent connectivity, strong demand, luxury, prime destination, investment potential, fast-growing, high-potential. "
            "Avoid generic filler such as helps buyers understand, offers a wide range, provides useful insights, helps set expectations, or gives a clear picture. "
            "Avoid robotic phrasing, stacked keyword strings, and repetitive search language. "
            "Use the primary keyword naturally. Use at most one alternate primary keyword variant only if it improves readability. "
            "The title should read like a clean, high-trust search result. "
            "The meta description should sound useful and page-specific, not generic. "
            "The H1 should be clear and natural. "
            "The intro snippet should feel like a genuine opening line for the page, not a metadata echo. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "metadata_plan": content_plan["metadata_plan"],
            "keyword_strategy": {
                "primary_keyword": content_plan["keyword_strategy"]["primary_keyword"],
                "primary_keyword_variants": content_plan["keyword_strategy"].get("primary_keyword_variants", []),
                "metadata_keyword_priority": content_plan["keyword_strategy"].get("metadata_keyword_priority", []),
                "metadata_keywords": content_plan["metadata_plan"]["supporting_keywords"],
                "exact_match_keywords": content_plan["keyword_strategy"]["exact_match_keywords"],
            },
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "requirements": {
                "brand": "Square Yards",
                "strict_grounding": True,
                "seo_rules": {
                    "use_primary_keyword_naturally": True,
                    "use_alternate_primary_keyword_variant_when_helpful": True,
                    "avoid_keyword_stuffing": True,
                    "meta_description_should_be_descriptive": True,
                    "write_for_humans_first": True,
                    "avoid_clickbait": True,
                },
                "style_rules": {
                    "tone": "natural, grounded, clear, human, SEO-friendly",
                    "avoid_robotic_patterns": True,
                    "avoid_repetition": True,
                    "avoid_internal_language": True,
                    "keep_brand_safe": True,
                },
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
            "You generate grounded editorial sections for Square Yards resale pages. "
            "Use only the provided section-level grounded context and section plan. "
            "Never invent numbers, claims, amenities, connectivity, demand strength, appreciation, investment potential, popularity, or buyer suitability unless explicitly present. "
            "If price is mentioned, use only the canonical page pricing metric: asking price. "
            "For the section id 'price_trends_and_rates', do not mention registration rate, registered rate, registration price, average resale price, average price per sq ft, or avg price per sq ft in prose. "
            "For review sections, use only explicit review counts, ratings, tag signals, and AI summary text if provided. "
            "For demand and supply sections, use only explicit counts, percentages, unit-type splits, listing ranges, and availability values. "
            "For property-type sections, stay within explicit residential property-type names, counts, rates, and grounded distributions. "
            "If the page is for one specific residential property type, stay tightly focused on that type. "
            "Do not mix residential and commercial property types. "
            "For the section id 'property_rates_ai_signals', remain tightly source-bound. Present the snapshot and the listed strengths, challenges, and opportunities without adding advice, interpretation, forecast, or conclusion. "
            "Each section must answer one distinct buyer-facing question. "
            "Use visible data as evidence, not as the entire prose structure. "
            "Do not write in the pattern metric -> restatement -> generic closing sentence. "
            "Do not use phrases such as visible dataset, structured inputs, source-backed layer, current structured data, currently represented on the page, visible row, grounded layer, or structured snapshot unless they appear in the source text itself. "
            "Do not use generic endings such as this helps buyers understand, this gives a useful picture, this helps set expectations, or this gives context. "
            "Write for a real buyer, not for an internal reviewer. "
            "Use 2 to 4 short paragraphs where the data allows. "
            "Vary sentence openings. Avoid filler, repetition, and template-style openings. "
            "Use keywords naturally and sparingly. "
            "You may use competitor-derived planning signals only for structure, emphasis, and hierarchy. Never copy competitor wording. "
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
            "section_generation_context": content_plan.get("section_generation_context", {}),
            "comparison_plan": content_plan.get("comparison_plan", []),
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "keyword_strategy": {
                "primary_keyword": content_plan["keyword_strategy"]["primary_keyword"],
                "primary_keyword_variants": content_plan["keyword_strategy"].get("primary_keyword_variants", []),
                "body_keyword_priority": content_plan["keyword_strategy"].get("body_keyword_priority", []),
                "secondary_keywords": content_plan["keyword_strategy"]["secondary_keywords"],
                "bhk_keywords": content_plan["keyword_strategy"]["bhk_keywords"],
                "price_keywords": content_plan["keyword_strategy"]["price_keywords"],
                "exact_match_keywords": content_plan["keyword_strategy"]["exact_match_keywords"],
                "competitor_intelligence": {
                    "relevant_competitor_keywords": content_plan.get("competitor_intelligence", {}).get(
                        "relevant_competitor_keywords", []
                    ),
                    "relevant_informational_keywords": content_plan.get("competitor_intelligence", {}).get(
                        "relevant_informational_keywords", []
                    ),
                    "relevant_overlap_keywords": content_plan.get("competitor_intelligence", {}).get(
                        "relevant_overlap_keywords", []
                    ),
                },
                "planning_signals": content_plan.get("planning_signals", {}),
            },
            "requirements": {
                "strict_grounding": True,
                "section_rules": {
                    "use_only_section_generation_context_for_narrative": True,
                    "price_trends_and_rates_prose_must_use_only_asking_price": True,
                    "exclude_non_canonical_pricing_metrics_from_prose": True,
                    "review_sections_must_use_explicit_review_inputs_only": True,
                    "demand_supply_sections_must_use_explicit_supply_demand_inputs_only": True,
                    "property_type_sections_must_use_residential_inputs_only": True,
                    "specific_property_type_pages_must_stay_type_specific": True,
                    "avoid_mixing_residential_and_commercial_types": True,
                    "allow_one_alternate_primary_keyword_variant_in_one_other_section": True,
                    "avoid_repeating_same_primary_keyword_in_every_section": True,
                    "min_target_words_per_section": 90,
                    "max_target_words_per_section": 220,
                    "write_like_human_editorial_copy": True,
                    "prefer_2_to_4_short_paragraphs": True,
                    "avoid_template_like_openings": True,
                    "avoid_cross_section_repetition": True,
                    "use_keywords_naturally": True,
                    "each_section_must_have_one_clear_takeaway": True,
                },
                "style_rules": {
                    "tone": "human, descriptive, grounded, SEO-friendly",
                    "reader_goal": "help a buyer understand the actual resale picture on the page",
                    "avoid_filler": True,
                    "avoid_marketing_hype": True,
                    "avoid_internal_workbench_language": True,
                    "prefer_specific_grounded_sentences": True,
                },
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
            "You generate grounded FAQ answers for Square Yards resale listing pages. "
            "Use only the provided FAQ plan and grounded data context. "
            "Do not invent numbers or claims. "
            "If price is mentioned, use only the canonical page pricing metric: asking price. "
            "For review FAQs, use only explicit rating, review-count, tag, or AI-summary inputs. "
            "For demand-supply FAQs, use only explicit counts, percentages, unit-type splits, and listing ranges. "
            "For property-type FAQs, use only explicit property-type, status, or rate inputs. "
            "Answer in a strong AEO style: begin with a direct answer sentence, then add one short explanatory paragraph if useful. "
            "Each answer should feel like a real response to a real buyer query, not like a rewritten section summary. "
            "Do not simply repeat inventory counts unless the question is explicitly about quantity. "
            "Do not use phrases such as visible dataset, structured inputs, source-backed layer, current structured data, or currently represented on the page. "
            "Do not use generic filler such as helps buyers understand, gives a clear picture, or helps set expectations. "
            "Questions should feel like realistic search or buyer questions. "
            "Use keyword variants only when natural. "
            "You may use competitor-derived planning signals only to expand coverage and prioritize realistic questions. Never copy wording. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": content_plan["entity"],
            "faq_plan": content_plan["faq_plan"],
            "data_context": content_plan["data_context"],
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "keyword_strategy": {
                "primary_keyword": content_plan["keyword_strategy"]["primary_keyword"],
                "primary_keyword_variants": content_plan["keyword_strategy"].get("primary_keyword_variants", []),
                "body_keyword_priority": content_plan["keyword_strategy"].get("body_keyword_priority", []),
            },
            "competitor_intelligence": {
                "relevant_competitor_keywords": content_plan.get("competitor_intelligence", {}).get(
                    "relevant_competitor_keywords", []
                ),
                "relevant_informational_keywords": content_plan.get("competitor_intelligence", {}).get(
                    "relevant_informational_keywords", []
                ),
                "relevant_overlap_keywords": content_plan.get("competitor_intelligence", {}).get(
                    "relevant_overlap_keywords", []
                ),
            },
            "planning_signals": content_plan.get("planning_signals", {}),
            "requirements": {
                "strict_grounding": True,
                "faq_rules": {
                    "review_faqs_must_use_explicit_review_inputs_only": True,
                    "demand_supply_faqs_must_use_explicit_inputs_only": True,
                    "property_type_faqs_must_use_explicit_inputs_only": True,
                    "exclude_non_canonical_pricing_metrics_from_price_answers": True,
                    "prefer_broader_coverage": True,
                    "prefer_descriptive_answers": True,
                    "allow_some_keyword_variant_question_phrasing": True,
                    "target_min_faqs": 8,
                    "target_max_faqs": 12,
                    "avoid_duplicate_questions": True,
                    "avoid_duplicate_answers": True,
                    "prefer_people_also_ask_style_questions": True,
                    "direct_answer_first": True,
                },
                "style_rules": {
                    "tone": "natural, buyer-friendly, grounded",
                    "prefer_clear_explanations": True,
                    "avoid_one_line_answers_when_context_exists": True,
                    "avoid_keyword_stuffing": True,
                    "avoid_internal_language": True,
                },
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
    def table_summary_prompt(
        table: dict,
        entity: dict,
        planning_signals: dict | None = None,
    ) -> tuple[str, str]:
        system_prompt = (
            "You generate a short human-readable summary for a grounded Square Yards data table. "
            "Use only the visible table title, columns, rows, and entity context provided. "
            "Do not invent trends, interpretations, recommendations, or unsupported market claims. "
            "Write 2 to 3 sentences maximum. "
            "Explain what the table helps the user compare or understand. "
            "If useful, mention one visible row-level value naturally. "
            "Do not use reviewer language, QA language, or phrases such as visible dataset, structured source data, visible row, or source-backed values. "
            "Do not just narrate the first row unless it supports the table purpose. "
            "You may use competitor-derived planning signals only to decide emphasis. Never copy wording. "
            "Return only valid JSON."
        )

        user_payload = {
            "entity": entity,
            "table": table,
            "planning_signals": planning_signals or {},
            "requirements": {
                "strict_grounding": True,
                "style_rules": {
                    "tone": "natural, informative, concise",
                    "min_sentences": 2,
                    "max_sentences": 3,
                    "avoid_robotic_patterns": True,
                    "avoid_generic_review_workbench_language": True,
                    "avoid_market_hype": True,
                },
                "output_schema": {
                    "summary": "string",
                },
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def repair_section_prompt(content_plan: dict, section: dict, validation: dict) -> tuple[str, str]:
        system_prompt = (
            "You repair a previously generated Square Yards section. "
            "Be surgical. Keep the same section id, title, and purpose. Rewrite only the body. "
            "Remove unsupported claims, forbidden adjectives, invalid numbers, robotic wording, repeated structure, and internal system language. "
            "If price is mentioned, use only the canonical asking price metric. "
            "For the section id 'price_trends_and_rates', do not mention registration rate, registered rate, registration price, average resale price, average price per sq ft, or avg price per sq ft in prose. "
            "For review-related sections, use only explicit review, rating, tag, or AI-summary inputs. "
            "For demand-supply sections, use only explicit counts, percentages, unit-type splits, and listing-range inputs. "
            "For property-type sections, use only explicit property-type, status, rate, and distribution inputs. "
            "For the section id 'property_rates_ai_signals', remain tightly source-bound and do not interpret the signals. "
            "Write like a polished human editor, not like an internal analyst. "
            "Return only valid JSON."
        )

        section_generation_context = content_plan.get("section_generation_context", {}).get(section.get("id"), {})

        user_payload = {
            "entity": content_plan["entity"],
            "section": section,
            "validator_feedback": validation,
            "suggested_safe_rewrite": validation.get("sanitized_text"),
            "section_generation_context": section_generation_context,
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "repair_rules": {
                "preserve_section_id": True,
                "preserve_section_title": True,
                "rewrite_body_only": True,
                "avoid_forbidden_claims": True,
                "avoid_non_canonical_pricing_terms": True,
                "price_trends_and_rates_prose_must_use_only_asking_price": True,
                "review_sections_must_use_explicit_review_inputs_only": True,
                "demand_supply_sections_must_use_explicit_inputs_only": True,
                "property_type_sections_must_use_explicit_inputs_only": True,
                "property_rates_ai_signals_must_feel_human_written": True,
                "keep_human_descriptive_style": True,
                "avoid_repetition": True,
                "avoid_internal_language": True,
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
            "Be surgical. Keep the same question. Rewrite only the answer. "
            "Remove unsupported claims, forbidden adjectives, invalid numbers, robotic wording, and internal system language. "
            "If price is mentioned, use only the canonical asking price metric. "
            "For review FAQs, use only explicit review, rating, tag, or AI-summary inputs. "
            "For demand-supply FAQs, use only explicit counts, percentages, unit-type splits, or listing-range inputs. "
            "For property-type FAQs, use only explicit property-type, status, or rate inputs. "
            "Answer directly first, then explain briefly if useful. "
            "Do not rewrite the answer as a generic page summary. "
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
                "review_faqs_must_use_explicit_review_inputs_only": True,
                "demand_supply_faqs_must_use_explicit_inputs_only": True,
                "property_type_faqs_must_use_explicit_inputs_only": True,
                "prefer_descriptive_grounded_answer": True,
                "avoid_repetition": True,
                "avoid_internal_language": True,
            },
            "output_schema": {
                "question": "string",
                "answer": "string",
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def repair_metadata_prompt(
        content_plan: dict,
        metadata: dict,
        issues_by_field: dict,
        validation_map: dict,
    ) -> tuple[str, str]:
        system_prompt = (
            "You repair previously generated Square Yards metadata. "
            "Be surgical. Preserve the field structure and rewrite only the fields that need fixing. "
            "Remove unsupported claims, forbidden adjectives, invalid numbers, robotic phrasing, and keyword stuffing. "
            "If price is mentioned, use only the canonical asking price metric. "
            "Do not introduce facts beyond the grounded data. "
            "Keep the result polished, specific, and human. "
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
                "keep_human_and_seo_friendly": True,
                "avoid_keyword_stuffing": True,
                "avoid_internal_language": True,
            },
            "output_schema": {
                "title": "string",
                "meta_description": "string",
                "h1": "string",
                "intro_snippet": "string",
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)