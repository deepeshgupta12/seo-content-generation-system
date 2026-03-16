from typing import Literal

from pydantic import BaseModel, Field, field_validator

from seo_content_engine.domain.enums import ListingType

ExportFormat = Literal["json", "markdown", "docx", "html"]


class BlueprintGenerateRequest(BaseModel):
    main_datacenter_json_path: str = Field(
        ..., description="Absolute or relative path to main datacenter JSON"
    )
    property_rates_json_path: str = Field(
        ..., description="Absolute or relative path to property rates JSON"
    )
    listing_type: ListingType = ListingType.RESALE
    write_artifact: bool = True


class KeywordIntelligenceRequest(BaseModel):
    main_datacenter_json_path: str = Field(
        ..., description="Absolute or relative path to main datacenter JSON"
    )
    property_rates_json_path: str = Field(
        ..., description="Absolute or relative path to property rates JSON"
    )
    listing_type: ListingType = ListingType.RESALE
    location_name: str | None = Field(
        default=None, description="Override DataForSEO location_name"
    )
    language_name: str | None = Field(
        default=None, description="Override DataForSEO language_name"
    )
    limit: int | None = Field(
        default=None, ge=1, le=100, description="Max keyword rows to request"
    )
    include_historical: bool = True
    write_artifact: bool = True


class ContentPlanGenerateRequest(BaseModel):
    main_datacenter_json_path: str = Field(
        ..., description="Absolute or relative path to main datacenter JSON"
    )
    property_rates_json_path: str = Field(
        ..., description="Absolute or relative path to property rates JSON"
    )
    listing_type: ListingType = ListingType.RESALE
    location_name: str | None = Field(
        default=None, description="Override DataForSEO location_name"
    )
    language_name: str | None = Field(
        default=None, description="Override DataForSEO language_name"
    )
    limit: int | None = Field(
        default=None, ge=1, le=100, description="Max keyword rows to request"
    )
    include_historical: bool = True
    write_artifact: bool = True


class DraftGenerateRequest(BaseModel):
    main_datacenter_json_path: str = Field(
        ..., description="Absolute or relative path to main datacenter JSON"
    )
    property_rates_json_path: str = Field(
        ..., description="Absolute or relative path to property rates JSON"
    )
    listing_type: ListingType = ListingType.RESALE
    location_name: str | None = Field(
        default=None, description="Override DataForSEO location_name"
    )
    language_name: str | None = Field(
        default=None, description="Override DataForSEO language_name"
    )
    limit: int | None = Field(
        default=None, ge=1, le=100, description="Max keyword rows to request"
    )
    include_historical: bool = True
    write_artifact: bool = False


class DraftPublishRequest(BaseModel):
    draft: dict
    export_formats: list[ExportFormat] = Field(
        default_factory=lambda: ["json", "markdown", "docx", "html"],
        description="Artifacts to write for the draft",
    )

    @field_validator("export_formats")
    @classmethod
    def validate_export_formats(cls, value: list[ExportFormat]) -> list[ExportFormat]:
        if not value:
            raise ValueError("At least one export format must be provided.")
        deduped: list[ExportFormat] = []
        seen: set[str] = set()
        for item in value:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped


class ReviewSessionCreateRequest(BaseModel):
    main_datacenter_json_path: str = Field(
        ..., description="Absolute or relative path to main datacenter JSON"
    )
    property_rates_json_path: str = Field(
        ..., description="Absolute or relative path to property rates JSON"
    )
    listing_type: ListingType = ListingType.RESALE
    location_name: str | None = Field(
        default=None, description="Override DataForSEO location_name"
    )
    language_name: str | None = Field(
        default=None, description="Override DataForSEO language_name"
    )
    limit: int | None = Field(
        default=None, ge=1, le=100, description="Max keyword rows to request"
    )
    include_historical: bool = True
    persist_session: bool = True
    primary_keyword_override: str | None = Field(
        default=None,
        description="Optional custom primary keyword override to use for this review session",
    )


class ReviewDraftRegenerateRequest(BaseModel):
    session_id: str = Field(..., description="Review session identifier")
    persist_session: bool = True
    action_label: str = Field(
        default="full_regenerate",
        description="Mutation label to record in version history",
    )


class ReviewSectionRegenerateRequest(BaseModel):
    session_id: str = Field(..., description="Review session identifier")
    section_id: str = Field(..., description="Section id to regenerate")
    persist_session: bool = True
    action_label: str = Field(
        default="section_regenerate",
        description="Mutation label to record in version history",
    )


class ReviewSectionUpdateRequest(BaseModel):
    session_id: str = Field(..., description="Review session identifier")
    section_id: str = Field(..., description="Section id to update")
    body: str = Field(..., min_length=1, description="Edited section body")
    persist_session: bool = True
    action_label: str = Field(
        default="section_edit",
        description="Mutation label to record in version history",
    )


class ReviewMetadataUpdateRequest(BaseModel):
    session_id: str = Field(..., description="Review session identifier")
    title: str = Field(..., min_length=1)
    meta_description: str = Field(..., min_length=1)
    h1: str = Field(..., min_length=1)
    intro_snippet: str = Field(..., min_length=1)
    persist_session: bool = True
    action_label: str = Field(
        default="metadata_edit",
        description="Mutation label to record in version history",
    )


class ReviewVersionRestoreRequest(BaseModel):
    session_id: str = Field(..., description="Review session identifier")
    version_id: str = Field(..., description="Version id to restore")
    persist_session: bool = True
    action_label: str = Field(
        default="restore_version",
        description="Mutation label to record in version history",
    )


class ReviewSessionExportRequest(BaseModel):
    session_id: str = Field(..., description="Review session identifier")
    export_formats: list[ExportFormat] = Field(
        default_factory=lambda: ["json", "markdown", "docx", "html"],
        description="Artifacts to export for the current session draft",
    )
    persist_session: bool = True

    @field_validator("export_formats")
    @classmethod
    def validate_export_formats(cls, value: list[ExportFormat]) -> list[ExportFormat]:
        if not value:
            raise ValueError("At least one export format must be provided.")
        deduped: list[ExportFormat] = []
        seen: set[str] = set()
        for item in value:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped