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
    assert report["quality_report"]["approval_status"] == "warning"
    assert "primary_keyword_stuffing_detected" in report["quality_report"]["warning_reasons"]