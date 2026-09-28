/**
 * Stub page for Anomaly Results — will be implemented in Stage 2.
 */

import PageShell from '../components/layout/PageShell';

export default function AnomalyResultsPage() {
  return (
    <PageShell
      title="Anomaly Detection Results"
      subtitle="Module A — Dynamic Outlier Detection"
    >
      <div className="alert alert--info">
        <span aria-hidden="true">ℹ️</span>
        <div>
          <strong>Coming in Stage 2</strong> — Anomaly detection with ensemble methods
          (Modified Z-Score, IQR, Isolation Forest, LOF) will be implemented next.
          This page will show flagged components with composite scores, risk levels,
          and population comparison charts.
        </div>
      </div>
    </PageShell>
  );
}
