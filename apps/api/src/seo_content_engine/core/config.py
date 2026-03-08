from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Square Yards SEO Content Engine"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    artifacts_dir: str = "data/artifacts"

    dataforseo_base_url: str = "https://api.dataforseo.com/v3"
    dataforseo_login: str = ""
    dataforseo_password: str = ""
    dataforseo_default_location_name: str = "India"
    dataforseo_default_language_name: str = "English"
    dataforseo_default_limit: int = 50
    dataforseo_related_depth: int = 2
    dataforseo_timeout_seconds: float = 45.0
    dataforseo_historical_keywords_limit: int = 50

    keyword_secondary_max_count: int = 10
    keyword_long_tail_max_count: int = 12
    keyword_bhk_max_count: int = 10
    keyword_price_max_count: int = 10
    keyword_ready_to_move_max_count: int = 8
    keyword_faq_max_count: int = 12
    keyword_metadata_max_count: int = 8

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()