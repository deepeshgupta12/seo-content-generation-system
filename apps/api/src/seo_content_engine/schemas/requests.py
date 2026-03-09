from pydantic import BaseModel, Field

from seo_content_engine.domain.enums import ListingType


class BlueprintGenerateRequest(BaseModel):
    main_datacenter_json_path: str = Field(..., description="Absolute or relative path to main datacenter JSON")
    property_rates_json_path: str = Field(..., description="Absolute or relative path to property rates JSON")
    listing_type: ListingType = ListingType.RESALE
    write_artifact: bool = True


class KeywordIntelligenceRequest(BaseModel):
    main_datacenter_json_path: str = Field(..., description="Absolute or relative path to main datacenter JSON")
    property_rates_json_path: str = Field(..., description="Absolute or relative path to property rates JSON")
    listing_type: ListingType = ListingType.RESALE
    location_name: str | None = Field(default=None, description="Override DataForSEO location_name")
    language_name: str | None = Field(default=None, description="Override DataForSEO language_name")
    limit: int | None = Field(default=None, ge=1, le=100, description="Max keyword rows to request")
    include_historical: bool = True
    write_artifact: bool = True


class ContentPlanGenerateRequest(BaseModel):
    main_datacenter_json_path: str = Field(..., description="Absolute or relative path to main datacenter JSON")
    property_rates_json_path: str = Field(..., description="Absolute or relative path to property rates JSON")
    listing_type: ListingType = ListingType.RESALE
    location_name: str | None = Field(default=None, description="Override DataForSEO location_name")
    language_name: str | None = Field(default=None, description="Override DataForSEO language_name")
    limit: int | None = Field(default=None, ge=1, le=100, description="Max keyword rows to request")
    include_historical: bool = True
    write_artifact: bool = True


class DraftGenerateRequest(BaseModel):
    main_datacenter_json_path: str = Field(..., description="Absolute or relative path to main datacenter JSON")
    property_rates_json_path: str = Field(..., description="Absolute or relative path to property rates JSON")
    listing_type: ListingType = ListingType.RESALE
    location_name: str | None = Field(default=None, description="Override DataForSEO location_name")
    language_name: str | None = Field(default=None, description="Override DataForSEO language_name")
    limit: int | None = Field(default=None, ge=1, le=100, description="Max keyword rows to request")
    include_historical: bool = True
    write_artifact: bool = False


class DraftPublishRequest(BaseModel):
    draft: dict


class ReviewSessionCreateRequest(BaseModel):
    main_datacenter_json_path: str = Field(..., description="Absolute or relative path to main datacenter JSON")
    property_rates_json_path: str = Field(..., description="Absolute or relative path to property rates JSON")
    listing_type: ListingType = ListingType.RESALE
    location_name: str | None = Field(default=None, description="Override DataForSEO location_name")
    language_name: str | None = Field(default=None, description="Override DataForSEO language_name")
    limit: int | None = Field(default=None, ge=1, le=100, description="Max keyword rows to request")
    include_historical: bool = True
    persist_session: bool = True


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