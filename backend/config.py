"""
Application configuration, storage paths, validation schemas, and constants.

Design decisions:
- Clean modular directory layout with root data/ and ml/ integration.
- Dynamic parameter detection: new electrical parameters are supported seamlessly.
- Robust column aliasing supports both snake_case and PascalCase CSV headers.
- Deterministic seeds for reproducible synthetic benchmarks.
- Conservative thresholds prioritizing recall (minimizing false negatives).
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
STORAGE_DIR = BACKEND_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
RESULTS_DIR = STORAGE_DIR / "results"

# Data directories
DATA_DIR = ROOT_DIR / "data"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
SAMPLES_DATA_DIR = DATA_DIR / "samples"
DEMO_DATA_DIR = BACKEND_DIR / "demo" / "synthetic_data"

# Add project root to sys.path so backend can import from ml
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure runtime directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DATA_DIR.mkdir(parents=True, exist_ok=True)
DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# CORS (for local dev — frontend on :5173, backend on :8000)
# ---------------------------------------------------------------------------
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

# ---------------------------------------------------------------------------
# Anomaly Detection Defaults (Module A)
# ---------------------------------------------------------------------------
ZSCORE_THRESHOLD = 2.5          # Modified z-score cutoff (lower → more sensitive)
IQR_MULTIPLIER = 1.5            # IQR fence multiplier
ISOLATION_FOREST_CONTAMINATION = 0.1   # Expected anomaly fraction
LOF_NEIGHBORS = 20              # LOF n_neighbors
ENSEMBLE_MIN_VOTES = 2          # Minimum detector agreement to flag

# ---------------------------------------------------------------------------
# Drift Prediction Defaults (Module B)
# ---------------------------------------------------------------------------
SAFETY_SLOPE_SIGMA = 2.0        # MAD multipliers for safety slope envelope
SMALL_BATCH_THRESHOLD = 50      # Below this → use Ridge instead of XGBoost
XGBOOST_PARAMS = {
    "n_estimators": 100,
    "max_depth": 4,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
}

# ---------------------------------------------------------------------------
# Risk Classification
# ---------------------------------------------------------------------------
RISK_THRESHOLDS = {
    "critical_anomaly_score": 0.9,
    "warning_anomaly_score": 0.6,
    "monitor_anomaly_score": 0.3,
}

# ---------------------------------------------------------------------------
# Data Schema & Aliasing Architecture
# ---------------------------------------------------------------------------
REQUIRED_CANONICAL_COLUMNS = [
    "component_id",
    "batch_id",
    "parameter_name",
    "unit",
    "spec_max",
    "value_0h",
    "value_24h",
    "value_96h",
    "value_168h",
]

OPTIONAL_CANONICAL_COLUMNS = [
    "component_type",
    "spec_min",
    "measurement_temperature",
    "measurement_voltage",
    "timestamp",
    "ground_truth_label",
    "defect_type",
    "status",
]

COLUMN_ALIASES: dict[str, list[str]] = {
    "component_id": ["component_id", "componentid", "comp_id", "compid", "component"],
    "batch_id": ["batch_id", "batchid", "lot_id", "lotid", "batch"],
    "component_type": ["component_type", "componenttype", "part_type", "type", "device_type"],
    "parameter_name": ["parameter_name", "parameter", "param", "param_name", "test_parameter"],
    "unit": ["unit", "units"],
    "spec_min": ["spec_min", "specmin", "abs_min", "min_spec", "lower_limit", "min_limit"],
    "spec_max": ["spec_max", "specmax", "abs_max", "max_spec", "upper_limit", "max_limit"],
    "value_0h": ["value_0h", "val_0h", "0h", "t0", "t_0", "val0", "value0h"],
    "value_24h": ["value_24h", "val_24h", "24h", "t24", "t_24", "val24", "value24h"],
    "value_96h": ["value_96h", "val_96h", "96h", "t96", "t_96", "val96", "value96h"],
    "value_168h": ["value_168h", "val_168h", "168h", "t168", "t_168", "val168", "value168h"],
    "measurement_temperature": ["measurement_temperature", "temperature", "temp", "temp_c", "chamber_temp"],
    "measurement_voltage": ["measurement_voltage", "voltage", "bias_voltage", "vcc", "vdd"],
    "timestamp": ["timestamp", "time", "date", "created_at", "test_date"],
    "ground_truth_label": ["ground_truth_label", "true_label", "ground_truth", "label"],
    "defect_type": ["defect_type", "anomaly_type", "defect", "failure_mode"],
    "status": ["status", "screening_status", "result", "pass_fail"],
}

# Legacy column lists for backward compatibility
REQUIRED_COLUMNS = [
    "Component_ID",
    "Batch_ID",
    "Parameter",
    "Unit",
    "Abs_Max",
    "Value_0h",
    "Value_24h",
    "Value_96h",
    "Value_168h",
]

OPTIONAL_COLUMNS = ["Status", "Component_Type", "Spec_Min", "True_Label", "Defect_Type"]

# Recommended common parameters (system supports ANY valid numerical parameter)
COMMON_PARAMETERS = [
    "iddq",
    "leakage_current",
    "propagation_delay",
    "voltage",
    "standby_current",
    "vout",
]

# Synthetic Demo Defaults
DEFAULT_DEMO_SEED = 42
DEFAULT_DEMO_COMPONENTS = 500
