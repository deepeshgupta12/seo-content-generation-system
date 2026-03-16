# SEO Content Generation System

A programmatic SEO content engine for **Square Yards** resale listing pages. The system ingests raw datacenter JSON exports, performs deep keyword research via DataForSEO, and uses OpenAI to produce publication-ready SEO drafts in multiple formats — all through a REST API with a React-based review workbench UI.

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
- [API Reference](#api-reference)
  - [Health](#health)
  - [Generation Endpoints](#generation-endpoints)
  - [Keywords Endpoint](#keywords-endpoint)
  - [Draft Publish Endpoint](#draft-publish-endpoint)
  - [Review Workbench Endpoints](#review-workbench-endpoints)
- [Core Concepts](#core-concepts)
  - [Entity Types and Page Types](#entity-types-and-page-types)
  - [Data Inputs](#data-inputs)
  - [Generation Pipeline](#generation-pipeline)
  - [Review Workbench & Version History](#review-workbench--version-history)
  - [Export Formats](#export-formats)
  - [Factual Validation](#factual-validation)
- [Service Layer](#service-layer)
- [Frontend (Review Workbench UI)](#frontend-review-workbench-ui)
- [Testing](#testing)
- [Data & Artifacts](#data--artifacts)
- [Development Notes](#development-notes)

---

## Overview

The SEO Content Generation System automates the creation of SEO-optimized content for Square Yards' property listing pages — covering resale properties at the city, micromarket, and locality level.

The workflow is:
1. Load structured JSON data exports from the Square Yards datacenter (locality overview + property rates)
2. Auto-detect the entity type (city / micromarket / locality) and normalize all fields
3. Run keyword research via the DataForSEO API (suggestions, related keywords, SERP analysis, competitor keywords, historical search volume, Google Ads data)
4. Build a content plan with keyword strategy, section structure, and SEO metadata guidelines
5. Generate a full draft (metadata, editorial sections, data tables, FAQs, internal links) using OpenAI GPT-4.1-mini
6. Validate the draft for factual accuracy and strip forbidden marketing claims
7. Publish the draft as JSON, Markdown, DOCX, and/or HTML artifacts
8. Optionally open the Review Workbench to iteratively edit, regenerate, and version-control the draft via a browser UI

---

## Architecture

The project is a **monorepo** with two apps:

```
seo-content-generation-system/
├── apps/
│   ├── api/          ← Python FastAPI backend
│   └── web/          ← React + TypeScript frontend (Review Workbench UI)
├── data/
│   ├── artifacts/    ← Generated output files (JSON, MD, DOCX, HTML)
│   ├── review_sessions/ ← Persisted review session JSON files
│   └── samples/      ← Sample input JSON files for development/testing
├── pyproject.toml    ← Python project config & dependencies
└── .env              ← Environment variables (not committed)
```

The API and web UI are decoupled — the API is a pure REST service; the UI connects to it over HTTP.

---

## Project Structure

### Backend (`apps/api/src/seo_content_engine/`)

```
seo_content_engine/
├── main.py                        ← FastAPI app entry point, CORS config, router registration
├── core/
│   ├── config.py                  ← Pydantic Settings — all env-driven configuration
│   └── logging.py                 ← Logging setup
├── domain/
│   └── enums.py                   ← EntityType, ListingType, PageType enums
├── api/
│   └── routes/
│       ├── health.py              ← GET /health
│       ├── generation.py          ← POST /v1/generate/* (blueprint, content-plan, draft, draft/publish)
│       ├── keywords.py            ← POST /v1/keywords/intelligence
│       ├── draft.py               ← POST /v1/draft/publish
│       └── review.py              ← POST/GET /v1/review/* (session, section, metadata, version, export, download)
├── schemas/
│   ├── requests.py                ← Pydantic request models for all endpoints
│   └── responses.py               ← Pydantic response models for all endpoints
├── services/
│   ├── normalizer.py              ← EntityNormalizer: parses raw datacenter JSON into a normalized dict
│   ├── blueprint_builder.py       ← BlueprintBuilder: builds the page structure blueprint
│   ├── keyword_seed_generator.py  ← KeywordSeedGenerator: generates seed keywords per page type
│   ├── dataforseo_client.py       ← DataForSEOClient: HTTP wrapper for all DataForSEO API calls
│   ├── keyword_intelligence_service.py ← Orchestrates full keyword research pipeline
│   ├── keyword_processing.py      ← Normalizes, evaluates, deduplicates, clusters keyword records
│   ├── content_plan_builder.py    ← ContentPlanBuilder: full content strategy document
│   ├── competitor_intelligence_service.py ← Analyzes competitor keyword data from SERP results
│   ├── openai_client.py           ← OpenAIClient: HTTP wrapper for OpenAI chat completions
│   ├── prompt_builder.py          ← PromptBuilder: builds system + user prompts for OpenAI
│   ├── draft_generation_service.py ← Orchestrates full draft generation (metadata, sections, FAQs)
│   ├── factual_validator.py       ← FactualValidator: validates drafts, strips forbidden claims
│   ├── markdown_renderer.py       ← MarkdownRenderer: renders a draft dict to Markdown text
│   ├── table_renderer.py          ← TableRenderer: renders structured data tables
│   ├── output_formatter.py        ← OutputFormatter: formats cell values for tables
│   ├── artifact_writer.py         ← ArtifactWriter: writes JSON, Markdown, DOCX, and HTML files
│   ├── draft_publish_service.py   ← DraftPublishService: thin wrapper around ArtifactWriter
│   ├── review_session_store.py    ← ReviewSessionStore: saves/loads review sessions from disk
│   ├── review_workbench_service.py ← ReviewWorkbenchService: manages full review session lifecycle
│   └── source_loader.py           ← SourceLoader: loads raw JSON input files
└── utils/
    └── formatters.py              ← slugify(), compact_dict(), and other formatting utilities
```

### Frontend (`apps/web/src/`)

```
src/
├── main.tsx                       ← React entry point
├── router/index.tsx               ← React Router route definitions
├── config/env.ts                  ← VITE_API_BASE_URL validation
├── api/
│   ├── http.ts                    ← Generic fetch wrapper with ApiError class
│   └── review.ts                  ← Typed API functions for all review endpoints
├── types/review.ts                ← TypeScript types matching backend schemas
├── pages/
│   ├── ReviewWorkbenchPage.tsx    ← Main workbench UI
│   └── NotFoundPage.tsx           ← 404 page
├── components/
│   └── AppLayout.tsx              ← Top-level layout wrapper
└── styles/app.css                 ← Global styles
```

---

## Tech Stack

### Backend
| Dependency | Version | Purpose |
|---|---|---|
| Python | ≥ 3.11 | Runtime |
| FastAPI | ≥ 0.115 | REST API framework |
| Uvicorn | ≥ 0.30 | ASGI server |
| Pydantic | ≥ 2.8 | Schema validation and settings |
| pydantic-settings | ≥ 2.4 | Env-driven configuration |
| python-dotenv | ≥ 1.0.1 | `.env` file loading |
| httpx | ≥ 0.27 | Async-capable HTTP client (used synchronously) |
| python-docx | ≥ 1.1.2 | DOCX artifact generation |
| pytest | ≥ 8.3 | Test runner |
| pytest-cov | ≥ 5.0 | Code coverage |
| ruff | ≥ 0.6 | Linting & formatting |

### Frontend
| Dependency | Version | Purpose |
|---|---|---|
| React | ^19.2 | UI framework |
| React DOM | ^19.2 | DOM rendering |
| React Router DOM | ^7.13 | Client-side routing |
| TypeScript | ~5.9 | Type safety |
| Vite | ^8.0.0-beta | Build tool & dev server |
| ESLint | ^9.39 | Linting |

### External APIs
| Service | Purpose |
|---|---|
| **DataForSEO** | Keyword suggestions, related keywords, SERP analysis, competitor keywords, keyword overview, historical search volume, Google Ads search volume |
| **OpenAI** | Draft metadata generation, editorial section writing, FAQ generation (uses `gpt-4.1-mini` by default) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- A DataForSEO account with API credentials
- An OpenAI API key

### Environment Setup

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values (see [Configuration Reference](#configuration-reference) for all options). At minimum, set:

```
DATAFORSEO_LOGIN=your_dataforseo_email
DATAFORSEO_PASSWORD=your_dataforseo_password
OPENAI_API_KEY=your_openai_api_key
```

### Running the API

**Install dependencies (with dev extras):**

```bash
pip install -e ".[dev]"
```

**Start the development server:**

```bash
uvicorn seo_content_engine.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive API docs (Swagger UI): `http://localhost:8000/docs`

Alternative API docs (ReDoc): `http://localhost:8000/redoc`

### Running the Web UI

```bash
cd apps/web
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

> The frontend connects to the API via `VITE_API_BASE_URL` defined in `apps/web/.env`. By default this is set to `http://127.0.0.1:8000`.

---

## Configuration Reference

All configuration is driven by environment variables, loaded from `.env` via pydantic-settings. Variable names are case-insensitive.

### Application

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Square Yards SEO Content Engine` | Application display name |
| `APP_ENV` | `local` | Environment name (local / staging / prod) |
| `APP_HOST` | `0.0.0.0` | Bind host for uvicorn |
| `APP_PORT` | `8000` | Bind port for uvicorn |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `ARTIFACTS_DIR` | `data/artifacts` | Directory where generated artifacts are written |

### DataForSEO

| Variable | Default | Description |
|---|---|---|
| `DATAFORSEO_BASE_URL` | `https://api.dataforseo.com/v3` | DataForSEO API base URL |
| `DATAFORSEO_LOGIN` | _(required)_ | DataForSEO account login email |
| `DATAFORSEO_PASSWORD` | _(required)_ | DataForSEO account password |
| `DATAFORSEO_DEFAULT_LOCATION_NAME` | `India` | Default location filter for keyword queries |
| `DATAFORSEO_DEFAULT_LANGUAGE_NAME` | `English` | Default language filter for keyword queries |
| `DATAFORSEO_DEFAULT_LIMIT` | `50` | Default max keyword rows per query |
| `DATAFORSEO_RELATED_DEPTH` | `2` | Depth for related keywords crawl |
| `DATAFORSEO_TIMEOUT_SECONDS` | `45` | HTTP timeout for DataForSEO requests |
| `DATAFORSEO_HISTORICAL_KEYWORDS_LIMIT` | `50` | Max keywords sent for historical search volume enrichment |
| `DATAFORSEO_SERP_SEED_LIMIT` | `3` | Number of seed keywords used for SERP validation |
| `DATAFORSEO_SERP_TOP_RESULTS_LIMIT` | `10` | Organic results per SERP query |
| `DATAFORSEO_COMPETITOR_DOMAIN_LIMIT` | `3` | Max competitor domains extracted from SERP |
| `DATAFORSEO_KEYWORDS_FOR_SITE_LIMIT` | `30` | Max keywords fetched per competitor domain |
| `DATAFORSEO_KEYWORD_OVERVIEW_LIMIT` | `100` | Max keywords for keyword overview enrichment |
| `DATAFORSEO_GOOGLE_ADS_LIMIT` | `100` | Max keywords for Google Ads search volume enrichment |

### Keyword Cluster Sizes

| Variable | Default | Description |
|---|---|---|
| `KEYWORD_SECONDARY_MAX_COUNT` | `10` | Max secondary keywords in cluster |
| `KEYWORD_LONG_TAIL_MAX_COUNT` | `12` | Max long-tail keywords |
| `KEYWORD_BHK_MAX_COUNT` | `10` | Max BHK-specific keywords |
| `KEYWORD_PRICE_MAX_COUNT` | `10` | Max price-intent keywords |
| `KEYWORD_READY_TO_MOVE_MAX_COUNT` | `8` | Max ready-to-move keywords |
| `KEYWORD_FAQ_MAX_COUNT` | `12` | Max FAQ keyword candidates |
| `KEYWORD_METADATA_MAX_COUNT` | `8` | Max metadata keywords |
| `KEYWORD_METADATA_EXACT_MATCH_MAX_COUNT` | `5` | Max exact-match metadata keywords |
| `KEYWORD_COMPETITOR_MAX_COUNT` | `12` | Max competitor keywords |
| `KEYWORD_INFORMATIONAL_MAX_COUNT` | `12` | Max informational keywords |
| `KEYWORD_SERP_VALIDATED_MAX_COUNT` | `12` | Max SERP-validated keywords |

### OpenAI

| Variable | Default | Description |
|---|---|---|
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API base URL |
| `OPENAI_API_KEY` | _(required)_ | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Model to use for all generation calls |
| `OPENAI_TIMEOUT_SECONDS` | `90` | HTTP timeout for OpenAI requests |
| `OPENAI_TEMPERATURE` | `0.2` | Temperature for generation (low = more deterministic) |

### Draft & Review

| Variable | Default | Description |
|---|---|---|
| `SQUAREYARDS_BASE_URL` | `https://www.squareyards.com` | Square Yards base URL (used for internal link resolution) |
| `DRAFT_REPAIR_MAX_PASSES` | `2` | Max validation repair passes after draft generation |
| `BLOCK_ARTIFACT_WRITE_ON_REVIEW` | `false` | If `true`, blocks artifact writes during review sessions |
| `DRAFT_DEFAULT_EXPORT_FORMATS` | `json,markdown,docx,html` | Comma-separated default export formats |

---

## API Reference

All endpoints return `{ "success": bool, "message": str, ... }` envelopes.

### Health

#### `GET /health`

Returns a simple health check response.

**Response:**
```json
{ "status": "ok" }
```

---

### Generation Endpoints

All generation endpoints accept two JSON data file paths as input (the `main_datacenter_json_path` and `property_rates_json_path` must be paths accessible from the server's filesystem).

#### `POST /v1/generate/blueprint`

Normalizes raw JSON data and builds the page structure blueprint. Does not call DataForSEO or OpenAI.

**Request body:**
```json
{
  "main_datacenter_json_path": "/path/to/locality.json",
  "property_rates_json_path": "/path/to/property-rates.json",
  "listing_type": "resale",
  "write_artifact": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Blueprint generated successfully",
  "blueprint": { ... },
  "artifact_path": "data/artifacts/entity-name-resale_locality-blueprint.json"
}
```

---

#### `POST /v1/generate/content-plan`

Runs the full keyword research pipeline via DataForSEO and builds a content plan with keyword strategy and section structure.

**Request body:**
```json
{
  "main_datacenter_json_path": "/path/to/locality.json",
  "property_rates_json_path": "/path/to/property-rates.json",
  "listing_type": "resale",
  "location_name": "India",
  "language_name": "English",
  "limit": 50,
  "include_historical": true,
  "write_artifact": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Content plan generated successfully",
  "content_plan": { ... },
  "artifact_path": "data/artifacts/entity-name-resale_locality-content-plan.json"
}
```

---

#### `POST /v1/generate/draft`

Runs the complete pipeline end-to-end: normalizes data → keyword research → content plan → OpenAI draft generation → factual validation. Returns the draft object but does not write artifact files.

**Request body:** Same as `/v1/generate/content-plan` plus `"write_artifact": false`.

**Response:**
```json
{
  "success": true,
  "message": "Draft generated successfully",
  "draft": { ... },
  "artifact_paths": null
}
```

---

#### `POST /v1/generate/draft/publish` _(legacy)_

Writes artifact files for a draft. Use `/v1/draft/publish` for the current implementation.

---

### Keywords Endpoint

#### `POST /v1/keywords/intelligence`

Runs the full DataForSEO keyword research pipeline in isolation — useful for inspecting the raw keyword data without generating a draft.

**Request body:** Same structure as `/v1/generate/content-plan`.

**Response:**
```json
{
  "success": true,
  "message": "Keyword intelligence generated successfully",
  "keyword_intelligence": { ... },
  "artifact_path": "data/artifacts/entity-name-resale_locality-keyword-intelligence.json"
}
```

---

### Draft Publish Endpoint

#### `POST /v1/draft/publish`

Writes artifact files for a previously generated draft in one or more export formats.

**Request body:**
```json
{
  "draft": { ... },
  "export_formats": ["json", "markdown", "docx", "html"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Draft artifacts published successfully",
  "artifact_paths": {
    "json_path": "data/artifacts/entity-name-resale_locality-draft.json",
    "markdown_path": "data/artifacts/entity-name-resale_locality-draft.md",
    "docx_path": "data/artifacts/entity-name-resale_locality-draft.docx",
    "html_path": "data/artifacts/entity-name-resale_locality-draft.html"
  }
}
```

---

### Review Workbench Endpoints

The Review Workbench allows editors to review, edit, and regenerate drafts in a stateful session with full version history.

#### `POST /v1/review/session`

Creates a new review session — runs the full pipeline (normalize → keyword intelligence → content plan → draft → validation) and persists the session to disk.

**Request body:**
```json
{
  "main_datacenter_json_path": "/path/to/locality.json",
  "property_rates_json_path": "/path/to/property-rates.json",
  "listing_type": "resale",
  "location_name": null,
  "language_name": null,
  "limit": null,
  "include_historical": true,
  "persist_session": true,
  "primary_keyword_overrides": ["flats for sale in andheri west mumbai"]
}
```

The `primary_keyword_overrides` field allows the caller to inject custom primary keywords that take precedence over the automatically selected ones.

**Response:**
```json
{
  "success": true,
  "message": "Review session created successfully",
  "review_session": {
    "session_id": "review-abc123...",
    "created_at": "2026-03-16T...",
    "entity": { ... },
    "keyword_preview": { ... },
    "source_preview": { ... },
    "draft": { ... },
    "section_review": [ ... ],
    "version_history": [ ... ],
    "latest_version_id": "v-abc123..."
  }
}
```

---

#### `GET /v1/review/session/{session_id}`

Fetches a previously persisted review session by ID.

---

#### `POST /v1/review/session/regenerate`

Regenerates the entire draft for an existing session using its stored normalized data and keyword intelligence.

**Request body:**
```json
{
  "session_id": "review-abc123...",
  "persist_session": true,
  "action_label": "full_regenerate"
}
```

**Response:** `ReviewMutationResponse` — includes the updated session and a mutation summary.

---

#### `POST /v1/review/section/regenerate`

Regenerates a single section within an existing session's draft while keeping all other sections intact.

**Request body:**
```json
{
  "session_id": "review-abc123...",
  "section_id": "market_snapshot",
  "persist_session": true,
  "action_label": "section_regenerate"
}
```

---

#### `POST /v1/review/section/update`

Replaces the body text of a specific section with editor-supplied content.

**Request body:**
```json
{
  "session_id": "review-abc123...",
  "section_id": "hero_intro",
  "body": "Updated section text...",
  "persist_session": true,
  "action_label": "section_edit"
}
```

---

#### `POST /v1/review/metadata/update`

Updates SEO metadata fields (title, meta description, H1, intro snippet) for the current draft.

**Request body:**
```json
{
  "session_id": "review-abc123...",
  "title": "Updated Page Title | Square Yards",
  "meta_description": "Updated meta description...",
  "h1": "Updated H1 Heading",
  "intro_snippet": "Updated intro paragraph...",
  "persist_session": true,
  "action_label": "metadata_edit"
}
```

---

#### `POST /v1/review/version/restore`

Restores a previous version from the session's version history.

**Request body:**
```json
{
  "session_id": "review-abc123...",
  "version_id": "v-xyz789...",
  "persist_session": true,
  "action_label": "restore_version"
}
```

---

#### `POST /v1/review/session/export`

Exports the current draft of a review session to one or more artifact files.

**Request body:**
```json
{
  "session_id": "review-abc123...",
  "export_formats": ["json", "markdown", "docx", "html"],
  "persist_session": true
}
```

---

#### `GET /v1/review/session/{session_id}/download/{format_name}`

Streams a file download for a specific export format. Supported `format_name` values: `json`, `markdown`, `docx`, `html`.

---

## Core Concepts

### Entity Types and Page Types

The system supports three entity types, each mapped to a page type:

| Entity Type | Page Type | Description |
|---|---|---|
| `city` | `resale_city` | A full city page (e.g. Mumbai resale) |
| `micromarket` | `resale_micromarket` | A micro-market / sub-zone page (e.g. Bandra West resale) |
| `locality` | `resale_locality` | A specific locality page (e.g. Andheri West resale) |

Entity type is **automatically detected** from the input JSON by inspecting the `rates_data.data.type` field and the `isMicroMarket` flag in `localityOverviewData`.

Currently only `listing_type = "resale"` is supported.

### Data Inputs

Every generation request requires two JSON files:

- **`main_datacenter_json_path`** — The locality/city overview JSON exported from the Square Yards backend. Contains listing counts, unit type distributions, property type distributions, nearby localities, reviews, AI summaries, featured projects, footer links, and more.

- **`property_rates_json_path`** — The property rates JSON. Contains asking price, registration rate, price trends, market overview, top projects, micromarket rates, and AI-generated market insights.

Sample files for development are expected in `data/samples/raw/`.

### Generation Pipeline

The full pipeline runs these steps in sequence:

1. **Normalize** (`EntityNormalizer`) — Loads and parses both JSON files. Detects entity type. Extracts a clean, flat normalized dict with consistent field names regardless of whether the entity is a city, micromarket, or locality.

2. **Keyword Seeds** (`KeywordSeedGenerator`) — Generates a set of seed keyword phrases tailored to the entity type and location. For example, a locality page for "Andheri West, Mumbai" produces seeds like "resale properties in Andheri West Mumbai", "2 bhk flats for sale in Andheri West Mumbai", etc.

3. **Keyword Intelligence** (`KeywordIntelligenceService`) — Calls DataForSEO APIs for each seed keyword:
   - **Keyword suggestions** — Finds related keywords from DataForSEO Labs
   - **Related keywords** — Crawls the keyword graph at depth 2
   - **SERP organic** — Fetches top organic results for SERP validation and competitor domain extraction
   - **Keywords for site** — Retrieves keywords ranking for each identified competitor domain
   - **Historical search volume** — Enriches keywords with monthly trend data
   - **Keyword overview** — Enriches with search volume, CPC, competition data
   - **Google Ads search volume** — Additional volume data from Google Ads
   - All results are deduplicated, normalized, evaluated, consolidated, and clustered into: primary keyword, secondary, BHK, price, ready-to-move, FAQ candidates, competitor, informational, SERP-validated, metadata, exact-match, and loose-match groups.

4. **Content Plan** (`ContentPlanBuilder`) — Combines normalized entity data and keyword intelligence into a detailed content brief: keyword strategy, metadata plan, section structure with data grounding instructions, table plan, FAQ keyword plan, competitor intelligence analysis, and internal links.

5. **Draft Generation** (`DraftGenerationService`) — Makes three sequential OpenAI calls:
   - **Metadata** — Generates title, meta description, H1, and intro snippet
   - **Sections** — Generates editorial section bodies from the content plan
   - **FAQs** — Generates FAQ questions and answers
   Assembles tables from structured data using `TableRenderer`, resolves internal links using `OutputFormatter`, renders a Markdown draft, and runs validation repair passes.

6. **Factual Validation** (`FactualValidator`) — Validates every section and FAQ body against the source data. Checks for forbidden marketing claims (e.g. "premium", "excellent connectivity", "strong demand", "investment potential") and pricing inconsistencies. Produces a detailed validation report and quality score. Applies sanitization to remove or flag problematic content.

7. **Artifact Writing** (`ArtifactWriter`) — Writes the finished draft to disk in up to four formats: JSON (full structured data), Markdown (readable text), DOCX (Word document with structured sections), and HTML (styled standalone page).

### Review Workbench & Version History

The Review Workbench (`ReviewWorkbenchService`) wraps the pipeline and adds:

- **Session persistence** — Every session is saved to `data/review_sessions/<session_id>.json`.
- **Version history** — Every mutation (full regenerate, section regenerate, section edit, metadata edit, version restore) appends a new version entry with a snapshot of the draft. Versions can be browsed and restored.
- **Primary keyword overrides** — Callers can inject custom primary keywords that override the auto-selected ones and propagate through the content plan and generation steps.
- **Section-level operations** — Individual sections can be regenerated in isolation (re-runs OpenAI for just that section and merges it back) or manually edited.
- **Mutation summary** — Every mutation returns a summary with the action type, approval status, quality score, and publish-readiness flag.

### Export Formats

| Format | Extension | Description |
|---|---|---|
| `json` | `.json` | Full draft data structure with all metadata, sections, tables, FAQs, links, validation report, quality report |
| `markdown` | `.md` | Rendered Markdown document for easy reading and copy-paste |
| `docx` | `.docx` | Word document with formatted headings, tables, and section content. Font: Arial 10.5pt |
| `html` | `.html` | Self-contained HTML page with inline CSS, suitable for previewing in a browser |

Artifact files are named using the pattern `{entity-name}-{page-type}-{artifact-type}.{ext}`, slugified for safe filenames.

### Factual Validation

The `FactualValidator` enforces content quality and accuracy:

- **Forbidden claims** — A hardcoded list of promotional phrases that are not permitted without specific data backing. Examples: "most sought-after", "premium status", "excellent connectivity", "investment potential", "luxury lifestyle", "strong demand".
- **Pricing consistency** — Checks that any price figures mentioned in sections match the canonical pricing fields (asking price, registration rate, avg price per sq ft) from the source data.
- **Quality scoring** — Produces per-section quality scores and an overall approval status of `pass` / `warn` / `fail`.
- **Sanitization** — Removes or flags content that fails validation rules.
- **Repair passes** — On initial draft generation, the system can run up to `DRAFT_REPAIR_MAX_PASSES` repair cycles where validation issues are fed back to the generation layer for self-correction.

---

## Service Layer

A summary of every service and its responsibility:

| Service | File | Responsibility |
|---|---|---|
| `EntityNormalizer` | `normalizer.py` | Parses raw datacenter + rates JSON into a normalized entity dict. Auto-detects entity type. Handles city, micromarket, and locality variants. |
| `BlueprintBuilder` | `blueprint_builder.py` | Builds the page structure blueprint with section plan, SEO stubs, and data block references. |
| `KeywordSeedGenerator` | `keyword_seed_generator.py` | Generates location-specific seed keyword phrases per page type. |
| `DataForSEOClient` | `dataforseo_client.py` | HTTP client wrapping all DataForSEO API endpoints (keyword suggestions, related keywords, SERP organic, keywords for site, keyword overview, historical search volume, Google Ads). |
| `KeywordIntelligenceService` | `keyword_intelligence_service.py` | Orchestrates all DataForSEO calls, deduplicates and normalizes results, applies SERP validation, enriches with historical/overview/ads data, evaluates and clusters keywords. |
| `KeywordProcessing` | `keyword_processing.py` | Low-level keyword normalization, evaluation scoring, deduplication, consolidation, and cluster building. |
| `CompetitorIntelligenceService` | `competitor_intelligence_service.py` | Analyzes competitor keyword data extracted from SERP results. Classifies keywords by theme. Identifies overlap and gap keywords. |
| `ContentPlanBuilder` | `content_plan_builder.py` | Builds the full content plan: keyword strategy, metadata plan, section structure with data grounding, table plan, FAQ plan, competitor intelligence. |
| `OpenAIClient` | `openai_client.py` | HTTP client for OpenAI chat completions. Always requests `json_object` response format. |
| `PromptBuilder` | `prompt_builder.py` | Builds system and user prompts for metadata, sections, and FAQ generation. Enforces grounding rules in prompts. |
| `DraftGenerationService` | `draft_generation_service.py` | Orchestrates OpenAI calls (metadata → sections → FAQs), assembles tables and internal links, renders Markdown, runs validation and repair passes. |
| `FactualValidator` | `factual_validator.py` | Validates draft content against source data. Checks for forbidden claims and pricing inconsistencies. Produces quality report. |
| `MarkdownRenderer` | `markdown_renderer.py` | Renders a draft dict to a Markdown string. |
| `TableRenderer` | `table_renderer.py` | Builds structured table dicts from normalized entity data. |
| `OutputFormatter` | `output_formatter.py` | Formats individual cell values for tables (prices, percentages, counts, etc.). |
| `ArtifactWriter` | `artifact_writer.py` | Writes draft artifacts to disk: JSON (raw), Markdown (rendered), DOCX (python-docx), HTML (string-built). |
| `DraftPublishService` | `draft_publish_service.py` | Thin wrapper around `ArtifactWriter.write_draft_bundle()`. |
| `ReviewSessionStore` | `review_session_store.py` | Saves and loads review session JSON files from `data/review_sessions/`. |
| `ReviewWorkbenchService` | `review_workbench_service.py` | Full review session lifecycle: build, fetch, regenerate draft, regenerate section, update section, update metadata, restore version, export. Manages version history. |
| `SourceLoader` | `source_loader.py` | Loads raw JSON input files from the filesystem. |
| `formatters` | `utils/formatters.py` | `slugify()`, `compact_dict()`, and other shared utilities. |

---

## Frontend (Review Workbench UI)

The web app is a single-page React application providing an interactive UI for the Review Workbench API.

**Tech:** React 19, TypeScript 5.9, Vite 8, React Router 7

**Key files:**

- `src/pages/ReviewWorkbenchPage.tsx` — The primary UI. Supports creating new review sessions, loading existing sessions by ID, viewing and editing section bodies and metadata, regenerating individual sections or the full draft, browsing version history and restoring versions, and exporting/downloading artifacts in all four formats.
- `src/api/review.ts` — Typed API functions for every review endpoint, built on top of the generic `apiRequest` wrapper.
- `src/api/http.ts` — Generic `fetch`-based HTTP client with typed `ApiError` class for structured error handling.
- `src/types/review.ts` — TypeScript type definitions matching the backend Pydantic schemas.
- `src/config/env.ts` — Validates `VITE_API_BASE_URL` is set and exposes it as `env.apiBaseUrl`.

**Environment:**

Create `apps/web/.env`:
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

**Build for production:**
```bash
cd apps/web
npm run build
# Output in apps/web/dist/
```

---

## Testing

Tests are located in `apps/api/tests/` and use `pytest` with `fastapi.testclient.TestClient`.

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=seo_content_engine --cov-report=term-missing
```

**Test structure:**

| Test File | What it tests |
|---|---|
| `test_health.py` | Health endpoint |
| `test_generation.py` | Blueprint, content plan, draft generation routes |
| `test_content_plan_route.py` | Content plan generation |
| `test_city_content_plan_route.py` | City-specific content plan |
| `test_draft_route.py` | Draft route with mocked dependencies |
| `test_city_draft_route.py` | City-specific draft route |
| `test_micromarket_draft_route.py` | Micromarket-specific draft route |
| `test_draft_publish_route.py` | Draft publish endpoint |
| `test_draft_repair_loop.py` | Validation repair pass logic |
| `test_draft_generation_service.py` | DraftGenerationService unit tests |
| `test_review_route.py` | Review workbench route tests |
| `test_review_workbench_service.py` | ReviewWorkbenchService unit tests |
| `test_keyword_intelligence_service.py` | KeywordIntelligenceService unit tests |
| `test_keyword_seed_generator.py` | KeywordSeedGenerator unit tests |
| `test_keywords_route.py` | Keywords intelligence route |
| `test_content_plan_builder.py` | ContentPlanBuilder unit tests |
| `test_factual_validator.py` | FactualValidator unit tests |
| `test_artifact_writer_blocking.py` | ArtifactWriter blocking behavior tests |

External services (DataForSEO, OpenAI) are mocked in all tests using dummy service classes.

---

## Data & Artifacts

### Input Data

Raw input JSON files should be placed in `data/samples/raw/` for development. Each generation request needs two files:
- `{locality-slug}-locality.json` — Main datacenter response
- `{locality-slug}-property-rates.json` — Property rates response

### Output Artifacts

Generated artifacts are written to `ARTIFACTS_DIR` (default: `data/artifacts/`). File naming follows the slug pattern `{entity-name}-{page-type}-{artifact-type}`:

```
data/artifacts/
├── andheri-west-resale-locality-blueprint.json
├── andheri-west-resale-locality-keyword-intelligence.json
├── andheri-west-resale-locality-content-plan.json
├── andheri-west-resale-locality-draft.json
├── andheri-west-resale-locality-draft.md
├── andheri-west-resale-locality-draft.docx
└── andheri-west-resale-locality-draft.html
```

### Review Sessions

Persisted review sessions are stored in `data/review_sessions/` as `{session_id}.json`. Session IDs follow the pattern `review-{hex_uuid}`.

---

## Development Notes

### Linting & Formatting

The project uses `ruff` for Python linting and formatting:

```bash
ruff check apps/api/src
ruff format apps/api/src
```

### Adding a New Page Type

1. Add the new enum value to `EntityType`, `PageType`, and map it in `EntityNormalizer.resolve_page_type()`
2. Add the entity normalization branch in `EntityNormalizer.normalize()`
3. Add the section map in `BlueprintBuilder.build()`
4. Add seed keywords in `KeywordSeedGenerator.generate()`
5. Add content plan section definitions in `ContentPlanBuilder`
6. Add tests for the new page type

### DataForSEO API Limits

The keyword intelligence pipeline makes multiple API calls per generation request. With default settings, a single call can make up to:
- `len(seeds)` × 2 calls for suggestions + related keywords (roughly 10–11 seeds for a locality)
- 3 SERP calls (configurable via `DATAFORSEO_SERP_SEED_LIMIT`)
- Up to 3 competitor keyword calls (configurable via `DATAFORSEO_COMPETITOR_DOMAIN_LIMIT`)
- 1 historical search volume call
- 1 keyword overview call
- 1 Google Ads call

**Total: ~20 API calls per generation.** Plan API credits accordingly.

### OpenAI Rate Limits

Each draft generation makes 3 OpenAI calls (metadata, sections, FAQs). All calls use `json_object` response format to guarantee parseable output. Temperature defaults to `0.2` for deterministic results.

### CORS

The API allows CORS from `http://localhost:5173` and `http://127.0.0.1:5173` (the Vite dev server defaults). Update `main.py` `allow_origins` for production deployments.
