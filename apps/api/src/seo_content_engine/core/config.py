from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Square Yards SEO Content Engine"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    artifacts_dir: str = "data/artifacts"
    review_sessions_dir: str = "data/review_sessions"

    dataforseo_base_url: str = "https://api.dataforseo.com/v3"
    dataforseo_login: str = ""
    dataforseo_password: str = ""
    dataforseo_default_location_name: str = "India"
    dataforseo_default_language_name: str = "English"
    dataforseo_default_limit: int = 50
    dataforseo_related_depth: int = 2
    dataforseo_timeout_seconds: float = 45.0
    dataforseo_historical_keywords_limit: int = 50

    dataforseo_serp_seed_limit: int = 5
    dataforseo_serp_top_results_limit: int = 10
    dataforseo_competitor_domain_limit: int = 3
    dataforseo_keywords_for_site_limit: int = 30
    dataforseo_keyword_overview_limit: int = 100
    dataforseo_google_ads_limit: int = 100

    keyword_secondary_max_count: int = 10
    keyword_long_tail_max_count: int = 12
    keyword_bhk_max_count: int = 10
    keyword_price_max_count: int = 10
    keyword_ready_to_move_max_count: int = 8
    keyword_faq_max_count: int = 12
    keyword_metadata_max_count: int = 8
    keyword_metadata_exact_match_max_count: int = 5
    keyword_competitor_max_count: int = 12
    keyword_informational_max_count: int = 12
    keyword_serp_validated_max_count: int = 12

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: float = 90.0
    openai_temperature: float = 0.2

    squareyards_base_url: str = "https://www.squareyards.com"

    draft_repair_max_passes: int = 2
    block_artifact_write_on_review: bool = False
    draft_default_export_formats: list[str] = ["json", "markdown", "docx", "html"]

    editorial_min_section_words: int = 80
    editorial_min_faq_words: int = 40
    editorial_force_safe_sections: list[str] = ["property_rates_ai_signals"]
    editorial_robotic_phrase_threshold: int = 2
    editorial_generic_filler_threshold: int = 2

    @field_validator("draft_default_export_formats")
    @classmethod
    def validate_draft_default_export_formats(cls, value: list[str]) -> list[str]:
        allowed = {"json", "markdown", "docx", "html"}
        if not value:
            return ["json", "markdown", "docx", "html"]

        normalized: list[str] = []
        seen: set[str] = set()

        for item in value:
            lowered = str(item).strip().lower()
            if lowered not in allowed:
                raise ValueError(
                    "draft_default_export_formats supports only: json, markdown, docx, html"
                )
            if lowered in seen:
                continue
            seen.add(lowered)
            normalized.append(lowered)

        return normalized

    @field_validator("editorial_force_safe_sections")
    @classmethod
    def validate_editorial_force_safe_sections(cls, value: list[str]) -> list[str]:
        if not value:
            return ["property_rates_ai_signals"]

        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            cleaned = str(item).strip()
            if not cleaned:
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)

        return normalized or ["property_rates_ai_signals"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()