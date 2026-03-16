from typing import Any

from pydantic import BaseModel


class BlueprintGenerateResponse(BaseModel):
    success: bool
    message: str
    blueprint: dict[str, Any]
    artifact_path: str | None = None


class KeywordIntelligenceResponse(BaseModel):
    success: bool
    message: str
    keyword_intelligence: dict[str, Any]
    artifact_path: str | None = None


class ContentPlanGenerateResponse(BaseModel):
    success: bool
    message: str
    content_plan: dict[str, Any]
    artifact_path: str | None = None


class DraftGenerateResponse(BaseModel):
    success: bool
    message: str
    draft: dict[str, Any]
    artifact_paths: dict[str, str] | None = None


class DraftPublishResponse(BaseModel):
    success: bool
    message: str
    artifact_paths: dict[str, str]


class ReviewSessionResponse(BaseModel):
    success: bool
    message: str
    review_session: dict[str, Any]


class ReviewMutationResponse(BaseModel):
    success: bool
    message: str
    review_session: dict[str, Any]
    mutation_summary: dict[str, Any]


class ReviewExportResponse(BaseModel):
    success: bool
    message: str
    review_session: dict[str, Any]
    artifact_paths: dict[str, str]