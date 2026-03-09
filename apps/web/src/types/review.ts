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
  draft?: {
    metadata?: {
      title?: string;
      meta_description?: string;
      h1?: string;
      intro_snippet?: string;
    };
    sections?: Array<{
      id?: string;
      title?: string;
      body?: string;
      validation_passed?: boolean;
      validation_issues?: string[];
    }>;
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
  validation_report?: Record<string, unknown>;
  quality_report?: {
    approval_status?: string;
    overall_quality_score?: number;
    warning_reasons?: string[];
  };
  section_review?: Array<{
    id?: string;
    title?: string;
    body?: string;
    validation?: Record<string, unknown>;
    quality?: Record<string, unknown>;
    validation_passed?: boolean;
    validation_issues?: string[];
  }>;
  version_history?: Array<{
    version_id?: string;
    version_number?: number;
    action_type?: string;
    created_at?: string;
    publish_ready?: boolean;
    approval_status?: string;
    overall_quality_score?: number;
  }>;
  latest_version_id?: string;
};

export type ReviewSessionResponse = {
  success: boolean;
  message: string;
  review_session: ReviewSession;
};
