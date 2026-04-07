# SEO Content Generation System

A programmatic SEO content engine for **Square Yards** resale listing pages. The system ingests raw datacenter JSON exports, runs deep keyword research via DataForSEO, and uses OpenAI GPT-4.1-mini to produce publication-ready SEO drafts — all through a REST API backed by a React review workbench UI.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Running the API](#running-the-api)
  - [Running the Web UI](#running-the-web-ui)
- [Configuration Reference](#configuration-reference)
- [Generation Pipeline](#generation-pipeline)
- [Core Concepts](#core-concepts)
  - [Entity Types](#entity-types)
  - [Data Inputs](#data-inputs)
  - [Keyword Intelligence](#keyword-intelligence)
  - [Content Plan](#content-plan)
  - [Draft Generation](#draft-generation)
  - [Review Workbench](#review-workbench)
  - [Export Formats](#export-formats)
  - [Factual Validation](#factual-validation)
- [API Reference](#api-reference)
  - [Health](#health)
  - [Generation Endpoints](#generation-endpoints)
  - [Review Workbench Endpoints](#review-workbench-endpoints)
- [Service Layer](#service-layer)
- [Frontend](#frontend)
- [Testing](#testing)
- [Data and Artifacts](#data-and-artifacts)

---

## Overview

The SEO Content Generation System automates the creation of SEO-optimized content for Square Yards' resale property listing pages — covering city, micromarket, and locality levels across India.

The end-to-end workflow is:

1. **Load** structured JSON exports from the Square Yards datacenter (locality overview + property rates)
2. **Normalise** all fields and auto-detect entity type (city / micromarket / locality)
3. **Run keyword intelligence** — 7 DataForSEO API calls to gather suggestions, related terms, SERP signals, competitor domains, and search volume enrichment
4. **Build a content plan** — section structure, FAQ intents, table plan, keyword strategy, and data context per section
5. **Generate a draft** with OpenAI — AEO-optimised (Answer Engine Optimisation) prose, deterministic tables, FAQ block, and JSON-LD schema markup
6. **Validate** the draft factually against source data
7. **Export** to JSON, Markdown, DOCX, and HTML
8. **Review and iterate** through the browser-based workbench — regenerate sections, edit FAQs, restore versions, stream live re-generation, and trigger incremental refreshes

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React Review Workbench (Vite + TypeScript)                  │
│  localhost:5173                                              │
└────────────────────────┬────────────────────────────────────┘
                         │ REST / SSE
┌────────────────────────▼────────────────────────────────────┐
│  FastAPI (Python 3.11+)   localhost:8000                     │
│                                                              │
│  /v1/blueprint          /v1/content-plan                     │
│  /v1/draft              /v1/draft/publish                    │
│  /v1/review/*           /v1/keywords/*                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Normalizer  │  │  Keyword     │  │  Content Plan    │  │
│  │              │  │  Intelligence│  │  Builder         │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Draft Gen   │  │  Factual     │  │  Review          │  │
│  │  Service     │  │  Validator   │  │  Workbench Svc   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────┬──────────────────┬───────────────────────────┘
               │                  │
    ┌──────────▼──────┐  ┌────────▼─────────┐
    │  DataForSEO API │  │  OpenAI API      │
    │  (7 endpoints)  │  │  gpt-4.1-mini    │
    └─────────────────┘  └──────────────────┘
```

---

## Project Structure

```
seo-content-generation-system/
├── apps/
│   ├── api/
│   │   ├── src/seo_content_engine/
│   │   │   ├── api/routes/          # FastAPI route handlers
│   │   │   │   ├── generation.py    # Blueprint, content-plan, draft, publish
│   │   │   │   ├── review.py        # Review workbench CRUD + SSE streaming
│   │   │   │   ├── keywords.py      # Standalone keyword intelligence
│   │   │   │   ├── draft.py         # Draft file download
│   │   │   │   └── health.py
│   │   │   ├── core/
│   │   │   │   ├── config.py        # Pydantic settings (all env vars)
│   │   │   │   └── logging.py
│   │   │   ├── domain/
│   │   │   │   └── enums.py         # EntityType, PageType, ListingType
│   │   │   ├── schemas/
│   │   │   │   ├── requests.py      # Pydantic request models
│   │   │   │   └── responses.py     # Pydantic response models
│   │   │   ├── services/
│   │   │   │   ├── normalizer.py              # Raw JSON → normalised dict
│   │   │   │   ├── keyword_intelligence_service.py
│   │   │   │   ├── keyword_processing.py      # Scoring, clustering, dedup
│   │   │   │   ├── keyword_seed_generator.py  # Seed keyword generation
│   │   │   │   ├── dataforseo_client.py       # DataForSEO HTTP client (+ retry)
│   │   │   │   ├── content_plan_builder.py    # Section + FAQ + table plan
│   │   │   │   ├── competitor_intelligence_service.py
│   │   │   │   ├── draft_generation_service.py
│   │   │   │   ├── prompt_builder.py          # Per-section LLM prompts
│   │   │   │   ├── factual_validator.py
│   │   │   │   ├── review_workbench_service.py
│   │   │   │   ├── review_session_store.py    # JSON file persistence
│   │   │   │   ├── schema_markup_generator.py # JSON-LD (FAQPage + WebPage)
│   │   │   │   ├── table_renderer.py
│   │   │   │   ├── markdown_renderer.py
│   │   │   │   ├── output_formatter.py
│   │   │   │   ├── artifact_writer.py
│   │   │   │   ├── draft_publish_service.py
│   │   │   │   ├── blueprint_builder.py
│   │   │   │   ├── openai_client.py
│   │   │   │   └── source_loader.py
│   │   │   └── utils/
│   │   │       └── formatters.py
│   │   └── tests/                   # pytest test suite (20+ test files)
│   └── web/
│       └── src/
│           ├── pages/
│           │   └── ReviewWorkbenchPage.tsx
│           ├── api/
│           │   ├── review.ts        # Review API calls
│           │   ├── streaming.ts     # SSE streaming hook (useStreamRegenerate)
│           │   └── http.ts
│           ├── types/review.ts
│           └── components/AppLayout.tsx
├── data/
│   ├── artifacts/                   # Generated drafts (JSON, MD, DOCX, HTML)
│   ├── review_sessions/             # Persisted review session JSON files
│   └── samples/raw/                 # Input JSON files (datacenter exports)
├── pyproject.toml
├── .env.example
└── scripts/run_api.sh
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.115+ |
| Language | Python 3.11+ |
| LLM | OpenAI GPT-4.1-mini |
| Keyword research | DataForSEO Labs + SERP API |
| Document export | python-docx |
| HTTP client | httpx |
| Settings | pydantic-settings |
| Frontend | React 19 + TypeScript + Vite 8 |
| Routing | React Router v7 |
| Testing | pytest + pytest-cov |
| Linting | Ruff |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- DataForSEO account (login + password)
- OpenAI API key

### Environment Setup

```bash
# Clone and enter the project
git clone <repo-url>
cd seo-content-generation-system

# Copy and fill in credentials
cp .env.example .env
# Edit .env — set DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD, OPENAI_API_KEY

# Create a Python virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running the API

```bash
# With the virtual environment active:
uvicorn seo_content_engine.main:app --reload --host 0.0.0.0 --port 8000

# Or use the convenience script:
bash scripts/run_api.sh
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### Running the Web UI

```bash
cd apps/web
npm install
npm run dev
```

The review workbench opens at `http://localhost:5173`.

---

## Configuration Reference

All settings live in `core/config.py` and are read from environment variables (or `.env`).

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | `8000` | API server port |
| `ARTIFACTS_DIR` | `data/artifacts` | Where generated files are saved |
| `REVIEW_SESSIONS_DIR` | `data/review_sessions` | Where review session JSON files are stored |
| `DATAFORSEO_LOGIN` | _(required)_ | DataForSEO account login |
| `DATAFORSEO_PASSWORD` | _(required)_ | DataForSEO account password |
| `DATAFORSEO_DEFAULT_LOCATION_NAME` | `India` | Default location for all DataForSEO calls |
| `DATAFORSEO_DEFAULT_LANGUAGE_NAME` | `English` | Default language |
| `DATAFORSEO_DEFAULT_LIMIT` | `50` | Results per keyword API call |
| `DATAFORSEO_SERP_SEED_LIMIT` | `5` | Number of seeds to run SERP validation against |
| `DATAFORSEO_TIMEOUT_SECONDS` | `45` | Per-request timeout |
| `OPENAI_API_KEY` | _(required)_ | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4.1-mini` | LLM model identifier |
| `OPENAI_TEMPERATURE` | `0.2` | Generation temperature |
| `OPENAI_TIMEOUT_SECONDS` | `90` | Per-request timeout |
| `DRAFT_REPAIR_MAX_PASSES` | `2` | Max auto-repair passes for validation failures |
| `BLOCK_ARTIFACT_WRITE_ON_REVIEW` | `false` | Prevent artifact writes during review sessions |
| `KEYWORD_FAQ_MAX_COUNT` | `12` | Max FAQ keyword candidates per cluster |
| `KEYWORD_SECONDARY_MAX_COUNT` | `10` | Max secondary keywords |
| `KEYWORD_METADATA_MAX_COUNT` | `8` | Max metadata keywords |

---

## Generation Pipeline

The system runs in six sequential stages. Each stage can be triggered individually via the API or all at once through the `/v1/draft` endpoint.

```
Raw JSON files
      │
      ▼
[1] Normalisation
      │   EntityNormalizer.normalize()
      │   Auto-detects entity type (city / micromarket / locality)
      │   Extracts: listing summary, pricing, distributions, nearby localities,
      │             landmarks (hospitals, schools, banks, etc.), govt registration
      │             stats, top developers, city-level hotSellingProjects +
      │             insightsData, review signals, AI market summary, and more
      ▼
[2] Keyword Intelligence
      │   KeywordIntelligenceService.build_keyword_intelligence()
      │   Runs 7 DataForSEO endpoints per entity:
      │     · keyword_suggestions (per seed)
      │     · related_keywords (per seed)
      │     · serp_organic_advanced (top N seeds)
      │     · keywords_for_site (competitor domains)
      │     · keyword_overview (batch enrichment)
      │     · historical_search_volume (batch enrichment)
      │     · google_ads_search_volume (batch enrichment)
      │   Outputs keyword clusters: primary, secondary, BHK, price,
      │   ready-to-move, FAQ candidates, long-tail, competitor, SERP-validated
      ▼
[3] Content Plan
      │   ContentPlanBuilder.build()  [v1.9]
      │   Builds section plan, FAQ intents, table plan, keyword strategy,
      │   per-section generation context and narrative guardrails.
      │   Includes competitor intelligence for section prioritisation.
      ▼
[4] Draft Generation
      │   DraftGenerationService (ThreadPoolExecutor for parallel sections)
      │   Calls OpenAI GPT-4.1-mini per section with AEO writing style.
      │   Assembles: sections + deterministic tables + FAQ block +
      │              JSON-LD schema (FAQPage + WebPage)
      ▼
[5] Factual Validation
      │   FactualValidator
      │   Checks all numeric claims in generated prose against source data.
      │   Auto-repairs up to DRAFT_REPAIR_MAX_PASSES times on failure.
      ▼
[6] Export
      DraftPublishService / ArtifactWriter
      Writes: .json · .md · .docx · .html
```

---

## Core Concepts

### Entity Types

The system supports three entity types, all under the `RESALE` listing type:

| Entity Type | Page Type | Description |
|---|---|---|
| `CITY` | `resale_city` | City-level page (e.g. Mumbai, Delhi) |
| `MICROMARKET` | `resale_micromarket` | Sub-city zone (e.g. Chandigarh Sectors) |
| `LOCALITY` | `resale_locality` | Neighbourhood-level page (e.g. Andheri West) |

Entity type is auto-detected from the `type` field in the property rates JSON, with a fallback to `isMicroMarket` in the locality overview JSON.

### Data Inputs

Each generation request requires two JSON files exported from the Square Yards datacenter:

- **Main datacenter JSON** — locality overview, listing counts, BHK distribution, nearby localities, landmarks (hospitals, schools, banks, ATMs, etc.), review data, AI summaries, city hotSellingProjects and insightsData
- **Property rates JSON** — asking price, price trends, property type rates, location rates, government registration stats (transaction count, gross value, registered rate), top developers, AI market analysis

These are passed as file paths in the API request payload. The normalizer extracts all relevant fields and handles missing data gracefully.

### Keyword Intelligence

The `KeywordIntelligenceService` runs up to 7 DataForSEO API calls for each request:

- **Seed generation** — `KeywordSeedGenerator` produces seed keywords from the entity name, city, and property context
- **Suggestions + Related** — fetched for every seed keyword
- **SERP validation** — top organic results fetched for the first 5 seeds to identify competitor domains and validate keyword relevance
- **Competitor site keywords** — top 3 competitor domains scraped for their ranking keywords
- **Enrichment** — keyword overview, historical search volume, and Google Ads volume applied in batch

The output is a set of **keyword clusters** used to guide section generation, FAQ writing, and metadata creation. Clusters are scored, deduped, and filtered for resale relevance (rent and commercial terms are excluded).

**Robustness features:**
- Primary keyword falls back to `seeds[0]` if all API calls return no usable records
- Empty API responses log specific `_empty_response` warnings (distinct from API failures)
- Transient HTTP errors (429, 5xx, timeouts) are automatically retried once with a 2-second delay
- Primary keyword overrides propagate into all clusters including `faq_keyword_candidates`

### Content Plan

The content plan (`ContentPlanBuilder.build()`) defines the complete structure for generation:

- **Section plan** — ordered list of sections with objectives, data dependencies, and keyword targets
- **FAQ plan** — FAQ intents with question templates and data dependencies
- **Table plan** — deterministic tables (price trend, BHK mix, nearby localities, location rates, property types)
- **Keyword strategy** — primary keyword, variants, metadata keywords, body keyword priority
- **Section generation context** — per-section data snapshot and narrative guardrails passed to the LLM
- **Competitor intelligence** — competitor domain analysis used to re-prioritise sections and FAQs

#### Standard Sections

| Section ID | Included for |
|---|---|
| `market_snapshot` | All |
| `micromarket_coverage` | City pages |
| `locality_coverage` | Micromarket pages |
| `nearby_alternatives` | Locality pages |
| `price_trends_and_rates` | All |
| `bhk_and_inventory_mix` | All |
| `review_and_rating_signals` | When review data is present |
| `property_rates_ai_signals` | When AI market summary is present |
| `demand_and_supply_signals` | When demand/supply data is present |
| `property_type_signals` | When residential property types are present |
| `property_type_rate_snapshot` | When residential property types are present |
| `neighbourhood_essentials` | Locality/micromarket pages with landmarks data |
| `market_registration_activity` | When govt registration or top developer data is present |
| `faq_section` | All |
| `internal_links` | All |

### Draft Generation

Sections are generated in parallel using a `ThreadPoolExecutor`. Each section receives a per-section LLM prompt built by `PromptBuilder` using the section's data context and narrative guardrails. The writing style is AEO (Answer Engine Optimisation): answer-first, evidence-second, no filler phrases. Featured snippet formatting is applied to the primary question in each section.

Schema markup is generated separately as JSON-LD and embedded in the final draft output.

### Review Workbench

The review workbench (`ReviewWorkbenchService`) provides a stateful session layer on top of generated drafts:

- **Session creation** — runs the full pipeline and persists the result as a review session JSON
- **Section regeneration** — regenerates a single section with optional keyword overrides
- **Full draft regeneration** — reruns generation for all sections
- **FAQ regeneration and editing** — regenerates or manually edits individual FAQ items
- **Metadata editing** — updates title, description, and keyword targets
- **Version history** — MD5 fingerprinting on each mutation; previous versions can be restored
- **Incremental refresh** — detects source data changes via MD5 fingerprint and regenerates only stale sections
- **SSE streaming** — `GET /v1/review/session/{id}/stream-regenerate` streams live token output during full regeneration
- **Export** — exports the reviewed draft to any combination of JSON, Markdown, DOCX, and HTML

### Export Formats

| Format | Description |
|---|---|
| `json` | Full structured draft with all sections, tables, FAQ, and schema markup |
| `markdown` | Clean Markdown with heading hierarchy, tables, and FAQ block |
| `docx` | Microsoft Word document with styled headings, tables, and paragraph formatting |
| `html` | Semantic HTML with embedded JSON-LD schema markup |

### Factual Validation

The `FactualValidator` scans all generated prose for numeric claims and checks each against the source data used to generate it. Failures trigger an auto-repair loop (up to `DRAFT_REPAIR_MAX_PASSES` times) where the failing section is re-generated with the specific validation error fed back into the prompt.

---

## API Reference

All endpoints are under the prefix `/v1`.

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/health` | Returns `{"status": "ok"}` |

### Generation Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/blueprint` | Normalise source JSON and return entity blueprint |
| `POST` | `/v1/content-plan` | Run keyword intelligence + build content plan |
| `POST` | `/v1/draft` | Full pipeline — normalise → keywords → plan → draft → validate → export |
| `POST` | `/v1/draft/publish` | Publish an existing draft artifact to export formats |
| `GET` | `/v1/keywords` | Run keyword intelligence only and return clusters |

All generation endpoints accept a JSON body with at minimum:

```json
{
  "main_datacenter_json_path": "data/samples/raw/andheri-west.json",
  "property_rates_json_path": "data/samples/raw/andheri-west-property-rates.json",
  "listing_type": "resale"
}
```

Optional fields include `primary_keyword_overrides`, `location_name`, `language_name`, and `export_formats`.

### Review Workbench Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/review/session` | Create a new review session (full pipeline) |
| `GET` | `/v1/review/session/{id}` | Retrieve a session by ID |
| `POST` | `/v1/review/session/regenerate` | Regenerate full draft within a session |
| `POST` | `/v1/review/section/regenerate` | Regenerate a single section |
| `POST` | `/v1/review/section/update` | Manually update a section's content |
| `POST` | `/v1/review/metadata/update` | Update session metadata (title, description, keywords) |
| `POST` | `/v1/review/version/restore` | Restore a previous section version |
| `POST` | `/v1/review/session/export` | Export session to specified formats |
| `GET` | `/v1/review/session/{id}/download/{format}` | Download an exported file |
| `GET` | `/v1/review/session/{id}/stream-regenerate` | SSE stream for live full regeneration |
| `POST` | `/v1/review/session/refresh` | Incremental refresh — regenerate only stale sections |
| `POST` | `/v1/review/faq/regenerate` | Regenerate FAQ block |
| `POST` | `/v1/review/faq/update` | Manually update individual FAQ items |

---

## Service Layer

| Service | Responsibility |
|---|---|
| `EntityNormalizer` | Parses raw JSON into a normalised dict; auto-detects entity type; extracts landmarks, govt registration stats, top developers, city insights |
| `KeywordSeedGenerator` | Generates seed keyword list from entity metadata |
| `DataForSEOClient` | HTTP client for all DataForSEO endpoints; includes retry logic for transient errors |
| `KeywordIntelligenceService` | Orchestrates all DataForSEO calls; scores and clusters keywords; primary keyword fallback |
| `KeywordProcessing` | Scoring, dedup, semantic consolidation, cluster building |
| `CompetitorIntelligenceService` | Extracts competitor domain patterns to inform section and FAQ priority |
| `ContentPlanBuilder` | Builds section plan, FAQ intents, table plan, keyword strategy, and per-section context |
| `PromptBuilder` | Assembles LLM prompts from section context and narrative guardrails |
| `DraftGenerationService` | Calls OpenAI in parallel threads; assembles final draft |
| `FactualValidator` | Validates numeric claims; drives auto-repair loop |
| `ReviewWorkbenchService` | Session CRUD, override propagation, version management, incremental refresh |
| `ReviewSessionStore` | JSON file persistence for review sessions |
| `SchemaMarkupGenerator` | Produces FAQPage + WebPage JSON-LD |
| `TableRenderer` | Renders deterministic Markdown/HTML tables from source data |
| `ArtifactWriter` | Writes draft files to `data/artifacts/` |
| `DraftPublishService` | Converts draft JSON into DOCX, HTML, Markdown |
| `BlueprintBuilder` | Lightweight entity blueprint (used by `/v1/blueprint`) |

---

## Frontend

The React review workbench at `apps/web/` is a single-page application (Vite 8 + React 19 + TypeScript) providing a browser-based UI for content review and editing:

- **ReviewWorkbenchPage** — main session interface: section editor, FAQ editor, metadata panel, version history, live streaming regeneration, and export controls
- **NotFoundPage** — 404 fallback

API communication is split across `api/review.ts` (REST calls), `api/streaming.ts` (SSE streaming hook `useStreamRegenerate`), and `api/http.ts` (base HTTP client).

The frontend expects the API at the URL defined in `apps/web/.env` (`VITE_API_URL`, defaults to `http://localhost:8000`).

---

## Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=seo_content_engine --cov-report=term-missing

# Run a specific test file
pytest apps/api/tests/test_keyword_intelligence_service.py -v
```

The test suite covers normalisation, keyword intelligence, content plan building, draft generation, factual validation, all API routes (using FastAPI `TestClient` with mocked external calls), review workbench mutations, artifact writer blocking, and SSE streaming.

---

## Data and Artifacts

```
data/
├── samples/raw/            # Input: datacenter JSON exports
│   ├── mumbai-city.json
│   ├── mumbai-property-rates.json
│   ├── andheri-west.json
│   ├── andheri-west-property-rates.json
│   ├── delhi-city.json
│   ├── delhi-property-rates.json
│   ├── bangalore-city.json
│   ├── bangalore-property-rates.json
│   ├── gurgaon-city.json
│   └── gurgaon-property-rates.json
├── artifacts/              # Output: generated drafts per entity slug
│   ├── <slug>-blueprint.json
│   ├── <slug>-keyword-intelligence.json
│   ├── <slug>-content-plan.json
│   ├── <slug>-draft.json
│   ├── <slug>-draft.md
│   ├── <slug>-draft.docx
│   └── <slug>-draft.html
└── review_sessions/        # Output: review session state
    └── review-<uuid>.json
```

Artifact filenames follow the pattern `{city-slug}-{page_type}-{artifact_type}.{ext}` — for example, `andheri-west-resale_locality-draft.docx`.

Review sessions are self-contained JSON files that include the full pipeline output, all section content, version history, and export references.
