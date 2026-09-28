"""
Parametric time-series feature extractor.

Computes physical drift rates (slopes), curvature (acceleration),
and relative metrics from burn-in checkpoints (0h, 24h, 96h, 168h).
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def extract_time_series_features(row: pd.Series | dict) -> dict[str, float]:
    """
    Extract time-series and drift features for a single component × parameter.

    Checkpoints:
        t0 = 0h, t1 = 24h (dt=24h)
        t2 = 96h (dt=72h)
        t3 = 168h (dt=72h)
    """
    v0 = float(row.get("value_0h", row.get("Value_0h", 0.0)))
    v24 = float(row.get("value_24h", row.get("Value_24h", 0.0)))
    v96 = float(row.get("value_96h", row.get("Value_96h", 0.0)))
    v168 = float(row.get("value_168h", row.get("Value_168h", 0.0)))
    spec_max = float(row.get("spec_max", row.get("Abs_Max", 1.0)))

    # Slopes (rate of change per hour)
    slope_0_24 = (v24 - v0) / 24.0
    slope_24_96 = (v96 - v24) / 72.0
    slope_96_168 = (v168 - v96) / 72.0
    overall_slope = (v168 - v0) / 168.0

    # Acceleration (change in slope between intervals)
    accel_early_to_mid = slope_24_96 - slope_0_24
    accel_mid_to_late = slope_96_168 - slope_24_96

    # Ratios and relative shifts
    eps = 1e-9
    ratio_24_0 = v24 / (v0 if abs(v0) > eps else eps)
    relative_drift_total = (v168 - v0) / (abs(v0) if abs(v0) > eps else eps)
    proximity_to_spec = v168 / (spec_max if abs(spec_max) > eps else eps)

    # Maximum rate of movement in any phase
    max_rate = max(abs(slope_0_24), abs(slope_24_96), abs(slope_96_168))

    return {
        "slope_0_24": round(slope_0_24, 6),
        "slope_24_96": round(slope_24_96, 6),
        "slope_96_168": round(slope_96_168, 6),
        "overall_slope": round(overall_slope, 6),
        "accel_early_to_mid": round(accel_early_to_mid, 6),
        "accel_mid_to_late": round(accel_mid_to_late, 6),
        "ratio_24_0": round(ratio_24_0, 6),
        "relative_drift_total": round(relative_drift_total, 6),
        "proximity_to_spec": round(proximity_to_spec, 6),
        "max_rate": round(max_rate, 6),
    }


def compute_batch_distribution_features(
    df: pd.DataFrame,
    param_col: str = "parameter_name",
    val_cols: list[str] | None = None,
) -> pd.DataFrame:
    """
    Augment batch dataframe with normalized distribution features (z-scores, percentiles).
    """
    if val_cols is None:
        val_cols = ["value_0h", "value_24h", "value_96h", "value_168h"]

    result_df = df.copy()

    for p_name, group in df.groupby(param_col):
        for col in val_cols:
            if col in group.columns:
                vals = pd.to_numeric(group[col], errors="coerce")
                mean_val = vals.mean()
                std_val = vals.std() if len(vals) > 1 else 1.0
                if std_val == 0 or np.isnan(std_val):
                    std_val = 1e-6

                z_col = f"z_{col}"
                result_df.loc[group.index, z_col] = (vals - mean_val) / std_val

    return result_df
