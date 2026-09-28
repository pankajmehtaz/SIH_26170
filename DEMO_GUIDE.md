# Demo Guide

> All data in this demo is **SYNTHETIC**. Thresholds, limits, and component characteristics are generated for demonstration and do NOT represent actual ISRO engineering data.

## Prerequisites

- Python 3.9+
- Node.js 18+
- npm

## Step 1: Generate Synthetic Data

```bash
cd backend
source venv/bin/activate    # or create venv first — see README.md
python demo/generate_synthetic.py
```

This produces:
- `demo/synthetic_data/demo_batch_screening.csv` — the dataset users would upload (no labels)
- `demo/synthetic_data/demo_batch_full.csv` — same data with hidden `True_Label` column (for evaluation)
- `demo/synthetic_data/demo_batch_labels.csv` — ground truth labels only

## Step 2: Start the Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Verify: `http://localhost:8000/api/health`

## Step 3: Start the Frontend

```bash
cd frontend
npm run dev
```

Open: `http://localhost:5173`

## Step 4: Walkthrough

1. **Upload Page** → Click "Load Demo Data" to load the synthetic batch
2. **Batch Overview** → Inspect parameter statistics and distributions
3. **Anomaly Results** → (Stage 2) Run Module A and inspect flagged components
4. **Drift Results** → (Stage 3) Run Module B and inspect drift predictions
5. **Component Detail** → (Stage 4) Deep-dive into a specific component
6. **Model Metrics** → (Stage 5) Review evaluation performance
7. **QA Report** → (Stage 5) Generate and export the screening report

## Synthetic Data Profile

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| Healthy | ~160 | 80% | Normal distribution, mild natural drift |
| Subtle Anomaly | ~20 | 10% | Within abs_max but 3–5σ from population mean |
| Obvious Failure | ~6 | 3% | Exceeds abs_max at 168h |
| Drift Defect | ~14 | 7% | Normal start, accelerating drift |

Parameters:
- **Iddq** (Standby Current): µA, abs_max = 50
- **Leakage_Current**: µA, abs_max = 100
- **Prop_Delay** (Propagation Delay): ns, abs_max = 25
- **Vout** (Output Voltage): mV, abs_max = 3500
