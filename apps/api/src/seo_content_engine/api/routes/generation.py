from fastapi import APIRouter, HTTPException

from seo_content_engine.schemas.requests import (
    BlueprintGenerateRequest,
    ContentPlanGenerateRequest,
    DraftGenerateRequest,
    DraftPublishRequest,
)
from seo_content_engine.schemas.responses import (
    BlueprintGenerateResponse,
    ContentPlanGenerateResponse,
    DraftGenerateResponse,
    DraftPublishResponse,
)
from seo_content_engine.services.artifact_writer import ArtifactWriter
from seo_content_engine.services.blueprint_builder import BlueprintBuilder
from seo_content_engine.services.content_plan_builder import ContentPlanBuilder
from seo_content_engine.services.draft_generation_service import DraftGenerationService
from seo_content_engine.services.keyword_intelligence_service import KeywordIntelligenceService
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


@router.post("/content-plan", response_model=ContentPlanGenerateResponse)
def generate_content_plan(payload: ContentPlanGenerateRequest) -> ContentPlanGenerateResponse:
    try:
        normalized = EntityNormalizer.normalize_from_paths(
            main_datacenter_json_path=payload.main_datacenter_json_path,
            property_rates_json_path=payload.property_rates_json_path,
            listing_type=payload.listing_type,
            source_loader=SourceLoader,
        )

        keyword_intelligence = KeywordIntelligenceService.build_keyword_intelligence(
            normalized=normalized,
            location_name=payload.location_name,
            language_name=payload.language_name,
            limit=payload.limit,
            include_historical=payload.include_historical,
        )

        content_plan = ContentPlanBuilder.build(
            normalized=normalized,
            keyword_intelligence=keyword_intelligence,
        )

        artifact_path = None
        if payload.write_artifact:
            artifact_path = ArtifactWriter.write_content_plan(content_plan)

        return ContentPlanGenerateResponse(
            success=True,
            message="Content plan generated successfully",
            content_plan=content_plan,
            artifact_path=artifact_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/draft", response_model=DraftGenerateResponse)
def generate_draft(payload: DraftGenerateRequest) -> DraftGenerateResponse:
    try:
        normalized = EntityNormalizer.normalize_from_paths(
            main_datacenter_json_path=payload.main_datacenter_json_path,
            property_rates_json_path=payload.property_rates_json_path,
            listing_type=payload.listing_type,
            source_loader=SourceLoader,
        )

        keyword_intelligence = KeywordIntelligenceService.build_keyword_intelligence(
            normalized=normalized,
            location_name=payload.location_name,
            language_name=payload.language_name,
            limit=payload.limit,
            include_historical=payload.include_historical,
        )

        draft = DraftGenerationService.generate(
            normalized=normalized,
            keyword_intelligence=keyword_intelligence,
        )

        return DraftGenerateResponse(
            success=True,
            message="Draft generated successfully",
            draft=draft,
            artifact_paths=None,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/draft/publish", response_model=DraftPublishResponse)
def publish_draft(payload: DraftPublishRequest) -> DraftPublishResponse:
    try:
        artifact_paths = ArtifactWriter.write_draft_bundle(payload.draft)
        return DraftPublishResponse(
            success=True,
            message="Draft artifact published successfully",
            artifact_paths=artifact_paths,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc