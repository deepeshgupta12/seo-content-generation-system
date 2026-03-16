from fastapi import APIRouter, HTTPException

from seo_content_engine.schemas.requests import DraftPublishRequest
from seo_content_engine.schemas.responses import DraftPublishResponse
from seo_content_engine.services.draft_publish_service import DraftPublishService

router = APIRouter(prefix="/v1/draft", tags=["draft"])


@router.post("/publish", response_model=DraftPublishResponse)
def publish_draft(payload: DraftPublishRequest) -> DraftPublishResponse:
    try:
        artifact_paths = DraftPublishService.publish_draft(
            draft=payload.draft,
            export_formats=payload.export_formats,
        )
        return DraftPublishResponse(
            success=True,
            message="Draft artifacts published successfully",
            artifact_paths=artifact_paths,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc