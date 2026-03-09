import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="page">
      <section className="panel">
        <div className="panel-header">
          <h2>Page not found</h2>
        </div>
        <p>This route does not exist.</p>
        <Link to="/" className="primary-button primary-button--link">
          Go to Review Workbench
        </Link>
      </section>
    </div>
  );
}
