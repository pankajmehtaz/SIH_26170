/**
 * Stub page for Drift Results — will be implemented in Stage 3.
 */

import PageShell from '../components/layout/PageShell';

export default function DriftResultsPage() {
  return (
    <PageShell
      title="Drift Prediction Results"
      subtitle="Module B — Time-Series Drift Prediction"
    >
      <div className="alert alert--info">
        <span aria-hidden="true">ℹ️</span>
        <div>
          <strong>Coming in Stage 3</strong> — Drift prediction using XGBoost regression
          to forecast 168h values from early measurements. This page will show predicted
          vs. actual scatter plots, safety slope comparisons, and drift risk flags.
        </div>
      </div>
    </PageShell>
  );
}
