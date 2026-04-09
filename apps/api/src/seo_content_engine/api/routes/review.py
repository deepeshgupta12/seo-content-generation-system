import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

logger = logging.getLogger(__name__)

from seo_content_engine.schemas.requests import (
    ReviewDraftRegenerateRequest,
    ReviewFaqRegenerateRequest,
    ReviewFaqUpdateRequest,
    ReviewMetadataUpdateRequest,
    ReviewSectionRegenerateRequest,
    ReviewSectionUpdateRequest,
    ReviewSessionCreateRequest,
    ReviewSessionExportRequest,
    ReviewSessionRefreshRequest,
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
        build_kwargs = {
            "main_datacenter_json_path": payload.main_datacenter_json_path,
            "property_rates_json_path": payload.property_rates_json_path,
            "listing_type": payload.listing_type,
            "location_name": payload.location_name,
            "language_name": payload.language_name,
            "limit": payload.limit,
            "include_historical": payload.include_historical,
            "persist_session": payload.persist_session,
        }
        if payload.page_url:
            build_kwargs["page_url"] = payload.page_url
        if payload.primary_keyword_overrides:
            build_kwargs["primary_keyword_overrides"] = payload.primary_keyword_overrides

        review_session = ReviewWorkbenchService.build_session(**build_kwargs)
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


# H6 — Streaming generation SSE endpoint


@router.get("/session/{session_id}/stream-regenerate")
def stream_regenerate_session(session_id: str, persist_session: bool = True):
    """H6 — Stream section generation progress via Server-Sent Events.

    Generates all editorial sections for an existing review session in parallel
    (reusing H4's ThreadPoolExecutor), yielding an SSE event for each section as
    it completes.  After all sections are done, generates metadata + FAQs, runs
    validation, updates the stored session, and yields a final ``done`` event.

    Event shapes::

        data: {"event": "start", "total_sections": 6, "session_id": "..."}
        data: {"event": "section_complete", "section_id": "market_snapshot", "title": "..."}
        data: {"event": "section_error",   "section_id": "...", "error": "..."}
        data: {"event": "done",            "session_id": "..."}
        data: {"event": "error",           "message": "..."}

    The full updated session is available after the ``done`` event via
    ``GET /v1/review/session/{session_id}``.
    """
    from seo_content_engine.services.content_plan_builder import ContentPlanBuilder
    from seo_content_engine.services.draft_generation_service import DraftGenerationService
    from seo_content_engine.services.factual_validator import FactualValidator
    from seo_content_engine.services.markdown_renderer import MarkdownRenderer
    from seo_content_engine.services.openai_client import OpenAIClient
    from seo_content_engine.services.prompt_builder import PromptBuilder
    from seo_content_engine.services.review_session_store import ReviewSessionStore
    from seo_content_engine.services.review_workbench_service import ReviewWorkbenchService
    from seo_content_engine.services.table_renderer import TableRenderer
    from copy import deepcopy

    def _sse(event_data: dict) -> str:
        return f"data: {json.dumps(event_data)}\n\n"

    def generate():  # synchronous generator for StreamingResponse
        try:
            session = ReviewSessionStore.load_session(session_id)
            content_plan = session.get("content_plan") or {}

            generative_sections = [
                s for s in content_plan.get("section_plan", [])
                if s.get("render_type") in {"generative", "hybrid"} and s.get("id") != "faq_section"
            ]

            yield _sse({
                "event": "start",
                "session_id": session_id,
                "total_sections": len(generative_sections),
            })

            client = OpenAIClient()
            generated_sections: list[dict] = []

            def _generate_one(section_entry: dict) -> dict:
                system_prompt, user_prompt = PromptBuilder.section_prompt_single(
                    content_plan, section_entry
                )
                result = client.generate_json(system_prompt, user_prompt)
                if isinstance(result, dict) and result.get("body"):
                    result.setdefault("id", section_entry.get("id"))
                    result.setdefault("title", section_entry.get("title", ""))
                    return result
                return {
                    "id": section_entry.get("id"),
                    "title": section_entry.get("title", ""),
                    "body": "",
                    "key_points": [],
                }

            index_map = {s.get("id"): i for i, s in enumerate(generative_sections)}
            result_slots: list[dict | None] = [None] * len(generative_sections)

            max_workers = min(len(generative_sections), 8) if generative_sections else 1
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_entry = {
                    executor.submit(_generate_one, s): s for s in generative_sections
                }
                for future in as_completed(future_to_entry):
                    entry = future_to_entry[future]
                    try:
                        section_result = future.result()
                        section_id_key = str(entry.get("id", ""))
                        idx = index_map.get(section_id_key, len(result_slots) - 1)
                        result_slots[idx] = section_result
                        yield _sse({
                            "event": "section_complete",
                            "section_id": section_id_key,
                            "title": section_result.get("title", ""),
                        })
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("stream_regenerate: section error for %s: %s", entry.get("id"), exc)
                        yield _sse({
                            "event": "section_error",
                            "section_id": str(entry.get("id", "")),
                            "error": str(exc),
                        })

            generated_sections = [s for s in result_slots if s is not None]

            # Post-process sections
            generated_sections = DraftGenerationService._ensure_planned_sections_present(
                content_plan, generated_sections
            )
            generated_sections = DraftGenerationService._enforce_strict_section_bodies(
                content_plan, generated_sections
            )
            generated_sections = DraftGenerationService._editorialize_sections(
                content_plan, generated_sections
            )

            # Metadata + FAQs
            metadata = DraftGenerationService._generate_metadata(content_plan, client)
            faqs = DraftGenerationService._generate_faqs(content_plan, client)
            faqs = DraftGenerationService._ensure_faq_coverage(content_plan, faqs)
            faqs = DraftGenerationService._editorialize_faqs(content_plan, faqs)
            faqs = DraftGenerationService._tag_featured_snippet_candidates(faqs)

            keyword_intelligence_version = session.get("keyword_intelligence", {}).get("version", "")
            draft = DraftGenerationService._build_base_draft(
                content_plan=content_plan,
                keyword_intelligence_version=keyword_intelligence_version,
                metadata=metadata,
                sections=generated_sections,
                faqs=faqs,
                client=client,
            )

            validation_report = FactualValidator.validate_draft(draft)
            from seo_content_engine.services.factual_validator import FactualValidator as FV
            sanitized = FV.apply_sanitization(draft, validation_report)
            sanitized["repair_passes_used"] = 0
            sanitized["validation_history"] = [
                DraftGenerationService._build_validation_history_entry(
                    "stream_regenerate", 0, validation_report
                )
            ]
            sanitized["pre_block_draft"] = deepcopy(draft)
            sanitized["debug_summary"] = FV.summarize_report(validation_report)
            sanitized["quality_report"] = validation_report.get("quality_report", {})
            sanitized["publish_ready"] = sanitized["quality_report"].get("approval_status") != "fail"
            sanitized["needs_review"] = sanitized["quality_report"].get("approval_status") == "fail"
            sanitized["markdown_draft"] = MarkdownRenderer.render(sanitized)

            updated_session = ReviewWorkbenchService._apply_draft_to_session(
                session, sanitized, action_type="stream_regenerate"
            )
            updated_session["content_plan"] = content_plan
            if persist_session:
                ReviewSessionStore.save_session(updated_session)

            yield _sse({"event": "done", "session_id": session_id})

        except FileNotFoundError as exc:
            yield _sse({"event": "error", "message": f"Session not found: {exc}"})
        except Exception as exc:
            logger.exception("stream_regenerate: unexpected error for session %s", session_id)
            yield _sse({"event": "error", "message": str(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# H5 — Incremental refresh endpoint


@router.post("/session/refresh", response_model=ReviewMutationResponse)
def refresh_review_session(payload: ReviewSessionRefreshRequest) -> ReviewMutationResponse:
    """H5 — Regenerate only sections whose underlying data dependencies changed.

    Uses data fingerprinting to identify stale sections; unchanged sections are
    preserved verbatim.  Faster than a full regenerate when only some data has changed.
    """
    try:
        review_session, mutation_summary = ReviewWorkbenchService.refresh_session(
            session_id=payload.session_id,
            persist_session=payload.persist_session,
            action_label=payload.action_label,
        )
        return ReviewMutationResponse(
            success=True,
            message="Session refreshed successfully (incremental)",
            review_session=review_session,
            mutation_summary=mutation_summary,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# C1 — Standalone FAQ endpoints


@router.post("/faq/regenerate", response_model=ReviewMutationResponse)
def regenerate_review_faqs(payload: ReviewFaqRegenerateRequest) -> ReviewMutationResponse:
    """Regenerate all FAQs for a session without touching sections or metadata."""
    try:
        review_session, mutation_summary = ReviewWorkbenchService.regenerate_faqs(
            session_id=payload.session_id,
            persist_session=payload.persist_session,
            action_label=payload.action_label,
        )
        return ReviewMutationResponse(
            success=True,
            message="FAQs regenerated successfully",
            review_session=review_session,
            mutation_summary=mutation_summary,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/faq/update", response_model=ReviewMutationResponse)
def update_review_faq(payload: ReviewFaqUpdateRequest) -> ReviewMutationResponse:
    """Update the answer for a single FAQ identified by its question text."""
    try:
        review_session, mutation_summary = ReviewWorkbenchService.update_faq(
            session_id=payload.session_id,
            question=payload.question,
            answer=payload.answer,
            persist_session=payload.persist_session,
            action_label=payload.action_label,
        )
        return ReviewMutationResponse(
            success=True,
            message="FAQ updated successfully",
            review_session=review_session,
            mutation_summary=mutation_summary,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc