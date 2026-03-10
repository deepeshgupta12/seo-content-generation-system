from seo_content_engine.services.factual_validator import FactualValidator


def test_factual_validator_flags_forbidden_claims_and_unknown_numbers() -> None:
    draft = {
        "metadata": {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Andheri West is one of the most sought-after areas with strong demand.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Average price is ₹99,999 here.",
        },
        "sections": [
            {
                "id": "hero_intro",
                "title": "Resale Property Overview in Andheri West, Mumbai",
                "body": "This locality has excellent connectivity and a premium status.",
            }
        ],
        "faqs": [
            {
                "question": "What is the average price?",
                "answer": "The average price is ₹40,238.",
            }
        ],
        "content_plan": {
            "generated_at": "2026-03-09T10:00:00+00:00",
            "metadata_plan": {
                "canonical_pricing_metric": {
                    "metric_name": "asking_price",
                    "label": "asking price",
                    "value": 40238,
                }
            },
            "data_context": {
                "pricing_summary": {"asking_price": 40238},
                "listing_summary": {"sale_count": 2039},
            },
            "source_meta": {
                "raw_source_meta": {
                    "last_modified_date": "2026-03-02",
                }
            },
            "keyword_strategy": {
                "primary_keyword": {"keyword": "flats for sale in andheri west mumbai"},
                "exact_match_keywords": [],
            },
        },
    }

    report = FactualValidator.validate_draft(draft)

    assert report["passed"] is False
    assert "forbidden_claims_detected" in report["metadata_checks"]["meta_description"]["issues"]
    assert "unreconciled_numbers_detected" in report["metadata_checks"]["intro_snippet"]["issues"]
    assert "forbidden_claims_detected" in report["section_checks"][0]["validation"]["issues"]


def test_factual_validator_flags_non_canonical_pricing_metric() -> None:
    validation = FactualValidator.validate_text(
        text="The registration rate is ₹26,616 in this locality.",
        allowed_numbers={"26616"},
        canonical_metric_name="asking_price",
    )

    assert validation["passed"] is False
    assert "non_canonical_pricing_metric_detected" in validation["issues"]


def test_factual_validator_allows_negative_decimal_when_grounded() -> None:
    validation = FactualValidator.validate_text(
        text="The grounded change percent is -6.11.",
        allowed_numbers={"-6.11"},
        canonical_metric_name="asking_price",
    )

    assert validation["passed"] is True
    assert validation["unreconciled_numbers"] == []


def test_factual_validator_flags_forbidden_property_type_claim() -> None:
    validation = FactualValidator.validate_text(
        text="Apartment is the best property type here.",
        allowed_numbers=set(),
        canonical_metric_name="asking_price",
    )

    assert validation["passed"] is False
    assert "forbidden_claims_detected" in validation["issues"]


def test_factual_validator_warns_for_stale_source_data() -> None:
    draft = {
        "metadata": {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Explore resale properties in Andheri West, Mumbai on Square Yards.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse resale listings in Andheri West, Mumbai.",
        },
        "sections": [
            {
                "id": "hero_intro",
                "title": "Resale Property Overview",
                "body": "Andheri West has 2,039 resale listings visible on Square Yards.",
            }
        ],
        "faqs": [],
        "content_plan": {
            "generated_at": "2026-03-20T10:00:00+00:00",
            "metadata_plan": {
                "canonical_pricing_metric": {
                    "metric_name": "asking_price",
                    "label": "asking price",
                    "value": 40238,
                }
            },
            "data_context": {
                "pricing_summary": {"asking_price": 40238},
                "listing_summary": {"sale_count": 2039},
            },
            "source_meta": {
                "raw_source_meta": {
                    "last_modified_date": "2026-01-01",
                }
            },
            "keyword_strategy": {
                "primary_keyword": {"keyword": "flats for sale in andheri west mumbai"},
                "exact_match_keywords": [],
            },
        },
    }

    report = FactualValidator.validate_draft(draft)

    assert report["passed"] is True
    assert report["quality_report"]["approval_status"] == "warning"
    assert "stale_source_data_detected" in report["quality_report"]["warning_reasons"]
    assert report["quality_report"]["stale_data_check"]["severity"] == "medium"
    assert report["quality_report"]["stale_data_check"]["blocking"] is False


def test_factual_validator_fails_for_severely_stale_source_data() -> None:
    draft = {
        "metadata": {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Explore resale properties in Andheri West, Mumbai on Square Yards.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse resale listings in Andheri West, Mumbai.",
        },
        "sections": [
            {
                "id": "hero_intro",
                "title": "Resale Property Overview",
                "body": "Andheri West has 2,039 resale listings visible on Square Yards.",
            }
        ],
        "faqs": [],
        "content_plan": {
            "generated_at": "2026-06-20T10:00:00+00:00",
            "metadata_plan": {
                "canonical_pricing_metric": {
                    "metric_name": "asking_price",
                    "label": "asking price",
                    "value": 40238,
                }
            },
            "data_context": {
                "pricing_summary": {"asking_price": 40238},
                "listing_summary": {"sale_count": 2039},
            },
            "source_meta": {
                "raw_source_meta": {
                    "last_modified_date": "2026-01-01",
                }
            },
            "keyword_strategy": {
                "primary_keyword": {"keyword": "flats for sale in andheri west mumbai"},
                "exact_match_keywords": [],
            },
        },
    }

    report = FactualValidator.validate_draft(draft)

    assert report["passed"] is True
    assert report["quality_report"]["approval_status"] == "fail"
    assert "severely_stale_source_data_detected" in report["quality_report"]["warning_reasons"]
    assert report["quality_report"]["stale_data_check"]["blocking"] is True


def test_factual_validator_warns_for_keyword_stuffing() -> None:
    stuffed = "flats for sale in andheri west mumbai " * 5

    draft = {
        "metadata": {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": stuffed.strip(),
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse resale listings in Andheri West, Mumbai.",
        },
        "sections": [
            {
                "id": "hero_intro",
                "title": "Resale Property Overview",
                "body": "Andheri West has 2,039 resale listings visible on Square Yards.",
            }
        ],
        "faqs": [],
        "content_plan": {
            "generated_at": "2026-03-09T10:00:00+00:00",
            "metadata_plan": {
                "canonical_pricing_metric": {
                    "metric_name": "asking_price",
                    "label": "asking price",
                    "value": 40238,
                }
            },
            "data_context": {
                "pricing_summary": {"asking_price": 40238},
                "listing_summary": {"sale_count": 2039},
            },
            "source_meta": {
                "raw_source_meta": {
                    "last_modified_date": "2026-03-02",
                }
            },
            "keyword_strategy": {
                "primary_keyword": {"keyword": "flats for sale in andheri west mumbai"},
                "exact_match_keywords": [{"keyword": "flats for sale in andheri west mumbai"}],
            },
        },
    }

    report = FactualValidator.validate_draft(draft)

    assert report["passed"] is True
    assert report["quality_report"]["approval_status"] in {"warning", "fail"}
    assert "primary_keyword_stuffing_detected" in report["quality_report"]["warning_reasons"]
    assert report["quality_report"]["keyword_stuffing_check"]["primary_keyword_count"] >= 5


def test_factual_validator_warns_for_repeated_section_patterns() -> None:
    repeated_body = (
        "This page provides grounded resale property data for the location including asking price, "
        "inventory mix, and nearby locality references."
    )

    draft = {
        "metadata": {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Explore resale properties in Andheri West, Mumbai on Square Yards.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse resale listings in Andheri West, Mumbai.",
        },
        "sections": [
            {
                "id": "hero_intro",
                "title": "Hero",
                "body": repeated_body,
            },
            {
                "id": "market_snapshot",
                "title": "Market Snapshot",
                "body": repeated_body,
            },
        ],
        "faqs": [],
        "content_plan": {
            "generated_at": "2026-03-09T10:00:00+00:00",
            "metadata_plan": {
                "canonical_pricing_metric": {
                    "metric_name": "asking_price",
                    "label": "asking price",
                    "value": 40238,
                }
            },
            "data_context": {
                "pricing_summary": {"asking_price": 40238},
                "listing_summary": {"sale_count": 2039},
            },
            "source_meta": {
                "raw_source_meta": {
                    "last_modified_date": "2026-03-02",
                }
            },
            "keyword_strategy": {
                "primary_keyword": {"keyword": "flats for sale in andheri west mumbai"},
                "exact_match_keywords": [],
            },
        },
    }

    report = FactualValidator.validate_draft(draft)

    assert report["passed"] is True
    assert report["quality_report"]["approval_status"] == "warning"
    assert "repeated_section_body_detected" in report["quality_report"]["warning_reasons"]
    assert report["quality_report"]["repetition_check"]["repeated_section_ids"] == [
        "market_snapshot"
    ]


def test_factual_validator_warns_for_duplicate_faq_answers() -> None:
    draft = {
        "metadata": {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Explore resale properties in Andheri West, Mumbai on Square Yards.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse resale listings in Andheri West, Mumbai.",
        },
        "sections": [
            {
                "id": "hero_intro",
                "title": "Hero Intro",
                "body": "Andheri West has 2,039 resale listings visible on Square Yards.",
            }
        ],
        "faqs": [
            {
                "question": "What is the asking price signal?",
                "answer": "The asking price signal is ₹40,238 based on the current page inputs.",
            },
            {
                "question": "How are rates represented on this page?",
                "answer": "The asking price signal is ₹40,238 based on the current page inputs.",
            },
        ],
        "content_plan": {
            "generated_at": "2026-03-09T10:00:00+00:00",
            "metadata_plan": {
                "canonical_pricing_metric": {
                    "metric_name": "asking_price",
                    "label": "asking price",
                    "value": 40238,
                }
            },
            "data_context": {
                "pricing_summary": {"asking_price": 40238},
                "listing_summary": {"sale_count": 2039},
            },
            "source_meta": {
                "raw_source_meta": {
                    "last_modified_date": "2026-03-02",
                }
            },
            "keyword_strategy": {
                "primary_keyword": {"keyword": "flats for sale in andheri west mumbai"},
                "exact_match_keywords": [],
            },
        },
    }

    report = FactualValidator.validate_draft(draft)

    assert report["passed"] is True
    assert "duplicate_faq_answer_detected" in report["quality_report"]["warning_reasons"]
    assert report["quality_report"]["repetition_check"]["duplicate_faq_answer_detected"] is True


def test_factual_validator_warns_for_low_distinct_term_ratio() -> None:
    repetitive_text = (
        "Resale property data in andheri west mumbai includes asking price resale property data "
        "andheri west mumbai resale property data with resale property data repeated across the page."
    )

    draft = {
        "metadata": {
            "title": "Resale Properties in Andheri West, Mumbai | Square Yards",
            "meta_description": "Explore resale properties in Andheri West, Mumbai on Square Yards.",
            "h1": "Resale Properties in Andheri West, Mumbai",
            "intro_snippet": "Browse resale listings in Andheri West, Mumbai.",
        },
        "sections": [
            {"id": "hero_intro", "title": "Hero", "body": repetitive_text},
            {"id": "market_snapshot", "title": "Market", "body": repetitive_text + " extra words"},
        ],
        "faqs": [],
        "content_plan": {
            "generated_at": "2026-03-09T10:00:00+00:00",
            "metadata_plan": {
                "canonical_pricing_metric": {
                    "metric_name": "asking_price",
                    "label": "asking price",
                    "value": 40238,
                }
            },
            "data_context": {
                "pricing_summary": {"asking_price": 40238},
                "listing_summary": {"sale_count": 2039},
            },
            "source_meta": {
                "raw_source_meta": {
                    "last_modified_date": "2026-03-02",
                }
            },
            "keyword_strategy": {
                "primary_keyword": {"keyword": "flats for sale in andheri west mumbai"},
                "exact_match_keywords": [],
            },
        },
    }

    report = FactualValidator.validate_draft(draft)

    assert report["passed"] is True
    assert report["quality_report"]["approval_status"] == "warning"
    assert "low_distinct_term_ratio_detected" in report["quality_report"]["warning_reasons"]
    assert report["quality_report"]["page_uniqueness_check"]["distinct_term_ratio"] < 0.45


def test_factual_validator_builds_warning_taxonomy() -> None:
    taxonomy = FactualValidator._build_warning_taxonomy(
        [
            "primary_keyword_stuffing_detected",
            "stale_source_data_detected",
            "repeated_section_body_detected",
        ]
    )

    assert "keyword" in taxonomy["categorized_warnings"]
    assert "freshness" in taxonomy["categorized_warnings"]
    assert "repetition" in taxonomy["categorized_warnings"]
    assert taxonomy["severity_counts"]["high"] >= 1
    assert taxonomy["severity_counts"]["medium"] >= 1


def test_factual_validator_preserves_natural_grounded_descriptive_copy() -> None:
    text = (
        "The current asking price signal for resale properties in Andheri West, Mumbai is ₹40,238. "
        "This page also reflects 2,039 resale listings and gives buyers a grounded view of available inventory."
    )

    validation = FactualValidator.validate_text(
        text=text,
        allowed_numbers={"40238", "2039"},
        canonical_metric_name="asking_price",
    )

    assert validation["passed"] is True
    assert validation["issues"] == []