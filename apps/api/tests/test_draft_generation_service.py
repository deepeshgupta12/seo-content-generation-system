from seo_content_engine.services.draft_generation_service import DraftGenerationService


class DummyOpenAIClient:
    def generate_json(self, system_prompt: str, user_prompt: str):
        if '"validation_by_field"' in user_prompt:
            return {
                "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
                "meta_description": "Explore resale properties in Andheri West, Mumbai with current price trends, BHK mix, nearby locality insights, and structured market signals on Square Yards.",
                "h1": "Resale Properties in Andheri West, Mumbai",
                "intro_snippet": "Browse current resale property options in Andheri West, Mumbai with grounded price, inventory, locality-level signals, and source-backed market notes on Square Yards.",
            }

        if '"faq"' in user_prompt and '"validator_feedback"' in user_prompt:
            return {
                "question": "What is the asking price signal for resale properties in Andheri West, Mumbai?",
                "answer": (
                    "The grounded asking price signal for resale properties in Andheri West, Mumbai is ₹40,238. "
                    "This page uses asking-price inputs and available trend context to help readers understand how current resale listings are positioned."
                ),
            }

        if '"section"' in user_prompt and '"validator_feedback"' in user_prompt:
            return {
                "id": "market_snapshot",
                "title": "Resale Market Snapshot",
                "body": (
                    "Andheri West currently shows 2,039 resale listings within a broader visible inventory base of 6,109 listings. "
                    "The grounded asking price signal is ₹40,238, giving buyers a practical starting point for understanding how listings on this page are positioned. "
                    "\n\n"
                    "Alongside pricing, the page also reflects inventory depth, nearby locality references, and structured BHK and property-type inputs. "
                    "That makes this snapshot more useful for comparing current supply with the broader resale landscape in Mumbai."
                ),
            }

        if '"faqs"' in user_prompt:
            return {
                "faqs": [
                    {
                        "question": "What is the asking price signal for resale properties in Andheri West, Mumbai?",
                        "answer": (
                            "The grounded asking price signal for resale properties in Andheri West, Mumbai is ₹40,238. "
                            "This figure gives a direct view of how current resale listings on the page are being represented in the source-backed pricing layer."
                        ),
                    },
                    {
                        "question": "How many resale properties are available in Andheri West, Mumbai?",
                        "answer": (
                            "The current resale page inputs show 2,039 sale listings, while the broader visible listing count is 6,109. "
                            "This helps readers understand both the active resale count and the wider inventory context available on the page."
                        ),
                    },
                    {
                        "question": "Which BHK options are commonly available in Andheri West, Mumbai?",
                        "answer": (
                            "The structured inventory mix includes BHK-level distribution inputs, and the available grounded example shows 3 BHK inventory in the resale mix. "
                            "These inputs help users understand which home configurations are appearing in the current page dataset."
                        ),
                    },
                    {
                        "question": "Are ready-to-move resale properties available in Andheri West, Mumbai?",
                        "answer": (
                            "Yes, the grounded property-status inputs include a Ready To Move bucket. "
                            "Where present, this section helps users understand how much of the visible resale inventory is already in a ready condition versus other status groupings."
                        ),
                    },
                    {
                        "question": "Which nearby localities can buyers also consider around Andheri West, Mumbai?",
                        "answer": (
                            "The page includes nearby locality references such as Sv Patel Nagar. "
                            "These nearby locality inputs are useful for users who want to compare resale options, pricing signals, and available inventory in surrounding areas."
                        ),
                    },
                    {
                        "question": "What review signals are available for this resale page?",
                        "answer": (
                            "The grounded review layer shows an average rating of 4.23 based on 97 reviews. "
                            "The page also includes review-tag signals and an AI summary field, allowing readers to inspect currently available opinion-based inputs without adding editorial interpretation."
                        ),
                    },
                    {
                        "question": "What market strengths, challenges, and opportunities are highlighted for Andheri West, Mumbai?",
                        "answer": (
                            "For Andheri West, Mumbai, the structured market-summary layer includes a snapshot that reads: "
                            "Balanced resale market with established apartment inventory and visible end-user demand. "
                            "It also highlights strengths such as established micro-market, challenges such as traffic pressure, "
                            "and opportunity cues such as ready-to-move resale stock. "
                            "These signals are presented as grounded market-summary notes only."
                        ),
                    },
                    {
                        "question": "What demand and supply inputs are available on this page?",
                        "answer": (
                            "The sale-side inputs include a 2 BHK listing count of 577, with demand percent at 30 and supply percent at 32. "
                            "The page also includes listing-range data, which helps frame the spread of resale inventory visible in the current dataset."
                        ),
                    },
                    {
                        "question": "Which property-type signals are available on this resale page?",
                        "answer": (
                            "Apartment appears in the grounded property-type inputs, and the structured data also includes average value and change-percent fields for available property-type buckets. "
                            "This helps readers understand how the resale inventory is distributed across different formats."
                        ),
                    },
                ]
            }

        if '"sections"' in user_prompt:
            return {
                "sections": [
                    {
                        "id": "hero_intro",
                        "title": "Resale Property Overview in Andheri West, Mumbai",
                        "body": (
                            "Andheri West currently shows 2,039 resale listings on Square Yards, making it a meaningful resale search area within Mumbai. "
                            "For users beginning their research, this creates a clear starting point to review prices, available inventory, and nearby alternatives in one place."
                            "\n\n"
                            "The page combines resale inventory signals with grounded pricing context, BHK distribution, and related local references. "
                            "That makes it easier to move beyond a single number and understand how the visible resale market is actually shaped at the page level."
                        ),
                    },
                    {
                        "id": "market_snapshot",
                        "title": "Resale Market Snapshot",
                        "body": (
                            "The resale snapshot for Andheri West is backed by 2,039 sale listings within a wider visible listing base of 6,109. "
                            "This gives users a direct sense of how much resale inventory is actively represented on the page at the moment."
                            "\n\n"
                            "Alongside this inventory view, the grounded asking price signal is ₹40,238. "
                            "When read together with BHK mix, property-type distribution, and nearby locality references, the page offers a more complete resale picture rather than a single isolated market statistic."
                        ),
                    },
                    {
                        "id": "price_trends_and_rates",
                        "title": "Price Trends and Rates",
                        "body": (
                            "The grounded asking price signal for resale properties in Andheri West, Mumbai is ₹40,238. "
                            "This serves as the main pricing anchor for understanding how current resale listings on the page are positioned."
                            "\n\n"
                            "The available trend snapshot also includes Dec 2025 as the latest tracked period, with locality and micromarket level values available in the structured source inputs. "
                            "That helps place the current asking-price view in a broader local context while keeping the narrative tied to grounded resale data."
                        ),
                    },
                    {
                        "id": "review_and_rating_signals",
                        "title": "Review and Rating Signals",
                        "body": (
                            "The current review layer shows an average rating of 4.23 based on 97 reviews. "
                            "These signals provide a source-backed snapshot of what review data is currently available on the page."
                            "\n\n"
                            "The page also includes tag-level signals such as metro connectivity and traffic, along with an AI summary for the locality. "
                            "Together, these inputs help reviewers understand the shape of the available sentiment layer without turning those signals into unsupported claims."
                        ),
                    },
                    {
                        "id": "property_rates_ai_signals",
                        "title": "Market Strengths, Challenges, and Opportunities",
                        "body": (
                            "For Andheri West, Mumbai, the structured property-rates AI summary describes the current resale market as follows: "
                            "Balanced resale market with established apartment inventory and visible end-user demand. "
                            "This gives readers a concise starting point for understanding how the attached market-summary layer frames the area."
                            "\n\n"
                            "The same source highlights strengths such as established micro-market and active resale supply, while also pointing to challenges such as traffic pressure and pricing dispersion across pockets. "
                            "It additionally surfaces opportunity areas such as ready-to-move resale stock and well-known apartment clusters. "
                            "These signals are included as grounded market-summary notes rather than promotional claims."
                        ),
                    },
                    {
                        "id": "demand_and_supply_signals",
                        "title": "Demand and Supply Signals",
                        "body": (
                            "The current sale-side inputs show active resale availability, with a 2 BHK listing count of 577 in the grounded demand-supply layer. "
                            "For that unit type, the available demand percent is 30 and supply percent is 32."
                            "\n\n"
                            "The page also includes listing-range data with document count and minimum-to-maximum price boundaries. "
                            "This combination helps users understand both the scale of visible inventory and the spread of listings represented in the source-backed dataset."
                        ),
                    },
                    {
                        "id": "property_type_signals",
                        "title": "Property Type Signals",
                        "body": (
                            "Apartment appears in the grounded property-type inputs for this resale page, with structured fields available for average price and change percent. "
                            "This makes it easier to understand how one of the main resale inventory buckets is represented in the current dataset."
                            "\n\n"
                            "The page also includes sale property-type mix signals and status-level inputs such as Ready To Move. "
                            "Together, these fields help build a clearer picture of how the visible resale stock is distributed across format and readiness."
                        ),
                    },
                ]
            }

        return {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Explore resale properties in Andheri West, Mumbai with current price trends, BHK mix, nearby locality insights, and structured market signals on Square Yards.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse current resale property options in Andheri West, Mumbai with grounded price, inventory, and locality-level signals on Square Yards.",
        }


