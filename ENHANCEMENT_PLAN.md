# SEO Content Generation System — Enhancement & Fix Plan

**Prepared:** April 7, 2026
**Repository:** `seo-content-generation-system`
**Scope:** 5 identified enhancement areas across backend services and frontend UI

---

## Enhancement 1 — Content Not Human-Friendly; Needs Real Estate Persona + SEO/AEO Alignment

### What's Wrong

The content generation prompts attempt to avoid generic SEO language, but they do it at the cost of depth and persona relevance. The prompts tell the model what to *avoid*, but don't tell it *who it's writing for* or *what a real buyer needs to know*. The result is cautious, stripped-back text that reads more like an internal data summary than an editorial page a buyer would trust.

**Specific root causes found in `prompt_builder.py`:**

- The `sections_prompts` system message says `"Write for a real buyer"` but never defines what kind of buyer — a first-time buyer comparing localities, an NRI investor doing due diligence, a family upgrading to a larger flat. Without persona context, the model defaults to neutral, generic prose.
- The `style_rules` in the sections prompt set `tone: "human, descriptive, grounded, SEO-friendly"` but there is no AEO-specific instruction (answer-first structure, conversational phrasing, schema-friendly question-answer patterns) outside the FAQ block.
- The `metadata_prompts` forbids patterns like `"Explore X with Y and Z"` and `"Browse X with details"`, but provides no positive examples of what *good* metadata looks like for a real estate search result.
- There are no locality-specific "buyer intent signals" injected into the section prompt — the model doesn't know whether the reader is a comparison shopper, a ready-to-buy buyer, or a researcher.

**Files to change:**

| File | Location | What needs updating |
|------|----------|---------------------|
| `prompt_builder.py` | `sections_prompts()` | Add real estate buyer persona definitions; add AEO-style guidance for body sections |
| `prompt_builder.py` | `metadata_prompts()` | Add positive examples of good title/meta patterns for real estate |
| `prompt_builder.py` | `faq_prompts()` | Reinforce "People Also Ask" question phrasing aligned to real estate buyer intent |
| `content_plan_builder.py` | `build()` | Inject buyer intent signals (comparison, due-diligence, ready-to-buy) into section generation context |

**Recommended changes:**

1. Add a `buyer_persona` block to the sections prompt user payload that describes: the primary reader profile (e.g., "a buyer comparing resale flats in Mumbai suburbs"), their key questions, and their decision stage.
2. Extend the system prompt in `sections_prompts()` with AEO-friendly directives: lead each section with a clear, scannable takeaway sentence that answers the section's core question directly, before supporting it with data.
3. Add positive metadata examples to `metadata_prompts()` — e.g., `"2 & 3 BHK Resale Flats in Andheri West — Prices, Projects & Listings | Square Yards"` — so the model has a quality target to aim for.
4. Update `style_rules` to explicitly include `"real_estate_editorial_tone"` and `"buyer_journey_aware"`.

---

## Enhancement 2 — FAQs Not Covering All Aspects of the JSON

### What's Wrong

The FAQ generation receives `content_plan["data_context"]` and `content_plan["faq_plan"]`, but neither of these is a complete mirror of the source JSON. Significant fields from the raw datacenter JSON are normalised and then only partially surfaced in the content plan. The FAQ prompt is also restricted to only what's *explicitly* in those two fields, which means whole categories of buyer questions simply can't be answered — even when the underlying data exists.

**Specific root causes found:**

- In `faq_prompts()` (`prompt_builder.py`), the user payload sends `data_context` and `faq_plan` but does NOT send the full `section_generation_context`. Key fields available in the normalised data — demand/supply breakdowns by BHK, listing ranges, RERA context, AI-generated locality signals, project linkages, micromarket coverage counts — are present in `section_generation_context` but absent from the FAQ prompt.
- The `ContentPlanBuilder` builds `faq_plan` from a limited set of signals. If the FAQ plan doesn't include a topic (e.g., "connectivity and infrastructure", "upcoming projects", "RERA registered listings"), the model won't generate FAQs for it even if data exists.
- The `faq_rules` in the prompt set `target_min_faqs: 8` and `target_max_faqs: 12`. For a comprehensive locality or micromarket page that has pricing, reviews, demand/supply, inventory mix, and project data, 12 FAQs is not enough to cover all angles.
- The FAQ system prompt explicitly says `"Do not turn every FAQ into a mini section summary"` — which is correct — but then doesn't guide the model toward the *other* data fields it should pull from.

**Files to change:**

| File | Location | What needs updating |
|------|----------|---------------------|
| `prompt_builder.py` | `faq_prompts()` | Add `section_generation_context` to the user payload |
| `content_plan_builder.py` | FAQ plan building section | Expand the set of FAQ topics derived from available JSON keys |
| `prompt_builder.py` | `faq_prompts()` requirements block | Raise `target_max_faqs` from 12 to 15; add topic coverage checklist |

**Recommended changes:**

