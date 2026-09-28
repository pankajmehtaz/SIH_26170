# AI-Driven Anomaly Detection in Component Burn-In & Screening

> **Engineering Decision-Support Prototype**  
> *Indian Space Research Organisation (ISRO) Problem Statement — Smart India Hackathon (SIH)*  
> **DISCLAIMER:** This is an independent engineering prototype developed for demonstration and algorithmic evaluation. It is **NOT** an official ISRO system. All demo thresholds and datasets are synthetic and clearly labeled as such.

---

## Overview

High-reliability electronic components (FPGAs, ADCs, Op-Amps, Voltage Regulators, DSPs) undergo environmental stress screening and burn-in testing (e.g. 125°C chamber temperature, voltage bias) to eliminate infant mortality and identify latent defects.

Traditional screening relies heavily on **static parametric pass/fail limits** ($V_{\text{out}} \ge \text{spec\_min}$, $I_{\text{ddq}} \le \text{spec\_max}$). However, critical latent defects can stay entirely within datasheet limits while exhibiting abnormal population behavior or subtle degradation/drift over time.

This prototype addresses the gap through two core analytical modules:
- **Module A — Dynamic Outlier Detection**: Identifies components that are anomalous relative to their batch population, even when comfortably inside absolute specification limits (e.g., $I_{\text{ddq}} = 45\,\mu\text{A}$ where batch mean is $12\,\mu\text{A}$ and limit is $50\,\mu\text{A}$).
- **Module B — Time-Series Drift Prediction**: Predicts 168h end-of-test values from early burn-in measurements (0h, 24h) and flags components with abnormal drift trajectories or accelerating degradation.

---

## Project Structure

```
SIH/
├── frontend/             # React 19 + TypeScript + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── api/          # Typed API client
│   │   ├── components/   # Layouts, Sidebar, Header, PageShell
│   │   ├── pages/        # Dashboard, Upload, BatchOverview, Anomaly, Drift, Detail, Reports
│   │   └── types/        # TypeScript type schemas
│   └── package.json
│
├── backend/              # FastAPI Python REST backend
│   ├── main.py           # App entry, CORS, dual /health routing
│   ├── config.py         # Configurable thresholds, paths, column aliases
│   ├── models/           # Pydantic schemas (schemas.py) & enums (enums.py)
│   ├── routers/          # API route definitions (data.py, analysis.py, reports.py)
│   ├── services/         # Business logic & CSV validation engine (data_service.py)
│   └── storage/          # Local file-based persistence (uploads/ and results/)
│
├── ml/                   # Modular ML package
│   ├── synthetic/        # Realistic burn-in generator with deterministic seeds
│   │   └── generator.py  # Multi-parameter trajectories with 8 defect archetypes
│   ├── features/         # Time-series feature extraction (slopes, acceleration, ratios)
│   ├── models/           # ML model definitions (Module A and Module B)
│   └── evaluation/       # Performance evaluation metrics
│
├── data/                 # Datasets & Benchmarks
│   ├── synthetic/        # Pre-generated benchmark batches (full & screening CSVs)
│   ├── samples/          # Test CSVs (valid sample, duplicate errors, unit mismatches, etc.)
│   └── schemas/          # Schema documentation
│
├── docs/                 # System Documentation
│   ├── ARCHITECTURE.md   # Architectural design, data flows, validation pipeline
│   ├── DATA_DICTIONARY.md# Field definitions, units, valid ranges, ML roles
│   ├── MODEL_CARD.md     # Model specifications and limitations
│   ├── DEMO_GUIDE.md     # Step-by-step evaluator guide
│   └── IMPLEMENTATION_STATUS.md # Current status & test verification
│
└── tests/                # Automated Test Suite
    └── test_data_foundation.py # Unittests for generator, validation, and APIs
```

---

## Quick Start

### 1. Prerequisites

- **Python 3.9+**
- **Node.js 18+** & **npm**

### 2. Backend Setup & Run

```bash
# From repository root:
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Run automated tests
python3 -m unittest tests/test_data_foundation.py

# Start the FastAPI server
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive Swagger documentation is available at `http://localhost:8000/docs`.

### 3. Frontend Setup & Run

```bash
# In a new terminal window:
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. All API requests are automatically proxied to the backend on port 8000.

---

## Data Foundation & Workflow

### Generating Demo / Benchmark Data

You can generate a reproducible benchmark dataset with deterministic random seed (`seed=42`) via CLI or REST API:

**Via CLI:**
```bash
./venv/bin/python3 ml/synthetic/generator.py
```

**Via REST API:**
```bash
curl -X POST http://localhost:8000/api/data/generate-demo \
  -H "Content-Type: application/json" \
  -d '{"seed": 42, "component_count": 500, "batch_id": "BATCH-DEMO-001"}'
```

This generates 500 components × 5 electrical parameters (2,500 rows) covering all 8 defect archetypes:
1. `HEALTHY` (350 components / 70%): Centered population with physical thermal drift and sensor noise.
2. `POPULATION_OUTLIER` (40 components / 8%): **Key Scenario** — starts at $42\text{--}48\,\mu\text{A}$ ($I_{\text{ddq}}$), below limit ($50\,\mu\text{A}$), passes static screening, but is a 25$\sigma$ population outlier.
3. `MILD_DRIFT` (25 components / 5%): Steady drift at 3x natural rate.
4. `STRONG_DRIFT` (25 components / 5%): Linear rapid degradation climbing near limit.
5. `ACCELERATING_DRIFT` (20 components / 4%): Normal early readings, superlinear acceleration by 168h.
6. `EARLY_DRIFT` (15 components / 3%): Infant mortality: sharp 0h→24h shift, then levels off.
7. `LATE_DRIFT` (15 components / 3%): Latent defect: normal through 96h, steep breakdown 96h→168h.
8. `STATIC_LIMIT_VIOLATION` (10 components / 2%): Exceeds $50\,\mu\text{A}$ at 168h (traditional failure).

### Uploading a CSV Batch

Upload custom screening CSVs via the Web UI at `/upload` or via curl:

```bash
curl -X POST http://localhost:8000/api/data/upload \
  -F "file=@data/samples/valid_multivariate_batch.csv"
```

The CSV ingestion pipeline runs 9 validation checks:
- Required column presence (with flexible alias matching for snake_case & PascalCase)
- Missing value detection with row indices
- Duplicate component-parameter detection
- Numerical validity (rejects NaN, Inf, non-numeric strings)
- Checkpoint integrity across 0h, 24h, 96h, 168h
- Unit consistency per parameter across the batch
- Specification integrity (`spec_min < spec_max` and consistency)

### Inspecting Component Trajectories & Summaries

```bash
# Get screening batch summary and yield:
curl -s http://localhost:8000/api/data/summary

# List components (paginated):
curl -s "http://localhost:8000/api/data/components?page=1&page_size=10"

# Deep-dive into single component with all parameters & physical drift rates:
curl -s "http://localhost:8000/api/data/components/COMP-0015"
```

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System architecture, modular design, and API contracts
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) — Exhaustive schema documentation, units, valid ranges, and ML roles
- [MODEL_CARD.md](MODEL_CARD.md) — ML model cards, algorithms, limitations, and ethical considerations
- [DEMO_GUIDE.md](DEMO_GUIDE.md) — Evaluator demo walkthrough
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) — Implementation status and test verification

---

## License

Prototype for educational and demonstration purposes.
# SIH_26170
