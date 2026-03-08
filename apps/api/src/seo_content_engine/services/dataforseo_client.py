from __future__ import annotations

from typing import Any

import httpx

from seo_content_engine.core.config import settings


class DataForSEOClient:
    def __init__(self) -> None:
        if not settings.dataforseo_login or not settings.dataforseo_password:
            raise ValueError(
                "Missing DataForSEO credentials. Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD in .env."
            )

        self.base_url = settings.dataforseo_base_url.rstrip("/")
        self.auth = (settings.dataforseo_login, settings.dataforseo_password)
        self.timeout = settings.dataforseo_timeout_seconds

    def _post_tasks(self, endpoint: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=self.timeout, auth=self.auth) as client:
            response = client.post(url, json=tasks)
            response.raise_for_status()
            return response.json()

    def get_keyword_suggestions(
        self,
        keyword: str,
        location_name: str,
        language_name: str,
        limit: int,
    ) -> dict[str, Any]:
        payload = [
            {
                "keyword": keyword,
                "location_name": location_name,
                "language_name": language_name,
                "limit": limit,
            }
        ]
        return self._post_tasks("dataforseo_labs/google/keyword_suggestions/live", payload)

    def get_related_keywords(
        self,
        keyword: str,
        location_name: str,
        language_name: str,
        limit: int,
        depth: int,
    ) -> dict[str, Any]:
        payload = [
            {
                "keyword": keyword,
                "location_name": location_name,
                "language_name": language_name,
                "limit": limit,
                "depth": depth,
            }
        ]
        return self._post_tasks("dataforseo_labs/google/related_keywords/live", payload)