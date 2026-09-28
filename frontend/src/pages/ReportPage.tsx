/**
 * Stub page for QA Report — will be implemented in Stage 5.
 */

import PageShell from '../components/layout/PageShell';

export default function ReportPage() {
  return (
    <PageShell
      title="QA Screening Report"
      subtitle="Generate and export comprehensive QA screening reports"
    >
      <div className="alert alert--info">
        <span aria-hidden="true">ℹ️</span>
        <div>
          <strong>Coming in Stage 5</strong> — Report preview with batch summary,
          anomaly/drift findings, component dispositions, and export to JSON/PDF.
        </div>
      </div>
    </PageShell>
  );
}
