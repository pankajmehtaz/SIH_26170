# Data Dictionary

> **Burn-In Screening & Parametric Anomaly Detection Data Schema**  
> Reference standard for time-series parametric screening data, feature engineering, and defect classification.  
> *Engineering Prototype — Not an official ISRO system.*

---

## 1. Input Data Schema (CSV / Tabular)

The ingestion pipeline accepts CSV files representing burn-in measurements. Each row represents **one component × one electrical parameter**. Components with multiple parameters are represented across multiple rows with the same `component_id` and `batch_id`.

The system includes a smart column resolver that accepts both standard lowercase snake_case (`component_id`, `spec_max`, etc.) and PascalCase (`Component_ID`, `Abs_Max`, etc.).

### Field Specifications

| Field Name | Meaning | Unit | Required / Optional | Example | Valid Range | Role in ML |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `component_id` | Unique identifier for the individual physical device/DUT | Dimensionless string | **Required** | `COMP-0042` | Non-empty alphanumeric string `[A-Za-z0-9_-]+` | Primary entity key; groups multi-parameter measurements and longitudinal trajectories. |
| `batch_id` | Manufacturing lot or burn-in chamber run identifier | Dimensionless string | **Required** | `BATCH-2026-A` | Non-empty alphanumeric string | Population grouping key; defines reference distribution for Module A outlier detection and baseline safety envelopes. |
| `component_type` | Device category, technology family, or part number | Dimensionless string | *Optional* | `Radiation-Hardened FPGA` | Standard string (e.g. FPGA, Op-Amp, ADC, DSP, Voltage Regulator) | Stratification feature; allows technology-specific drift priors and outlier thresholds. |
| `parameter_name` | Electrical test parameter being measured | Dimensionless string | **Required** | `iddq` | Any valid identifier (e.g. `iddq`, `leakage_current`, `propagation_delay`, `standby_current`, `voltage`) | Channel identifier; models train and evaluate distributions per parameter. System dynamically supports new parameters without code changes. |
| `unit` | Physical engineering unit of measurement | SI / Engineering unit | **Required** | `µA`, `ns`, `mV` | Standard electrical unit symbols; must be consistent across all rows for the same parameter in a batch | Scale consistency verification; ensures normalization and physical drift rates match across batch. |
| `spec_min` | Minimum datasheet specification limit | Same as `unit` | *Optional* | `0.0` or `3150.0` | Lower bound float; if present, must satisfy `spec_min < spec_max` | Static screening lower limit; identifies traditional threshold failures and defines proximity to lower bounds. |
| `spec_max` | Absolute maximum datasheet specification limit | Same as `unit` | **Required** | `50.0` or `100.0` | Finite positive float; `spec_max > spec_min` | Traditional pass/fail threshold. Key reference in ML: critical for detecting population outliers that stay within `spec_max` while anomalous. |
| `value_0h` | Measurement at start of burn-in ($t = 0\,\text{hours}$) | Same as `unit` | **Required** | `12.15` | Finite float | Baseline reading; starting point for infant mortality analysis, baseline z-score, and trajectory slope denominator. |
| `value_24h` | Measurement at checkpoint 1 ($t = 24\,\text{hours}$) | Same as `unit` | **Required** | `12.40` | Finite float | Early burn-in reading; used with `value_0h` in Module B for 168h end-of-life drift prediction and early drift detection. |
| `value_96h` | Measurement at intermediate checkpoint 2 ($t = 96\,\text{hours}$) | Same as `unit` | **Required** | `12.85` | Finite float | Mid-test checkpoint; detects trajectory curvature, inflection points, and accelerating vs. leveling drift. |
| `value_168h` | Measurement at final burn-in completion ($t = 168\,\text{hours}$ / 7 days) | Same as `unit` | **Required** | `13.10` | Finite float | Burn-in completion state; target variable for Module B drift regression and final dynamic outlier evaluation. |
| `measurement_temperature` | Chamber or junction temperature during test | °C | *Optional* | `125.0` | `-55.0` to `200.0` °C | Environmental stress covariate; enables temperature-adjusted drift modeling across Arrhenius acceleration curves. |
| `measurement_voltage` | Supply bias voltage applied during burn-in ($V_{\text{DD}}$ / $V_{\text{CC}}$) | V | *Optional* | `3.3` | `0.5` to `28.0` V | Bias stress covariate; normalizes quiescent currents under variable voltage stress. |
| `timestamp` | ISO 8601 test execution timestamp | ISO 8601 string | *Optional* | `2026-09-28T12:00:00Z` | Valid ISO datetime string | Temporal tracking for test logging, chamber scheduling, and historical lot traceability. |
| `ground_truth_label` | Benchmark label (DEMO/SYNTHETIC data only) | Enum string | *Optional* (Demo only) | `ANOMALOUS` or `NORMAL` | `NORMAL`, `ANOMALOUS` | Binary ground truth for supervised ML validation, confusion matrix, precision, recall, and F1 calculation. |
| `defect_type` | Specific failure mechanism archetype (DEMO only) | Enum string | *Optional* (Demo only) | `POPULATION_OUTLIER` | `HEALTHY`, `POPULATION_OUTLIER`, `MILD_DRIFT`, `STRONG_DRIFT`, `ACCELERATING_DRIFT`, `EARLY_DRIFT`, `LATE_DRIFT`, `STATIC_LIMIT_VIOLATION` | Granular evaluation of which specific failure modes are caught by dynamic outlier vs drift vs static screening. |
| `status` | Traditional static screening result | Enum string | *Optional* | `PASS` | `PASS`, `FAIL`, `SUSPECT` | Comparison baseline to highlight components passed by static limits but caught by AI screening. |

