/**
 * Dashboard page — landing page showing system overview and batch summary.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageShell from '../components/layout/PageShell';
import { listBatches } from '../api/client';
import type { BatchListItem } from '../types';

export default function DashboardPage() {
  const [batches, setBatches] = useState<BatchListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    listBatches()
      .then(setBatches)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageShell
      title="Dashboard"
      subtitle="Burn-In Screening Anomaly Detection — System Overview"
    >
      {/* Prototype disclaimer */}
      <div className="alert alert--demo" style={{ marginBottom: '24px' }}>
        <span aria-hidden="true">ℹ️</span>
        <div>
          <strong>Prototype System</strong> — This is an engineering prototype for AI-driven
          anomaly detection in component burn-in screening. This is NOT an official ISRO system.
          All synthetic data and thresholds are for demonstration purposes only.
        </div>
      </div>

      {/* Quick stats */}
      <div className="stat-grid" style={{ marginBottom: '24px' }}>
        <div className="stat-card stat-card--info">
          <div className="stat-card-label">Batches Loaded</div>
          <div className="stat-card-value">{loading ? '—' : batches.length}</div>
          <div className="stat-card-sub">Available for analysis</div>
        </div>
        <div className="stat-card stat-card--normal">
          <div className="stat-card-label">Analysed (Anomaly)</div>
          <div className="stat-card-value">
            {loading ? '—' : batches.filter((b) => b.has_anomaly_results).length}
          </div>
          <div className="stat-card-sub">Module A completed</div>
        </div>
        <div className="stat-card stat-card--warning">
          <div className="stat-card-label">Analysed (Drift)</div>
          <div className="stat-card-value">
            {loading ? '—' : batches.filter((b) => b.has_drift_results).length}
          </div>
          <div className="stat-card-sub">Module B completed</div>
        </div>
      </div>

      {/* Batch list */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Loaded Batches</h3>
          <button className="btn btn--primary btn--sm" onClick={() => navigate('/upload')}>
            Upload / Load Data
          </button>
        </div>
        <div className="card-body">
          {loading && (
            <div className="loading-overlay">
              <span className="spinner" />
              Loading batches...
            </div>
          )}

          {error && (
            <div className="alert alert--error">
              <span aria-hidden="true">⚠</span>
              {error}. Make sure the backend is running on port 8000.
            </div>
          )}

          {!loading && !error && batches.length === 0 && (
            <div className="empty-state">
              <div className="empty-state-icon">📁</div>
              <div className="empty-state-title">No batches loaded</div>
              <div className="empty-state-text">
                Upload a CSV dataset or load the demo data to get started.
              </div>
              <button
                className="btn btn--primary"
                style={{ marginTop: '16px' }}
                onClick={() => navigate('/upload')}
              >
                Go to Upload
              </button>
            </div>
          )}

          {!loading && batches.length > 0 && (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Batch ID</th>
                    <th>Components</th>
                    <th>Parameters</th>
                    <th>Type</th>
                    <th>Anomaly</th>
                    <th>Drift</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.map((batch) => (
                    <tr key={batch.batch_id}>
                      <td>
                        <strong>{batch.batch_id}</strong>
                      </td>
                      <td className="numeric">{batch.total_components}</td>
                      <td>{batch.parameters.join(', ')}</td>
                      <td>
                        {batch.is_demo ? (
                          <span className="badge badge--demo">DEMO</span>
                        ) : (
                          <span className="badge badge--info">UPLOADED</span>
                        )}
                      </td>
                      <td>
                        {batch.has_anomaly_results ? (
                          <span className="badge badge--normal">✓ Done</span>
                        ) : (
                          <span className="badge badge--info">Pending</span>
                        )}
                      </td>
                      <td>
                        {batch.has_drift_results ? (
                          <span className="badge badge--normal">✓ Done</span>
                        ) : (
                          <span className="badge badge--info">Pending</span>
                        )}
                      </td>
                      <td>
                        <button
                          className="btn btn--secondary btn--sm"
                          onClick={() => navigate(`/batch?id=${batch.batch_id}`)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* System capabilities summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '24px' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Module A — Dynamic Outlier Detection</h3>
          </div>
          <div className="card-body" style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
            <p>Ensemble of 4 statistical/ML methods to detect components that are anomalous relative to their batch population, even when within absolute specification limits.</p>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              <li>Modified Z-Score</li>
              <li>IQR Fence</li>
              <li>Isolation Forest</li>
              <li>Local Outlier Factor</li>
            </ul>
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Module B — Time-Series Drift Prediction</h3>
          </div>
          <div className="card-body" style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
            <p>Predictive regression using early measurements (0h, 24h) to forecast 168h values. Identifies components with abnormal drift before full burn-in completion.</p>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              <li>XGBoost / Ridge regression</li>
              <li>Safety slope comparison</li>
              <li>SHAP explainability</li>
              <li>Per-component risk classification</li>
            </ul>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
