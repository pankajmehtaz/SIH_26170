"""
Pydantic schemas for API request/response models.
Comprehensive data model supporting component-level burn-in screening,
CSV validation with detailed diagnostics, parameter statistics,
and analytical results.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field

from .enums import RiskLevel, ComponentStatus, DefectType, ValidationIssueType


# ---------------------------------------------------------------------------
# Data Schemas & Validation
# ---------------------------------------------------------------------------

class ValidationIssue(BaseModel):
    """A single data validation issue with location and categorization."""
    column: str
    row: Optional[int] = None
    message: str
    severity: str = "error"  # "error" | "warning"
    issue_type: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of comprehensive CSV screening validation."""
    is_valid: bool
    row_count: int
    column_count: int
    columns_found: list[str]
    missing_columns: list[str]
    error_count: int = 0
    warning_count: int = 0
    issues: list[ValidationIssue]
    warnings: list[str] = []


class ParameterStats(BaseModel):
    """Descriptive statistics for a single parameter within a batch."""
    parameter: str
    unit: str
    spec_min: Optional[float] = None
    abs_max: float
    spec_max: Optional[float] = None
    count: int
    mean: float
    std: float
    median: float
    min: float
    max: float
    q1: float
    q3: float
    iqr: float
    cv: Optional[float] = None  # coefficient of variation


class BatchMetadata(BaseModel):
    """Summary metadata for an uploaded or generated batch."""
    batch_id: str
    total_components: int
    total_rows: int
    parameters: list[str]
    parameter_stats: list[ParameterStats]
    is_demo: bool = False
    file_name: Optional[str] = None
    random_seed: Optional[int] = None
    component_types: Optional[list[str]] = None
    generated_at: Optional[str] = None


class BatchListItem(BaseModel):
    """Lightweight batch info for listing."""
    batch_id: str
    total_components: int
    parameters: list[str]
    is_demo: bool = False
    has_anomaly_results: bool = False
    has_drift_results: bool = False


# ---------------------------------------------------------------------------
# Component Measurement & Profile Schemas
# ---------------------------------------------------------------------------

class ComponentMeasurement(BaseModel):
    """Raw measurements for a single component × parameter."""
    component_id: str
    batch_id: Optional[str] = None
    component_type: Optional[str] = None
    parameter: str = Field(..., alias="parameter_name")
    unit: str
    spec_min: Optional[float] = None
    abs_max: float = Field(..., alias="spec_max")
    value_0h: float
    value_24h: float
    value_96h: float
    value_168h: float
    measurement_temperature: Optional[float] = None
    measurement_voltage: Optional[float] = None
    timestamp: Optional[str] = None
    status: ComponentStatus = ComponentStatus.UNKNOWN
    ground_truth_label: Optional[str] = None
    defect_type: Optional[str] = None

    class Config:
        populate_by_name = True


class ComponentSummaryItem(BaseModel):
    """Summary view for component row in inventory or screening table."""
    component_id: str
    batch_id: str
    component_type: Optional[str] = None
    status: str = "PASS"
    ground_truth_label: Optional[str] = None
    defect_type: Optional[str] = None
    parameters: dict[str, dict[str, Any]]


class ComponentListResponse(BaseModel):
    """Paginated list of components for a batch."""
    batch_id: str
    total_components: int
    page: int
    page_size: int
    total_pages: int
    components: list[ComponentSummaryItem]


class ComponentParameterDetail(BaseModel):
    """Detailed time-series and population context for a parameter."""
    parameter_name: str
    unit: str
    spec_min: Optional[float] = None
    spec_max: float
    value_0h: float
    value_24h: float
    value_96h: float
    value_168h: float
    slopes: dict[str, float]
    batch_mean: float
    batch_median: float
    batch_std: float
    z_score_168h: float
    status: str


class ComponentDetailResponse(BaseModel):
    """Comprehensive single-component view with all parameters and stats."""
    component_id: str
    batch_id: str
    component_type: Optional[str] = None
    status: str = "PASS"
    ground_truth_label: Optional[str] = None
    defect_type: Optional[str] = None
    parameters: list[ComponentParameterDetail]


