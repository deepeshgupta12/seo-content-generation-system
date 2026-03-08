from fastapi import APIRouter, HTTPException

from seo_content_engine.schemas.requests import KeywordIntelligenceRequest
from seo_content_engine.schemas.responses import KeywordIntelligenceResponse
from seo_content_engine.services.artifact_writer import ArtifactWriter
from seo_content_engine.services.keyword_intelligence_service import KeywordIntelligenceService
from seo_content_engine.services.normalizer import EntityNormalizer
from seo_content_engine.services.source_loader import SourceLoader

router = APIRouter(prefix="/v1/keywords", tags=["keywords"])


@router.post("/intelligence", response_model=KeywordIntelligenceResponse)
def build_keyword_intelligence(payload: KeywordIntelligenceRequest) -> KeywordIntelligenceResponse:
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
        )

        artifact_path = None
        if payload.write_artifact:
            artifact_path = ArtifactWriter.write_keyword_intelligence(keyword_intelligence)

        return KeywordIntelligenceResponse(
            success=True,
            message="Keyword intelligence generated successfully",
            keyword_intelligence=keyword_intelligence,
            artifact_path=artifact_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc