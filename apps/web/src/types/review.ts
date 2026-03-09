export type ListingType = "resale";

export type ReviewSessionCreateRequest = {
  main_datacenter_json_path: string;
  property_rates_json_path: string;
  listing_type: ListingType;
  location_name?: string | null;
  language_name?: string | null;
  limit?: number | null;
  include_historical?: boolean;
  persist_session?: boolean;
};

export type ReviewDraftRegenerateRequest = {
  session_id: string;
  persist_session?: boolean;
  action_label?: string;
};

export type ReviewSectionRegenerateRequest = {
  session_id: string;
  section_id: string;
  persist_session?: boolean;
  action_label?: string;
};

export type ReviewSectionUpdateRequest = {
  session_id: string;
  section_id: string;
  body: string;
  persist_session?: boolean;
  action_label?: string;
};

export type ReviewMetadataUpdateRequest = {
  session_id: string;
  title: string;
  meta_description: string;
  h1: string;
  intro_snippet: string;
  persist_session?: boolean;
  action_label?: string;
};

export type ReviewVersionRestoreRequest = {
  session_id: string;
  version_id: string;
  persist_session?: boolean;
  action_label?: string;
};

export type ReviewTable = {
  id?: string;
  title?: string;
  summary?: string;
  columns?: string[];
  rows?: Array<Record<string, unknown>>;
};

export type ReviewFaq = {
  question?: string;
  answer?: string;
  validation_passed?: boolean;
  validation_issues?: string[];
};

export type ReviewSection = {
  id?: string;
  title?: string;
  body?: string;
  validation_passed?: boolean;
  validation_issues?: string[];
};

export type ReviewSectionReview = {
  id?: string;
  title?: string;
  body?: string;
  validation?: Record<string, unknown>;
  quality?: Record<string, unknown>;
  validation_passed?: boolean;
  validation_issues?: string[];
};

export type ReviewVersionHistoryItem = {
  version_id?: string;
  version_number?: number;
  action_type?: string;
  created_at?: string;
  publish_ready?: boolean;
  approval_status?: string;
  overall_quality_score?: number;
};

export type ReviewDraft = {
  metadata?: {
    title?: string;
    meta_description?: string;
    h1?: string;
    intro_snippet?: string;
  };
  sections?: ReviewSection[];
  tables?: ReviewTable[];
  faqs?: ReviewFaq[];
  markdown_draft?: string;
  publish_ready?: boolean;
  quality_report?: {
    approval_status?: string;
    overall_quality_score?: number;
    warning_reasons?: string[];
  };
  debug_summary?: {
    blocked?: boolean;
    approval_status?: string;
    blocking_reasons?: string[];
  };
};

export type ReviewSession = {
  session_id: string;
  created_at?: string;
  updated_at?: string;
  entity?: {
    entity_name?: string;
    city_name?: string;
    page_type?: string;
    listing_type?: string;
  };
  source_preview?: Record<string, unknown>;
  keyword_preview?: Record<string, unknown>;
  normalized?: Record<string, unknown>;
  keyword_intelligence?: Record<string, unknown>;
  content_plan?: Record<string, unknown>;
  draft?: ReviewDraft;
  validation_report?: Record<string, unknown>;
  quality_report?: {
    approval_status?: string;
    overall_quality_score?: number;
    warning_reasons?: string[];
  };
  section_review?: ReviewSectionReview[];
  version_history?: ReviewVersionHistoryItem[];
  latest_version_id?: string;
};

export type ReviewSessionResponse = {
  success: boolean;
  message: string;
  review_session: ReviewSession;
};

export type ReviewMutationResponse = {
  success: boolean;
  message: string;
  review_session: ReviewSession;
  mutation_summary: Record<string, unknown>;
};