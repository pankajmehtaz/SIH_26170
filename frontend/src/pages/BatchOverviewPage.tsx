/**
 * Batch Overview page — parameter statistics and data inspection.
 */

import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import PageShell from '../components/layout/PageShell';
import { getBatchMetadata, getBatchRawData } from '../api/client';
import type { BatchMetadata, BatchRawData } from '../types';

export default function BatchOverviewPage() {
  const [searchParams] = useSearchParams();
  const batchId = searchParams.get('id');
  const navigate = useNavigate();

  const [metadata, setMetadata] = useState<BatchMetadata | null>(null);
  const [rawData, setRawData] = useState<BatchRawData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'stats' | 'data'>('stats');

  useEffect(() => {
    if (!batchId) {
      setLoading(false);
      return;
    }

    Promise.all([getBatchMetadata(batchId), getBatchRawData(batchId)])
      .then(([meta, raw]) => {
        setMetadata(meta);
        setRawData(raw);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [batchId]);

  if (!batchId) {
    return (
      <PageShell title="Batch Overview" subtitle="Select a batch to inspect">
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-title">No batch selected</div>
          <div className="empty-state-text">Load data first, then select a batch from the dashboard.</div>
          <button className="btn btn--primary" style={{ marginTop: '16px' }} onClick={() => navigate('/upload')}>
            Go to Upload
          </button>
        </div>
      </PageShell>
    );
  }

  if (loading) {
    return (
      <PageShell title="Batch Overview">
        <div className="loading-overlay"><span className="spinner" /> Loading batch data...</div>
      </PageShell>
    );
  }

  if (error || !metadata) {
    return (
      <PageShell title="Batch Overview">
        <div className="alert alert--error"><span aria-hidden="true">⚠</span> {error || 'Batch not found'}</div>
      </PageShell>
    );
  }

  // Prepare chart data
  const statsChartData = metadata.parameter_stats.map((s) => ({
    name: s.parameter,
    Mean: Number(s.mean.toFixed(2)),
    Median: Number(s.median.toFixed(2)),
    Min: Number(s.min.toFixed(2)),
    Max: Number(s.max.toFixed(2)),
    Abs_Max: Number(s.abs_max.toFixed(2)),
  }));

  const rangeChartData = metadata.parameter_stats.map((s) => ({
    name: s.parameter,
    Q1: Number(s.q1.toFixed(2)),
    Q3: Number(s.q3.toFixed(2)),
    IQR: Number(s.iqr.toFixed(2)),
    Std: Number(s.std.toFixed(2)),
  }));

  return (
    <PageShell
      title={`Batch: ${metadata.batch_id}`}
      subtitle={`${metadata.total_components} components · ${metadata.parameters.length} parameters · ${metadata.total_rows} measurements`}
      actions={
        metadata.is_demo ? <span className="badge badge--demo">SYNTHETIC DATA</span> : undefined
      }
    >
      {/* Summary stats */}
      <div className="stat-grid" style={{ marginBottom: '24px' }}>
        <div className="stat-card stat-card--info">
          <div className="stat-card-label">Components</div>
          <div className="stat-card-value">{metadata.total_components}</div>
        </div>
        <div className="stat-card stat-card--info">
          <div className="stat-card-label">Parameters</div>
          <div className="stat-card-value">{metadata.parameters.length}</div>
          <div className="stat-card-sub">{metadata.parameters.join(', ')}</div>
        </div>
        <div className="stat-card stat-card--info">
          <div className="stat-card-label">Total Rows</div>
          <div className="stat-card-value">{metadata.total_rows}</div>
        </div>
      </div>

      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
        <button
          className={`btn ${activeTab === 'stats' ? 'btn--primary' : 'btn--secondary'} btn--sm`}
          onClick={() => setActiveTab('stats')}
        >
          Parameter Statistics
        </button>
        <button
          className={`btn ${activeTab === 'data' ? 'btn--primary' : 'btn--secondary'} btn--sm`}
          onClick={() => setActiveTab('data')}
        >
          Raw Data Table
        </button>
      </div>

      {activeTab === 'stats' && (
        <>
          {/* Parameter statistics table */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <h3 className="card-title">Parameter Statistics (at 168h)</h3>
            </div>
            <div className="card-body">
              <div className="data-table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Parameter</th>
                      <th>Unit</th>
                      <th>Count</th>
                      <th>Mean</th>
                      <th>Std</th>
                      <th>Median</th>
                      <th>Min</th>
                      <th>Max</th>
                      <th>Q1</th>
                      <th>Q3</th>
                      <th>IQR</th>
                      <th>CV</th>
                      <th>Abs Max</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metadata.parameter_stats.map((s) => (
                      <tr key={s.parameter}>
                        <td><strong>{s.parameter}</strong></td>
                        <td>{s.unit}</td>
                        <td className="numeric">{s.count}</td>
                        <td className="numeric">{s.mean.toFixed(2)}</td>
                        <td className="numeric">{s.std.toFixed(2)}</td>
                        <td className="numeric">{s.median.toFixed(2)}</td>
                        <td className="numeric">{s.min.toFixed(2)}</td>
                        <td className="numeric">{s.max.toFixed(2)}</td>
                        <td className="numeric">{s.q1.toFixed(2)}</td>
                        <td className="numeric">{s.q3.toFixed(2)}</td>
                        <td className="numeric">{s.iqr.toFixed(2)}</td>
                        <td className="numeric">{s.cv != null ? s.cv.toFixed(4) : '—'}</td>
                        <td className="numeric" style={{ color: 'var(--color-critical)', fontWeight: 600 }}>
                          {s.abs_max.toFixed(1)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Parameter Range Overview</h3>
              </div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={statsChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Min" fill="#85c1e9" name="Min" />
                    <Bar dataKey="Mean" fill="#2980b9" name="Mean" />
                    <Bar dataKey="Max" fill="#1a5276" name="Max" />
                    <Bar dataKey="Abs_Max" fill="#c0392b" name="Abs Max" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Dispersion (IQR & Std Dev)</h3>
              </div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={rangeChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="IQR" fill="#27ae60" name="IQR" />
                    <Bar dataKey="Std" fill="#e67e22" name="Std Dev" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'data' && rawData && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Raw Data ({rawData.row_count} rows)</h3>
          </div>
          <div className="card-body">
            <div className="data-table-wrapper" style={{ maxHeight: '500px', overflow: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    {rawData.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rawData.data.slice(0, 100).map((row, i) => (
                    <tr key={i}>
                      {rawData.columns.map((col) => (
                        <td key={col} className={typeof row[col] === 'number' ? 'numeric' : ''}>
                          {row[col] != null ? String(row[col]) : '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {rawData.data.length > 100 && (
                <div style={{ padding: '12px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>
                  Showing first 100 of {rawData.data.length} rows
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </PageShell>
  );
}
