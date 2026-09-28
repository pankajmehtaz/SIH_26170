/**
 * Stub page for Model Metrics — will be implemented in Stage 5.
 */

import PageShell from '../components/layout/PageShell';

export default function ModelMetricsPage() {
  return (
    <PageShell
      title="Model Metrics"
      subtitle="Evaluation performance of anomaly detection and drift prediction"
    >
      <div className="alert alert--info">
        <span aria-hidden="true">ℹ️</span>
        <div>
          <strong>Coming in Stage 5</strong> — Confusion matrix, precision/recall/F1,
          MAE/RMSE/R², residual plots, and ROC curves.
        </div>
      </div>
    </PageShell>
  );
}