---

## 2. Derived Features (Engineered Parametric Metrics)

The feature pipeline (`ml/features/extractor.py`) derives longitudinal, physical rate, and population features:

| Feature Name | Formula | Unit | Range | Role in ML Models |
| :--- | :--- | :--- | :--- | :--- |
| `slope_0_24` | $\frac{\text{value\_24h} - \text{value\_0h}}{24.0}$ | unit / hour | $(-\infty, +\infty)$ | Primary early feature for Module B; captures initial burn-in rate of movement. |
| `slope_24_96` | $\frac{\text{value\_96h} - \text{value\_24h}}{72.0}$ | unit / hour | $(-\infty, +\infty)$ | Mid-phase degradation velocity. |
| `slope_96_168` | $\frac{\text{value\_168h} - \text{value\_96h}}{72.0}$ | unit / hour | $(-\infty, +\infty)$ | Late-phase wearout velocity; detects late breakdown. |
| `overall_slope` | $\frac{\text{value\_168h} - \text{value\_0h}}{168.0}$ | unit / hour | $(-\infty, +\infty)$ | Mean drift velocity across full 7-day screening period. |
| `accel_early_to_mid` | $\text{slope\_24\_96} - \text{slope\_0\_24}$ | unit / $\text{hour}^2$ | $(-\infty, +\infty)$ | Initial curvature; negative indicates infant mortality settling; positive indicates emerging degradation. |
| `accel_mid_to_late` | $\text{slope\_96\_168} - \text{slope\_24\_96}$ | unit / $\text{hour}^2$ | $(-\infty, +\infty)$ | Late acceleration; key indicator for accelerating drift defects. |
| `ratio_24_0` | $\frac{\text{value\_24h}}{\text{value\_0h}}$ | Dimensionless | $[0, \infty)$ | Relative early expansion ratio; scale-invariant feature for cross-technology comparison. |
| `relative_drift_total`| $\frac{\text{value\_168h} - \text{value\_0h}}{\text{value\_0h}}$ | Dimensionless | $(-1, \infty)$ | Percentage parametric shift over screening lifetime. |
| `proximity_to_spec` | $\frac{\text{value\_168h}}{\text{spec\_max}}$ | Dimensionless | $[0, \infty)$ | Safety margin indicator; values $>0.85$ indicate high risk even if not yet violating limit. |
| `max_rate` | $\max(\|\text{slope}_{0\_24}\|, \|\text{slope}_{24\_96}\|, \|\text{slope}_{96\_168}\|)$ | unit / hour | $[0, \infty)$ | Maximum instantaneous physical movement in any measurement interval. |
| `z_score_168h` | $\frac{\text{value\_168h} - \mu_{\text{batch}}}{\sigma_{\text{batch}}}$ | Dimensionless | $(-\infty, +\infty)$ | Statistical distance from population center in standard deviations. |
| `iqr_distance_168h` | $\frac{\text{value\_168h} - \text{median}_{\text{batch}}}{\text{IQR}_{\text{batch}}}$ | Dimensionless | $(-\infty, +\infty)$ | Robust non-parametric population distance. |

