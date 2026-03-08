from typing import Any
from pydantic import BaseModel


class BlueprintGenerateResponse(BaseModel):
    success: bool
    message: str
    blueprint: dict[str, Any]
    artifact_path: str | None = None