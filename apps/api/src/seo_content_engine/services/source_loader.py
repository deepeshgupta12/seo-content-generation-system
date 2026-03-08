from __future__ import annotations

import json
from pathlib import Path


class SourceLoader:
    @staticmethod
    def load_json(path_str: str) -> dict:
        path = Path(path_str).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {path}")
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)