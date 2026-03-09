from fastapi import APIRouter, HTTPException

from seo_content_engine.schemas.requests import ReviewSessionCreateRequest
from seo_content_engine.schemas.responses import ReviewSessionResponse
from seo_content_engine.services.review_workbench_service import ReviewWorkbenchService

router = APIRouter(prefix="/v1/review", tags=["review"])


@router.post("/session", response_model=ReviewSessionResponse)
def create_review_session(payload: ReviewSessionCreateRequest) -> ReviewSessionResponse:
    try:
        review_session = ReviewWorkbenchService.build_session(
            main_datacenter_json_path=payload.main_datacenter_json_path,
            property_rates_json_path=payload.property_rates_json_path,
            listing_type=payload.listing_type,
            location_name=payload.location_name,
            language_name=payload.language_name,
            limit=payload.limit,
            include_historical=payload.include_historical,
            persist_session=payload.persist_session,
        )
        return ReviewSessionResponse(
            success=True,
            message="Review session created successfully",
            review_session=review_session,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/session/{session_id}", response_model=ReviewSessionResponse)
def get_review_session(session_id: str) -> ReviewSessionResponse:
    try:
        review_session = ReviewWorkbenchService.get_session(session_id)
        return ReviewSessionResponse(
            success=True,
            message="Review session fetched successfully",
            review_session=review_session,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc