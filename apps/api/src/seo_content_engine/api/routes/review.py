from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from seo_content_engine.schemas.requests import (
    ReviewDraftRegenerateRequest,
    ReviewMetadataUpdateRequest,
    ReviewSectionRegenerateRequest,
    ReviewSectionUpdateRequest,
    ReviewSessionCreateRequest,
    ReviewSessionExportRequest,
    ReviewVersionRestoreRequest,
)
from seo_content_engine.schemas.responses import (
    ReviewExportResponse,
    ReviewMutationResponse,
    ReviewSessionResponse,
)
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
            primary_keyword_overrides=payload.primary_keyword_overrides,
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


@router.post("/session/regenerate", response_model=ReviewMutationResponse)
def regenerate_review_draft(payload: ReviewDraftRegenerateRequest) -> ReviewMutationResponse:
    try:
        review_session, mutation_summary = ReviewWorkbenchService.regenerate_draft(
            session_id=payload.session_id,
            persist_session=payload.persist_session,
            action_label=payload.action_label,
        )
        return ReviewMutationResponse(
            success=True,
            message="Review draft regenerated successfully",
            review_session=review_session,
            mutation_summary=mutation_summary,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/section/regenerate", response_model=ReviewMutationResponse)
def regenerate_review_section(payload: ReviewSectionRegenerateRequest) -> ReviewMutationResponse:
    try:
        review_session, mutation_summary = ReviewWorkbenchService.regenerate_section(
            session_id=payload.session_id,
            section_id=payload.section_id,
            persist_session=payload.persist_session,
            action_label=payload.action_label,
        )
        return ReviewMutationResponse(
            success=True,
            message="Review section regenerated successfully",
            review_session=review_session,
            mutation_summary=mutation_summary,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/section/update", response_model=ReviewMutationResponse)
def update_review_section(payload: ReviewSectionUpdateRequest) -> ReviewMutationResponse:
    try:
        review_session, mutation_summary = ReviewWorkbenchService.update_section_body(
            session_id=payload.session_id,
            section_id=payload.section_id,
            body=payload.body,
            persist_session=payload.persist_session,
            action_label=payload.action_label,
        )
        return ReviewMutationResponse(
            success=True,
            message="Review section updated successfully",
            review_session=review_session,
            mutation_summary=mutation_summary,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/metadata/update", response_model=ReviewMutationResponse)
def update_review_metadata(payload: ReviewMetadataUpdateRequest) -> ReviewMutationResponse:
    try:
        review_session, mutation_summary = ReviewWorkbenchService.update_metadata(
            session_id=payload.session_id,
            title=payload.title,
            meta_description=payload.meta_description,
            h1=payload.h1,
            intro_snippet=payload.intro_snippet,
            persist_session=payload.persist_session,
            action_label=payload.action_label,
        )
        return ReviewMutationResponse(
            success=True,
            message="Review metadata updated successfully",
            review_session=review_session,
            mutation_summary=mutation_summary,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/version/restore", response_model=ReviewMutationResponse)
def restore_review_version(payload: ReviewVersionRestoreRequest) -> ReviewMutationResponse:
    try:
        review_session, mutation_summary = ReviewWorkbenchService.restore_version(
            session_id=payload.session_id,
            version_id=payload.version_id,
            persist_session=payload.persist_session,
            action_label=payload.action_label,
        )
        return ReviewMutationResponse(
            success=True,
            message="Review version restored successfully",
            review_session=review_session,
            mutation_summary=mutation_summary,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/session/export", response_model=ReviewExportResponse)
def export_review_session(payload: ReviewSessionExportRequest) -> ReviewExportResponse:
    try:
        review_session, artifact_paths = ReviewWorkbenchService.export_session(
            session_id=payload.session_id,
            export_formats=payload.export_formats,
            persist_session=payload.persist_session,
        )
        return ReviewExportResponse(
            success=True,
            message="Review session exported successfully",
            review_session=review_session,
            artifact_paths=artifact_paths,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/session/{session_id}/download/{format_name}")
def download_review_export(session_id: str, format_name: str):
    try:
        export_format = format_name.lower().strip()
        if export_format not in {"json", "markdown", "docx", "html"}:
            raise ValueError(f"Unsupported export format: {format_name}")

        file_path = ReviewWorkbenchService.export_and_get_file_path(
            session_id=session_id,
            export_format=export_format,
        )
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Exported file not found: {file_path}")

        media_type_map = {
            "json": "application/json",
            "markdown": "text/markdown",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "html": "text/html",
        }
        download_name = path_obj.name

        return FileResponse(
            path=str(path_obj),
            media_type=media_type_map[export_format],
            filename=download_name,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc