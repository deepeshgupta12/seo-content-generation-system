import { useEffect, useMemo, useState } from "react";

import {
  createReviewSession,
  exportReviewSession,
  getReviewDownloadUrl,
  getReviewSession,
  regenerateDraft,
  regenerateSection,
  restoreVersion,
  updateMetadata,
  updateSection,
} from "../api/review";

import type {
  ReviewFaq,
  ReviewSectionReview,
  ReviewSession,
  ReviewTable,
  ReviewVersionHistoryItem,
} from "../types/review";

const DEFAULT_MAIN_PATH =
  "/Users/deepeshgupta/Projects/seo-content-generation-system/data/samples/raw/andheri-west-locality.json";

const DEFAULT_RATES_PATH =
  "/Users/deepeshgupta/Projects/seo-content-generation-system/data/samples/raw/andheri-west-property-rates.json";

type ValidationTabKey = "summary" | "metadata" | "sections" | "faqs" | "raw";

function stringifyValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function getRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}

function getArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function getStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => stringifyValue(item)) : [];
}

function parseKeywordOverridesInput(value: string): string[] {
  const parts = value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);

  const deduped: string[] = [];
  const seen = new Set<string>();

  for (const item of parts) {
    const signature = item.toLowerCase();
    if (seen.has(signature)) continue;
    seen.add(signature);
    deduped.push(item);
  }

  return deduped;
}

function ValidationBadge({ passed }: { passed: boolean | undefined }) {
  return (
    <span className={`badge ${passed ? "badge--success" : "badge--warning"}`}>
      {passed ? "passed" : "needs review"}
    </span>
  );
}

