/**
 * Stub page for Component Detail — will be implemented in Stage 4.
 */

import PageShell from '../components/layout/PageShell';

export default function ComponentDetailPage() {
  return (
    <PageShell
      title="Component Detail"
      subtitle="Deep-dive into individual component analysis"
    >
      <div className="alert alert--info">
        <span aria-hidden="true">ℹ️</span>
        <div>
          <strong>Coming in Stage 4</strong> — Full component profile with time-series trace,
          population comparison overlay, anomaly/drift explanations, SHAP waterfall,
          risk classification, and recommended disposition.
        </div>
      </div>
    </PageShell>
  );
}