1. In `faq_prompts()`, add `section_generation_context` from the content plan to the user payload so the model has access to all grounded data fields — not just what was pre-selected for the FAQ plan.
2. In `ContentPlanBuilder`, audit the FAQ plan builder to explicitly include topics for: listing price range, BHK-wise availability, review/rating signals, demand/supply ratio, project-level coverage, RERA context (if available), nearby locality comparison, and property type mix.
3. Raise the FAQ target to 12–15 and add a coverage checklist in the system prompt that maps data fields to FAQ categories, so the model knows to cover each category at least once.
4. Add a `"data_coverage_guide"` field to the FAQ prompt that lists every major data axis available (pricing, reviews, inventory, demand, location, projects) and asks the model to produce at least one FAQ per axis when data is present.

---

## Enhancement 3 — Cannot Export Draft When It Needs Review

### What's Wrong

There is a guard in `artifact_writer.py` that can block all artifact writes when a draft is flagged as needing review:

```python
# artifact_writer.py, line 44-46
@staticmethod
def _guard_review_block(draft: dict) -> None:
    if settings.block_artifact_write_on_review and draft.get("needs_review"):
        raise ValueError("Draft still needs review")
```

The `needs_review` flag is set on the draft by two separate services with **inconsistent logic**:

- **`draft_generation_service.py` line 2075:** `needs_review = not bool(validation_report.get("passed"))` — triggers on *any* failed validation check, including minor/warning-level issues.
- **`factual_validator.py` line 1083:** `needs_review = approval_status == "fail"` — triggers only on hard failures.

When the draft goes through final validation in `DraftGenerationService`, it uses the first (stricter) logic. So a draft with a "needs review" warning status — not a hard "fail" — can still end up with `needs_review = True`, which then blocks export if `block_artifact_write_on_review` is set to `True` in the `.env` file.

Even when the setting is `False` (the default), the `publish_ready` field is calculated inconsistently: `draft_generation_service.py` sets `publish_ready = approval_status != "fail"`, meaning even a "needs review" draft is technically publish-ready, but the UI shows the validation as failed — creating a confusing mixed signal.

**Files to change:**

| File | Location | What needs updating |
|------|----------|---------------------|
| `artifact_writer.py` | `_guard_review_block()` | Remove the hard block; replace with a warning/flag that is logged but does not raise |
| `draft_generation_service.py` | Line 2075 | Align `needs_review` logic with `factual_validator.py` — use `approval_status == "fail"` as the only trigger |
| `core/config.py` | `block_artifact_write_on_review` | Add a comment clarifying this should remain `False` for review-stage exports |
| `apps/web/src/pages/ReviewWorkbenchPage.tsx` | Export button section | Add an inline notice when `needs_review` is `True`: "This draft has validation warnings — you can still export for review" |

**Recommended changes:**

1. Unify `needs_review` logic: use `approval_status == "fail"` (hard fail only) across both services, so that warning-level drafts are never incorrectly flagged as blocked.
2. Replace the `_guard_review_block` hard raise with a logged warning. Export should always succeed; the review flag is informational, not a gate.
3. In the UI, add a visible notice next to the export button when `approval_status` is `"needs_review"`: something like *"Draft has validation warnings — export will include a review flag."* This makes the intent clear without blocking the workflow.
4. Consider adding a `"draft_status"` field to the exported artifacts so reviewers know the validation state without having to re-run the pipeline.

---

## Enhancement 4 — Property Status Tables Must Be Removed from Generated Content

### What's Wrong

The `table_renderer.py` and `content_plan_builder.py` include table types that show property status breakdowns — specifically the `property_types_table` and `coverage_summary_table`. These tables render rows like "New Launch / 42 listings", "Ready to Move / 118 listings", "Under Construction / 31 listings" which are **new-project metrics, not resale metrics**. On a resale page, these tables are either misleading or irrelevant.

**Specific tables to remove or suppress (from `table_renderer.py`):**

| Table ID | Problem |
|----------|---------|
| `property_types_table` | Shows property type distribution including commercial rows (partially filtered) and status-like data that conflates resale and new-launch inventory |
| `coverage_summary_table` | Shows resale inventory counts and project coverage in a way that reads as "project status" rather than resale market depth |

The `_filter_property_type_rows()` method in `table_renderer.py` already filters out commercial property types, but the table itself is still rendered and exported. The filtering addresses content accuracy but not the structural problem of including status-level data on a resale page.

**Files to change:**

| File | Location | What needs updating |
|------|----------|---------------------|
| `content_plan_builder.py` | `table_plan` builder | Remove `property_types_table` and `coverage_summary_table` from the default table plan for resale pages |
| `table_renderer.py` | `render_table()` and `_build_table_summary()` | Add a blocklist of table IDs that should never render on resale page types |
| `artifact_writer.py` | `_add_tables()` | Add a filter that skips rendering blocked table IDs in all output formats (DOCX, HTML, Markdown) |
| `markdown_renderer.py` | Table rendering section | Same filter for Markdown output |

**Recommended changes:**

