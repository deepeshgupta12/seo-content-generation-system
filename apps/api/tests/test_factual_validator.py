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
            "data_context": {
                "pricing_summary": {"asking_price": 40238},
                "listing_summary": {"sale_count": 2039},
            }
        },
    }

    report = FactualValidator.validate_draft(draft)

    assert report["passed"] is False
    assert "forbidden_claims_detected" in report["metadata_checks"]["meta_description"]["issues"]
    assert "unreconciled_numbers_detected" in report["metadata_checks"]["intro_snippet"]["issues"]