# Implementation Context — Enhancement Tracking

**Last Updated:** April 7, 2026

This file is the source of truth for all changes made across two implementation sessions.
Each section lists the exact file and what was changed.

---

## Session 1 — Fixes 1–5 (COMPLETE)

### Fix 3 — Export Block
- `draft_generation_service.py:2075`: `needs_review = sanitized["quality_report"].get("approval_status") == "fail"`
- `artifact_writer.py`: `_guard_review_block()`: removed hard raise, added warning log

### Fix 4 — Remove Property Status Tables
- `content_plan_builder.py`: Added `RESALE_BLOCKED_TABLE_IDS = frozenset({"property_status_table", "coverage_summary_table"})`, removed both from `_build_table_plan()`
- `table_renderer.py`: Added `RESALE_BLOCKED_TABLE_IDS`, `should_render()`, updated `render_all()`

### Fix 5 — Content Length + Bullet Structure
- `prompt_builder.py`: Word range min=150 max=400, bullet instruction added, `key_points` in output schema, system prompt updated
- `draft_generation_service.py — _generate_sections()`: preserve `key_points` from response
- `markdown_renderer.py — _render_sections()`: emit `key_points` as `- bullet` list
- `artifact_writer.py — _add_sections()`: emit `key_points` as DOCX List Bullet; HTML `<ul>`

### Fix 1 — Real Estate Persona + AEO Alignment
- `prompt_builder.py`: buyer persona block in system prompt, AEO directive, positive title examples in metadata_prompts

### Fix 2 — FAQ Coverage Expansion
- `prompt_builder.py — faq_prompts()`: `section_generation_context` in payload, `data_coverage_guide`, target_max_faqs→15, coverage_checklist
- `content_plan_builder.py — _build_faq_plan()`: added intents: price_range, price_trend, demand_supply_bhk_split, location_vs_benchmark, city_market_coverage, micromarket_locality_coverage

---

## Session 2 — Content Deterioration Fixes + Parts A–G (COMPLETE)

### Content Deterioration Fix 1 — `_faq_answer_for_inventory` raw field names
**File:** `apps/api/src/seo_content_engine/services/draft_generation_service.py`
**Change:** Replaced `f"sale_count {sale_count}"` and `f"total_listings {total_listings}"` with natural language: `f"{sale_count:,} active resale listings"` and `f"{total_listings:,} total listings tracked"`.

### Content Deterioration Fix 2 — `_faq_should_use_safe_answer` over-triggering
**File:** `apps/api/src/seo_content_engine/services/draft_generation_service.py`
**Change:** Safe FAQ answer now only triggered for `forbidden_claims_detected` (hard block), not for soft issues like `unreconciled_numbers_detected` or `non_canonical_pricing_metric_detected`.

### Content Deterioration Fix 3 — `_fallback_section_if_needed` over-triggering
**File:** `apps/api/src/seo_content_engine/services/draft_generation_service.py`
**Change:** Section safe body fallback now only triggered for `forbidden_claims_detected` (hard block). Soft issues (unreconciled numbers, non-canonical metrics) no longer replace LLM output with raw data dumps.

### Content Deterioration Fix 4 — `nearby_localities_table` for CITY pages
**File:** `apps/api/src/seo_content_engine/services/content_plan_builder.py`
**Change:** `nearby_localities_table` is now excluded for `RESALE_CITY` pages. City pages already have `location_rates_table` (Micromarket Rate Snapshot) which covers the same data without duplicating. The table is still included for MICROMARKET and LOCALITY pages.

### Content Deterioration Fix 5 — `property_types_table` commercial row filtering
**File:** `apps/api/src/seo_content_engine/services/table_renderer.py`
**Change:** Added `_filter_property_type_rows` to `render_table()` so commercial property types (shop, office space, co-working space, etc.) are filtered from the actual rendered `formatted_rows`, not just from the summary text.

---

## A1 — Expanded Type-Aware Keyword Seeds (COMPLETE)

