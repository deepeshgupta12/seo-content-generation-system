from __future__ import annotations

import json


class PromptBuilder:
    @staticmethod
    def metadata_prompts(content_plan: dict) -> tuple[str, str]:
        system_prompt = (
            "You generate SEO metadata for Square Yards resale listing pages. "
            "Stay fully grounded in the provided data and keyword plan. "
            "Do not invent facts, amenities, popularity claims, demand claims, investment claims, growth claims, or numbers. "
            "If price is mentioned, use only the canonical page pricing metric: sale price. "
            "Write like a strong human editor, not like an SEO template engine. "
            "Avoid phrases such as premium, most sought-after, excellent connectivity, strong demand, luxury, prime destination, investment potential. "
            "Avoid robotic phrasing, stacked keyword strings, and repetitive search language. "
            "Avoid generic intros that could fit any city page. "
            "The title should read like a clean, high-trust search result — specific, location-anchored, and useful to a real buyer. "
            "Good title examples: "
            "'2 & 3 BHK Resale Flats in Andheri West — Prices, Listings & Market Data | Square Yards', "
            "'Resale Properties in Bandra East — Sale Prices & BHK Options | Square Yards', "
            "'Mumbai Resale Property Market — Prices by Micromarket | Square Yards'. "
            "The meta description should answer what a buyer gets from this page in one direct sentence — price signals, BHK options, or locality context. "
            "Good meta description examples: "
            "'Browse resale flats in Andheri West with current sale prices starting from ₹X, BHK availability, and nearby locality comparisons on Square Yards.', "
            "'Check resale property prices in Bandra East — 1 to 4 BHK options, price trends by quarter, and grounded market context on Square Yards.' "
            "The H1 should be natural and clear — not a keyword dump. "
            "The intro snippet should feel like the first sentence of a page a real buyer would trust, not a metadata echo. "
            "Bad patterns to avoid: "
            "'Explore X with Y and Z', "
            "'Find X with insights', "
            "'Browse X with details', "
            "'This page offers useful information'. "
            "Use the primary keyword naturally. Use at most one alternate primary keyword variant only if it improves readability. "
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
            "The primary reader is a real estate buyer — typically someone shortlisting resale properties, "
            "comparing localities, evaluating price points for their budget, or doing final due diligence before visiting. "
            "Write as if you are a knowledgeable real estate editor helping that buyer make sense of what the data shows. "
            "Every section must open with a clear, direct answer to the section's core buyer question — "
            "state the key takeaway in the first sentence, then support it with data in the following sentences. "
            "This is AEO-style writing: answer first, evidence second. "
            "Use only the provided section-level grounded context and section plan. "
            "Never invent numbers, claims, amenities, connectivity, demand strength, appreciation, investment potential, popularity, or buyer suitability unless explicitly present. "
            "If price is mentioned, use only the canonical page pricing metric: sale price. "
            "For the section id 'price_trends_and_rates', do not mention registration rate, registered rate, registration price, average resale price, average price per sq ft, or avg price per sq ft in prose. "
            "For review sections, use only explicit review counts, ratings, tag signals, and AI summary text if provided. "
            "For demand and supply sections, use only explicit counts, percentages, unit-type splits, listing ranges, and availability values. "
            "For property-type sections, stay within explicit residential property-type names, counts, rates, and grounded distributions. "
            "If the page is for one specific residential property type, stay tightly focused on that type. "
            "Do not mix residential and commercial property types. "
            "CRITICAL — PAGE FILTER COMPLIANCE: "
            "If page_filter_reminder is present in the section context and has active_filters, you MUST comply with ALL listed filters. "
            "If bhk_config is set in page_property_type_context (e.g. '2 BHK'), EVERY paragraph and bullet MUST refer "
            "exclusively to that BHK type. Never mention other BHK sizes as alternatives or context. "
            "Never quote total-inventory counts that include all BHK types — only use the count for the filtered BHK. "
            "If the section data shows multiple BHK rows, discuss ONLY the row matching the BHK filter. "
            "Do NOT mention commercial property types (shops, office spaces, warehouses, showrooms) "
            "in any section of a residential page. "
            "For the section id 'property_rates_ai_signals', remain tightly source-bound. Present the snapshot and the listed strengths, challenges, and opportunities without adding advice, interpretation, forecast, ranking, or forward-looking conclusions. "
            "Do not use phrases such as visible dataset, structured inputs, source-backed layer, current structured data, visible row, grounded layer, or structured snapshot. "
            "Do not restate the same metric twice. "
            "Do not end with generic filler like: "
            "'this helps buyers understand', "
            "'this helps set expectations', "
            "'this provides useful insights', "
            "'this offers a wide selection'. "
            "Each section must answer one distinct buyer question. "
            "Write 3 to 4 paragraphs of 2 to 3 sentences each. "
            "For sections that contain data-driven findings (pricing, BHK mix, inventory, demand/supply), "
            "follow the prose paragraphs with exactly 3 to 4 bullet points in the key_points field. "
            "CRITICAL — no prose/bullet duplication: bullet points and prose paragraphs must never cover the same information. "
            "If a fact, figure, or observation is stated in the prose, it must NOT appear in the bullet points. "
            "Bullet points must add distinct, additional grounded facts not already covered in the prose — sharp standalone takeaways a buyer would want to scan quickly. "
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

        entity = content_plan["entity"]
        page_type = entity.get("page_type", "")
        entity_name = entity.get("entity_name", "")
        city_name = entity.get("city_name", entity_name)

        if "city" in page_type.lower():
            buyer_persona = (
                f"A buyer researching the broader {city_name} resale market — "
                "comparing micromarkets, understanding sale price bands across zones, "
                "and deciding which area fits their budget and lifestyle."
            )
        elif "micromarket" in page_type.lower():
            buyer_persona = (
                f"A buyer who has shortlisted {entity_name} as a target area and is now "
                "comparing specific localities within it — evaluating sale price levels, "
                "available BHK sizes, and how the area compares to adjacent zones."
            )
        else:
            buyer_persona = (
                f"A buyer actively evaluating resale flats in {entity_name} — "
                "checking current sale prices, available BHK configurations, "
                "nearby alternatives, and what existing residents say about the locality."
            )

        user_payload = {
            "entity": entity,
            "buyer_persona": buyer_persona,
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
                    "price_trends_and_rates_prose_must_use_only_sale_price": True,
                    "exclude_non_canonical_pricing_metrics_from_prose": True,
                    "review_sections_must_use_explicit_review_inputs_only": True,
                    "demand_supply_sections_must_use_explicit_supply_demand_inputs_only": True,
                    "property_type_sections_must_use_residential_inputs_only": True,
                    "specific_property_type_pages_must_stay_type_specific": True,
                    "avoid_mixing_residential_and_commercial_types": True,
                    "allow_one_alternate_primary_keyword_variant_in_one_other_section": True,
                    "avoid_repeating_same_primary_keyword_in_every_section": True,
                    "min_target_words_per_section": 150,
                    "max_target_words_per_section": 400,
                    "write_like_human_editorial_copy": True,
                    "write_3_to_4_paragraphs_of_2_to_3_sentences_each": True,
                    "add_3_to_4_key_points_bullets_for_data_driven_sections": True,
                    "key_points_must_be_grounded_standalone_facts_not_prose_repeats": True,
                    "no_prose_bullet_duplication": "Facts stated in prose must NOT appear in bullets and vice versa — each must cover distinct information",
                    "aeo_style_lead_sentence_answers_section_question_directly": True,
                    "avoid_template_like_openings": True,
                    "avoid_cross_section_repetition": True,
                    "use_keywords_naturally": True,
                    "each_section_must_have_one_clear_takeaway": True,
                },
                "style_rules": {
                    "tone": "human, editorial, grounded, real-estate-buyer-friendly, SEO-friendly, AEO-ready",
                    "reader_goal": "help a resale property buyer understand the data and make a confident shortlisting decision",
                    "avoid_filler": True,
                    "avoid_marketing_hype": True,
                    "avoid_internal_workbench_language": True,
                    "prefer_specific_grounded_sentences": True,
                    "persona_aware": True,
                },
                "output_schema": {
                    "sections": [
                        {
                            "id": "string — same as input section id",
                            "title": "string",
                            "body": "string — 3 to 4 paragraphs of prose",
                            "key_points": [
                                "string — one sharp grounded fact per bullet",
                                "string",
                                "string",
                            ],
                        }
                    ]
                },
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def section_prompt_single(content_plan: dict, section_entry: dict) -> tuple[str, str]:
        """H4 — Single-section prompt for parallel generation.

        Generates the same system prompt as ``sections_prompts`` but sends only
        ONE section in the user payload.  The response schema is also single-section:
        ``{"id": ..., "title": ..., "body": ..., "key_points": [...]}``.

        This method is designed to be called concurrently via ThreadPoolExecutor —
        one call per section_entry from the section_plan.
        """
        system_prompt = (
            "You generate a single grounded editorial section for a Square Yards resale page. "
            "The primary reader is a real estate buyer — typically someone shortlisting resale properties, "
            "comparing localities, evaluating price points for their budget, or doing final due diligence before visiting. "
            "Write as if you are a knowledgeable real estate editor helping that buyer make sense of what the data shows. "
            "Open with a clear, direct answer to the section's core buyer question — "
            "state the key takeaway in the first sentence, then support it with data in the following sentences. "
            "This is AEO-style writing: answer first, evidence second. "
            "Use only the provided section-level grounded context. "
            "Never invent numbers, claims, amenities, connectivity, demand strength, appreciation, investment potential, popularity, or buyer suitability unless explicitly present. "
            "If price is mentioned, use only the canonical page pricing metric: sale price. "
            "CRITICAL — PAGE FILTER COMPLIANCE: "
            "If page_filter_reminder is present in the section_context and has active_filters, comply with ALL listed filters. "
            "If bhk_config is set in page_property_type_context (e.g. '2 BHK'), EVERY paragraph and bullet MUST refer "
            "exclusively to that BHK type. Never mention other BHK sizes as primary topics. "
            "Use only the filtered inventory count for that BHK — never quote the total unfiltered city count. "
            "Do NOT mention commercial property types (shops, office spaces, warehouses, showrooms) on a residential page. "
            "Do not use phrases such as visible dataset, structured inputs, source-backed layer, current structured data, visible row, grounded layer, or structured snapshot. "
            "Do not restate the same metric twice. "
            "Do not end with generic filler like 'this helps buyers understand', 'this helps set expectations', 'this provides useful insights'. "
            "Write 3 to 4 paragraphs of 2 to 3 sentences each. "
            "For sections that contain data-driven findings (pricing, BHK mix, inventory, demand/supply), "
            "follow the prose paragraphs with exactly 3 to 4 bullet points in the key_points field. "
            "CRITICAL — no prose/bullet duplication: bullet points and prose paragraphs must never cover the same information. "
            "If a fact, figure, or observation is stated in the prose, it must NOT appear in the bullet points. "
            "Bullet points must add distinct, additional grounded facts not already covered in the prose — sharp standalone takeaways a buyer would want to scan quickly. "
            "Vary sentence openings. Avoid filler, repetition, and template-style openings. "
            "Use keywords naturally and sparingly. "
            "You may use competitor-derived planning signals only for structure, emphasis, and hierarchy. Never copy competitor wording. "
            "Return only valid JSON."
        )

        entity = content_plan["entity"]
        page_type = entity.get("page_type", "")
        entity_name = entity.get("entity_name", "")
        city_name = entity.get("city_name", entity_name)

        if "city" in page_type.lower():
            buyer_persona = (
                f"A buyer researching the broader {city_name} resale market — "
                "comparing micromarkets, understanding sale price bands across zones, "
                "and deciding which area fits their budget and lifestyle."
            )
        elif "micromarket" in page_type.lower():
            buyer_persona = (
                f"A buyer who has shortlisted {entity_name} as a target area and is now "
                "comparing specific localities within it — evaluating sale price levels, "
                "available BHK sizes, and how the area compares to adjacent zones."
            )
        else:
            buyer_persona = (
                f"A buyer actively evaluating resale flats in {entity_name} — "
                "checking current sale prices, available BHK configurations, "
                "nearby alternatives, and what existing residents say about the locality."
            )

        section_context = (
            content_plan.get("section_generation_context", {})
            .get(section_entry.get("id"), {})
        )

        user_payload = {
            "entity": entity,
            "buyer_persona": buyer_persona,
            "section": section_entry,
            "section_context": section_context,
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
                # Restored: competitor intelligence and planning signals were missing from the
                # parallel per-section prompt, causing keyword quality regression vs. the
                # original single-call sections_prompts().
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
                "min_target_words": 150,
                "max_target_words": 400,
                "aeo_style_lead_sentence": True,
                "write_3_to_4_paragraphs": True,
                "add_3_to_4_key_points_for_data_driven_sections": True,
                "no_prose_bullet_duplication": "Facts stated in prose must NOT appear in bullets and vice versa — each must cover distinct information",
                "allow_one_alternate_primary_keyword_variant_in_one_other_section": True,
                "avoid_repeating_same_primary_keyword": True,
                "use_keywords_naturally": True,
            },
            "output_schema": {
                "id": "string — same as input section id",
                "title": "string",
                "body": "string — 3 to 4 paragraphs of prose",
                "key_points": ["string — one sharp grounded fact per bullet"],
            },
        }

        return system_prompt, json.dumps(user_payload, ensure_ascii=False, indent=2)

    @staticmethod
    def faq_prompts(content_plan: dict) -> tuple[str, str]:
        system_prompt = (
            "You generate grounded FAQ answers for Square Yards resale listing pages. "
            "The reader is a real estate buyer — someone comparing resale options, checking prices, "
            "evaluating a locality, or doing due diligence before visiting. "
            "Use the provided FAQ plan, data context, and section generation context. "
            "The section generation context contains all grounded data available on this page — "
            "use it to generate FAQs that cover every major data axis: pricing, BHK availability, "
            "inventory, demand/supply, reviews, property type mix, nearby localities, and any AI signals. "
            "CRITICAL — PAGE FILTER COMPLIANCE: "
            "If page_filter_context is provided and scope is 'specific', all FAQ questions and answers "
            "MUST be written exclusively for those filter constraints. "
            "If bhk_config is set (e.g. '2 BHK'), every FAQ must refer ONLY to that BHK type. "
            "NEVER ask about 'all BHK configurations' or list other BHK types as alternatives. "
            "The inventory count in FAQs must reflect the filtered count (e.g. 6,100 2 BHK flats), "
            "NOT the total unfiltered city count (e.g. 39,071). "
            "If budget_label is set, frame all price answers relative to that budget band. "
            "If furnishing_type is set, only discuss properties with that furnishing status. "
            "CRITICAL — FILTERED PAGE CONTENT RESTRICTIONS: "
            "When bhk_config is set in page_filter_context, you MUST NOT generate any FAQ about: "
            "(1) market strengths, challenges, or investment opportunities — this data is not BHK-specific; "
            "(2) rental yield, rental rates, or rental income — this is a sale page, not a rental page; "
            "(3) registered transaction rates — use only the asking-price (sale price) metric; "
            "(4) commercial property types (shops, office spaces, warehouses, showrooms) — "
            "this is a residential resale page. "
            "CRITICAL — NO TOPIC OVERLAP OR ANSWER BLEED: "
            "Each FAQ question must address a unique topic not already covered by another FAQ in your output. "
            "Each answer must contain only information relevant to its own question. "
            "Do not repeat the same statistic, count, or claim across multiple answers. "
            "If two candidate questions would use the same data point, merge them into one richer FAQ. "
            "Do not invent numbers or claims. "
            "If price is mentioned, use only the canonical page pricing metric: sale price. "
            "For review FAQs, use only explicit rating, review-count, tag, or AI-summary inputs. "
            "For demand-supply FAQs, use only explicit counts, percentages, unit-type splits, and listing ranges. "
            "For property-type FAQs, use only explicit residential property-type, status, or rate inputs. "
            "Do NOT mention commercial property types (shops, office spaces, warehouses, showrooms) "
            "in any FAQ unless this is explicitly a commercial property page. "
            "Answer in a strong AEO style: start with a direct answer sentence, then add 1 to 3 explanatory sentences. "
            "Do not sound robotic, repetitive, or system-generated. "
            "Do not use phrases such as visible dataset, structured inputs, source-backed layer, current structured data, or currently represented on the page. "
            "Do not turn every FAQ into a mini section summary. "
            "Do not answer a price-range question with city-rate comparisons unless listing-range data actually exists. "
            "Questions should feel like realistic buyer questions — the kind a person would type into Google. "
            "Use keyword variants only when natural. "
            "You may use competitor-derived planning signals only to expand coverage and prioritize realistic questions. Never copy wording. "
            "Return only valid JSON."
        )

        entity = content_plan["entity"]
        entity_name = entity.get("entity_name", "")
        city_name = entity.get("city_name", entity_name)
        page_type = entity.get("page_type", "")

        # Extract page filter context FIRST — these variables are used both in the
        # data_coverage_guide block below and in the user payload further down.
        _entity_for_faq = entity
        _dc_pt_ctx = (content_plan.get("data_context") or {}).get("page_property_type_context") or {}
        _faq_page_filter_context: dict = {}
        _bhk_cfg = _dc_pt_ctx.get("bhk_config") or _entity_for_faq.get("page_bhk_config")
        _budget_lbl = _dc_pt_ctx.get("budget_label") or _entity_for_faq.get("page_budget_label") or ""
        _furnishing = _dc_pt_ctx.get("furnishing_type") or _entity_for_faq.get("page_furnishing_type")
        _faq_scope = _dc_pt_ctx.get("scope") or _entity_for_faq.get("page_property_type_scope") or "all"
        _filters_label = _dc_pt_ctx.get("filters_label") or _entity_for_faq.get("page_filters_label") or ""

        # Build a data coverage guide so the model knows which axes to cover (C2 — per-axis limits)
        # When a BHK/budget/furnishing filter is active, suppress the ai_market_signals axis —
        # that data is city-level and not filtered to the specific property type; surfacing it
        # on a filtered page (e.g. "2 BHK for sale in Gurgaon") would introduce commercial,
        # rental, and investment content that is irrelevant and misleading for that buyer intent.
        _bhk_filter_active = bool(_bhk_cfg)
        _optional_axes = [
            "rera_or_buyer_protection — Are listings RERA-registered?",
            "location_comparison — How do prices here compare to the city or micromarket average?",
            "micromarket_or_locality_coverage — How many areas does this page cover?",
        ]
        if not _bhk_filter_active:
            # Only include ai_market_signals on unfiltered (all-BHK) pages where the
            # city-level market snapshot data is actually relevant to the reader's query.
            _optional_axes.insert(
                1,
                "ai_market_signals — What strengths, challenges, or opportunities does the data highlight?",
            )

        _market_signals_axis_target = (
            {"min": 0, "max": 0} if _bhk_filter_active else {"min": 1, "max": 2}
        )

        data_coverage_guide = {
            "instruction": (
                "Ensure at least one FAQ covers each of the following data axes "
                "when data is present in data_context or section_generation_context. "
                "Skip an axis only if no data exists for it. "
                "Respect per_axis_target limits to avoid over-indexing on pricing at the expense of other axes."
                + (
                    " IMPORTANT: ai_market_signals is suppressed on this page because the page is "
                    "filtered to a specific BHK type. Do NOT generate a FAQ about market strengths, "
                    "challenges, investment opportunities, or the overall market outlook — that data "
                    "is not scoped to the BHK filter and would mislead buyers."
                    if _bhk_filter_active else ""
                )
            ),
            "required_axes": [
                "sale_price_or_price_range — What does a buyer pay for a resale property here?",
                "bhk_availability — Which BHK configurations are available?",
                "inventory_count — How many resale listings are visible?",
                "price_trend — How have sale prices moved recently?",
                "property_type_mix — What types of residential properties are available?",
                "nearby_localities — What alternatives can buyers explore nearby?",
                "reviews_and_ratings — What do residents say about this location?",
                "demand_supply — What does the supply picture look like?",
            ],
            "optional_axes_if_data_present": _optional_axes,
            "per_axis_target": {
                "pricing_and_price_range": {"min": 2, "max": 3},
                "bhk_and_inventory": {"min": 1, "max": 2},
                "nearby_localities": {"min": 1, "max": 2},
                "reviews_and_ratings": {"min": 1, "max": 2},
                "demand_supply": {"min": 1, "max": 2},
                "property_type_mix": {"min": 1, "max": 2},
                "market_context_and_ai_signals": _market_signals_axis_target,
            },
        }

        if "city" in page_type.lower():
            buyer_context = f"A buyer exploring the resale market across {city_name} and trying to narrow down which micromarket or zone fits their budget."
        elif "micromarket" in page_type.lower():
            buyer_context = f"A buyer who has identified {entity_name} as a shortlisted area and needs specific data to compare localities within it."
        else:
            buyer_context = f"A buyer actively evaluating resale properties in {entity_name} and looking for specific, grounded answers before scheduling visits."

        # Build the page filter context object that goes into the user payload.
        if _faq_scope == "specific":
            _faq_page_filter_context = {
                "scope": _faq_scope,
                "filters_label": _filters_label,
                "bhk_config": _bhk_cfg,
                "budget_label": _budget_lbl,
                "furnishing_type": _furnishing,
                "instruction": (
                    f"All FAQs on this page are scoped to: {_filters_label or 'specific filter'}. "
                    + (
                        f"Every question and answer must be about {_bhk_cfg} properties ONLY. "
                        f"Do NOT ask about or mention other BHK types. "
                        f"Use the filtered inventory count ({_bhk_cfg} listings only), "
                        f"not the total city count. "
                        if _bhk_cfg else ""
                    )
                    + (
                        f"All price discussions must be framed relative to the budget band: {_budget_lbl}. "
                        if _budget_lbl else ""
                    )
                    + (
                        f"All property discussions must reference {_furnishing} status. "
                        if _furnishing else ""
                    )
                ),
            }

        user_payload = {
            "entity": entity,
            "buyer_context": buyer_context,
            "page_filter_context": _faq_page_filter_context if _faq_page_filter_context else None,
            "faq_plan": content_plan["faq_plan"],
            "data_context": content_plan["data_context"],
            "section_generation_context": content_plan.get("section_generation_context", {}),
            "data_coverage_guide": data_coverage_guide,
            "canonical_pricing_metric": content_plan["metadata_plan"]["canonical_pricing_metric"],
            "keyword_strategy": {
                "primary_keyword": content_plan["keyword_strategy"]["primary_keyword"],
                "primary_keyword_variants": content_plan["keyword_strategy"].get("primary_keyword_variants", []),
                "body_keyword_priority": content_plan["keyword_strategy"].get("body_keyword_priority", []),
                # B4: Pass FAQ-specific keyword candidates so the model can phrase questions
                # using the exact keyword forms buyers search for.
                "faq_keyword_candidates": content_plan["keyword_strategy"].get("faq_keyword_candidates", []),
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
                    "cover_all_required_data_axes_from_data_coverage_guide": True,
                    "prefer_broader_coverage_over_depth_repetition": True,
                    "prefer_descriptive_answers_1_to_3_sentences": True,
                    "allow_some_keyword_variant_question_phrasing": True,
                    "target_min_faqs": 10,
                    "target_max_faqs": 15,
                    "avoid_duplicate_questions": True,
                    "avoid_duplicate_answers": True,
                    "no_topic_overlap_between_faqs": (
                        "Each FAQ must cover a UNIQUE topic. "
                        "Before writing each FAQ, check that no other FAQ in your output "
                        "already addresses the same data point or buyer question. "
                        "If two candidate questions are about the same topic (e.g. both about price, "
                        "or both about inventory count), MERGE them into one FAQ with a richer answer "
                        "rather than producing two separate near-duplicate questions. "
                        "Do NOT split a single data point across multiple questions just to reach the minimum FAQ count."
                    ),
                    "no_answer_content_bleed": (
                        "Each answer must contain ONLY information relevant to its own question. "
                        "Do not repeat the same number, statistic, or claim in more than one answer. "
                        "If a fact (e.g. the total listing count) was used in one answer, "
                        "do not reference it again in another answer."
                    ),
                    "prefer_people_also_ask_style_questions": True,
                    "direct_answer_first_then_explanation": True,
                },
                "style_rules": {
                    "tone": "natural, buyer-friendly, grounded, real-estate-conversational",
                    "prefer_clear_plain_language_explanations": True,
                    "avoid_one_line_answers_when_context_exists": True,
                    "avoid_keyword_stuffing": True,
                    "avoid_internal_language": True,
                    "write_questions_a_real_buyer_would_google": True,
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
            "You generate a human-readable summary for a grounded Square Yards data table. "
            "The reader is a resale property buyer trying to understand what this table means for their search. "
            "Use only the visible table title, columns, rows, and entity context provided. "
            "Do not invent trends, interpretations, recommendations, or unsupported market claims. "
            "Write 3 to 5 sentences. "
            "First sentence: describe what insight or value a buyer gains from the data — lead with the location, the price, the BHK type, or the key pattern visible. "
            "Never start the first sentence with 'This table' or 'The table'. Open with a noun or verb that leads directly into the insight. "
            "Second and third sentences: highlight one or two specific data points visible in the rows that a buyer would find useful — "
            "for example, the lowest price, the dominant BHK type, the closest nearby locality, or the sharpest price change. "
            "Optional fourth/fifth sentence: give a brief practical framing — how should a buyer use this data in their search? "
            "Do not use reviewer language, QA language, or phrases such as visible dataset, structured source data, visible row, or source-backed values. "
            "Do not narrate the first row mechanically — extract the insight, not the raw values. "
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
                    "tone": "natural, buyer-helpful, informative, real-estate-grounded",
                    "min_sentences": 3,
                    "max_sentences": 5,
                    "buyer_framing_encouraged": True,
                    "highlight_specific_visible_data_points": True,
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
            "Remove unsupported claims, forbidden adjectives, invalid numbers, robotic wording, repeated metric restatement, and internal system language. "
            "If price is mentioned, use only the canonical sale price metric. "
            "For the section id 'price_trends_and_rates', do not mention registration rate, registered rate, registration price, average resale price, average price per sq ft, or avg price per sq ft in prose. "
            "For review-related sections, use only explicit review, rating, tag, or AI-summary inputs. "
            "For demand-supply sections, use only explicit counts, percentages, unit-type splits, and listing-range inputs. "
            "For property-type sections, use only explicit residential property-type, status, rate, and distribution inputs. "
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
                "price_trends_and_rates_prose_must_use_only_sale_price": True,
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
            "If price is mentioned, use only the canonical sale price metric. "
            "For review FAQs, use only explicit review, rating, tag, or AI-summary inputs. "
            "For demand-supply FAQs, use only explicit counts, percentages, unit-type splits, or listing-range inputs. "
            "For property-type FAQs, use only explicit residential property-type, status, or rate inputs. "
            "Answer directly first, then explain briefly if useful. "
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
            "If price is mentioned, use only the canonical sale price metric. "
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