1. In `ContentPlanBuilder`, add a `RESALE_BLOCKED_TABLE_IDS` constant: `{"property_types_table", "coverage_summary_table"}` and skip adding these to the table plan when `listing_type == "resale"`.
2. In `TableRenderer`, add a `should_render()` static method that takes `table_id` and `page_context` and returns `False` for blocked table IDs — this prevents the table from being generated at all, not just filtered after the fact.
3. Audit the remaining tables (`price_trend_table`, `sale_unit_type_distribution_table`, `nearby_localities_table`, `location_rates_table`) to confirm they are genuinely resale-relevant and don't contain status-level columns that should be removed.

---

## Enhancement 5 — Content Too Short; Needs 3–4 Lines + Bullet Points Per Section

### What's Wrong

Every editorial section is capped at a very tight word range, and the output schema for sections only produces a single `body` string with no structural elements. The model is told to write "2 to 4 short paragraphs" but is never asked to include bullet points, and the target word range of 90–220 words produces text that often equates to just 3–5 sentences — far too thin for an SEO/AEO page.

**Specific root causes found in `prompt_builder.py` and `draft_generation_service.py`:**

- `min_target_words_per_section: 90` and `max_target_words_per_section: 220` are set in the `requirements` block of the sections prompt. 220 words is approximately 3 short paragraphs with no room for bullets, context, or elaboration.
- The `output_schema` for sections is `{ "id": "string", "title": "string", "body": "string" }` — a flat string. There is no `bullets` field, no `key_takeaways` field, no structural support for bullet points.
- The system prompt says `"prefer_2_to_4_short_paragraphs"` but does not mention bullet points at all.
- The table summary prompt (`table_summary_prompt()`) caps summaries at 2–3 sentences — far too short to be useful standalone content for a buyer. These summaries appear above each data table and are often the only editorial context a reader gets for understanding a table.
- The `ArtifactWriter._add_sections()` method splits `body` on `\n` and adds each paragraph, but does not handle markdown bullet syntax (`-`, `*`, numbered lists) — so even if the model output bullets, they'd render as plain text.
- `MarkdownRenderer` also doesn't explicitly handle bullet-formatted body text within sections.

**Files to change:**

| File | Location | What needs updating |
|------|----------|---------------------|
| `prompt_builder.py` | `sections_prompts()` requirements block | Raise word limits; add bullet point structure requirement |
| `prompt_builder.py` | `sections_prompts()` output_schema | Add an optional `key_points` list field alongside `body` |
| `prompt_builder.py` | `table_summary_prompt()` | Raise from 2–3 sentences to 3–5 sentences |
| `draft_generation_service.py` | `_generate_sections()` result handling | Map `key_points` from the response into the section dict |
| `artifact_writer.py` | `_add_sections()` | Add bullet point rendering for `key_points` and markdown bullet detection in `body` |
| `markdown_renderer.py` | Section rendering | Support `key_points` as a bullet list rendered after the prose body |

**Recommended changes:**

1. Update the section word target in the sections prompt to `min: 150`, `max: 350` — this gives the model room to write 3–4 substantive paragraphs.
2. Change the system prompt from `"Use 2 to 4 short paragraphs"` to `"Use 3 to 4 paragraphs of 2–3 sentences each. For sections with data-driven findings, follow the prose with 3 to 4 bullet points summarising the key facts a buyer should take away."`
3. Extend the output schema to:
   ```json
   {
     "id": "string",
     "title": "string",
     "body": "string",
     "key_points": ["string", "string", "string"]
   }
   ```
   Make `key_points` required for sections of type `generative` and optional for `hybrid` sections.
4. Update `table_summary_prompt()` to allow 3–5 sentences and add context-specific buyer framing (e.g., "explain what this means for a buyer shortlisting flats in this locality").
5. Update `ArtifactWriter._add_sections()` to render `key_points` as a bulleted list after the prose body in DOCX and HTML output.
6. Update `MarkdownRenderer` to emit `key_points` as a Markdown unordered list (`- point one`) after the section body.

---

## Summary Table

| # | Enhancement | Key Files | Severity |
|---|-------------|-----------|----------|
| 1 | Content not persona-aware or AEO-structured | `prompt_builder.py`, `content_plan_builder.py` | High |
| 2 | FAQs missing whole data categories | `prompt_builder.py`, `content_plan_builder.py` | High |
| 3 | Export blocked for "needs review" drafts | `artifact_writer.py`, `draft_generation_service.py`, `ReviewWorkbenchPage.tsx` | High |
| 4 | Property status tables in resale content | `content_plan_builder.py`, `table_renderer.py`, `artifact_writer.py` | Medium |
| 5 | Content too short; no bullet points | `prompt_builder.py`, `artifact_writer.py`, `markdown_renderer.py` | High |

---

## Suggested Implementation Order

1. **Fix 3 first** — the export block is a workflow blocker and is the smallest code change (2–3 lines).
2. **Fix 4 next** — removing tables is additive (add a blocklist), low risk, immediately improves output quality.
3. **Fix 5** — word count and bullet structure changes affect the core prompt and output schema; do this before changing persona (Fix 1) so you have a larger content canvas to work with.
4. **Fix 1** — persona and AEO alignment requires the most prompt design iteration; tackle after content structure is solid.
5. **Fix 2** — FAQ coverage expansion depends on both the prompt changes (Fix 1) and having the section context already improved (Fix 5), so do this last.