**File:** `apps/api/src/seo_content_engine/services/keyword_seed_generator.py`
**Changes:**
- LOCALITY: Added 4 BHK seeds, landmark searches, pincode-based seeds (uses `entity.pincode`), amenity-qualified seeds, ready possession seeds. Total: 14–16 seeds.
- MICROMARKET: Added seeds without city suffix, locality-comparison intent, affordable flats, ready possession. Total: 12 seeds.
- CITY: Added zone/area seeds, best area to buy, 1 BHK and 4 BHK variants, affordable seeds. Total: 14 seeds.
- Pincode seeds gated on `entity.get("pincode")` being present.

---

## A2 — Type-Differentiated Section Generation Context (COMPLETE)

**File:** `apps/api/src/seo_content_engine/services/content_plan_builder.py`
**Changes in `_build_section_generation_context()`:**
- Added `page_type: PageType | None = None` parameter.
- Added `entity_type_context` dict injected into EVERY section, containing `page_type` and a type-specific `framing_note`.
- Added `locality_coverage` narrative guardrails for MICROMARKET pages (previously had none).
- Added `nearby_alternatives` narrative guardrails for LOCALITY pages.
- For LOCALITY `market_snapshot`: resolved and injected `ai_summary` (including `locality_character_summary` from `ai_summary.locality_summary`) without changing `data_dependencies`.
- Updated the call in `build()` to pass `page_type=page_type`.

---

## A3 — `nearby_alternatives` Narrative Rules (COMPLETE)

Implemented as part of A2 — `narrative_guardrails` for `nearby_alternatives` section added in `_build_section_generation_context()`.

---

## A4 — Tiered Forbidden-Terms Validator (COMPLETE)

**File:** `apps/api/src/seo_content_engine/services/factual_validator.py`
**Changes:**
- Split `FORBIDDEN_CLAIMS` into three tiers:
  - `HARD_BLOCK_CLAIMS`: 35 terms always stripped and always trigger `forbidden_claims_detected`.
  - `CONDITIONAL_CLAIMS`: 4 terms (`largest category`, `most numerous`, `highest average price`, `lowest average price`) — only forbidden when NOT data-backed (no number within 40 chars).
  - `SOFT_DEMOTE_CLAIMS`: 2 terms (`premium`, `excellent`) — flagged as warnings in `soft_demote_warnings` but NOT stripped and do NOT trigger issues.
- `FORBIDDEN_CLAIMS` kept as backwards-compat alias = `HARD_BLOCK_CLAIMS + CONDITIONAL_CLAIMS`.
- Added `_is_data_backed(text, phrase, window=40)` static helper.
- Added `_find_soft_demote_warnings(text)` static helper.
- Updated `_find_forbidden_claims()` for tiered logic.
- Updated `_sanitize_text()` to strip hard blocks unconditionally, strip conditional only if not data-backed, skip soft-demote.
- Added `soft_demote_warnings` to `validate_text()` return value.

---

## B1 — Type-Differentiated Keyword Priority in Content Plan (COMPLETE)

**File:** `apps/api/src/seo_content_engine/services/content_plan_builder.py`
**Changes:**
- Added `_keyword_limits_by_type(page_type)` method returning per-cluster limits.
- Updated `_body_keyword_priority()` signature to accept `page_type: PageType | None = None`.
- Now includes BHK keywords in body_keyword_priority with type-specific limits (LOCALITY: 8, CITY: 4, MICROMARKET: 6).
- Updated call in `build()` to pass `page_type=page_type`.
- Updated call in `_build_section_generation_context()` to pass `page_type=page_type`.

---

## B2 — BHK Keywords Injected into Section Context (COMPLETE)

Implemented as part of A2 — `target_bhk_phrases` injected into `bhk_and_inventory_mix` section context in `_build_section_generation_context()`.

---

## B4 — FAQ Keyword Candidates into faq_prompts (COMPLETE)

**File:** `apps/api/src/seo_content_engine/services/prompt_builder.py`
**Change:** Added `faq_keyword_candidates` from `keyword_strategy` into the `keyword_strategy` block of `faq_prompts()` user payload.

---

## C1 — Standalone FAQ Regenerate Endpoint (COMPLETE)

