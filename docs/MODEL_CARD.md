# Model Card

> **Prototype Models** — These models are trained on synthetic data for demonstration purposes. They do NOT represent production-grade screening models and should NOT be used for actual component screening decisions.

## Module A — Dynamic Outlier Detection

### Model Description
An ensemble of four complementary anomaly detection methods that vote on each component:

| Method | Type | Key Parameter | Catches |
|--------|------|---------------|---------|
| Modified Z-Score | Statistical | threshold=2.5 | Univariate outliers (robust to non-Gaussian) |
| IQR Fence | Statistical | multiplier=1.5 | Distribution tail outliers |
| Isolation Forest | ML (unsupervised) | contamination=0.1 | Multivariate anomalies |
| Local Outlier Factor | ML (unsupervised) | n_neighbors=20 | Local density anomalies |

### Ensemble Logic
- A component is **flagged** if ≥2 of 4 methods agree
- A **composite anomaly score** (0–1) is computed as a weighted average of normalised individual scores
- Weights: Z-Score (0.25), IQR (0.2), Isolation Forest (0.3), LOF (0.25)

### Input Features (per component × parameter)
- `Value_0h`, `Value_24h`, `Value_96h`, `Value_168h`
- `slope_0_24`, `slope_24_96`, `slope_96_168`

### Evaluation Metrics
- Primary: **Recall** (sensitivity) — must be maximised
- Secondary: Precision, F1, FPR, FNR
- Visualisation: Confusion matrix

### Limitations
- Trained per-batch: requires sufficient batch size (≥20 components)
- Assumes unimodal healthy population per parameter
- Cannot detect inter-batch drift without cross-batch reference

---

## Module B — Time-Series Drift Prediction

### Model Description
Gradient Boosted Trees (XGBoost) regressor trained to predict `Value_168h` from early burn-in measurements.

Falls back to Ridge Regression for batches with <50 components.

### Input Features
| Feature | Description |
|---------|-------------|
| `Value_0h` | Initial measurement |
| `Value_24h` | 24-hour measurement |
| `slope_0_24` | (Value_24h − Value_0h) / 24 |
| `ratio_24_0` | Value_24h / Value_0h |
| `proximity_to_limit` | Value_0h / Abs_Max |
| `batch_mean_0h` | Batch mean at 0h |
| `batch_std_0h` | Batch std at 0h |

### Output
- Predicted `Value_168h`
- Predicted slope
- Comparison against safety slope envelope

### Safety Slope
- Computed from healthy population: `median_slope ± 2 × MAD(slopes)`
- Components exceeding the upper safety slope are flagged as `DRIFT_RISK`

### Evaluation Metrics
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R² (Coefficient of Determination)
- Per-parameter breakdown

### Explainability
- SHAP values for feature importance
- Per-component feature contribution waterfall

### Limitations
- Predicting 168h from 0h+24h only — accuracy improves with 96h data
- Small batch sizes may lead to overfitting
- Assumes monotonic drift patterns; non-monotonic failures may be missed
- Synthetic training data does not capture all real-world failure modes

---

## Risk Classification (Combined)

| Risk Level | Criteria |
|------------|----------|
| NORMAL | Not flagged by either module |
| MONITOR | Flagged by one module with low-to-moderate score |
| WARNING | Flagged by one module with high score, or both with moderate |
| CRITICAL | Both modules flag, or anomaly score >0.9, or predicted 168h > Abs_Max |

## Ethical Considerations
- This system provides decision **support**, not autonomous decisions
- All flagged components should be reviewed by a qualified QA engineer
- The system should augment, not replace, existing screening processes
- False negative rate should be continuously monitored in production use