class BatchSummaryResponse(BaseModel):
    """High-level batch screening summary."""
    batch_id: str
    total_components: int
    total_rows: int
    parameters: list[str]
    component_types: list[str]
    parameter_stats: list[ParameterStats]
    defect_distribution: Optional[dict[str, int]] = None
    static_screening_summary: dict[str, Any]
    is_demo: bool = False
    file_name: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class GenerateDemoRequest(BaseModel):
    """Request payload for deterministic demo data generation."""
    seed: int = Field(default=42, description="Deterministic random seed")
    component_count: int = Field(default=500, ge=10, le=5000, description="Total components to generate")
    batch_id: str = Field(default="BATCH-DEMO-001", description="Identifier for generated batch")


# ---------------------------------------------------------------------------
# Anomaly Detection Schemas (Module A)
# ---------------------------------------------------------------------------

class AnomalyMethodResult(BaseModel):
    """Result from a single anomaly detection method."""
    method: str
    is_anomaly: bool
    score: float = Field(ge=0.0, le=1.0)
    detail: str


class AnomalyExplanation(BaseModel):
    """Human-readable explanation for a flagged component."""
    summary: str
    population_comparison: str
    anomaly_score: float
    current_value: float
    abs_max: float
    batch_mean: float
    batch_median: float
    batch_std: float
    z_score: float
    percentile: float
    deviation_from_median: float
    methods_flagged: list[str]
    individual_scores: dict[str, float]


class ComponentAnomalyResult(BaseModel):
    """Anomaly detection result for one component × parameter."""
    component_id: str
    parameter: str
    unit: str
    risk_level: RiskLevel
    composite_score: float = Field(ge=0.0, le=1.0)
    is_flagged: bool
    method_results: list[AnomalyMethodResult]
    explanation: Optional[AnomalyExplanation] = None
    value_0h: float
    value_24h: float
    value_96h: float
    value_168h: float
    abs_max: float


class AnomalyResultsSummary(BaseModel):
    """Aggregate anomaly detection results for a batch."""
    batch_id: str
    total_components: int
    flagged_count: int
    risk_distribution: dict[str, int]
    results: list[ComponentAnomalyResult]


# ---------------------------------------------------------------------------
# Drift Prediction Schemas (Module B)
# ---------------------------------------------------------------------------

class DriftPrediction(BaseModel):
    """Drift prediction for one component × parameter."""
    component_id: str
    parameter: str
    unit: str
    predicted_168h: float
    actual_168h: Optional[float] = None
    prediction_error: Optional[float] = None
    observed_slope_0_24: float
    predicted_slope: float
    safety_slope_upper: float
    is_drift_risk: bool
    risk_level: RiskLevel
    feature_contributions: Optional[dict[str, float]] = None
    explanation: Optional[str] = None


class DriftResultsSummary(BaseModel):
    """Aggregate drift prediction results for a batch."""
    batch_id: str
    total_components: int
    drift_risk_count: int
    results: list[DriftPrediction]


# ---------------------------------------------------------------------------
# Evaluation Metrics Schemas
# ---------------------------------------------------------------------------

class ClassificationMetrics(BaseModel):
    """Anomaly detection evaluation metrics."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    false_negative_rate: float
    confusion_matrix: list[list[int]]  # [[TN, FP], [FN, TP]]
    support: int


class RegressionMetrics(BaseModel):
    """Drift prediction evaluation metrics."""
    mae: float
    rmse: float
    r2: float
    per_parameter: Optional[dict[str, dict[str, float]]] = None


class EvaluationResults(BaseModel):
    """Combined evaluation results."""
    batch_id: str
    classification: Optional[ClassificationMetrics] = None
    regression: Optional[RegressionMetrics] = None


# ---------------------------------------------------------------------------
# Combined Component Profile
# ---------------------------------------------------------------------------

class ComponentProfile(BaseModel):
    """Full component profile combining anomaly + drift results."""
    component_id: str
    batch_id: str
    measurements: list[ComponentMeasurement]
    anomaly_results: Optional[list[ComponentAnomalyResult]] = None
    drift_predictions: Optional[list[DriftPrediction]] = None
    overall_risk: RiskLevel = RiskLevel.NORMAL
    recommended_disposition: str = "No action required"
    explanation_summary: str = ""
