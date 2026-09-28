/**
 * Upload page — CSV upload with drag-drop and demo data loading.
 */

import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import PageShell from '../components/layout/PageShell';
import { uploadCSV, loadDemoData, validateCSV } from '../api/client';
import type { BatchMetadata, ValidationResult } from '../types';

export default function UploadPage() {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [result, setResult] = useState<BatchMetadata | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const resetState = () => {
    setResult(null);
    setValidation(null);
    setError(null);
  };

  const handleFile = useCallback(async (file: File) => {
    resetState();
    setSelectedFile(file);

    // Auto-validate
    setValidating(true);
    try {
      const vResult = await validateCSV(file);
      setValidation(vResult);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Validation failed');
    } finally {
      setValidating(false);
    }
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError(null);
    try {
      const meta = await uploadCSV(selectedFile);
      setResult(meta);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleLoadDemo = async () => {
    resetState();
    setLoadingDemo(true);
    try {
      const meta = await loadDemoData();
      setResult(meta);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load demo data');
    } finally {
      setLoadingDemo(false);
    }
  };

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <PageShell
      title="Upload Screening Data"
      subtitle="Upload a CSV dataset or load the synthetic demo data for analysis"
    >
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        {/* Upload zone */}
        <div>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Upload CSV File</h3>
            </div>
            <div className="card-body">
              <div
                className={`upload-zone${dragActive ? ' upload-zone--active' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={onDrop}
                onClick={() => inputRef.current?.click()}
                role="button"
                tabIndex={0}
                aria-label="Drop CSV file here or click to browse"
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click(); }}
              >
                <div className="upload-zone-icon">📁</div>
                <div className="upload-zone-text">
                  {selectedFile ? selectedFile.name : 'Drop CSV file here or click to browse'}
                </div>
                <div className="upload-zone-hint">
                  Accepted format: .csv with required columns (Component_ID, Batch_ID, Parameter, Unit, Abs_Max, Value_0h, Value_24h, Value_96h, Value_168h)
                </div>
                <input
                  ref={inputRef}
                  type="file"
                  accept=".csv"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFile(file);
                  }}
                  aria-label="Select CSV file"
                />
              </div>

              {/* Validation result */}
              {validating && (
                <div className="loading-overlay">
                  <span className="spinner" /> Validating...
                </div>
              )}

              {validation && (
                <div style={{ marginTop: '16px' }}>
                  <div className={`alert ${validation.is_valid ? 'alert--success' : 'alert--error'}`}>
                    <span aria-hidden="true">{validation.is_valid ? '✓' : '✗'}</span>
                    <div>
                      <strong>{validation.is_valid ? 'Validation passed' : 'Validation failed'}</strong>
                      <span style={{ marginLeft: '8px' }}>
                        {validation.row_count} rows, {validation.column_count} columns
                      </span>
                    </div>
                  </div>

                  {validation.issues.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      <strong style={{ fontSize: '0.82rem' }}>Issues:</strong>
                      <ul style={{ margin: '4px 0 0', paddingLeft: '20px', fontSize: '0.8rem', color: 'var(--color-critical)' }}>
                        {validation.issues.map((issue, i) => (
                          <li key={i}><strong>{issue.column}:</strong> {issue.message}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {validation.warnings.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      <strong style={{ fontSize: '0.82rem' }}>Warnings:</strong>
                      <ul style={{ margin: '4px 0 0', paddingLeft: '20px', fontSize: '0.8rem', color: 'var(--color-warning)' }}>
                        {validation.warnings.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {validation.is_valid && (
                    <button
                      className="btn btn--primary"
                      style={{ marginTop: '12px' }}
                      onClick={handleUpload}
                      disabled={uploading}
                    >
                      {uploading ? (
                        <><span className="spinner" /> Uploading...</>
                      ) : (
                        'Upload & Process'
                      )}
                    </button>
                  )}
                </div>
              )}

              {error && (
                <div className="alert alert--error" style={{ marginTop: '16px' }}>
                  <span aria-hidden="true">⚠</span> {error}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar: Demo data + format info */}
        <div>
          {/* Demo data card */}
          <div className="card" style={{ marginBottom: '16px' }}>
            <div className="card-header">
              <h3 className="card-title">Demo Data</h3>
              <span className="badge badge--demo">SYNTHETIC</span>
            </div>
            <div className="card-body">
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                Load a pre-generated synthetic dataset with 200 components × 4 parameters.
                Includes healthy, anomalous, and drift-defect components for demonstration.
              </p>
              <div className="alert alert--demo" style={{ marginBottom: '12px', fontSize: '0.78rem' }}>
                <span aria-hidden="true">⚠</span>
                <span>Synthetic data only. Thresholds do not represent actual engineering limits.</span>
              </div>
              <button
                className="btn btn--secondary btn--lg"
                style={{ width: '100%' }}
                onClick={handleLoadDemo}
                disabled={loadingDemo}
              >
                {loadingDemo ? (
                  <><span className="spinner" /> Loading...</>
                ) : (
                  '📦 Load Demo Data'
                )}
              </button>
            </div>
          </div>

          {/* Expected format */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Expected CSV Format</h3>
            </div>
            <div className="card-body" style={{ fontSize: '0.78rem' }}>
              <div className="data-table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Type</th>
                      <th>Required</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ['Component_ID', 'string', true],
                      ['Batch_ID', 'string', true],
                      ['Parameter', 'string', true],
                      ['Unit', 'string', true],
                      ['Abs_Max', 'float', true],
                      ['Value_0h', 'float', true],
                      ['Value_24h', 'float', true],
                      ['Value_96h', 'float', true],
                      ['Value_168h', 'float', true],
                      ['Status', 'string', false],
                    ].map(([col, type, req]) => (
                      <tr key={col as string}>
                        <td><code>{col as string}</code></td>
                        <td>{type as string}</td>
                        <td>{req ? '✓' : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Success result */}
      {result && (
        <div className="card" style={{ marginTop: '24px' }}>
          <div className="card-header">
            <h3 className="card-title">✓ Data Loaded Successfully</h3>
            {result.is_demo && <span className="badge badge--demo">SYNTHETIC DATA</span>}
          </div>
          <div className="card-body">
            <div className="stat-grid">
              <div className="stat-card stat-card--info">
                <div className="stat-card-label">Batch ID</div>
                <div className="stat-card-value" style={{ fontSize: '1rem' }}>{result.batch_id}</div>
              </div>
              <div className="stat-card stat-card--info">
                <div className="stat-card-label">Components</div>
                <div className="stat-card-value">{result.total_components}</div>
              </div>
              <div className="stat-card stat-card--info">
                <div className="stat-card-label">Total Rows</div>
                <div className="stat-card-value">{result.total_rows}</div>
              </div>
              <div className="stat-card stat-card--info">
                <div className="stat-card-label">Parameters</div>
                <div className="stat-card-value">{result.parameters.length}</div>
                <div className="stat-card-sub">{result.parameters.join(', ')}</div>
              </div>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
              <button className="btn btn--primary" onClick={() => navigate(`/batch?id=${result.batch_id}`)}>
                View Batch Overview →
              </button>
              <button className="btn btn--secondary" onClick={() => navigate('/')}>
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      )}
    </PageShell>
  );
}