function TableSnapshot({ table }: { table: ReviewTable }) {
  const columns = table.columns ?? [];
  const rows = table.rows ?? [];

  return (
    <div className="stack-card">
      <div className="stack-card__header">
        <div>
          <div className="stack-card__title">{table.title ?? "Untitled table"}</div>
          <div className="stack-card__meta">ID: {table.id ?? "—"}</div>
        </div>
        <div className="stack-card__badges">
          <span className="badge">rows: {rows.length}</span>
          <span className="badge">columns: {columns.length}</span>
        </div>
      </div>

      {table.summary ? <div className="stack-card__body">{table.summary}</div> : null}

      {columns.length === 0 ? (
        <div className="empty-state">No table columns available.</div>
      ) : rows.length === 0 ? (
        <div className="empty-state">No table rows available.</div>
      ) : (
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={`${table.id ?? "table"}-${rowIndex}`}>
                  {columns.map((column) => (
                    <td key={`${table.id ?? "table"}-${rowIndex}-${column}`}>
                      {stringifyValue(row[column])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function FaqSnapshot({ faq }: { faq: ReviewFaq }) {
  return (
    <div className="stack-card">
      <div className="stack-card__header">
        <div>
          <div className="stack-card__title">{faq.question ?? "Untitled FAQ"}</div>
        </div>
        <div className="stack-card__badges">
          <ValidationBadge passed={faq.validation_passed} />
        </div>
      </div>

      <div className="stack-card__body">{faq.answer ?? "—"}</div>

      <div className="stack-card__footer">
        <strong>Issues:</strong>{" "}
        {faq.validation_issues?.length ? faq.validation_issues.join(", ") : "none"}
      </div>
    </div>
  );
}

function KeywordChipList({
  items,
  emptyLabel = "—",
}: {
  items: string[];
  emptyLabel?: string;
}) {
  if (!items.length) {
    return <div className="empty-state">{emptyLabel}</div>;
  }

  return (
    <div className="chip-list">
      {items.map((item, index) => (
        <span className="chip" key={`${item}-${index}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

export function ReviewWorkbenchPage() {
  const [mainPath, setMainPath] = useState(DEFAULT_MAIN_PATH);
  const [ratesPath, setRatesPath] = useState(DEFAULT_RATES_PATH);
  const [pageUrl, setPageUrl] = useState("");
  const [includeHistorical, setIncludeHistorical] = useState(true);
  const [persistSession, setPersistSession] = useState(true);
  const [primaryKeywordOverride, setPrimaryKeywordOverride] = useState("");

  const [sessionIdInput, setSessionIdInput] = useState("");
  const [session, setSession] = useState<ReviewSession | null>(null);

  const [isCreating, setIsCreating] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [isRegeneratingDraft, setIsRegeneratingDraft] = useState(false);
  const [isSavingMetadata, setIsSavingMetadata] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [activeSectionActionId, setActiveSectionActionId] = useState<string | null>(null);
  const [activeRestoreVersionId, setActiveRestoreVersionId] = useState<string | null>(null);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [showRawPayload, setShowRawPayload] = useState(false);
  const [activeValidationTab, setActiveValidationTab] =
    useState<ValidationTabKey>("summary");

  const [metadataForm, setMetadataForm] = useState({
    title: "",
    meta_description: "",
    h1: "",
    intro_snippet: "",
  });

  const [sectionDrafts, setSectionDrafts] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!session?.draft?.metadata) return;

    setMetadataForm({
      title: session.draft.metadata.title ?? "",
      meta_description: session.draft.metadata.meta_description ?? "",
      h1: session.draft.metadata.h1 ?? "",
      intro_snippet: session.draft.metadata.intro_snippet ?? "",
    });
  }, [session?.draft?.metadata]);

  useEffect(() => {
    const nextDrafts: Record<string, string> = {};
    for (const section of session?.section_review ?? []) {
      if (section.id) {
        nextDrafts[section.id] = section.body ?? "";
      }
    }
    setSectionDrafts(nextDrafts);
  }, [session?.section_review]);

  const headerSummary = useMemo(() => {
    if (!session) return null;

    return {
      entityName: session.entity?.entity_name ?? "—",
      cityName: session.entity?.city_name ?? "—",
      pageType: session.entity?.page_type ?? "—",
      listingType: session.entity?.listing_type ?? "—",
      approvalStatus: session.quality_report?.approval_status ?? "—",
      qualityScore: session.quality_report?.overall_quality_score ?? "—",
      latestVersionId: session.latest_version_id ?? "—",
      warningCount: session.quality_report?.warning_reasons?.length ?? 0,
      sectionCount: session.section_review?.length ?? 0,
      versionCount: session.version_history?.length ?? 0,
      faqCount: session.draft?.faqs?.length ?? 0,
      tableCount: session.draft?.tables?.length ?? 0,
      primaryKeywordOverrides:
        session.inputs?.primary_keyword_overrides?.length
          ? session.inputs.primary_keyword_overrides.join(", ")
          : "—",
    };
  }, [session]);

  const metadata = session?.draft?.metadata;
  const qualityReport = session?.quality_report;
  const draftQualityReport = session?.draft?.quality_report;
  const debugSummary = session?.draft?.debug_summary;

  const listingSummary = getRecord(session?.source_preview?.listing_summary);
  const pricingSummary = getRecord(session?.source_preview?.pricing_summary);

  const primaryKeyword = getRecord(session?.keyword_preview?.primary_keyword);
  const primaryKeywordOverrides = getStringArray(
    session?.keyword_preview?.primary_keyword_overrides,
  );
  const secondaryKeywords = getArray(session?.keyword_preview?.secondary_keywords);
  const priceKeywords = getArray(session?.keyword_preview?.price_keywords);
  const bhkKeywords = getArray(session?.keyword_preview?.bhk_keywords);
  const faqKeywords = getArray(session?.keyword_preview?.faq_keyword_candidates);
  const competitorKeywords = getArray(session?.keyword_preview?.competitor_keywords);
  const informationalKeywords = getArray(session?.keyword_preview?.informational_keywords);
  const serpValidatedKeywords = getArray(session?.keyword_preview?.serp_validated_keywords);

  const relevantCompetitorKeywords = getArray(
    session?.keyword_preview?.relevant_competitor_keywords,
  );
  const relevantInformationalKeywords = getArray(
    session?.keyword_preview?.relevant_informational_keywords,
  );
  const relevantOverlapKeywords = getArray(
    session?.keyword_preview?.relevant_overlap_keywords,
  );
  const competitorDomains = getStringArray(session?.keyword_preview?.competitor_domains);
  const serpSeedKeywordsChecked = getStringArray(session?.keyword_preview?.serp_seed_keywords_checked);
  const totalIncludedKeywords = stringifyValue(session?.keyword_preview?.total_included_keywords);
  const totalExcludedKeywords = stringifyValue(session?.keyword_preview?.total_excluded_keywords);

  const contentPlanRecord = getRecord(session?.content_plan);
  const competitorIntelligence = getRecord(contentPlanRecord?.competitor_intelligence);
  const competitorBreakdown = getArray(competitorIntelligence?.competitor_breakdown);
  const competitorIntersection = getRecord(competitorIntelligence?.keyword_intersection);
  const competitorSerpOverlap = getRecord(competitorIntelligence?.serp_overlap);
  const competitorInspiration = getRecord(competitorIntelligence?.inspiration_signals);

  const competitorIntersectionKeywords = getArray(
    competitorIntersection?.intersection_keywords,
  );
  const competitorRecommendedSections = getArray(
    competitorInspiration?.recommended_sections,
  );
  const competitorRecommendedFaqThemes = getArray(
    competitorInspiration?.recommended_faq_themes,
  );
  const competitorRecommendedTableThemes = getArray(
    competitorInspiration?.recommended_table_themes,
  );
  const competitorSchemaHierarchyPatterns = getArray(
    competitorInspiration?.recommended_schema_hierarchy_patterns,
  );

  const competitorKeywordLabels = relevantCompetitorKeywords.length
    ? relevantCompetitorKeywords.map((item) => stringifyValue(getRecord(item)?.keyword))
    : competitorKeywords.map((item) => stringifyValue(getRecord(item)?.keyword));

  const informationalKeywordLabels = relevantInformationalKeywords.length
    ? relevantInformationalKeywords.map((item) => stringifyValue(getRecord(item)?.keyword))
    : informationalKeywords.map((item) => stringifyValue(getRecord(item)?.keyword));

  const overlapKeywordLabels = relevantOverlapKeywords.length
    ? relevantOverlapKeywords.map((item) => stringifyValue(getRecord(item)?.keyword))
    : serpValidatedKeywords.map((item) => stringifyValue(getRecord(item)?.keyword));

  const warningReasons = qualityReport?.warning_reasons ?? [];
  const sectionReview = session?.section_review ?? [];
  const versionHistory = session?.version_history ?? [];
  const tables = session?.draft?.tables ?? [];
  const faqs = session?.draft?.faqs ?? [];
  const latestExportPaths = session?.latest_exports?.artifact_paths;

  const validationSummary = getRecord(session?.validation_report);
  const metadataChecks = getRecord(session?.validation_report?.metadata_checks);
  const sectionChecks = getArray(session?.validation_report?.section_checks);
  const faqChecks = getArray(session?.validation_report?.faq_checks);

  function resetBanners() {
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  function applyUpdatedSession(nextSession: ReviewSession, message: string) {
    setSession(nextSession);
    setSessionIdInput(nextSession.session_id ?? "");
    setPrimaryKeywordOverride(
      nextSession.inputs?.primary_keyword_overrides?.join("\n") ?? "",
    );
    setSuccessMessage(message);
    setErrorMessage(null);
  }

  async function handleCreateSession(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsCreating(true);
    resetBanners();

    try {
      const response = await createReviewSession({
        main_datacenter_json_path: mainPath,
        property_rates_json_path: ratesPath,
        listing_type: "resale",
        page_url: pageUrl.trim() || undefined,
        include_historical: includeHistorical,
        persist_session: persistSession,
        primary_keyword_overrides: parseKeywordOverridesInput(primaryKeywordOverride).length
          ? parseKeywordOverridesInput(primaryKeywordOverride)
          : null,
      });

      applyUpdatedSession(response.review_session, response.message);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to create review session";
      setErrorMessage(message);
    } finally {
      setIsCreating(false);
    }
  }

  async function handleFetchSession(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!sessionIdInput.trim()) {
      setErrorMessage("Enter a review session id to fetch an existing session.");
      return;
    }

    setIsFetching(true);
    resetBanners();

    try {
      const response = await getReviewSession(sessionIdInput.trim());
      applyUpdatedSession(response.review_session, response.message);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to fetch review session";
      setErrorMessage(message);
    } finally {
      setIsFetching(false);
    }
  }

  async function handleRegenerateDraft() {
    if (!session?.session_id) return;

    setIsRegeneratingDraft(true);
    resetBanners();

    try {
      const response = await regenerateDraft({
        session_id: session.session_id,
        persist_session: persistSession,
      });
      applyUpdatedSession(response.review_session, response.message);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to regenerate draft";
      setErrorMessage(message);
    } finally {
      setIsRegeneratingDraft(false);
    }
  }

  async function handleRegenerateSection(sectionId: string) {
    if (!session?.session_id) return;

    setActiveSectionActionId(`regen:${sectionId}`);
    resetBanners();

    try {
      const response = await regenerateSection({
        session_id: session.session_id,
        section_id: sectionId,
        persist_session: persistSession,
      });
      applyUpdatedSession(response.review_session, response.message);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : `Failed to regenerate section ${sectionId}`;
      setErrorMessage(message);
    } finally {
      setActiveSectionActionId(null);
    }
  }

  async function handleSaveSection(sectionId: string) {
    if (!session?.session_id) return;

    const body = sectionDrafts[sectionId] ?? "";
    if (!body.trim()) {
      setErrorMessage("Section body cannot be empty.");
      return;
    }

    setActiveSectionActionId(`save:${sectionId}`);
    resetBanners();

    try {
      const response = await updateSection({
        session_id: session.session_id,
        section_id: sectionId,
        body,
        persist_session: persistSession,
      });
      applyUpdatedSession(response.review_session, response.message);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : `Failed to save section ${sectionId}`;
      setErrorMessage(message);
    } finally {
      setActiveSectionActionId(null);
    }
  }

  async function handleSaveMetadata(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session?.session_id) return;

    setIsSavingMetadata(true);
    resetBanners();

    try {
      const response = await updateMetadata({
        session_id: session.session_id,
        title: metadataForm.title,
        meta_description: metadataForm.meta_description,
        h1: metadataForm.h1,
        intro_snippet: metadataForm.intro_snippet,
        persist_session: persistSession,
      });
      applyUpdatedSession(response.review_session, response.message);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to update metadata";
      setErrorMessage(message);
    } finally {
      setIsSavingMetadata(false);
    }
  }

  async function handleRestoreVersion(versionId: string) {
    if (!session?.session_id) return;

    setActiveRestoreVersionId(versionId);
    resetBanners();

    try {
      const response = await restoreVersion({
        session_id: session.session_id,
        version_id: versionId,
        persist_session: persistSession,
      });
      applyUpdatedSession(response.review_session, response.message);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : `Failed to restore version ${versionId}`;
      setErrorMessage(message);
    } finally {
      setActiveRestoreVersionId(null);
    }
  }

  async function handleExportDraft() {
    if (!session?.session_id) return;

    setIsExporting(true);
    resetBanners();

    try {
      const response = await exportReviewSession({
        session_id: session.session_id,
        export_formats: ["json", "markdown", "docx", "html"],
        persist_session: persistSession,
      });
      applyUpdatedSession(response.review_session, response.message);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to export review session";
      setErrorMessage(message);
    } finally {
      setIsExporting(false);
    }
  }

  function renderValidationPanel() {
    if (!session) {
      return <div className="empty-state">No validation report available yet.</div>;
    }

    if (activeValidationTab === "summary") {
      return (
        <div className="details-grid">
          <div className="detail-card">
            <div className="detail-card__label">Draft Passed</div>
            <div className="detail-card__value">
              {stringifyValue(validationSummary?.passed)}
            </div>
          </div>

          <div className="detail-card">
            <div className="detail-card__label">Approval Status</div>
            <div className="detail-card__value">
              {qualityReport?.approval_status ?? "—"}
            </div>
          </div>

          <div className="detail-card">
            <div className="detail-card__label">Canonical Metric</div>
            <div className="detail-card__value">
              {stringifyValue(validationSummary?.canonical_metric_name)}
            </div>
          </div>

          <div className="detail-card">
            <div className="detail-card__label">Warnings</div>
            <div className="detail-card__value">
              {warningReasons.length ? warningReasons.join(", ") : "—"}
            </div>
          </div>
        </div>
      );
    }

    if (activeValidationTab === "metadata") {
      return (
        <div className="stack-list">
          {metadataChecks ? (
            Object.entries(metadataChecks).map(([fieldName, fieldValue]) => {
              const fieldRecord = getRecord(fieldValue);
              const issues = getStringArray(fieldRecord?.issues);

              return (
                <div className="stack-card" key={fieldName}>
                  <div className="stack-card__header">
                    <div>
                      <div className="stack-card__title">{fieldName}</div>
                    </div>

                    <div className="stack-card__badges">
                      <ValidationBadge passed={Boolean(fieldRecord?.passed)} />
                    </div>
                  </div>

                  <div className="stack-card__body">
                    {stringifyValue(fieldRecord?.sanitized_text ?? fieldRecord?.original_text)}
                  </div>

                  <div className="stack-card__footer">
                    <strong>Issues:</strong> {issues.length ? issues.join(", ") : "none"}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">No metadata checks available.</div>
          )}
        </div>
      );
    }

    if (activeValidationTab === "sections") {
      return (
        <div className="stack-list">
          {sectionChecks.length ? (
            sectionChecks.map((item, index) => {
              const record = getRecord(item);
              const validation = getRecord(record?.validation);
              const issues = getStringArray(validation?.issues);

              return (
                <div className="stack-card" key={`${record?.id ?? "section"}-${index}`}>
                  <div className="stack-card__header">
                    <div>
                      <div className="stack-card__title">
                        {stringifyValue(record?.title)}
                      </div>
                      <div className="stack-card__meta">
                        ID: {stringifyValue(record?.id)}
                      </div>
                    </div>

                    <div className="stack-card__badges">
                      <ValidationBadge passed={Boolean(validation?.passed)} />
                    </div>
                  </div>

                  <div className="stack-card__body">
                    {stringifyValue(validation?.sanitized_text ?? validation?.original_text)}
                  </div>

                  <div className="stack-card__footer">
                    <strong>Issues:</strong> {issues.length ? issues.join(", ") : "none"}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">No section checks available.</div>
          )}
        </div>
      );
    }

    if (activeValidationTab === "faqs") {
      return (
        <div className="stack-list">
          {faqChecks.length ? (
            faqChecks.map((item, index) => {
              const record = getRecord(item);
              const validation = getRecord(record?.validation);
              const issues = getStringArray(validation?.issues);

              return (
                <div className="stack-card" key={`faq-${index}`}>
                  <div className="stack-card__header">
                    <div>
                      <div className="stack-card__title">
                        {stringifyValue(record?.question)}
                      </div>
                    </div>

                    <div className="stack-card__badges">
                      <ValidationBadge passed={Boolean(validation?.passed)} />
                    </div>
                  </div>

                  <div className="stack-card__body">
                    {stringifyValue(validation?.sanitized_text ?? validation?.original_text)}
                  </div>

                  <div className="stack-card__footer">
                    <strong>Issues:</strong> {issues.length ? issues.join(", ") : "none"}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">No FAQ checks available.</div>
          )}
        </div>
      );
    }

    return <pre className="json-viewer">{JSON.stringify(session.validation_report, null, 2)}</pre>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Review Workbench</h1>
          <p className="page-subtitle">
            Create, fetch, inspect, edit, regenerate, and restore backend review sessions.
          </p>
        </div>

        {session ? (
          <div className="page-actions">
            <button
              className="primary-button"
              type="button"
              onClick={handleRegenerateDraft}
              disabled={isRegeneratingDraft || isExporting}
            >
              {isRegeneratingDraft ? "Regenerating..." : "Regenerate full draft"}
            </button>

            <button
              className="secondary-button"
              type="button"
              onClick={handleExportDraft}
              disabled={isRegeneratingDraft || isExporting}
            >
              {isExporting ? "Exporting..." : "Export JSON / MD / DOCX / HTML"}
            </button>
          </div>
        ) : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Create review session</h2>
        </div>

        <form className="form-grid" onSubmit={handleCreateSession}>
          <label className="field">
            <span className="field-label">Main datacenter JSON path</span>
            <input
              className="field-input"
              value={mainPath}
              onChange={(event) => setMainPath(event.target.value)}
            />
          </label>

          <label className="field">
            <span className="field-label">Property rates JSON path</span>
            <input
              className="field-input"
              value={ratesPath}
              onChange={(event) => setRatesPath(event.target.value)}
            />
          </label>

          <label className="field">
            <span className="field-label">
              Page URL{" "}
              <span style={{ fontWeight: 400, color: "#888" }}>(optional — Square Yards canonical URL)</span>
            </span>
            <input
              className="field-input"
              type="url"
              placeholder="https://www.squareyards.com/sale/2-bhk-for-sale-in-gurgaon"
              value={pageUrl}
              onChange={(event) => setPageUrl(event.target.value)}
            />
            <span style={{ fontSize: "0.78rem", color: "#888", marginTop: "4px", display: "block" }}>
              Extracts filters (property type, BHK, budget, furnishing, amenities) to scope content generation.
            </span>
          </label>

          <label className="field">
            <span className="field-label">Custom primary keyword overrides</span>
            <textarea
              className="field-textarea"
              rows={4}
              placeholder={`One keyword per line or comma-separated\nExample:\nresale properties in Andheri West Mumbai\nflats for sale in Andheri West Mumbai`}
              value={primaryKeywordOverride}
              onChange={(event) => setPrimaryKeywordOverride(event.target.value)}
            />
          </label>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={includeHistorical}
              onChange={(event) => setIncludeHistorical(event.target.checked)}
            />
            <span>Include historical keywords</span>
          </label>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={persistSession}
              onChange={(event) => setPersistSession(event.target.checked)}
            />
            <span>Persist session</span>
          </label>

          <div className="form-actions">
            <button className="primary-button" type="submit" disabled={isCreating}>
              {isCreating ? "Creating..." : "Create review session"}
            </button>
          </div>
        </form>

        {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
        {successMessage ? <div className="success-banner">{successMessage}</div> : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Fetch existing review session</h2>
        </div>

        <form className="inline-form" onSubmit={handleFetchSession}>
          <label className="field field--inline-grow">
            <span className="field-label">Review session id</span>
            <input
              className="field-input"
              placeholder="review-xxxxxxxxxxxxxxxx"
              value={sessionIdInput}
              onChange={(event) => setSessionIdInput(event.target.value)}
            />
          </label>

          <div className="form-actions">
            <button className="primary-button" type="submit" disabled={isFetching}>
              {isFetching ? "Fetching..." : "Fetch session"}
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Current session snapshot</h2>
        </div>

        {!session ? (
          <div className="empty-state">No session loaded yet.</div>
        ) : (
          <div className="session-grid">
            <div className="summary-card">
              <div className="summary-card__label">Session ID</div>
              <div className="summary-card__value">{session.session_id}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Entity</div>
              <div className="summary-card__value">
                {headerSummary?.entityName}, {headerSummary?.cityName}
              </div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Page Type</div>
              <div className="summary-card__value">{headerSummary?.pageType}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Listing Type</div>
              <div className="summary-card__value">{headerSummary?.listingType}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Approval Status</div>
              <div className="summary-card__value">{headerSummary?.approvalStatus}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Quality Score</div>
              <div className="summary-card__value">{String(headerSummary?.qualityScore)}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Warning Count</div>
              <div className="summary-card__value">{String(headerSummary?.warningCount)}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Sections</div>
              <div className="summary-card__value">{String(headerSummary?.sectionCount)}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">FAQs</div>
              <div className="summary-card__value">{String(headerSummary?.faqCount)}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Tables</div>
              <div className="summary-card__value">{String(headerSummary?.tableCount)}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Versions</div>
              <div className="summary-card__value">{String(headerSummary?.versionCount)}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Latest Version</div>
              <div className="summary-card__value">{headerSummary?.latestVersionId}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Primary Keyword Overrides</div>
              <div className="summary-card__value">{headerSummary?.primaryKeywordOverrides}</div>
            </div>
          </div>
        )}
      </section>

      {session ? (
        <>
          <section className="panel">
            <div className="panel-header">
              <h2>Combined generated content snapshot</h2>
            </div>

            <div className="stack-list">
              <div className="stack-card">
                <div className="stack-card__header">
                  <div>
                    <div className="stack-card__title">{metadata?.h1 ?? "Draft heading"}</div>
                    <div className="stack-card__meta">Title: {metadata?.title ?? "—"}</div>
                  </div>

                  <div className="stack-card__badges">
                    <span className="badge">
                      status: {qualityReport?.approval_status ?? "—"}
                    </span>
                    <span className="badge">
                      publish ready: {stringifyValue(session.draft?.publish_ready)}
                    </span>
                  </div>
                </div>

                <div className="stack-card__body">
                  {metadata?.intro_snippet ?? "—"}
                </div>
              </div>

              {(session.draft?.sections ?? []).map((section) => (
                <div className="stack-card" key={section.id ?? section.title}>
                  <div className="stack-card__header">
                    <div>
                      <div className="stack-card__title">
                        {section.title ?? "Untitled section"}
                      </div>
                      <div className="stack-card__meta">ID: {section.id ?? "—"}</div>
                    </div>
                  </div>

                  <div className="stack-card__body">{section.body ?? "—"}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Edit metadata</h2>
            </div>

            <form className="form-grid" onSubmit={handleSaveMetadata}>
              <label className="field">
                <span className="field-label">Title</span>
                <input
                  className="field-input"
                  value={metadataForm.title}
                  onChange={(event) =>
                    setMetadataForm((current) => ({
                      ...current,
                      title: event.target.value,
                    }))
                  }
                />
              </label>

              <label className="field">
                <span className="field-label">Meta Description</span>
                <textarea
                  className="field-textarea"
                  rows={4}
                  value={metadataForm.meta_description}
                  onChange={(event) =>
                    setMetadataForm((current) => ({
                      ...current,
                      meta_description: event.target.value,
                    }))
                  }
                />
              </label>

              <label className="field">
                <span className="field-label">H1</span>
                <input
                  className="field-input"
                  value={metadataForm.h1}
                  onChange={(event) =>
                    setMetadataForm((current) => ({
                      ...current,
                      h1: event.target.value,
                    }))
                  }
                />
              </label>

              <label className="field">
                <span className="field-label">Intro Snippet</span>
                <textarea
                  className="field-textarea"
                  rows={4}
                  value={metadataForm.intro_snippet}
                  onChange={(event) =>
                    setMetadataForm((current) => ({
                      ...current,
                      intro_snippet: event.target.value,
                    }))
                  }
                />
              </label>

              <div className="form-actions">
                <button className="primary-button" type="submit" disabled={isSavingMetadata}>
                  {isSavingMetadata ? "Saving..." : "Save metadata"}
                </button>
              </div>
            </form>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Quality and publishability</h2>
            </div>

            <div className="details-grid">
              <div className="detail-card">
                <div className="detail-card__label">Approval Status</div>
                <div className="detail-card__value">{qualityReport?.approval_status ?? "—"}</div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Overall Quality Score</div>
                <div className="detail-card__value">
                  {stringifyValue(
                    qualityReport?.overall_quality_score ?? draftQualityReport?.overall_quality_score,
                  )}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Publish Ready</div>
                <div className="detail-card__value">
                  {stringifyValue(session.draft?.publish_ready)}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Blocked</div>
                <div className="detail-card__value">
                  {stringifyValue(debugSummary?.blocked)}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Blocking Reasons</div>
                <div className="detail-card__value">
                  {debugSummary?.blocking_reasons?.length
                    ? debugSummary.blocking_reasons.join(", ")
                    : "—"}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Warnings</div>
                <div className="detail-card__value">
                  {warningReasons.length ? warningReasons.join(", ") : "—"}
                </div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Validation report</h2>
            </div>

            <div className="tab-row">
              {(["summary", "metadata", "sections", "faqs", "raw"] as ValidationTabKey[]).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={activeValidationTab === tab ? "tab-button tab-button--active" : "tab-button"}
                  onClick={() => setActiveValidationTab(tab)}
                >
                  {tab === "raw" ? "Raw" : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            <div className="tab-panel">{renderValidationPanel()}</div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Source data preview</h2>
            </div>

            <div className="details-grid">
              <div className="detail-card">
                <div className="detail-card__label">Sale Count</div>
                <div className="detail-card__value">
                  {stringifyValue(listingSummary?.sale_count)}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Total Listings</div>
                <div className="detail-card__value">
                  {stringifyValue(listingSummary?.total_listings)}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Total Projects</div>
                <div className="detail-card__value">
                  {stringifyValue(listingSummary?.total_projects)}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Asking Price</div>
                <div className="detail-card__value">
                  {stringifyValue(pricingSummary?.asking_price)}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Registration Rate</div>
                <div className="detail-card__value">
                  {stringifyValue(pricingSummary?.registration_rate)}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Last Modified Date</div>
                <div className="detail-card__value">
                  {stringifyValue(
                    getRecord(session.source_preview?.raw_source_meta)?.last_modified_date,
                  )}
                </div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Keyword preview</h2>
            </div>

            <div className="details-grid">
              <div className="detail-card">
                <div className="detail-card__label">Primary Keyword</div>
                <div className="detail-card__value">
                  {stringifyValue(primaryKeyword?.keyword)}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Primary Keyword Overrides</div>
                <div className="detail-card__value">
                  <KeywordChipList items={primaryKeywordOverrides} />
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Secondary Keywords</div>
                <div className="detail-card__value">
                  {secondaryKeywords.length
                    ? secondaryKeywords
                        .map((item) => stringifyValue(getRecord(item)?.keyword))
                        .join(", ")
                    : "—"}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Price Keywords</div>
                <div className="detail-card__value">
                  {priceKeywords.length
                    ? priceKeywords
                        .map((item) => stringifyValue(getRecord(item)?.keyword))
                        .join(", ")
                    : "—"}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">BHK Keywords</div>
                <div className="detail-card__value">
                  {bhkKeywords.length
                    ? bhkKeywords
                        .map((item) => stringifyValue(getRecord(item)?.keyword))
                        .join(", ")
                    : "—"}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">FAQ Keywords</div>
                <div className="detail-card__value">
                  {faqKeywords.length
                    ? faqKeywords.map((item) => stringifyValue(getRecord(item)?.keyword)).join(", ")
                    : "—"}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Relevant Competitor Keywords</div>
                <div className="detail-card__value">
                  <KeywordChipList items={competitorKeywordLabels} />
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Relevant Informational Signals</div>
                <div className="detail-card__value">
                  <KeywordChipList items={informationalKeywordLabels} />
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Relevant Overlap Keywords</div>
                <div className="detail-card__value">
                  <KeywordChipList items={overlapKeywordLabels} />
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Competitor Domains</div>
                <div className="detail-card__value">
                  {competitorDomains.length ? competitorDomains.join(", ") : "—"}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">SERP Seeds Checked</div>
                <div className="detail-card__value">
                  {serpSeedKeywordsChecked.length ? serpSeedKeywordsChecked.join(", ") : "—"}
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Total Included Keywords</div>
                <div className="detail-card__value">{totalIncludedKeywords}</div>
              </div>

              <div className="detail-card">
                <div className="detail-card__label">Total Excluded Keywords</div>
                <div className="detail-card__value">{totalExcludedKeywords}</div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Planning signals from competitor patterns</h2>
            </div>

            {!competitorIntelligence ? (
              <div className="empty-state">No competitor intelligence available yet.</div>
            ) : (
              <>
                <div className="details-grid">
                  <div className="detail-card">
                    <div className="detail-card__label">Selected Competitors</div>
                    <div className="detail-card__value">
                      {competitorDomains.length ? competitorDomains.join(", ") : "—"}
                    </div>
                  </div>

                  <div className="detail-card">
                    <div className="detail-card__label">SERP Overlap Domains</div>
                    <div className="detail-card__value">
                      {getStringArray(competitorSerpOverlap?.overlapping_domains).length
                        ? getStringArray(competitorSerpOverlap?.overlapping_domains).join(", ")
                        : "—"}
                    </div>
                  </div>

                  <div className="detail-card">
                    <div className="detail-card__label">Keyword Intersection Count</div>
                    <div className="detail-card__value">
                      {stringifyValue(competitorIntersection?.intersection_count)}
                    </div>
                  </div>

                  <div className="detail-card">
                    <div className="detail-card__label">Inspiration Confidence</div>
                    <div className="detail-card__value">
                      {stringifyValue(competitorInspiration?.confidence)}
                    </div>
                  </div>

                  <div className="detail-card">
                    <div className="detail-card__label">Structural Usage Rule</div>
                    <div className="detail-card__value">
                      {stringifyValue(competitorInspiration?.usage_rule)}
                    </div>
                  </div>

                  <div className="detail-card">
                    <div className="detail-card__label">Intersection Keywords</div>
                    <div className="detail-card__value">
                      {competitorIntersectionKeywords.length
                        ? competitorIntersectionKeywords
                            .map((item) => stringifyValue(getRecord(item)?.keyword))
                            .join(", ")
                        : "—"}
                    </div>
                  </div>
                </div>

                <div className="stack-list" style={{ marginTop: 16 }}>
                  {competitorBreakdown.length ? (
                    competitorBreakdown.map((item, index) => {
                      const competitor = getRecord(item);
                      const pageFamilies = getArray(competitor?.page_family_breakdown);
                      const themeBreakdown = getArray(competitor?.theme_breakdown);
                      const topKeywords = getArray(competitor?.top_keywords);

                      return (
                        <div className="stack-card" key={`competitor-${index}`}>
                          <div className="stack-card__header">
                            <div>
                              <div className="stack-card__title">
                                {stringifyValue(competitor?.domain)}
                              </div>
                              <div className="stack-card__meta">
                                keyword count: {stringifyValue(competitor?.keyword_count)}
                              </div>
                            </div>
                          </div>

                          <div className="details-grid">
                            <div className="detail-card">
                              <div className="detail-card__label">Top Keywords</div>
                              <div className="detail-card__value">
                                {topKeywords.length
                                  ? topKeywords
                                      .map((record) => stringifyValue(getRecord(record)?.keyword))
                                      .join(", ")
                                  : "—"}
                              </div>
                            </div>

                            <div className="detail-card">
                              <div className="detail-card__label">Page Families</div>
                              <div className="detail-card__value">
                                {pageFamilies.length
                                  ? pageFamilies
                                      .map((family) => {
                                        const record = getRecord(family);
                                        return `${stringifyValue(record?.page_family)} (${stringifyValue(
                                          record?.keyword_count,
                                        )})`;
                                      })
                                      .join(", ")
                                  : "—"}
                              </div>
                            </div>

                            <div className="detail-card">
                              <div className="detail-card__label">Theme Breakdown</div>
                              <div className="detail-card__value">
                                {themeBreakdown.length
                                  ? themeBreakdown
                                      .map((theme) => {
                                        const record = getRecord(theme);
                                        return `${stringifyValue(record?.theme)} (${stringifyValue(
                                          record?.count,
                                        )})`;
                                      })
                                      .join(", ")
                                  : "—"}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="empty-state">No competitor breakdown available.</div>
                  )}
                </div>

                <div className="details-grid" style={{ marginTop: 16 }}>
                  <div className="detail-card">
                    <div className="detail-card__label">Recommended Sections</div>
                    <div className="detail-card__value">
                      {competitorRecommendedSections.length
                        ? competitorRecommendedSections
                            .map((item) => {
                              const record = getRecord(item);
                              return `${stringifyValue(record?.title)} [${stringifyValue(record?.theme)}]`;
                            })
                            .join(", ")
                        : "—"}
                    </div>
                  </div>

                  <div className="detail-card">
                    <div className="detail-card__label">Recommended FAQ Themes</div>
                    <div className="detail-card__value">
                      {competitorRecommendedFaqThemes.length
                        ? competitorRecommendedFaqThemes
                            .map((item) => {
                              const record = getRecord(item);
                              return stringifyValue(record?.question_pattern);
                            })
                            .join(", ")
                        : "—"}
                    </div>
                  </div>

                  <div className="detail-card">
                    <div className="detail-card__label">Recommended Table Themes</div>
                    <div className="detail-card__value">
                      {competitorRecommendedTableThemes.length
                        ? competitorRecommendedTableThemes
                            .map((item) => {
                              const record = getRecord(item);
                              return stringifyValue(record?.table_pattern);
                            })
                            .join(", ")
                        : "—"}
                    </div>
                  </div>

                  <div className="detail-card">
                    <div className="detail-card__label">Schema / Hierarchy Patterns</div>
                    <div className="detail-card__value">
                      {competitorSchemaHierarchyPatterns.length
                        ? competitorSchemaHierarchyPatterns
                            .map((item) => {
                              const record = getRecord(item);
                              return stringifyValue(record?.pattern);
                            })
                            .join(", ")
                        : "—"}
                    </div>
                  </div>
                </div>
              </>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Section edit and review</h2>
            </div>

            {sectionReview.length === 0 ? (
              <div className="empty-state">No section review items available.</div>
            ) : (
              <div className="stack-list">
                {sectionReview.map((section: ReviewSectionReview) => {
                  const sectionId = section.id ?? "";
                  const quality = getRecord(section.quality);

                  return (
                    <div className="stack-card" key={section.id ?? section.title}>
                      <div className="stack-card__header">
                        <div>
                          <div className="stack-card__title">
                            {section.title ?? "Untitled section"}
                          </div>
                          <div className="stack-card__meta">ID: {section.id ?? "—"}</div>
                        </div>

                        <div className="stack-card__badges">
                          <ValidationBadge passed={section.validation_passed} />
                          <span className="badge">
                            score: {stringifyValue(quality?.score)}
                          </span>
                        </div>
                      </div>

                      <label className="field">
                        <span className="field-label">Section body</span>
                        <textarea
                          className="field-textarea field-textarea--section"
                          rows={8}
                          value={sectionDrafts[sectionId] ?? section.body ?? ""}
                          onChange={(event) =>
                            setSectionDrafts((current) => ({
                              ...current,
                              [sectionId]: event.target.value,
                            }))
                          }
                        />
                      </label>

                      <div className="form-actions">
                        <button
                          className="primary-button"
                          type="button"
                          onClick={() => handleSaveSection(sectionId)}
                          disabled={activeSectionActionId !== null}
                        >
                          {activeSectionActionId === `save:${sectionId}`
                            ? "Saving..."
                            : "Save section"}
                        </button>

                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => handleRegenerateSection(sectionId)}
                          disabled={activeSectionActionId !== null}
                        >
                          {activeSectionActionId === `regen:${sectionId}`
                            ? "Regenerating..."
                            : "Regenerate section"}
                        </button>
                      </div>

                      <div className="stack-card__footer">
                        <strong>Issues:</strong>{" "}
                        {section.validation_issues?.length
                          ? section.validation_issues.join(", ")
                          : "none"}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Tables snapshot</h2>
            </div>

            {tables.length === 0 ? (
              <div className="empty-state">No tables available in the draft.</div>
            ) : (
              <div className="stack-list">
                {tables.map((table, index) => (
                  <TableSnapshot key={`${table.id ?? "table"}-${index}`} table={table} />
                ))}
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>FAQs snapshot</h2>
            </div>

            {faqs.length === 0 ? (
              <div className="empty-state">No FAQs available in the draft.</div>
            ) : (
              <div className="stack-list">
                {faqs.map((faq, index) => (
                  <FaqSnapshot key={`faq-${index}`} faq={faq} />
                ))}
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Version history snapshot</h2>
            </div>

            {versionHistory.length === 0 ? (
              <div className="empty-state">No version history available.</div>
            ) : (
              <div className="stack-list">
                {versionHistory.map((version: ReviewVersionHistoryItem) => (
                  <div className="stack-card" key={version.version_id ?? version.created_at}>
                    <div className="stack-card__header">
                      <div>
                        <div className="stack-card__title">
                          {version.version_id ?? "Unknown version"}
                        </div>
                        <div className="stack-card__meta">
                          action: {version.action_type ?? "—"} | number:{" "}
                          {stringifyValue(version.version_number)}
                        </div>
                      </div>

                      <div className="stack-card__badges">
                        <span className="badge">
                          status: {version.approval_status ?? "—"}
                        </span>
                        <span className="badge">
                          score: {stringifyValue(version.overall_quality_score)}
                        </span>
                      </div>
                    </div>

                    <div className="stack-card__footer">
                      created at: {version.created_at ?? "—"} | publish ready:{" "}
                      {stringifyValue(version.publish_ready)}
                    </div>

                    <div className="form-actions form-actions--top-gap">
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => handleRestoreVersion(version.version_id ?? "")}
                        disabled={!version.version_id || activeRestoreVersionId !== null}
                      >
                        {activeRestoreVersionId === version.version_id
                          ? "Restoring..."
                          : "Restore version"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Export artifacts</h2>
            </div>

            {!latestExportPaths ? (
              <div className="empty-state">
                No export generated yet. Click “Export JSON / MD / DOCX / HTML” to create artifacts.
              </div>
            ) : (
              <div className="details-grid">
                <div className="detail-card">
                  <div className="detail-card__label">JSON</div>
                  <div className="detail-card__value">
                    {latestExportPaths.json_path ?? "—"}
                  </div>
                  {session?.session_id ? (
                    <div className="form-actions form-actions--top-gap">
                      <a
                        className="secondary-button"
                        href={getReviewDownloadUrl(session.session_id, "json")}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Download JSON
                      </a>
                    </div>
                  ) : null}
                </div>

                <div className="detail-card">
                  <div className="detail-card__label">Markdown</div>
                  <div className="detail-card__value">
                    {latestExportPaths.markdown_path ?? "—"}
                  </div>
                  {session?.session_id ? (
                    <div className="form-actions form-actions--top-gap">
                      <a
                        className="secondary-button"
                        href={getReviewDownloadUrl(session.session_id, "markdown")}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Download Markdown
                      </a>
                    </div>
                  ) : null}
                </div>

                <div className="detail-card">
                  <div className="detail-card__label">DOCX</div>
                  <div className="detail-card__value">
                    {latestExportPaths.docx_path ?? "—"}
                  </div>
                  {session?.session_id ? (
                    <div className="form-actions form-actions--top-gap">
                      <a
                        className="secondary-button"
                        href={getReviewDownloadUrl(session.session_id, "docx")}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Download DOCX
                      </a>
                    </div>
                  ) : null}
                </div>

                <div className="detail-card">
                  <div className="detail-card__label">HTML</div>
                  <div className="detail-card__value">
                    {latestExportPaths.html_path ?? "—"}
                  </div>
                  {session?.session_id ? (
                    <div className="form-actions form-actions--top-gap">
                      <a
                        className="secondary-button"
                        href={getReviewDownloadUrl(session.session_id, "html")}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Download HTML
                      </a>
                    </div>
                  ) : null}
                </div>

                <div className="detail-card">
                  <div className="detail-card__label">Exported At</div>
                  <div className="detail-card__value">
                    {session?.latest_exports?.exported_at ?? "—"}
                  </div>
                </div>
              </div>
            )}
          </section>
          
          <section className="panel">
            <div className="panel-header panel-header--row">
              <h2>Raw review session payload</h2>
              <button
                className="secondary-button"
                type="button"
                onClick={() => setShowRawPayload((current) => !current)}
              >
                {showRawPayload ? "Hide payload" : "Show payload"}
              </button>
            </div>

            {showRawPayload ? (
              <pre className="json-viewer">{JSON.stringify(session, null, 2)}</pre>
            ) : (
              <div className="empty-state">
                Raw payload is hidden. Click “Show payload” to inspect it.
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}