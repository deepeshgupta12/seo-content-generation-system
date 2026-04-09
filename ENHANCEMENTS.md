# SEO Content Engine — Enhancements & Bug Fix Log

> **IMPORTANT**: This file is the single source of truth for all code changes made to this codebase.
> Every bug fix, enhancement, and refactor must be recorded here with impacted files listed.
> Before making any code change, re-read the relevant entries to avoid regressions.

---

## Session 1 — URL Filter Wiring (commit `0413fc0`)

### Feature: Page URL input wires DSE filter signals through the full pipeline

**What changed:**
A new `UrlParser` class parses Square Yards `/sale/` DSE URLs into structured filter signals (BHK, property type, budget, furnishing, amenities, ownership). These signals flow through the entire content pipeline to scope H1 headlines, section data, and LLM prompts to the URL's filter context.

**Impacted files:**

| File | Change |
|---|---|
| `apps/api/src/seo_content_engine/services/url_parser.py` | NEW — `UrlParser.parse(url)` returns `PageFilters` dict. Key fixes: semi-furnished/furnished precedence via `sorted(by len, reverse=True)`; Studio BHK+type deduplication via `_bhk_is_redundant` check. |
| `apps/api/src/seo_content_engine/schemas/requests.py` | Added `page_url: str \| None` field to `ReviewSessionCreateRequest`. |
| `apps/api/src/seo_content_engine/services/normalizer.py` | Added `_build_page_filter_context_from_url()`, updated `_infer_page_property_type_context()` to accept `page_url` as highest-priority source; added all filter fields to entity dict in both CITY and LOCALITY/MICROMARKET branches. |
| `apps/api/src/seo_content_engine/services/review_workbench_service.py` | Added `page_url` to `build_session()` signature; passes it to `EntityNormalizer.normalize_from_paths()`. |
| `apps/api/src/seo_content_engine/api/routes/review.py` | Passes `page_url` from request payload to `build_session()`. |
| `apps/api/src/seo_content_engine/services/content_plan_builder.py` | `_page_property_type_context()` exposes all filter fields; `_build_metadata_plan()` uses `filters_label` for richer H1 (e.g. "2 BHK Flats Under ₹2 Cr for Sale in Gurgaon"). |
| `apps/web/src/types/review.ts` | Added `page_url?: string \| null` to `ReviewSessionCreateRequest` type. |
| `apps/web/src/pages/ReviewWorkbenchPage.tsx` | Added URL input field; passes `page_url` to `createReviewSession()`. |

---

## Session 2 — BHK/Filter Scope Enforcement (commit `6822df5`)

### Bug: Sections, tables, and FAQs not scoped to URL filter (2 BHK)

**Root causes:**
- `sale_unit_type_distribution` passed unfiltered to section generation context → sections discussed all BHK types
- `sale_unit_type_distribution_table` not filtered → BHK table showed all 5 rows instead of 2 BHK row only
- FAQ prompt had no BHK filter signal → FAQs used total city count (39,071) instead of 2 BHK count (6,100)
- Section/FAQ system prompts lacked BHK compliance blocks

**Impacted files:**

| File | Change |
|---|---|
| `apps/api/src/seo_content_engine/services/content_plan_builder.py` | In `_build_section_generation_context()`: BHK-filters `sale_unit_type_distribution` to target BHK only before injecting into section context. Injects `page_filter_reminder` into every section context when filters are active. |
| `apps/api/src/seo_content_engine/services/table_renderer.py` | Added `_filter_to_target_bhk(rows, bhk_config)` — filters `sale_unit_type_distribution_table` rows using startswith match on `key` field; applied in `render_table()`. |
| `apps/api/src/seo_content_engine/services/prompt_builder.py` | Section/single-section system prompts: added CRITICAL PAGE FILTER COMPLIANCE block. FAQ system prompt: same block + `page_filter_context` in user payload with filtered count instruction. |
| `apps/api/src/seo_content_engine/services/draft_generation_service.py` | Added `_COMMERCIAL_SIGNAL_TERMS` frozenset; `_is_commercial_signal()` helper; `_clean_market_signal_items(exclude_commercial=True)` strips commercial items from market signals lists; BHK-aware safe body in `_build_market_snapshot_safe_body()`. |

---

## Session 3 — Commercial/Rental Content Suppression on BHK-Filtered Pages (commit `5f8c53b`)

### Bug: "Market Insights" section and FAQ still showing commercial data, rental yield, investment advice on 2 BHK page

**Root causes:**
1. Raw `marketSnapshotOverview` API string contained commercial and rental sentences; stored verbatim → LLM reproduced them
2. `property_rates_ai_signals` section was included in the section plan even on BHK-filtered pages
3. `property_rates_ai_signals` FAQ intent was added to the FAQ plan even on BHK-filtered pages
4. `data_coverage_guide` in `faq_prompts()` still listed `ai_market_signals` as an optional axis on filtered pages

**Impacted files:**

| File | Change |
|---|---|
| `apps/api/src/seo_content_engine/services/normalizer.py` | Added `_COMMERCIAL_PROSE_TERMS` tuple and `_sanitize_prose_for_resale()` function. Applied via new `_ss()` helper in `_extract_property_rates_ai_data()` — strips commercial/rental sentences from `market_snapshot`, `insights_long`, `insights_short`, `asking_price_trends_description`, `rates_by_property_types_description`, `registration_overview_description` before storing. |
| `apps/api/src/seo_content_engine/services/content_plan_builder.py` | `_build_sections()`: when `entity.page_bhk_config` is set, `has_property_rates_ai` forced to `False` → "Market Insights" section excluded from section plan entirely. `_build_faq_plan()`: `property_rates_ai_signals` FAQ intent suppressed when BHK filter active via `_bhk_filter_active_faq` gate. |
| `apps/api/src/seo_content_engine/services/prompt_builder.py` | `faq_prompts()`: `ai_market_signals` removed from `data_coverage_guide.optional_axes_if_data_present` on BHK-filtered pages; `market_context_and_ai_signals` per-axis target set to `{min:0, max:0}`; system prompt gains explicit prohibition on market-signals/rental/investment FAQs when `bhk_config` set. Added `no_topic_overlap_between_faqs` and `no_answer_content_bleed` deduplication rules. |

---

## Session 3 — Hotfix: UnboundLocalError in faq_prompts() (commit `4e04005`)

### Bug: `cannot access local variable '_bhk_cfg' where it is not associated with a value`

**Root cause:**
In `faq_prompts()`, `data_coverage_guide` block used `_bhk_cfg` on line 422 but `_bhk_cfg` was only assigned on line 488. Python hoists local variable scope so the early reference raised `UnboundLocalError`.

**Impacted files:**

| File | Change |
|---|---|
| `apps/api/src/seo_content_engine/services/prompt_builder.py` | Moved the entire page filter context extraction block (`_entity_for_faq`, `_dc_pt_ctx`, `_bhk_cfg`, `_budget_lbl`, `_furnishing`, `_faq_scope`, `_filters_label`) to immediately after entity/page_type setup and **before** the `data_coverage_guide` block. Removed the now-duplicate extraction that was previously below the guide. |

---

---

## Session 4 — HTML Output Review: 5 Content Quality Fixes (commit `2c1914f`)

### Issues identified from reviewing `gurgaon-2bhk-properties.html` and `gurgaon-resale_city-draft.html`

**Impacted files:**