---

## 3. Defect Archetypes (Benchmark Dataset)

The synthetic benchmark generator implements 8 distinct behavioral archetypes:

```
Defect Archetype Breakdown:
├── HEALTHY (70%)                     ── Stable, tight distribution, normal thermal drift
├── POPULATION_OUTLIER (8%)           ── *Key Scenario*: In static limits (40-48 µA, max 50), abnormal vs pop (10-15 µA)
├── MILD_DRIFT (5%)                   ── Gradual drift at 3x-4x natural rate
├── STRONG_DRIFT (5%)                 ── Steep linear climb towards spec_max
├── ACCELERATING_DRIFT (4%)           ── Normal at 0h & 24h; quadratic acceleration at 96h & 168h
├── EARLY_DRIFT (3%)                  ── Infant mortality: sharp 0h→24h jump, then levels off
├── LATE_DRIFT (3%)                   ── Latent defect: normal through 96h, steep breakdown 96h→168h
└── STATIC_LIMIT_VIOLATION (2%)       ── Catastrophic drift crossing spec_max / spec_min at 168h
```

### The Key Problem Scenario
- **Parameter**: `iddq`
- **Datasheet Absolute Limit (`spec_max`)**: `50.0 µA`
- **Healthy Batch Population**: Mean `12.0 µA`, Standard Deviation `1.1 µA` (Distribution: `~9.5 – 14.5 µA`)
- **Anomalous Component**: Starts at `42.0 – 47.5 µA`, finishes at `43.0 – 48.0 µA`
- **Static Screening Verdict**: `PASS` (below 50.0 µA)
- **AI Dynamic Screening Verdict**: `CRITICAL ANOMALY` ($Z\text{-score} > 25\sigma$, LOF and Isolation Forest flag immediately).

---

## 4. Column Aliases & Mapping

The ingestion engine maps common industry header variants to canonical fields:

| Canonical Field | Accepted Aliases |
| :--- | :--- |
| `component_id` | `Component_ID`, `componentid`, `comp_id`, `compid`, `component` |
| `batch_id` | `Batch_ID`, `batchid`, `lot_id`, `lotid`, `batch` |
| `component_type` | `Component_Type`, `componenttype`, `part_type`, `type`, `device_type` |
| `parameter_name` | `Parameter`, `parameter_name`, `param`, `param_name`, `test_parameter` |
| `unit` | `Unit`, `units` |
| `spec_min` | `Spec_Min`, `specmin`, `abs_min`, `min_spec`, `lower_limit`, `min_limit` |
| `spec_max` | `Abs_Max`, `Spec_Max`, `specmax`, `max_spec`, `upper_limit`, `max_limit` |
| `value_0h` | `Value_0h`, `val_0h`, `0h`, `t0`, `t_0`, `val0`, `value0h` |
| `value_24h` | `Value_24h`, `val_24h`, `24h`, `t24`, `t_24`, `val24`, `value24h` |
| `value_96h` | `Value_96h`, `val_96h`, `96h`, `t96`, `t_96`, `val96`, `value96h` |
| `value_168h` | `Value_168h`, `val_168h`, `168h`, `t168`, `t_168`, `val168`, `value168h` |
| `measurement_temperature` | `Measurement_Temperature`, `temperature`, `temp`, `temp_c`, `chamber_temp` |
| `measurement_voltage` | `Measurement_Voltage`, `voltage`, `bias_voltage`, `vcc`, `vdd` |
| `timestamp` | `Timestamp`, `time`, `date`, `created_at`, `test_date` |
| `ground_truth_label` | `True_Label`, `ground_truth_label`, `ground_truth`, `label` |
| `defect_type` | `Defect_Type`, `defect_type`, `anomaly_type`, `failure_mode` |
| `status` | `Status`, `screening_status`, `result`, `pass_fail` |
