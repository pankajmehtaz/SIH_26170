/**
 * TypeScript type definitions for the Burn-In Screening application.
 */

// ─── Enums ──────────────────────────────────────────────────────────────────

export type RiskLevel = 'NORMAL' | 'MONITOR' | 'WARNING' | 'CRITICAL';
export type ComponentStatus = 'PASS' | 'FAIL' | 'SUSPECT' | 'UNKNOWN';
export type AnalysisState = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'ERROR';
export type DefectType =
  | 'HEALTHY'
  | 'POPULATION_OUTLIER'
  | 'MILD_DRIFT'
  | 'STRONG_DRIFT'
  | 'ACCELERATING_DRIFT'
  | 'EARLY_DRIFT'
  | 'LATE_DRIFT'
  | 'STATIC_LIMIT_VIOLATION'
  | 'NOISY_MEASUREMENT'
  | 'UNKNOWN';

// ─── Data ───────────────────────────────────────────────────────────────────

export interface ValidationIssue {
  column: string;
  row?: number;
  message: string;
  severity: string;
  issue_type?: string;
}

export interface ValidationResult {
  is_valid: boolean;
  row_count: number;
  column_count: number;
  columns_found: string[];
  missing_columns: string[];
  error_count?: number;
  warning_count?: number;
  issues: ValidationIssue[];
  warnings: string[];
}

export interface ParameterStats {
  parameter: string;
  unit: string;
  spec_min?: number;
  abs_max: number;
  spec_max?: number;
  count: number;
  mean: number;
  std: number;
  median: number;
  min: number;
  max: number;
  q1: number;
  q3: number;
  iqr: number;
  cv?: number;
}

export interface BatchMetadata {
  batch_id: string;
  total_components: number;
  total_rows: number;
  parameters: string[];
  parameter_stats: ParameterStats[];
  is_demo: boolean;
  file_name?: string;
  random_seed?: number;
  component_types?: string[];
  generated_at?: string;
}

export interface BatchListItem {
  batch_id: string;
  total_components: number;
  parameters: string[];
  is_demo: boolean;
  has_anomaly_results: boolean;
  has_drift_results: boolean;
}

export interface BatchSummaryResponse {
  batch_id: string;
  total_components: number;
  total_rows: number;
  parameters: string[];
  component_types: string[];
  parameter_stats: ParameterStats[];
  defect_distribution?: Record<string, number>;
  static_screening_summary: {
    total_screened: number;
    static_pass_count: number;
    static_fail_count: number;
    static_pass_rate: number;
  };
  is_demo: boolean;
  file_name?: string;
  metadata?: Record<string, unknown>;
}

export interface ComponentSummaryItem {
  component_id: string;
  batch_id: string;
  component_type?: string;
  status: string;
  ground_truth_label?: string;
  defect_type?: string;
  parameters: Record<string, Record<string, unknown>>;
}

export interface ComponentListResponse {
  batch_id: string;
  total_components: number;
  page: number;
  page_size: number;
  total_pages: number;
  components: ComponentSummaryItem[];
}

export interface ComponentParameterDetail {
  parameter_name: string;
  unit: string;
  spec_min?: number;
  spec_max: number;
  value_0h: number;
  value_24h: number;
  value_96h: number;
  value_168h: number;
  slopes: Record<string, number>;
  batch_mean: number;
  batch_median: number;
  batch_std: number;
  z_score_168h: number;
  status: string;
}

export interface ComponentDetailResponse {
  component_id: string;
  batch_id: string;
  component_type?: string;
  status: string;
  ground_truth_label?: string;
  defect_type?: string;
  parameters: ComponentParameterDetail[];
}

export interface GenerateDemoRequest {
  seed?: number;
  component_count?: number;
  batch_id?: string;
}

// ─── Anomaly Detection (Module A) ───────────────────────────────────────────

export interface AnomalyMethodResult {
  method: string;
  is_anomaly: boolean;
  score: number;
  detail: string;
}

export interface AnomalyExplanation {
  summary: string;
  population_comparison: string;
  anomaly_score: number;
  current_value: number;
  abs_max: number;
  batch_mean: number;
  batch_median: number;
  batch_std: number;
  z_score: number;
  percentile: number;
  deviation_from_median: number;
  methods_flagged: string[];
  individual_scores: Record<string, number>;
}

export interface ComponentAnomalyResult {
  component_id: string;
  parameter: string;
  unit: string;
  risk_level: RiskLevel;
  composite_score: number;
  is_flagged: boolean;
  method_results: AnomalyMethodResult[];
  explanation?: AnomalyExplanation;
  value_0h: number;
  value_24h: number;
  value_96h: number;
  value_168h: number;
  abs_max: number;
}

export interface AnomalyResultsSummary {
  batch_id: string;
  total_components: number;
  flagged_count: number;
  risk_distribution: Record<string, number>;
  results: ComponentAnomalyResult[];
}

// ─── Drift Prediction (Module B) ────────────────────────────────────────────

export interface DriftPrediction {
  component_id: string;
  parameter: string;
  unit: string;
  predicted_168h: number;
  actual_168h?: number;
  prediction_error?: number;
  observed_slope_0_24: number;
  predicted_slope: number;
  safety_slope_upper: number;
  is_drift_risk: boolean;
  risk_level: RiskLevel;
  feature_contributions?: Record<string, number>;
  explanation?: string;
}

export interface DriftResultsSummary {
  batch_id: string;
  total_components: number;
  drift_risk_count: number;
  results: DriftPrediction[];
}

// ─── Evaluation ─────────────────────────────────────────────────────────────

export interface ClassificationMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  false_positive_rate: number;
  false_negative_rate: number;
  confusion_matrix: number[][];
  support: number;
}

export interface RegressionMetrics {
  mae: number;
  rmse: number;
  r2: number;
  per_parameter?: Record<string, Record<string, number>>;
}

export interface EvaluationResults {
  batch_id: string;
  classification?: ClassificationMetrics;
  regression?: RegressionMetrics;
}

// ─── Component Profile ──────────────────────────────────────────────────────

export interface ComponentMeasurement {
  component_id: string;
  parameter: string;
  unit: string;
  abs_max: number;
  value_0h: number;
  value_24h: number;
  value_96h: number;
  value_168h: number;
  status: ComponentStatus;
}

export interface ComponentProfile {
  component_id: string;
  batch_id: string;
  measurements: ComponentMeasurement[];
  anomaly_results?: ComponentAnomalyResult[];
  drift_predictions?: DriftPrediction[];
  overall_risk: RiskLevel;
  recommended_disposition: string;
  explanation_summary: string;
}

// ─── Raw Data ───────────────────────────────────────────────────────────────

export interface BatchRawData {
  batch_id: string;
  columns: string[];
  data: Record<string, unknown>[];
  row_count: number;
}
