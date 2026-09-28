# System Architecture & Design

> **AI-Driven Component Burn-In & Screening**  
> Scalable, modular architecture for environmental stress screening (burn-in) anomaly detection and parametric drift prediction.  
> *Engineering Prototype — Not an official ISRO system.*

---

## 1. High-Level Modular Project Structure

The codebase is organized into five decoupled production-grade modules:

```
SIH/
├── frontend/             # Single Page Application (React 19 + TypeScript + Vite + Tailwind CSS)
│   ├── src/
│   │   ├── api/          # Typed API client with complete backend endpoints
│   │   ├── components/   # Reusable UI components & layouts (Sidebar, Header, Shell)
│   │   ├── pages/        # Dashboard, Upload, BatchOverview, Anomaly, Drift, Detail, Reports
│   │   └── types/        # TypeScript schemas mirroring backend Pydantic models
│   └── package.json
│
├── backend/              # Python FastAPI REST API Service
│   ├── main.py           # Application entry point, CORS middleware, dual /health routing
│   ├── config.py         # System paths, validation schemas, column aliases, thresholds
│   ├── models/           # Pydantic schemas (schemas.py) and enums (enums.py)
│   ├── routers/          # API route definitions (data.py, analysis.py, reports.py)
│   ├── services/         # Business logic (data_service.py validation & stats)
│   └── storage/          # Local persistent file store (uploads/ and results/)
│
├── ml/                   # Standalone, Reusable Machine Learning Package
│   ├── synthetic/        # Realistic burn-in dataset generator with deterministic seeds
│   │   └── generator.py  # 8 defect archetypes, multi-parameter physical drift modeling
│   ├── features/         # Parametric time-series feature engineering pipeline
│   │   └── extractor.py  # Checkpoint slopes, acceleration, curvature, proximity ratios
│   ├── models/           # Module A (outlier detectors) & Module B (drift predictors) stubs
│   └── evaluation/       # Precision, recall, F1, MAE, RMSE metrics calculation
│
├── data/                 # Data Assets, Benchmarks, and Verification Samples
│   ├── synthetic/        # Pre-generated benchmark screening & labeled evaluation datasets
│   ├── samples/          # Test CSVs (valid batches, duplicate errors, unit mismatches, etc.)
│   └── schemas/          # Schema documentation and data dictionaries
│
└── docs/                 # Engineering Specifications & Documentation
    ├── ARCHITECTURE.md   # Architectural design, data flows, and subsystem specifications
    ├── DATA_DICTIONARY.md# Complete field dictionary, valid ranges, and ML roles
    ├── MODEL_CARD.md     # Machine learning model cards, limitations, and ethical guidelines
    ├── DEMO_GUIDE.md     # Step-by-step evaluation guide for reviewers
    └── IMPLEMENTATION_STATUS.md # Current completion status, verified APIs, and next tasks
```

---

## 2. End-to-End System Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Data Ingestion Layer                          │
│                                                                        │
│   User CSV Upload       Deterministic Synthetic Generator (seed=42)    │
│   (Any parameters)      (500 components × 5 params = 2500 measurements)│
└───────────────────┬────────────────────────────┬───────────────────────┘
                    │                            │
                    ▼                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Validation & Standardization Engine                  │
│                                                                        │
│  [1] File Format & Parseability Verification                           │
│  [2] Canonical Column Resolution (Flexible Aliasing)                   │
│  [3] Required Column Enforcement                                       │
│  [4] Missing Value & Null Row Detection                                │
│  [5] Duplicate Component-Parameter Detection                           │
│  [6] Non-Numeric & Infinite Value Detection                            │
│  [7] Checkpoint Integrity (0h, 24h, 96h, 168h finite values)           │
│  [8] Batch Unit Consistency per Parameter                              │
│  [9] Specification Integrity (spec_min < spec_max & consistency)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                        ┌───────────┴───────────┐
                   Valid│                       │Invalid
                        ▼                       ▼
┌────────────────────────────────────────┐   ┌───────────────────────────┐
│     Standardized In-Memory / File      │   │ Return Detailed HTTP 422  │
│   Storage (backend/storage/uploads)    │   │ Diagnostics (Rows & Types)│
└───────────────────┬────────────────────┘   └───────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Feature Engineering Pipeline (ml/)                   │
│                                                                        │
│  • Slopes (dt=24h, 72h): slope_0_24, slope_24_96, slope_96_168        │
│  • Acceleration: accel_early_to_mid, accel_mid_to_late                 │
│  • Scale-Invariant Shifts: ratio_24_0, relative_drift_total            │
│  • Safety Margins: proximity_to_spec                                   │
│  • Statistical Population Distances: batch_mean, z_score, iqr_distance  │
└───────────────────┬────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    FastAPI REST Endpoints Layer                        │
│                                                                        │
│  GET  /health                   - Health check & API version           │
│  POST /api/data/upload          - Validates, standardizes, stores CSV  │
│  POST /api/data/generate-demo   - Deterministic synthetic generator    │
│  GET  /api/data/summary         - Parametric stats, yield, defects     │
│  GET  /api/data/components      - Paginated, filterable component list │
│  GET  /api/data/components/{id} - Full time-series & population curves │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   React 19 SPA Frontend (Port 5173)                    │
│                                                                        │
│  • Institutional QA Engineering Theme (Slate & Deep Blue Palette)      │
│  • Batch Overview & Parametric Distribution Charts (Recharts)          │
│  • Component Inspection & Time-Series Trajectory Visualizer            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Foundation & Ingestion Rules

