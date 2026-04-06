from __future__ import annotations

import json
from typing import Any

import httpx

from seo_content_engine.core.config import settings


class OpenAIClient:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in .env.")

        self.base_url = settings.openai_base_url.rstrip("/")
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.timeout = settings.openai_timeout_seconds
        self.temperature = settings.openai_temperature

    @staticmethod
    def _extract_json_object(content: str) -> dict[str, Any]:
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = content[start : end + 1]
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed

        raise ValueError("Model response did not contain a valid JSON object.")

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Model returned an empty response.")

        return self._extract_json_object(content)