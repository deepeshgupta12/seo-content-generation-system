import { apiRequest } from "./http";
import type {
  ReviewDraftRegenerateRequest,
  ReviewMetadataUpdateRequest,
  ReviewMutationResponse,
  ReviewSectionRegenerateRequest,
  ReviewSectionUpdateRequest,
  ReviewSessionCreateRequest,
  ReviewSessionResponse,
  ReviewVersionRestoreRequest,
} from "../types/review";

export async function createReviewSession(
  payload: ReviewSessionCreateRequest,
): Promise<ReviewSessionResponse> {
  return apiRequest<ReviewSessionResponse>("/v1/review/session", {
    method: "POST",
    body: payload,
  });
}

export async function getReviewSession(
  sessionId: string,
): Promise<ReviewSessionResponse> {
  return apiRequest<ReviewSessionResponse>(`/v1/review/session/${sessionId}`);
}

export async function regenerateDraft(
  payload: ReviewDraftRegenerateRequest,
): Promise<ReviewMutationResponse> {
  return apiRequest<ReviewMutationResponse>("/v1/review/session/regenerate", {
    method: "POST",
    body: payload,
  });
}

export async function regenerateSection(
  payload: ReviewSectionRegenerateRequest,
): Promise<ReviewMutationResponse> {
  return apiRequest<ReviewMutationResponse>("/v1/review/section/regenerate", {
    method: "POST",
    body: payload,
  });
}

export async function updateSection(
  payload: ReviewSectionUpdateRequest,
): Promise<ReviewMutationResponse> {
  return apiRequest<ReviewMutationResponse>("/v1/review/section/update", {
    method: "POST",
    body: payload,
  });
}

export async function updateMetadata(
  payload: ReviewMetadataUpdateRequest,
): Promise<ReviewMutationResponse> {
  return apiRequest<ReviewMutationResponse>("/v1/review/metadata/update", {
    method: "POST",
    body: payload,
  });
}

export async function restoreVersion(
  payload: ReviewVersionRestoreRequest,
): Promise<ReviewMutationResponse> {
  return apiRequest<ReviewMutationResponse>("/v1/review/version/restore", {
    method: "POST",
    body: payload,
  });
}