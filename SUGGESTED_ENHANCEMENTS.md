# Suggested Enhancements — Beyond the 5 Implemented Fixes

**Prepared:** April 7, 2026
**Based on:** Full codebase audit covering normalizer, keyword pipeline, content plan builder, section generation context, factual validator, and frontend API

---

## PART A — Entity Type Handling: City vs Micromarket vs Locality

The system correctly detects entity type and has separate section plans for each, but the actual *content instructions*, *keyword seeds*, and *section generation context* are nearly identical across types. This is the biggest gap for multi-type support.

---

### A1 — Keyword Seeds Are Too Generic and Not Type-Aware

**File:** `apps/api/src/seo_content_engine/services/keyword_seed_generator.py`

**Current state:** All three entity types generate the same flat list of "resale properties in {location}" variants. No type-specific angles.

**What's missing:**

**LOCALITY seeds should include:**
- `"resale flat in {locality} near {landmark}"` — locality buyers search by landmark
- `"{locality} flat for sale {pincode}"` — pincode-level searches are common for localities
- `"resale apartment in {locality} with parking"` — amenity-qualified locality searches
- `"flat for sale in {locality} under {price_band}"` — budget-anchored
- `"1 bhk / 2 bhk / 3 bhk resale flat {locality}"` — all BHK variants, not just 2 & 3

**MICROMARKET seeds should include:**
- `"resale property in {micromarket}"` — without city suffix (users often omit city)
- `"localities in {micromarket} for resale"` — MM buyers compare localities within MM
- `"affordable flats in {micromarket}"` — value-seeking MM buyers
- `"resale flats {micromarket} {city} ready possession"`

**CITY seeds should include:**
- `"best area to buy resale property in {city}"` — informational, high-volume
- `"resale flat {city} under {price_band}"` — budget-qualified city searches
- `"resale property {city} by zone"` — zone-comparison intent
- `"resale 2 bhk {city}"` — city-level BHK intent is very common

**Recommended change:**
- Expand `keyword_seed_generator.py` to 12–15 seeds per type (from current 7–10)
- Add BHK variants for all 3 types (currently only 2 & 3 BHK; missing 1 BHK and 4+ BHK)
- For LOCALITY, pass `pincode` from the entity into seeds
- For CITY, add zone/area-qualified seeds derived from `location_rates` labels

---

### A2 — Section Generation Context Is Not Differentiated by Entity Type

**File:** `apps/api/src/seo_content_engine/services/content_plan_builder.py` — `_build_section_generation_context()`

**Current state:** `market_snapshot`, `price_trends_and_rates`, and `bhk_and_inventory_mix` receive the same data fields and keyword instructions regardless of whether the page is a city, micromarket, or locality.

**What's missing by type:**

**LOCALITY — `market_snapshot` and `price_trends_and_rates` should additionally receive:**
- `ai_summary.locality_summary` — the AI-generated locality character (extracted in `normalizer.py` line 158) but not in `market_snapshot`'s `data_dependencies`
- `pincode` — present in entity dict but never passed to section context
- `review_summary.positive_tags` and `negative_tags` — available but only included in the separate `review_and_rating_signals` section; a brief nod in market_snapshot would anchor the page

**MICROMARKET — `locality_coverage` section has NO narrative guardrails:**
- This is the type-specific section for micromarket pages (line 357 in `_build_sections()`)
- Unlike `micromarket_coverage` (city) which gets `buyer_segmentation` and pricing band instructions, `locality_coverage` gets raw data with no "how to frame this for a buyer" instruction
- It should receive: instruction to explain the count of localities covered, top-priced and lowest-priced localities visible, how a buyer should navigate across them

**CITY — `micromarket_coverage` receives `buyer_segmentation` but it is only conditionally passed:**
- If `buyer_segmentation` doesn't exist (which is possible for smaller cities), the section gets no pricing context at all
- Should fall back to `pricing_summary.location_rates` explicitly with an instruction to frame zones by asking price band

**Recommended change:**
- In `_build_section_generation_context()`, add an `entity_type_context` block to each section's context containing type-specific framing instructions:
  ```python
  "entity_type_context": {
      "page_type": "resale_locality",
      "framing_note": "This is a locality-level page. The reader is comparing this specific area to nearby alternatives.",
      "locality_summary": ai_summary.get("locality_summary"),  # for LOCALITY
  }
  ```
- For `locality_coverage` (MICROMARKET only), add explicit `narrative_rules` matching the quality of `micromarket_coverage`
- Add `ai_summary.locality_summary` to `data_dependencies` of `market_snapshot` for LOCALITY pages only

---

### A3 — `nearby_alternatives` Section (LOCALITY) Lacks Buyer Framing

**File:** `content_plan_builder.py` — `_build_sections()` LOCALITY branch

**Current state:** The `nearby_alternatives` section (inserted for LOCALITY pages, line 1034) receives raw `nearby_localities` data but has no instruction about what a buyer should understand from it — distance, price comparison, or supply comparison.

The section objective is generic: "Highlight nearby locality options a buyer can consider."

**Recommended change:**
Add `narrative_rules` to this section that explicitly instruct the model to:
- Frame each nearby locality by distance and asking-price delta vs the current locality
- Highlight which alternatives have more inventory (where visible)
- Avoid listing more than 4–5 alternatives (the table already lists all; prose should highlight the most relevant)

---

### A4 — Forbidden-Term Validator Strips Factual Statements for All Types

**File:** `apps/api/src/seo_content_engine/services/factual_validator.py`

**Current state:** `FORBIDDEN_CLAIMS` includes terms like `"highest average price"`, `"lowest average price"`, `"largest category"`, `"most numerous"`, `"premium"`, and `"excellent"`. These are blanket string-matches applied to all content regardless of whether the claim is data-backed.

**Specific problems:**
- `"highest average price"` — A CITY page legitimately needs to say "Zone X has the highest average asking price at ₹Y per sq ft." This is factual, data-backed, and useful to buyers.
- `"lowest average price"` — Same issue on the other end of the price spectrum.
- `"largest category"` — A locality with 68% 2 BHK listings legitimately has "the largest category." Stripping this removes a factual claim.
- `"most numerous"` — Same as above.
- `"premium"` — Over-broad. "Premium segment" and "premium pricing" are valid real estate terms that buyers search for. The system should block `"premium location"`, `"premium lifestyle"` but not `"premium segment"`.
- `"excellent"` — Blocks "excellent location" (correct to block) but also "excellent school proximity" which is factual if the AI summary mentions it.

**Recommended change:**
Split `FORBIDDEN_CLAIMS` into three tiers:
1. **Hard-block always** (invented superlatives): `"most sought-after"`, `"prime destination"`, `"luxury lifestyle"`, `"world-class amenities"`, `"strong demand"`, `"investment potential"`, `"growth potential"`, `"healthy appreciation"`
2. **Block only when not data-backed** (requires number/data nearby): `"highest average price"`, `"lowest average price"`, `"largest category"`, `"most numerous"` — if these appear within 30 characters of a number like `"₹15,000"` or `"68%"`, allow them
3. **Soft-demote only** (flag for human review but don't strip): `"premium"`, `"excellent"` — log them as warnings, don't silently remove

This requires moving from a simple string-replacement approach to a context-aware validator.

---

## PART B — Keyword Implementation Gaps

---

### B1 — Keyword Clusters Are Not Type-Differentiated in Content Plan

**File:** `apps/api/src/seo_content_engine/services/content_plan_builder.py`

**Current state:** The `keyword_strategy` block built for the content plan uses the same `_top_keywords()` function with the same limits for all entity types. There is no differentiation of which keyword types are more important for which page type.

**What should differ:**

| Keyword Type | LOCALITY | MICROMARKET | CITY |
|---|---|---|---|
| Primary keyword | `"resale flats in {locality}"` | `"resale properties in {mm}"` | `"resale properties in {city}"` |
| BHK keywords | Critical (locality buyers search by BHK) | Important | Moderate |
| Price keywords | Important (budget check) | Important | Critical (zone comparison) |
| Connectivity/neighborhood keywords | Critical for localities | Not applicable | Not applicable |
| Zone/area keywords | Not applicable | Moderate | Critical |
| FAQ keyword candidates | Locality-specific questions | MM-aggregation questions | City-breadth questions |

**Recommended change:**
Add a `_keyword_priority_by_type()` method that adjusts how many keywords from each cluster get surfaced per section based on page type:
```python
if page_type == PageType.RESALE_LOCALITY:
    # Give more weight to BHK keywords and price keywords
    bhk_limit = 8  # vs current 6
    price_limit = 6  # vs current 5
    zone_limit = 0  # not relevant for locality
elif page_type == PageType.RESALE_CITY:
    # Give more weight to secondary and price keywords for zone comparison
    bhk_limit = 4
    price_limit = 8
    zone_limit = 6  # new keyword type
```

---

### B2 — BHK Keywords Are Generated but Not Injected into Section Context as Keywords

**File:** `content_plan_builder.py` — `_build_section_generation_context()`

**Current state:** `bhk_keywords` are extracted and clustered by the keyword intelligence service. They appear in the `bhk_and_inventory_mix` section's `target_keywords` field. However, the `section_generation_context` block for this section only receives raw distribution data (`sale_unit_type_distribution`, `sale_property_type_distribution`) — not the keyword list.

The model sees "2 BHK: 180 listings, 3 BHK: 95 listings" as data, but it doesn't know that "2 bhk resale flat Andheri West" is the exact keyword phrase it should naturally use.

**Recommended change:**
In `_build_section_generation_context()`, for the `bhk_and_inventory_mix` section, explicitly pass the top BHK keywords into context:
```python
if section_id == "bhk_and_inventory_mix":
    section_context["target_bhk_phrases"] = ContentPlanBuilder._top_keywords(
        keyword_clusters.get("bhk_keywords", []), 6
    )
```

This gives the LLM both the data (distribution counts) and the exact keyword forms to use when writing about that data.

---

### B3 — Keyword Intelligence Does Not Filter Type-Irrelevant Keywords

**File:** `apps/api/src/seo_content_engine/services/keyword_processing.py`

**Current state:** Keywords returned by DataForSEO are filtered for rental terms (`rent`, `rental`, `lease`, `pg`) but not for entity-type-irrelevant terms.

**Problem:**
- For a LOCALITY page, keywords like "resale property Mumbai entire city" are irrelevant — too broad
- For a CITY page, keywords like "resale flat Andheri West" are irrelevant — too specific
- For a MICROMARKET page, keywords like "resale property Mumbai entire city" and locality-specific terms from OTHER micromarkets are irrelevant

**Recommended change:**
Add an entity-type relevance filter in `keyword_processing.py`:
```python
# For LOCALITY: boost keywords containing entity_name; demote keywords that are city-only
# For CITY: boost keywords containing city_name only; demote keywords with specific locality names
# For MICROMARKET: boost keywords containing micromarket name; demote pure city-level or locality-specific ones
```

This prevents city-level keyword pollution on locality pages and vice versa.

---

### B4 — Keywords Do Not Flow Into FAQ Section Context as Intended

**File:** `content_plan_builder.py` — `_build_section_generation_context()` for `faq_section`

**Current state:** The FAQ section (the actual section plan entry, not the FAQs themselves) has `target_keywords` from `faq_keyword_candidates`, but the `keyword_usage_plan` block injected into section_generation_context only passes the primary keyword and `body_keyword_priority` (which is primary + secondary). FAQ-specific keyword candidates don't explicitly reach the faq_generation context.

When `faq_prompts()` is called (separately from sections), it receives:
```python
"keyword_strategy": {
    "primary_keyword": ...,
    "primary_keyword_variants": ...,
    "body_keyword_priority": ...
}
```

But `faq_keyword_candidates` — the keywords extracted specifically for FAQ questions — are not passed.

**Recommended change:**
Add `faq_keyword_candidates` to the `keyword_strategy` in `faq_prompts()`:
```python
"keyword_strategy": {
    "primary_keyword": ...,
    "primary_keyword_variants": ...,
    "body_keyword_priority": ...,
    "faq_keyword_candidates": content_plan["keyword_strategy"].get("faq_keywords", []),
}
```

---

## PART C — FAQ System Gaps

---

### C1 — No Standalone FAQ Regeneration Endpoint

**Files:** `apps/api/src/seo_content_engine/api/routes/review.py`, `apps/web/src/api/review.ts`

**Current state:** To regenerate FAQs, the user must regenerate the entire draft (`POST /v1/review/session/regenerate`). This triggers a full re-run of all sections plus FAQs — wasting tokens and time when only FAQs need to be updated.

**Recommended change:**
Add two new endpoints:
1. `POST /v1/review/faq/regenerate` — Regenerates all FAQs for a session using the existing content plan
2. `POST /v1/review/faq/update` — Updates the answer to a single FAQ (like the existing `section/update`)

The FAQ regenerate endpoint should call `DraftGenerationService._generate_faqs(content_plan, client)` directly without touching sections or metadata.

Add corresponding `RegenerateFaqRequest` and `UpdateFaqRequest` schemas and expose in frontend.

---

### C2 — FAQ Coverage Balance: No Per-Axis Topic Limits

**File:** `apps/api/src/seo_content_engine/services/prompt_builder.py` — `faq_prompts()`

**Current state:** The FAQ plan has 10–15 intents (after the Fix 2 expansion), but the model is free to generate more FAQs on pricing (easy, lots of data) and fewer on demand/supply or reviews (harder, less data). The result is an imbalanced FAQ set.

**Recommended change:**
Add a `per_axis_target` block to `data_coverage_guide`:
```python
"per_axis_target": {
    "pricing_and_price_range": {"min": 2, "max": 3},
    "bhk_and_inventory": {"min": 1, "max": 2},
    "nearby_localities": {"min": 1, "max": 2},
    "reviews_and_ratings": {"min": 1, "max": 2},
    "demand_supply": {"min": 1, "max": 2},
    "property_type_mix": {"min": 1, "max": 2},
    "market_context": {"min": 1, "max": 2},
}
```

---

### C3 — FAQs Are Not Regenerated When Section Data Changes

**Files:** `apps/api/src/seo_content_engine/services/review_workbench_service.py`

**Current state:** When a user edits or regenerates a specific section (e.g., `price_trends_and_rates`), the FAQs remain unchanged — even though the edited section may have introduced new numbers or removed old ones that FAQs reference.

**Recommended change:**
When a section body is mutated (via `update_section_body` or `regenerate_section`), check if the section is in a "FAQ-relevant" set (`price_trends_and_rates`, `bhk_and_inventory_mix`, `demand_and_supply_signals`). If so, append a warning to the mutation summary:
```json
{
    "faq_consistency_warning": "Section 'price_trends_and_rates' was updated. Consider regenerating FAQs to ensure pricing FAQs remain consistent."
}
```

---

## PART D — Content Plan Builder Gaps

---

### D1 — `market_snapshot` Doesn't Receive AI Locality Summary for Locality Pages

**File:** `content_plan_builder.py` — `_build_sections()` and `_build_section_generation_context()`

**Current state:** `ai_summary.locality_summary` is extracted by the normalizer for LOCALITY pages. It contains a human-readable AI summary of the locality's character. However, it is only included in the `review_and_rating_signals` section's data dependencies.

The `market_snapshot` section — the page's opening narrative — doesn't receive this signal. This means the opening of a LOCALITY page is written purely from inventory/pricing numbers, with no locality character context.

**Recommended change:**
For LOCALITY pages only, add `ai_summary` to `data_dependencies` of `market_snapshot`:
```python
if page_type == PageType.RESALE_LOCALITY and ContentPlanBuilder._has_review_signals(normalized):
    market_snapshot_section["data_dependencies"].append("ai_summary")
```

This gives the LOCALITY `market_snapshot` access to the locality character summary that makes the page feel grounded and specific.

---

### D2 — `location_rates` Label Differs by Entity Type but Framing Is the Same

**File:** `content_plan_builder.py` — `_build_table_plan()` and `table_renderer.py`

**Current state:** For CITY pages, `location_rates` contains micromarket-level rates. For MICROMARKET pages, it contains locality-level rates. For LOCALITY pages, it may contain sub-locality rates.

The `location_rates_table` is generated the same way for all types, with column headers `["name", "avgRate", "changePercentage"]` regardless of what "name" represents (micromarket? locality? sub-locality?).

**Recommended change:**
In `_build_table_plan()`, rename the table title and summary instruction based on page type:
```python
location_rates_table_title = {
    PageType.RESALE_CITY: "Micromarket Rate Snapshot",
    PageType.RESALE_MICROMARKET: "Locality Rate Snapshot",
    PageType.RESALE_LOCALITY: "Sub-Locality Rate Snapshot",
}.get(page_type, "Location Rate Snapshot")
```

Also update `table_renderer.py`'s `_build_table_summary()` for `location_rates_table` to use type-aware language.

---

### D3 — `micromarket_coverage` and `locality_coverage` Sections Have Duplicate Logic

**File:** `content_plan_builder.py` — `_build_sections()`

**Current state:** The CITY-specific `micromarket_coverage` section and the MICROMARKET-specific `locality_coverage` section have nearly identical objectives, data dependencies, and context. The only difference is the label ("micromarket" vs "locality").

This creates maintenance risk — any change to one must be mirrored in the other.

**Recommended change:**
Refactor into a single `_build_coverage_section(page_type, entity, keyword_clusters, normalized)` method that returns the appropriate section with type-specific title, label, and objective. This reduces duplicate code and ensures consistent guardrails for both.

---

## PART E — Schema and API Gaps

---

### E1 — No Keyword Override Preview Before Draft Generation

**Files:** `apps/api/src/seo_content_engine/schemas/requests.py`, `apps/web/src/pages/ReviewWorkbenchPage.tsx`

**Current state:** The user can specify `primary_keyword_overrides` when creating a review session, but there's no way to preview what keyword cluster will result from those overrides before paying the full generation cost.

**Recommended change:**
Add a `POST /v1/keywords/preview` endpoint that accepts the same payload as the session creation request but returns only the computed keyword strategy (primary, variants, secondary, BHK, price keywords) without running draft generation. This lets users validate keyword choices before committing.

---

### E2 — No Section-Level Prompt Preview

**Current state:** When a section is regenerated, the exact prompt sent to the LLM is not visible to the reviewer. Debugging why a section produced poor content requires either logging or code inspection.

**Recommended change:**
Add an optional `include_prompt_preview: bool` flag to `ReviewSectionRegenerateRequest`. When true, return the `system_prompt` and `user_prompt` in the mutation response under a `debug.prompt_preview` field. This enables prompt debugging from the UI without code changes.

---

### E3 — Export Does Not Tag Draft Status in the Output File

**File:** `apps/api/src/seo_content_engine/services/artifact_writer.py`

**Current state:** When a draft is exported with `needs_review=True` (a hard validation fail), the exported Markdown, DOCX, and HTML files contain the content but no visible indication of the review status. A reviewer downloading the file has no way to know it failed validation.

**Recommended change:**
In all export formats, prepend a status banner for drafts where `needs_review=True`:
- **Markdown:** Add a `> ⚠️ DRAFT STATUS: Validation failed — review required before publishing.` blockquote at the top
- **HTML:** Add a visible `<div class="review-banner">` warning at the top of the page
- **DOCX:** Add a highlighted "REVIEW REQUIRED" paragraph before the H1

---

## PART F — Frontend (Review Workbench) Gaps

---

### F1 — No FAQ Edit or Regenerate in the UI

**File:** `apps/web/src/pages/ReviewWorkbenchPage.tsx`

**Current state:** FAQs are displayed in a read-only `FaqSnapshot` component. There is no edit button, no regenerate-individual-FAQ button, and no way to add or remove a specific FAQ. The only way to affect FAQs is to regenerate the entire draft.

This is the most impactful UX gap for content reviewers.

**Recommended change:**
For each FAQ card, add:
1. An edit mode toggle that reveals a textarea for editing the answer (like the existing section edit UI)
2. A "Regenerate this FAQ" button that calls the new `/v1/review/faq/regenerate` endpoint (Enhancement C1 above)
3. A "Remove FAQ" action that removes it from the session draft locally

---

### F2 — Section Validation Issues Are Not Explained to the Reviewer

**File:** `apps/web/src/pages/ReviewWorkbenchPage.tsx`

**Current state:** Each section shows a `ValidationBadge` (passed / needs review) but the `validation_issues` list is shown only in the footer as a comma-separated label string (e.g., "forbidden_claims_detected, unreconciled_numbers_detected").

A reviewer cannot tell *what* the forbidden claim was or *which number* was unreconciled without downloading the raw JSON and inspecting the `validation_report`.

**Recommended change:**
Expand the section footer to show:
- The specific forbidden phrases detected (from `section.validation.forbidden_claims[]`)
- The specific unreconciled numbers detected (from `section.validation.unreconciled_numbers[]`)
- A copyable diff of `original_text` vs `sanitized_text` (collapsed by default)

---

### F3 — No Keyword Intelligence Tab

**File:** `apps/web/src/pages/ReviewWorkbenchPage.tsx`

**Current state:** The review workbench exposes keyword data in the "source preview" area (keyword chips visible), but there is no dedicated view for:
- The full keyword strategy with primary, secondary, BHK, price, and FAQ keywords
- Which keywords are being used in which sections
- Which competitor domains were found
- Whether the keyword research returned enough signals (coverage quality)

**Recommended change:**
Add a "Keywords" tab in the review workbench that shows:
- Primary keyword and variants (with volume if available)
- Keyword clusters by type (BHK, price, secondary, FAQ)
- Competitor domains and their overlap keywords
- DataForSEO raw result count (how many keywords were retrieved vs included vs excluded)

---

## PART G — Operational and Quality Gaps

---

### G1 — No Automated Regression Test for Multi-Type Generation

**Current state:** The repository has a `tests/` directory but the audit found no tests that run the full generation pipeline for all three entity types (CITY, MICROMARKET, LOCALITY) against the sample JSON files in `data/samples/raw/`.

**Recommended change:**
Add integration tests that:
1. Run `ReviewWorkbenchService.build_session()` with each of the three sample JSON pairs
2. Assert that the draft contains the expected type-specific section (e.g., LOCALITY has `nearby_alternatives`, not `locality_coverage`)
3. Assert that FAQs meet minimum count (10+) and cover the required axes
4. Assert that no blocked table IDs appear in the rendered tables

---

### G2 — Micromarket and Locality Sample JSONs May Differ Structurally

**Current state:** Three sample JSON files exist (`Mumbai city.json`, `Chandigarh micromarket.json`, `andheri-west-locality.json`). The normalizer handles all three but may behave differently if field names differ across cities/regions in the production data.

**Recommended change:**
- Add at least one more LOCALITY sample from a different city (e.g., a Bangalore or Pune locality)
- Add at least one more MICROMARKET sample from a different city
- Run the full pipeline against each and compare section output quality
- Document any normalizer field mappings that differ across city data providers

---

### G3 — Content Plan Is Not Persisted in the Review Session

**File:** `apps/api/src/seo_content_engine/services/review_workbench_service.py`

**Current state:** The review session stores: `draft`, `keyword_preview`, `source_preview`, `content_plan`, `section_review`, `version_history`. The `content_plan` is stored but is the same across versions — when a draft is regenerated, the content plan is not regenerated or versioned.

**Problem:** If a reviewer adds a keyword override and regenerates, the new draft uses the new content plan, but the stored `content_plan` in the session may still show the old one.

**Recommended change:**
When a draft is fully regenerated (`regenerate_draft`), update the stored `content_plan` in the session to match the content plan used for that regeneration. Optionally include the `content_plan` in the `version_history` snapshot.

---

## Priority Order for Implementation

| Priority | Enhancement | Effort | Impact |
|----------|-------------|--------|--------|
| 1 | **C1** — Standalone FAQ regenerate endpoint | Low | High — most-requested UX fix |
| 2 | **F1** — FAQ edit/regenerate in UI | Medium | High — directly unblocks reviewer workflow |
| 3 | **A1** — Expanded type-aware keyword seeds | Low | High — improves keyword quality for all types |
| 4 | **A2** — Type-differentiated section generation context | Medium | High — directly fixes City/Micromarket/Locality content quality |
| 5 | **D1** — AI locality summary into market_snapshot for LOCALITY | Low | High — makes LOCALITY pages distinctly better |
| 6 | **B1** — Type-differentiated keyword strategy in content plan | Medium | High — fixes keyword flow for all three entity types |
| 7 — | **B2** — BHK keywords injected into section context | Low | Medium — closes the BHK keyword-to-content gap |
| 8 | **A4** — Tiered forbidden-terms validator | Medium | Medium — reduces false positive content stripping |
| 9 | **D2** — Type-aware location_rates table labels | Low | Medium — makes tables accurate across types |
| 10 | **E3** — Review status banner in exported files | Low | Medium — critical for reviewer workflows |
| 11 | **B3** — Type-relevance filter in keyword processing | Medium | Medium — reduces keyword pollution across types |
| 12 | **B4** — FAQ keyword candidates into faq_prompts | Low | Medium — closes FAQ keyword gap |
| 13 | **C2** — Per-axis FAQ topic limits | Low | Medium — improves FAQ balance |
| 14 | **F2** — Validation issue details in section cards | Medium | Medium — improves reviewer diagnostic ability |
| 15 | **A3** — Narrative rules for nearby_alternatives | Low | Low-medium — marginal locality content improvement |
| 16 | **E1** — Keyword preview endpoint | Medium | Low-medium — nice-to-have for power users |
| 17 | **G1** — Multi-type integration tests | Medium | High (for stability) |
| 18 | **D3** — Refactor coverage section duplication | Low | Low (maintenance) |
| 19 | **G3** — Content plan versioning in session | Low | Low |
| 20 | **C3** — FAQ consistency warning on section edit | Low | Low |