**Files:**
- `apps/api/src/seo_content_engine/schemas/requests.py`: Added `ReviewFaqRegenerateRequest` and `ReviewFaqUpdateRequest` schemas.
- `apps/api/src/seo_content_engine/services/draft_generation_service.py`: Added `generate_faqs_standalone(content_plan, openai_client)` static method.
- `apps/api/src/seo_content_engine/services/review_workbench_service.py`: Added `regenerate_faqs()` and `update_faq()` static methods.
- `apps/api/src/seo_content_engine/api/routes/review.py`: Added `POST /v1/review/faq/regenerate` and `POST /v1/review/faq/update` endpoints.

---

## C2 — Per-Axis FAQ Topic Limits (COMPLETE)

**File:** `apps/api/src/seo_content_engine/services/prompt_builder.py`
**Change:** Added `per_axis_target` block to `data_coverage_guide` in `faq_prompts()` with min/max per axis (pricing: 2-3, bhk: 1-2, nearby: 1-2, reviews: 1-2, demand/supply: 1-2, property_type: 1-2, market_context: 1-2).

---

## C3 — FAQ Consistency Warning on Section Edit (COMPLETE)

**File:** `apps/api/src/seo_content_engine/services/review_workbench_service.py`
**Change:** In `update_section_body()`, if the edited section is in `_FAQ_RELEVANT_SECTIONS` (`price_trends_and_rates`, `bhk_and_inventory_mix`, `demand_and_supply_signals`, `market_snapshot`), a `faq_consistency_warning` is included in the mutation summary response.

---

## D1 — AI Locality Summary into market_snapshot (COMPLETE)

Implemented as part of A2 — In `_build_section_generation_context()`, for LOCALITY pages, `ai_summary` (including `locality_character_summary`) is injected into the `market_snapshot` section context. The `entity_type_context.locality_character_summary` is populated from `ai_summary.locality_summary`.

---

## D2 — Type-Aware location_rates Table Labels (COMPLETE)

**File:** `apps/api/src/seo_content_engine/services/content_plan_builder.py`
**Change:** In `_build_table_plan()`, the `location_rates_table` title and `summary_instruction` now vary by page type:
- CITY: "Micromarket Rate Snapshot" — instructs rows represent zones/micromarkets
- MICROMARKET: "Locality Rate Snapshot" — instructs rows represent localities
- LOCALITY: "Sub-Locality Rate Snapshot" — instructs rows represent sub-localities

---

## E3 — Review Status Banner in Exported Files (COMPLETE)

**Files:**
- `apps/api/src/seo_content_engine/services/markdown_renderer.py`: Added blockquote banner at the top when `draft.needs_review=True`.
- `apps/api/src/seo_content_engine/services/artifact_writer.py`:
  - DOCX: Added bold red "⚠️ REVIEW REQUIRED" paragraph before H1.
  - HTML: Added `.review-banner` CSS class and `<div class="review-banner">` before H1 when `needs_review=True`.

---

## Unchanged files (verified safe to skip)

- `factual_validator.py — needs_review logic`: already correct (only fires on "fail")
- `review_workbench_service.py — G3`: `regenerate_draft()` already calls `_safe_refresh_content_plan()` which updates `content_plan` in session on full regeneration.
- `normalizer.py`: no changes needed
- `source_loader.py`: no changes needed
- `keyword_processing.py`: B3 (type-relevance filter) deferred — lower priority, DataForSEO keyword relevance filtering requires careful testing
- `ReviewWorkbenchPage.tsx`: F1 (FAQ edit/regenerate UI) and F2 (validation details) deferred — backend endpoints (C1) are ready; frontend implementation depends on UI framework work
- `core/config.py`: `block_artifact_write_on_review: bool = False` stays False

---

## Priority Items NOT Yet Implemented (deferred)

| Enhancement | Reason Deferred |
|---|---|
| B3 — Type-relevance keyword filter | Requires DataForSEO keyword corpus analysis; risk of over-filtering |
| F1 — FAQ edit/regenerate UI | Backend C1 is done; frontend React/TS work is separate |
| F2 — Validation details in section cards | Frontend work; backend data already available in validation_report |
| F3 — Keywords Intelligence tab | Frontend work |
| E1 — Keyword preview endpoint | Lower priority; nice-to-have |
| E2 — Prompt preview flag | Lower priority; diagnostic tool |
| G1 — Multi-type integration tests | Operational; separate testing effort |
| G2 — Additional sample JSONs | Operational; requires production data samples |
