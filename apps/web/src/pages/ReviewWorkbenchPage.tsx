import { useMemo, useState } from "react";

import { createReviewSession } from "../api/review";
import type { ReviewSession } from "../types/review";

const DEFAULT_MAIN_PATH =
  "/Users/deepeshgupta/Projects/seo-content-generation-system/data/samples/raw/andheri-west-locality.json";

const DEFAULT_RATES_PATH =
  "/Users/deepeshgupta/Projects/seo-content-generation-system/data/samples/raw/andheri-west-property-rates.json";

export function ReviewWorkbenchPage() {
  const [mainPath, setMainPath] = useState(DEFAULT_MAIN_PATH);
  const [ratesPath, setRatesPath] = useState(DEFAULT_RATES_PATH);
  const [includeHistorical, setIncludeHistorical] = useState(true);
  const [persistSession, setPersistSession] = useState(true);

  const [session, setSession] = useState<ReviewSession | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const headerSummary = useMemo(() => {
    if (!session) return null;

    return {
      entityName: session.entity?.entity_name ?? "—",
      cityName: session.entity?.city_name ?? "—",
      pageType: session.entity?.page_type ?? "—",
      approvalStatus: session.quality_report?.approval_status ?? "—",
      qualityScore: session.quality_report?.overall_quality_score ?? "—",
    };
  }, [session]);

  async function handleCreateSession(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await createReviewSession({
        main_datacenter_json_path: mainPath,
        property_rates_json_path: ratesPath,
        listing_type: "resale",
        include_historical: includeHistorical,
        persist_session: persistSession,
      });

      setSession(response.review_session);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to create review session";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Review Workbench</h1>
          <p className="page-subtitle">
            Create and inspect backend review sessions before building edit and mutation flows.
          </p>
        </div>
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
            <button className="primary-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create review session"}
            </button>
          </div>
        </form>

        {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Current session snapshot</h2>
        </div>

        {!session ? (
          <div className="empty-state">
            No session loaded yet.
          </div>
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
              <div className="summary-card__label">Approval Status</div>
              <div className="summary-card__value">{headerSummary?.approvalStatus}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Quality Score</div>
              <div className="summary-card__value">{String(headerSummary?.qualityScore)}</div>
            </div>

            <div className="summary-card">
              <div className="summary-card__label">Latest Version</div>
              <div className="summary-card__value">{session.latest_version_id ?? "—"}</div>
            </div>
          </div>
        )}
      </section>

      {session ? (
        <section className="panel">
          <div className="panel-header">
            <h2>Raw review session payload</h2>
          </div>
          <pre className="json-viewer">{JSON.stringify(session, null, 2)}</pre>
        </section>
      ) : null}
    </div>
  );
}
