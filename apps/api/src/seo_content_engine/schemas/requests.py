from pydantic import BaseModel, Field
from seo_content_engine.domain.enums import ListingType


class BlueprintGenerateRequest(BaseModel):
    main_datacenter_json_path: str = Field(..., description="Absolute or relative path to main datacenter JSON")
    property_rates_json_path: str = Field(..., description="Absolute or relative path to property rates JSON")
    listing_type: ListingType = ListingType.RESALE
    write_artifact: bool = True