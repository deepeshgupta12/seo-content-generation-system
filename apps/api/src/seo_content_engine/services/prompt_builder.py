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
            "The output should still sound natural, readable, and SEO-friendly. "
            "Write metadata that feels human, specific, and useful without becoming promotional or making unsupported claims. "
            "Use the resolved primary keyword naturally, and where helpful, use one alternate primary keyword variant naturally across the title, H1, or meta description. "
            "Do not force all primary keyword variants into every field. "
            "Avoid keyword stuffing, repetitive phrasing, and robotic search-optimized wording. "
            "If a fact is not explicitly present in the input, do not mention it. "
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
                    "tone": "natural, grounded, clear, SEO-friendly",
                    "avoid_robotic_patterns": True,
                    "avoid_repetition": True,
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
            "You generate grounded section copy for Square Yards resale property pages. "
            "Use only the provided section-level grounded context and section plan. "
            "Never invent numbers or unsupported claims. "
            "Do not mention connectivity, amenities, appreciation, investment potential, market strength, popularity, luxury positioning, or buyer suitability unless explicitly present in the input. "
            "Do not use adjectives like premium, excellent, prime, sought-after, fast-growing, high-demand. "
            "When discussing price, use only the canonical page pricing metric: asking price. "
            "For the section id 'price_trends_and_rates', do not mention registration rate, registered rate, registration price, average resale price, average price per sq ft, or avg price per sq ft in prose. "
            "If such metrics exist in broader source data, treat them as non-narrative context and do not write them in the section body. "
            "For review or rating sections, only summarize explicit review counts, average rating, tag signals, and AI summaries if provided. "
            "Do not infer sentiment, satisfaction, desirability, or quality beyond the input. "
            "For demand and supply sections, only summarize explicit counts, percentages, unit-type splits, listing ranges, and availability values from the input. "
            "Do not say demand is strong, weak, healthy, rising, falling, or favorable unless that exact interpretation is explicitly provided. "
            "For property-type sections, only summarize explicit property-type names, counts, rates, status buckets, and grounded distributions from the input. "
            "Do not rank, recommend, or interpret which property type is better. "
            "For the section id 'property_rates_ai_signals', write in restrained editorial prose using only the provided snapshot, strengths, challenges, and opportunity notes. "
            "Do not infer what the signals suggest beyond the source text. "
            "Do not describe the locality as stable, attractive, active, promising, dynamic, or similar unless that wording is explicitly present in the source input. "
            "Do not introduce advisory language, recommendation language, or forward-looking market conclusions. "
            "Use the main primary keyword naturally in the hero intro. "
            "If alternate primary keyword variants are provided, use at most one alternate variant naturally in an early body section when it fits cleanly. "
            "Do not repeat the same primary keyword phrase across every section. "
            "Keep the section human-readable, but source-bound. "
            "Write in a natural, human, descriptive style with 2 to 4 short paragraphs per section when the data allows. "
            "Each section should feel SEO-friendly and readable, not robotic or overly templated, while remaining fully grounded. "
            "Use natural transitions and vary sentence openings. "
            "Do not write generic filler like 'this page provides' or 'users can explore' unless it is necessary and specific. "
            "Make each section meaningfully different from the others. "
            "Prefer explanatory prose that helps a real buyer understand the visible data on the page. "
            "You may use competitor-derived planning signals only for structural inspiration such as section emphasis, section depth, and hierarchy. "
            "Never copy competitor phrasing, claims, or FAQ wording. "
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
                "ready_to_move_keywords": content_plan["keyword_strategy"]["ready_to_move_keywords"],
                "exact_match_keywords": content_plan["keyword_strategy"]["exact_match_keywords"],
                "competitor_intelligence": {
                    "relevant_competitor_keywords": content_plan.get("competitor_intelligence", {}).get("relevant_competitor_keywords", []),
                    "relevant_informational_keywords": content_plan.get("competitor_intelligence", {}).get("relevant_informational_keywords", []),
                    "relevant_overlap_keywords": content_plan.get("competitor_intelligence", {}).get("relevant_overlap_keywords", []),
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
                    "property_type_sections_must_use_explicit_property_type_inputs_only": True,
                    "market_strengths_section_must_feel_human_written": True,
                    "market_strengths_section_must_not_read_like_raw_source_dump": True,
                    "hero_must_use_primary_keyword_naturally": True,
                    "allow_one_alternate_primary_keyword_variant_in_early_body": True,
                    "avoid_repeating_same_primary_keyword_in_every_section": True,
                    "min_target_words_per_section": 90,
                    "max_target_words_per_section": 220,
                    "write_like_human_editorial_copy": True,
                    "prefer_2_to_4_short_paragraphs": True,
                    "avoid_template_like_openings": True,
                    "avoid_cross_section_repetition": True,
                    "use_keywords_naturally": True,
                },
                "style_rules": {
                    "tone": "human, descriptive, grounded, SEO-friendly",
                    "reader_goal": "help a buyer understand visible resale data on the page",
                    "avoid_filler": True,
                    "avoid_marketing_hype": True,
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
            "You generate FAQ answers for Square Yards resale listing pages. "
            "Use only the provided FAQ plan and grounded data context. "
            "Answer directly, avoid fluff, and do not invent numbers or claims. "
            "When referencing price, prefer the canonical page pricing metric: asking price. "
            "For review-related FAQs, use only explicit rating, review-count, review-tag, or AI-summary inputs if present. "
            "Do not infer quality, trust, or desirability. "
            "For demand-supply FAQs, use only explicit counts, percentages, unit-type splits, or listing ranges if present. "
            "Do not add market interpretation beyond explicit data. "
            "For property-type FAQs, use only explicit property-type, status, or rate inputs if present. "
            "Do not recommend one property type over another. "
            "Generate broad FAQ coverage and be more descriptive than a one-line answer. "
            "Target 8 to 12 FAQs when the plan supports it, with each answer usually 45 to 110 words. "
            "Questions should feel realistic for actual search or buyer intent. "
            "Prefer people-also-ask style phrasing where appropriate, but keep the wording natural and specific to the page. "
            "If multiple primary keyword variants are provided, you may vary some FAQ question phrasing using those variants naturally. "
            "Do not force every variant into the FAQ set. "
            "Answers should be readable, grounded, and naturally written, not repetitive or robotic. "
            "You may use competitor-derived planning signals only to expand FAQ coverage and prioritize realistic buyer questions. "
            "Never copy competitor phrasing, claims, or FAQ wording. "
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
                "relevant_competitor_keywords": content_plan.get("competitor_intelligence", {}).get("relevant_competitor_keywords", []),
                "relevant_informational_keywords": content_plan.get("competitor_intelligence", {}).get("relevant_informational_keywords", []),
                "relevant_overlap_keywords": content_plan.get("competitor_intelligence", {}).get("relevant_overlap_keywords", []),
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
                },
                "style_rules": {
                    "tone": "natural, buyer-friendly, grounded",
                    "prefer_clear_explanations": True,
                    "avoid_one_line_answers_when_context_exists": True,
                    "avoid_keyword_stuffing": True,
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
            "Write 3 to 4 sentences maximum. "
            "The summary must be user-friendly, reviewer-friendly, and SEO-friendly without sounding robotic. "
            "It should explain what the table covers, why it matters, and reference visible row-level grounded values when useful. "
            "Do not write generic QA or reviewer-workbench language. "
            "Do not mention row counts or column counts unless it is genuinely useful. "
            "You may use competitor-derived planning signals only to decide what to emphasize structurally in the summary. "
            "Never copy competitor wording or claims. "
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
                    "min_sentences": 3,
                    "max_sentences": 4,
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
            "Be surgical. Keep the same section id, section purpose, and grounded meaning. "
            "Only rewrite the body. Remove unsupported claims, forbidden adjectives, and invalid numbers. "
            "If price is mentioned, use only the canonical asking price metric. "
            "For the section id 'price_trends_and_rates', do not mention registration rate, registered rate, registration price, average resale price, average price per sq ft, or avg price per sq ft in prose. "
            "For review-related sections, only use explicit rating, review-count, review-tag, or AI-summary inputs if present. "
            "For demand-supply sections, only use explicit counts, percentages, unit-type splits, or listing-range inputs if present. "
            "For property-type sections, only use explicit property-type, status, rate, and distribution inputs if present. "
            "For the section id 'property_rates_ai_signals', the rewrite must remain tightly source-bound. "
            "Do not interpret what the strengths, challenges, or opportunity notes mean. "
            "Do not introduce advisory, promotional, or forward-looking language. "
            "Present the snapshot and listed points in restrained paragraph form only. "
            "Make the rewrite sound natural and descriptive, but still grounded. "
            "Keep the rewritten section distinct from other sections and avoid robotic phrasing. "
            "Do not introduce any fact that is not present in the provided grounded data. "
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
            "For review-related FAQs, only use explicit rating, review-count, review-tag, or AI-summary inputs if present. "
            "For demand-supply FAQs, only use explicit counts, percentages, unit-type splits, or listing-range inputs if present. "
            "For property-type FAQs, only use explicit property-type, status, or rate inputs if present. "
            "Keep the answer more descriptive than a single sentence when the grounded inputs allow it. "
            "Do not introduce any fact that is not present in the grounded data. "
            "Avoid robotic phrasing and repetitive wording. "
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
            "Remove unsupported claims, forbidden adjectives, and invalid numbers. "
            "If price is mentioned, use only the canonical asking price metric. "
            "Do not introduce facts beyond the grounded data. "
            "Keep the result natural and SEO-friendly. "
            "Avoid stiff, repetitive, or stuffed keyword phrasing. "
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
            },
            "output_schema": {
                "title": "string",
                "meta_description": "string",
                "h1": "string",
                "intro_snippet": "string",
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)