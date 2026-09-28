/**
 * API client for the Burn-In Screening backend.
 * All requests go through the Vite proxy (/api → localhost:8000).
 */

import type {
  BatchMetadata,
  BatchListItem,
  ValidationResult,
  BatchRawData,
  AnomalyResultsSummary,
  DriftResultsSummary,
  EvaluationResults,
  ComponentProfile,
  BatchSummaryResponse,
  ComponentListResponse,
  ComponentDetailResponse,
  GenerateDemoRequest,
} from '../types';

const BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = body?.detail?.message || body?.detail || res.statusText;
    throw new Error(typeof message === 'object' ? JSON.stringify(message) : message);
  }

  return res.json();
}

// ─── Data Endpoints ─────────────────────────────────────────────────────────

export async function uploadCSV(file: File): Promise<BatchMetadata> {
  const form = new FormData();
  form.append('file', file);

  const res = await fetch(`${BASE}/data/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail?.message || body?.detail || 'Upload failed');
  }
  return res.json();
}

export async function validateCSV(file: File): Promise<ValidationResult> {
  const form = new FormData();
  form.append('file', file);

  const res = await fetch(`${BASE}/data/validate`, { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail?.message || body?.detail || 'Validation failed');
  }
  return res.json();
}

export async function generateDemoData(payload?: GenerateDemoRequest): Promise<BatchMetadata> {
  return request<BatchMetadata>('/data/generate-demo', {
    method: 'POST',
    body: JSON.stringify(payload || { seed: 42, component_count: 500, batch_id: 'BATCH-DEMO-001' }),
  });
}

export async function loadDemoData(): Promise<BatchMetadata> {
  return request<BatchMetadata>('/data/demo', { method: 'POST' });
}

export async function getDataSummary(batchId?: string): Promise<BatchSummaryResponse> {
  const query = batchId ? `?batch_id=${encodeURIComponent(batchId)}` : '';
  return request<BatchSummaryResponse>(`/data/summary${query}`);
}

export async function getComponentsList(params?: {
  batchId?: string;
  componentType?: string;
  defectType?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}): Promise<ComponentListResponse> {
  const q = new URLSearchParams();
  if (params?.batchId) q.append('batch_id', params.batchId);
  if (params?.componentType) q.append('component_type', params.componentType);
  if (params?.defectType) q.append('defect_type', params.defectType);
  if (params?.search) q.append('search', params.search);
  if (params?.page) q.append('page', String(params.page));
  if (params?.pageSize) q.append('page_size', String(params.pageSize));

  const queryStr = q.toString() ? `?${q.toString()}` : '';
  return request<ComponentListResponse>(`/data/components${queryStr}`);
}

export async function getComponentDetail(componentId: string, batchId?: string): Promise<ComponentDetailResponse> {
  const query = batchId ? `?batch_id=${encodeURIComponent(batchId)}` : '';
  return request<ComponentDetailResponse>(`/data/components/${encodeURIComponent(componentId)}${query}`);
}

export async function listBatches(): Promise<BatchListItem[]> {
  return request<BatchListItem[]>('/data/batches');
}

export async function getBatchMetadata(batchId: string): Promise<BatchMetadata> {
  return request<BatchMetadata>(`/data/batch/${batchId}`);
}

export async function getBatchRawData(batchId: string): Promise<BatchRawData> {
  return request<BatchRawData>(`/data/batch/${batchId}/data`);
}

// ─── Analysis Endpoints ─────────────────────────────────────────────────────

export async function runAnomalyDetection(batchId: string): Promise<AnomalyResultsSummary> {
  return request<AnomalyResultsSummary>(`/analysis/anomaly/${batchId}`, { method: 'POST' });
}

export async function runDriftPrediction(batchId: string): Promise<DriftResultsSummary> {
  return request<DriftResultsSummary>(`/analysis/drift/${batchId}`, { method: 'POST' });
}

export async function getAnalysisResults(batchId: string): Promise<{
  anomaly?: AnomalyResultsSummary;
  drift?: DriftResultsSummary;
}> {
  return request(`/analysis/results/${batchId}`);
}

export async function getComponentProfile(batchId: string, componentId: string): Promise<ComponentProfile> {
  return request<ComponentProfile>(`/analysis/component/${batchId}/${componentId}`);
}

export async function getEvaluationMetrics(batchId: string): Promise<EvaluationResults> {
  return request<EvaluationResults>(`/analysis/metrics/${batchId}`);
}

// ─── Reports ────────────────────────────────────────────────────────────────

export async function getReport(batchId: string): Promise<unknown> {
  return request(`/reports/${batchId}`);
}

// ─── Health ─────────────────────────────────────────────────────────────────

export async function healthCheck(): Promise<{ status: string; service: string; version: string }> {
  return request('/health');
}
