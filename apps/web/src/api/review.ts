import { apiRequest } from "./http";
import type {
  ReviewSessionCreateRequest,
  ReviewSessionResponse,
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