The data ingestion pipeline enforces nine deterministic validation checks to guarantee that corrupted data never pollutes ML training or screening decisions. Bad rows are never silently discarded.

1. **File Type Validation**: Rejects non-CSV files; validates encoding and delimiter structure.
2. **Column Alias Resolution**: Automatically resolves diverse naming conventions (e.g. `Component_ID` vs `component_id`, `Abs_Max` vs `spec_max`, `Parameter` vs `parameter_name`).
3. **Required Column Check**: Enforces presence of core burn-in attributes (`component_id`, `batch_id`, `parameter_name`, `unit`, `spec_max`, `value_0h`, `value_24h`, `value_96h`, `value_168h`).
4. **Missing Value Detection**: Detects empty or null entries, tracking exact row indices and field names.
5. **Duplicate Component Detection**: Flags duplicate `(component_id, parameter_name)` entries in the same batch.
6. **Data Type & Numerical Validation**: Verifies numbers are parseable floats; rejects NaN, Inf, and -Inf.
7. **Checkpoint Integrity**: Confirms all 4 chronological checkpoints (0h, 24h, 96h, 168h) are present.
8. **Unit Consistency**: Verifies that every parameter uses a single consistent physical unit across the entire batch (e.g. catches accidental mixtures of `µA` and `mA`).
9. **Specification Validation**: Verifies that `spec_min < spec_max` and alerts on conflicting limits within the batch.

---

## 4. Multi-Parameter Scalability Architecture

A critical architectural requirement is that **new electrical parameters can be added without modifying the codebase**.

To achieve this:
- **No hardcoded parameter enumerations**: The backend dynamically groups data by `parameter_name`.
- **Dynamic statistical aggregation**: Parameter statistics (mean, median, IQR, std, min, max, cv) are computed dynamically for every unique parameter detected.
- **Generic feature extraction**: Physical drift calculations operate on checkpoint values regardless of the parameter name.
- **Model modularity**: Outlier models and drift regressors fit separate per-parameter estimators keyed dynamically to `parameter_name`.

---

## 5. Synthetic Generator & Problem-Specific Benchmarks

The synthetic generator (`ml/synthetic/generator.py`) generates high-fidelity burn-in screening datasets with deterministic seeds (`seed=42`) for reproducibility.

### The Targeted Problem Scenario
Traditional static screening relies on fixed datasheet limits (`spec_max`). Latent manufacturing defects frequently remain below static limits during burn-in, but display abnormal population behavior.

To simulate this:
- **Parameter**: `iddq`
- **Datasheet Absolute Limit (`spec_max`)**: `50.0 µA`
- **Healthy Batch Population**: Mean `12.0 µA`, Standard Deviation `1.1 µA` (Healthy range: `~9.5 – 14.5 µA`)
- **Population Outlier Component**: Starts at `42.0 – 47.5 µA`, finishes at `43.0 – 48.0 µA`
- **Static Screening Verdict**: `PASS` (below 50.0 µA)
- **Dynamic Anomaly Verdict**: `CRITICAL ANOMALY` ($Z > 25\sigma$, LOF/IF isolation)

### Defect Archetype Taxonomy
1. `HEALTHY` (70%): Centered population, physical thermal drift, Gaussian measurement noise.
2. `POPULATION_OUTLIER` (8%): Inside static limits, but extreme population outlier.
3. `MILD_DRIFT` (5%): Steady gradual drift at 3x-4x normal rate.
4. `STRONG_DRIFT` (5%): Linear rapid degradation climbing near `spec_max`.
5. `ACCELERATING_DRIFT` (4%): Normal at 0h/24h, superlinear acceleration at 96h/168h.
6. `EARLY_DRIFT` (3%): Infant mortality: sharp 0h→24h shift, then levels off.
7. `LATE_DRIFT` (3%): Normal through 96h, steep breakdown between 96h and 168h.
8. `STATIC_LIMIT_VIOLATION` (2%): Violates `spec_max` or `spec_min` at 168h.

---

## 6. REST API Endpoints

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health Check | Root health status, API version, and stage information. |
| `GET` | `/api/health` | API Health Check | Prefixed health check endpoint for reverse proxy compatibility. |
| `POST` | `/api/data/upload` | Upload CSV | Accepts CSV multipart upload, executes 9 validation rules, stores batch, and returns metadata. |
| `POST` | `/api/data/validate` | Validate CSV | Validates CSV upload without storing it; returns detailed issues and warnings. |
| `POST` | `/api/data/generate-demo` | Generate Benchmark | Generates deterministic synthetic dataset with specified seed and component count. |
| `POST` | `/api/data/demo` | Load Default Demo | Loads or regenerates default benchmark batch (`BATCH-DEMO-001`). |
| `GET` | `/api/data/summary` | Batch Summary | Descriptive stats, component types, yield, and defect distributions. |
| `GET` | `/api/data/components` | List Components | Paginated, filterable component list with all parameter measurements. |
| `GET` | `/api/data/components/{id}` | Component Profile | Full time-series checkpoints, computed drift rates, and population comparison for DUT. |
| `GET` | `/api/data/batches` | List Batches | Lists all available batches with component counts and analysis statuses. |
| `GET` | `/api/data/batch/{id}` | Batch Metadata | Retrieves metadata and parameter statistics for a batch. |
| `GET` | `/api/data/batch/{id}/data` | Raw Batch Data | Tabular raw data records for table display and inspection. |
