from __future__ import annotations

import json
from pathlib import Path

from seo_content_engine.core.config import settings


class ReviewSessionStore:
    @staticmethod
    def _ensure_sessions_dir() -> Path:
        sessions_dir = Path(settings.review_sessions_dir)
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return sessions_dir

    @staticmethod
    def _session_path(session_id: str) -> Path:
        return ReviewSessionStore._ensure_sessions_dir() / f"{session_id}.json"

    @staticmethod
    def save_session(session_payload: dict) -> str:
        session_id = session_payload["session_id"]
        output_path = ReviewSessionStore._session_path(session_id)

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(session_payload, file, ensure_ascii=False, indent=2)

        return str(output_path)

    @staticmethod
    def load_session(session_id: str) -> dict:
        input_path = ReviewSessionStore._session_path(session_id)
        if not input_path.exists():
            raise FileNotFoundError(f"Review session not found: {session_id}")

        with input_path.open("r", encoding="utf-8") as file:
            return json.load(file)