def test_draft_generation_service() -> None:
    normalized = {
        "entity": {
            "entity_type": "locality",
            "page_type": "resale_locality",
            "listing_type": "resale",
            "entity_name": "Andheri West",
            "city_name": "Mumbai",
            "micromarket_name": "Mumbai Western Suburbs",
        },
        "listing_summary": {
            "sale_count": 2039,
            "total_listings": 6109,
            "total_projects": 1762,
            "sale_available": 2039,
        },
        "pricing_summary": {
            "asking_price": 40238,
            "registration_rate": 26616,
            "price_trend": [{"quarterName": "Dec 2025", "locationRate": 40238, "micromarketRate": 21180}],
            "location_rates": [{"name": "Yari Road", "avgRate": 32638, "changePercentage": 0}],
            "property_types": [{"propertyType": "apartment", "avgPrice": 40238, "changePercent": 4.61}],
            "property_status": [{"status": "Ready To Move", "units": 957, "avgPrice": 31639, "changePercent": -2.88}],
        },
        "distributions": {
            "sale_unit_type_distribution": [{"key": "3 BHK", "doc_count": 789}],
            "sale_property_type_distribution": [{"key": "Apartment", "doc_count": 1658}],
        },
        "nearby_localities": [
            {
                "name": "Sv Patel Nagar",
                "distance_km": 0.587,
                "sale_count": 38,
                "sale_avg_price_per_sqft": 29775.32,
                "url": "sv-patel-nagar-mumbai",
            }
        ],
        "links": {
            "sale_unit_type_urls": [[{"unitType": "2 BHK", "url": "sale/2-bhk-for-sale-in-andheri-west-mumbai"}]],
            "sale_property_type_urls": [[{"propertyType": "Apartment", "url": "sale/apartments-for-sale-in-andheri-west-mumbai"}]],
            "sale_quick_links": [{"label": "New Projects in Andheri West", "url": "projects-in-andheri-west-mumbai"}],
        },
        "top_projects": {"byTransactions": {"projects": []}},
        "review_summary": {
            "overview": {"avg_rating": 4.23, "rating_count": 97, "review_count": 97},
            "star_distribution": [{"rating": 5, "count": 40}],
            "positive_tags": ["metro connectivity"],
            "negative_tags": ["traffic"],
        },
        "ai_summary": {"locality_summary": "Established locality with mixed residential inventory."},
        "property_rates_ai_summary": {
            "market_snapshot": "Balanced resale market with established apartment inventory and visible end-user demand.",
            "market_strengths": ["established micro-market", "active resale supply"],
            "market_challenges": ["traffic pressure", "pricing dispersion across pockets"],
            "investment_opportunities": ["ready-to-move resale stock", "well-known apartment clusters"],
        },
        "insight_rates": {"name": "Andheri West", "avg_rate": 40238},
        "demand_supply": {"sale": {"unitType": [{"name": "2 BHK", "listing": 577, "demandPercent": 30, "supplyPercent": 32}]}},
        "listing_ranges": {"sale_listing_range": {"doc_count": 1933, "min_price": 2320000, "max_price": 4900000000}},
        "cms_faq": [{"question": "Sample question", "answer": "Sample answer"}],
        "featured_projects": [{"name": "Project A", "url": "projects-in-andheri-west-mumbai/project-a"}],
        "projects_by_status": {},
        "raw_source_meta": {
            "main_message": "locality Found",
            "rates_message": "Property Rates Data Found",
            "last_modified_date": "2026-03-02",
        },
    }

    keyword_intelligence = {
        "version": "v1.1",
        "keyword_clusters": {
            "primary_keyword": {
                "keyword": "flats for sale in andheri west mumbai",
                "score": 92,
                "semantic_signature": ("andheri", "flats", "for", "in", "mumbai", "sale", "west"),
            },
            "secondary_keywords": [{"keyword": "apartments for sale in andheri west mumbai"}],
            "bhk_keywords": [{"keyword": "2 bhk flats for sale in andheri west mumbai"}],
            "price_keywords": [{"keyword": "property prices in andheri west mumbai"}],
            "ready_to_move_keywords": [{"keyword": "ready possession flats in andheri west"}],
            "faq_keyword_candidates": [{"keyword": "property prices in andheri west mumbai"}],
            "metadata_keywords": [
                "flats for sale in andheri west mumbai",
                "apartments for sale in andheri west mumbai",
            ],
            "exact_match_keywords": [{"keyword": "flats for sale in andheri west mumbai"}],
            "loose_match_keywords": [],
        },
    }

    draft = DraftGenerationService.generate(
        normalized=normalized,
        keyword_intelligence=keyword_intelligence,
        openai_client=DummyOpenAIClient(),
    )

    assert draft["version"] == "v2.5"
    assert draft["metadata"]["h1"] == "Resale Properties in Andheri West, Mumbai"
    assert len(draft["sections"]) > 0
    assert len(draft["tables"]) > 0
    assert len(draft["faqs"]) >= 5
    assert "validation_report" in draft
    assert "quality_report" in draft
    assert "repair_passes_used" in draft
    assert "validation_history" in draft
    assert "pre_block_draft" in draft
    assert "debug_summary" in draft

    review_section = next(section for section in draft["sections"] if section["id"] == "review_and_rating_signals")
    property_rates_ai_section = next(section for section in draft["sections"] if section["id"] == "property_rates_ai_signals")
    demand_section = next(section for section in draft["sections"] if section["id"] == "demand_and_supply_signals")
    property_type_section = next(section for section in draft["sections"] if section["id"] == "property_type_signals")

    assert property_rates_ai_section["title"] == "Market Strengths, Challenges, and Opportunities"
    assert "4.23" in review_section["body"]
    assert "balanced resale market" in property_rates_ai_section["body"].lower()
    assert "established micro-market" in property_rates_ai_section["body"].lower()
    assert "traffic pressure" in property_rates_ai_section["body"].lower()
    assert "ready-to-move resale stock" in property_rates_ai_section["body"].lower()
    assert "demand percent" in demand_section["body"].lower()
    assert "apartment" in property_type_section["body"].lower()
    assert draft["quality_report"]["approval_status"] in {"pass", "warning"}
    assert "overall_quality_score" in draft["quality_report"]
    assert "warning_taxonomy" in draft["quality_report"]
    assert "page_uniqueness_check" in draft["quality_report"]

    property_rates_ai_faq = next(
        faq for faq in draft["faqs"] if "market strengths, challenges, and opportunities" in faq["question"].lower()
    )
    assert "grounded market-summary notes" in property_rates_ai_faq["answer"].lower()

    first_table = draft["tables"][0]
    assert "summary" in first_table
    assert isinstance(first_table["summary"], str)
    assert len(first_table["summary"]) > 40

    assert "## Key Data Tables" in draft["markdown_draft"]
    assert "This table shows the recent resale price trend" in draft["markdown_draft"]
    assert "The grounded asking price signal for resale properties in Andheri West, Mumbai is ₹40,238." in draft["markdown_draft"]
    assert "balanced resale market" in draft["markdown_draft"].lower()
    assert "traffic pressure" in draft["markdown_draft"].lower()
    assert "ready-to-move resale stock" in draft["markdown_draft"].lower()
    assert "https://www.squareyards.com/" in draft["markdown_draft"]


def test_micromarket_property_type_safe_body_allows_single_decimal_grounded_value() -> None:
    normalized = {
        "entity": {
            "entity_type": "micromarket",
            "page_type": "resale_micromarket",
            "listing_type": "resale",
            "entity_name": "Chandigarh Sectors",
            "city_name": "Chandigarh",
            "micromarket_name": "Chandigarh Sectors",
        },
        "listing_summary": {
            "sale_count": 10,
            "total_listings": 10,
            "total_projects": 2,
            "sale_available": 10,
        },
        "pricing_summary": {
            "asking_price": 25000,
            "registration_rate": 20000,
            "price_trend": [{"quarterName": "Dec 2025", "micromarketRate": 25000}],
            "location_rates": [{"name": "Sector 51", "avgRate": 18543, "changePercentage": 16.47}],
            "property_types": [{"propertyType": "villa", "avgPrice": 36631, "changePercent": 8.4}],
            "property_status": [{"status": "Ready To Move", "units": 1, "avgPrice": 20047}],
        },
        "distributions": {
            "sale_unit_type_distribution": [{"key": "3 BHK", "doc_count": 4}],
            "sale_property_type_distribution": [{"key": "Villa", "doc_count": 2}],
        },
        "nearby_localities": [],
        "links": {
            "sale_unit_type_urls": [],
            "sale_property_type_urls": [],
            "sale_quick_links": [],
        },
        "top_projects": {"byTransactions": {"projects": []}},
        "review_summary": {"overview": {}},
        "ai_summary": {},
        "property_rates_ai_summary": {},
        "insight_rates": {},
        "demand_supply": {},
        "listing_ranges": {},
        "cms_faq": [],
        "featured_projects": [],
        "projects_by_status": {},
        "raw_source_meta": {
            "main_message": "micromarket Found",
            "rates_message": "Property Rates Data Found",
            "last_modified_date": "2026-03-05",
        },
    }

    keyword_intelligence = {
        "version": "v1.1",
        "keyword_clusters": {
            "primary_keyword": {"keyword": "resale properties in chandigarh sectors chandigarh", "score": 90},
            "secondary_keywords": [{"keyword": "apartments for sale in chandigarh sectors chandigarh"}],
            "bhk_keywords": [],
            "price_keywords": [{"keyword": "property prices in chandigarh sectors chandigarh"}],
            "ready_to_move_keywords": [],
            "faq_keyword_candidates": [],
            "metadata_keywords": ["resale properties in chandigarh sectors chandigarh"],
            "exact_match_keywords": [{"keyword": "resale properties in chandigarh sectors chandigarh"}],
            "loose_match_keywords": [],
        },
    }

    content_plan = DraftGenerationService.generate(
        normalized=normalized,
        keyword_intelligence=keyword_intelligence,
        openai_client=DummyOpenAIClient(),
    )["content_plan"]

    safe_body = DraftGenerationService._build_property_type_safe_body(content_plan)

    assert "8.4" in safe_body
    assert "16.47" in safe_body