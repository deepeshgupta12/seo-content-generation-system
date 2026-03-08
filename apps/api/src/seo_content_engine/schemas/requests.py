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