| File | Fix |
|---|---|
| `apps/api/src/seo_content_engine/services/draft_generation_service.py` | Fix 1: Added `_FAQ_INTENT_TOPIC_SIGNATURES` dict and `_faq_intent_is_covered()` to `_ensure_faq_coverage()` — LLM-rephrased questions (e.g. "2 BHK" added to template) now recognized as covering the intent, preventing safe-body duplicate FAQs. |
| `apps/api/src/seo_content_engine/services/draft_generation_service.py` | Fix 2: Extended `_COMMERCIAL_SIGNAL_TERMS` frozenset to include rental metrics: "rental yield", "rental rate", "rental rates", "rental income", "rental option", "rental options", "rental market", "rent per", "per month", "lakh per month", "investment opportunity", "investment potential", "registered rate", "registration rate". |
| `apps/api/src/seo_content_engine/services/normalizer.py` | Fix 2 (part 2): Extended `_COMMERCIAL_PROSE_TERMS` with "rental options", "rental rates", "per month", "lakh per month" so the prose sanitizer strips rental-amount sentences from market_snapshot. |
| `apps/api/src/seo_content_engine/services/content_plan_builder.py` | Fix 3: In `_build_section_generation_context()`, applied `_filter_residential_distribution()` to `sale_property_type_distribution` before storing in section context — prevents LLM from citing shop/office space counts on residential pages. |
| `apps/api/src/seo_content_engine/services/draft_generation_service.py` | Fix 4: Rewrote `_build_property_type_rate_snapshot_safe_body()` to produce buyer-facing prose ("Villas in Gurgaon average ₹25,262 per sq ft, up 0.87% recently") instead of raw data format ("asking-rate signal of ₹25,262, change signal of 0.87"). |
| `apps/api/src/seo_content_engine/services/prompt_builder.py` | Fix 5: In `faq_prompts()`, filter `data_context.distributions.sale_unit_type_distribution` to target BHK rows when `_bhk_cfg` is set, so LLM doesn't list all BHK types in the bhk_availability FAQ on a 2 BHK page. |

---

## Key Invariants to Maintain

These rules must be respected in all future changes:

1. **BHK filter gate pattern**: Any data source that is city-level (not BHK-scoped) must be suppressed on pages where `entity.page_bhk_config` is set. The gate is `bool(entity.get("page_bhk_config"))`. Currently applied to: `property_rates_ai_signals` section and FAQ, `ai_market_signals` coverage axis.

2. **`_sanitize_prose_for_resale()`**: Must be called on all prose fields from `property_rates_ai_summary` that could contain commercial/rental content. Do NOT use the raw `_s()` helper for `market_snapshot`, `insights_long`, `insights_short`, `asking_price_trends_description`, `rates_by_property_types_description`, `registration_overview_description`.

3. **Filter variable ordering in `faq_prompts()`**: `_bhk_cfg` and all filter context variables must be extracted BEFORE the `data_coverage_guide` block. Do not move them below it.

4. **`sale_unit_type_distribution` BHK filtering**: Applied in `content_plan_builder._build_section_generation_context()`. Must run before the distribution is stored in section context.

5. **Table BHK filtering**: Applied in `table_renderer.render_table()` via `_filter_to_target_bhk()`. Only for `sale_unit_type_distribution_table` and only when `bhk_config` is set.

6. **Commercial item stripping in lists**: `draft_generation_service._clean_market_signal_items(exclude_commercial=True)` strips commercial items from `market_strengths`, `market_challenges`, `investment_opportunities` lists at safe-body generation time. `_COMMERCIAL_SIGNAL_TERMS` also covers rental metrics — do not remove rental terms from this set.

7. **`sale_property_type_distribution` commercial filtering**: Applied in `content_plan_builder._build_section_generation_context()` for ALL pages (not just BHK-filtered). Uses `_filter_residential_distribution()` to strip shops/office spaces before LLM sees the data.

8. **FAQ deduplication — topic signatures**: `_ensure_faq_coverage()` uses BOTH exact string match AND `_faq_intent_is_covered()` topic-signature match. If you add new `faq_plan` intent IDs, add a corresponding entry to `_FAQ_INTENT_TOPIC_SIGNATURES` in `draft_generation_service.py` so the LLM's rephrased question is recognized as covering that intent.

9. **BHK filtering in FAQ prompt**: `prompt_builder.faq_prompts()` filters `data_context.distributions.sale_unit_type_distribution` to target BHK rows when `_bhk_cfg` is set. This must mirror the filtering in `content_plan_builder._build_section_generation_context()`.

10. **Property Type Rates safe-body**: `_build_property_type_rate_snapshot_safe_body()` uses buyer-facing prose. Do NOT revert to raw data format ("asking-rate signal of…", "change signal of…").
