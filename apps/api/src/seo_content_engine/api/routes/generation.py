from fastapi import APIRouter, HTTPException

from seo_content_engine.schemas.requests import BlueprintGenerateRequest
from seo_content_engine.schemas.responses import BlueprintGenerateResponse
from seo_content_engine.services.artifact_writer import ArtifactWriter
from seo_content_engine.services.blueprint_builder import BlueprintBuilder
from seo_content_engine.services.normalizer import EntityNormalizer
from seo_content_engine.services.source_loader import SourceLoader

router = APIRouter(prefix="/v1/generate", tags=["generation"])


@router.post("/blueprint", response_model=BlueprintGenerateResponse)
def generate_blueprint(payload: BlueprintGenerateRequest) -> BlueprintGenerateResponse:
    try:
        normalized = EntityNormalizer.normalize_from_paths(
            main_datacenter_json_path=payload.main_datacenter_json_path,
            property_rates_json_path=payload.property_rates_json_path,
            listing_type=payload.listing_type,
            source_loader=SourceLoader,
        )
        blueprint = BlueprintBuilder.build(normalized)

        artifact_path = None
        if payload.write_artifact:
            artifact_path = ArtifactWriter.write_blueprint(blueprint)

        return BlueprintGenerateResponse(
            success=True,
            message="Blueprint generated successfully",
            blueprint=blueprint,
            artifact_path=artifact_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc