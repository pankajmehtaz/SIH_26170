"""
Data Service: CSV upload, schema validation, data standardization,
batch statistics, synthetic benchmark generation, and component queries.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from config import (
    UPLOAD_DIR,
    RESULTS_DIR,
    DEMO_DATA_DIR,
    SYNTHETIC_DATA_DIR,
    REQUIRED_CANONICAL_COLUMNS,
    OPTIONAL_CANONICAL_COLUMNS,
    COLUMN_ALIASES,
    DEFAULT_DEMO_SEED,
    DEFAULT_DEMO_COMPONENTS,
)
from models.enums import ValidationIssueType, ComponentStatus
from models.schemas import (
    ValidationResult,
    ValidationIssue,
    BatchMetadata,
    ParameterStats,
    BatchListItem,
    BatchSummaryResponse,
    ComponentSummaryItem,
    ComponentListResponse,
    ComponentDetailResponse,
    ComponentParameterDetail,
)
from ml.features.extractor import extract_time_series_features
from ml.synthetic.generator import SyntheticDatasetGenerator


def resolve_canonical_columns(df: pd.DataFrame) -> tuple[dict[str, str], list[str]]:
    """
    Map raw dataframe column names to canonical names using aliases.

    Returns:
        col_mapping: dict mapping raw_col_name -> canonical_name
        missing_required: list of required canonical columns not found in df
    """
    col_mapping: dict[str, str] = {}
    normalized_to_raw: dict[str, str] = {}

    for raw_col in df.columns:
        norm = str(raw_col).strip().lower().replace(" ", "_").replace("-", "_")
        normalized_to_raw[norm] = raw_col

    # Match canonical names
    for canonical, aliases in COLUMN_ALIASES.items():
        matched_raw = None
        for alias in aliases:
            norm_alias = alias.lower()
            if norm_alias in normalized_to_raw:
                matched_raw = normalized_to_raw[norm_alias]
                break

        if matched_raw is not None:
            col_mapping[matched_raw] = canonical

    # Check which required canonical columns are missing
    found_canonicals = set(col_mapping.values())
    missing_required = [col for col in REQUIRED_CANONICAL_COLUMNS if col not in found_canonicals]

    return col_mapping, missing_required


def validate_csv(file_path: Path) -> ValidationResult:
    """
    Validate an uploaded CSV file against comprehensive screening requirements.

    Checks performed:
    1. File parseability and non-emptiness
    2. Required column presence (with alias resolution)
    3. Missing value detection (per row & column)
    4. Duplicate component detection (same component_id & parameter in batch)
    5. Data type & non-numeric value validation
    6. Invalid checkpoint detection (finite, non-null numeric floats)
    7. Unit consistency validation (per parameter)
    8. Specification limits validation (spec_min < spec_max, consistency)
    """
    issues: list[ValidationIssue] = []
    warnings: list[str] = []

    # 1. Parse CSV
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            row_count=0,
            column_count=0,
            columns_found=[],
            missing_columns=REQUIRED_CANONICAL_COLUMNS,
            error_count=1,
            warning_count=0,
            issues=[
                ValidationIssue(
                    column="file",
                    message=f"Failed to parse CSV file: {str(e)}",
                    severity="error",
                    issue_type=ValidationIssueType.INVALID_FILE.value,
                )
            ],
            warnings=[],
        )

    columns_found = [str(c) for c in df.columns]
    row_count = len(df)

    if row_count == 0:
        return ValidationResult(
            is_valid=False,
            row_count=0,
            column_count=len(columns_found),
            columns_found=columns_found,
            missing_columns=REQUIRED_CANONICAL_COLUMNS,
            error_count=1,
            warning_count=0,
            issues=[
                ValidationIssue(
                    column="file",
                    message="CSV file contains 0 data rows.",
                    severity="error",
                    issue_type=ValidationIssueType.INVALID_FILE.value,
                )
            ],
            warnings=[],
        )

    # 2. Required columns validation
    col_mapping, missing_required = resolve_canonical_columns(df)
    if missing_required:
        for missing_col in missing_required:
            issues.append(
                ValidationIssue(
                    column=missing_col,
                    message=f"Required column '{missing_col}' is missing (aliases: {', '.join(COLUMN_ALIASES.get(missing_col, []))})",
                    severity="error",
                    issue_type=ValidationIssueType.MISSING_COLUMN.value,
                )
            )
        return ValidationResult(
            is_valid=False,
            row_count=row_count,
            column_count=len(columns_found),
            columns_found=columns_found,
            missing_columns=missing_required,
            error_count=len(issues),
            warning_count=0,
            issues=issues,
            warnings=warnings,
        )

    # Standardize working dataframe using canonical column names
    standard_df = df.rename(columns=col_mapping)

    # 3. Missing Value Detection
    for canonical_col in REQUIRED_CANONICAL_COLUMNS:
        null_indices = standard_df[standard_df[canonical_col].isna()].index.tolist()
        if null_indices:
            for idx in null_indices[:15]:  # report first 15 rows with missing values
                issues.append(
                    ValidationIssue(
                        column=canonical_col,
                        row=int(idx) + 1,
                        message=f"Row {idx + 1}: Missing or empty value in required column '{canonical_col}'",
                        severity="error",
                        issue_type=ValidationIssueType.MISSING_VALUE.value,
                    )
                )
            if len(null_indices) > 15:
                issues.append(
                    ValidationIssue(
                        column=canonical_col,
                        message=f"Total {len(null_indices)} rows with missing values in '{canonical_col}'",
                        severity="error",
                        issue_type=ValidationIssueType.MISSING_VALUE.value,
                    )
                )

    # 4. Duplicate Component Detection
    if "component_id" in standard_df.columns and "parameter_name" in standard_df.columns:
        dups = standard_df[standard_df.duplicated(subset=["component_id", "parameter_name"], keep=False)]
        if not dups.empty:
            for idx, row in dups.head(10).iterrows():
                issues.append(
                    ValidationIssue(
                        column="component_id",
                        row=int(idx) + 1,
                        message=(
                            f"Row {int(idx) + 1}: Duplicate component measurement detected for "
                            f"component_id='{row['component_id']}' and parameter='{row['parameter_name']}'"
                        ),
                        severity="error",
                        issue_type=ValidationIssueType.DUPLICATE_COMPONENT.value,
                    )
                )
            if len(dups) > 10:
                issues.append(
                    ValidationIssue(
                        column="component_id",
                        message=f"Total {len(dups)} duplicate component-parameter measurement rows found.",
                        severity="error",
                        issue_type=ValidationIssueType.DUPLICATE_COMPONENT.value,
                    )
                )

    # 5. Data Type & Invalid Numerical Value Detection
    numeric_columns = ["spec_max", "value_0h", "value_24h", "value_96h", "value_168h"]
    if "spec_min" in standard_df.columns:
        numeric_columns.append("spec_min")
    if "measurement_temperature" in standard_df.columns:
        numeric_columns.append("measurement_temperature")
    if "measurement_voltage" in standard_df.columns:
        numeric_columns.append("measurement_voltage")

    for num_col in numeric_columns:
        if num_col in standard_df.columns:
            non_numeric = pd.to_numeric(standard_df[num_col], errors="coerce").isna() & standard_df[num_col].notna()
            bad_indices = standard_df.index[non_numeric].tolist()
            if bad_indices:
                for idx in bad_indices[:10]:
                    issues.append(
                        ValidationIssue(
                            column=num_col,
                            row=int(idx) + 1,
                            message=f"Row {int(idx) + 1}: Non-numeric value '{standard_df.loc[idx, num_col]}' in column '{num_col}'",
                            severity="error",
                            issue_type=ValidationIssueType.INVALID_DATA_TYPE.value,
                        )
                    )

            # Check for Inf / -Inf
            numeric_vals = pd.to_numeric(standard_df[num_col], errors="coerce")
            inf_indices = standard_df.index[np.isinf(numeric_vals)].tolist()
            if inf_indices:
                for idx in inf_indices[:5]:
                    issues.append(
                        ValidationIssue(
                            column=num_col,
                            row=int(idx) + 1,
                            message=f"Row {int(idx) + 1}: Infinite value found in column '{num_col}'",
                            severity="error",
                            issue_type=ValidationIssueType.INVALID_NUMERICAL_VALUE.value,
                        )
                    )

    # 6. Invalid Checkpoint Validation
    checkpoint_cols = ["value_0h", "value_24h", "value_96h", "value_168h"]
    for chk in checkpoint_cols:
        vals = pd.to_numeric(standard_df[chk], errors="coerce")
        # Extreme negative check for non-voltage params
        for idx, row in standard_df.iterrows():
            param = str(row.get("parameter_name", "")).lower()
            val = vals.loc[idx]
            if not pd.isna(val) and val < 0 and "volt" not in param and "vout" not in param:
                warnings.append(
                    f"Row {int(idx) + 1}: Negative checkpoint value {val} for parameter '{row.get('parameter_name')}' in column '{chk}'."
                )

    # 7. Unit Consistency Validation
    if "parameter_name" in standard_df.columns and "unit" in standard_df.columns:
        for param, group in standard_df.groupby("parameter_name"):
            units = group["unit"].dropna().unique()
            if len(units) > 1:
                issues.append(
                    ValidationIssue(
                        column="unit",
                        message=(
                            f"Inconsistent units detected for parameter '{param}': "
                            f"found multiple units {list(units)} in the same batch."
                        ),
                        severity="error",
                        issue_type=ValidationIssueType.INCONSISTENT_UNITS.value,
                    )
                )

    # 8. Specification Validation
    if "spec_min" in standard_df.columns and "spec_max" in standard_df.columns:
        min_vals = pd.to_numeric(standard_df["spec_min"], errors="coerce")
        max_vals = pd.to_numeric(standard_df["spec_max"], errors="coerce")

        invalid_spec = (min_vals.notna()) & (max_vals.notna()) & (min_vals >= max_vals)
        invalid_spec_indices = standard_df.index[invalid_spec].tolist()
        if invalid_spec_indices:
            for idx in invalid_spec_indices[:10]:
                issues.append(
                    ValidationIssue(
                        column="spec_min",
                        row=int(idx) + 1,
                        message=(
                            f"Row {int(idx) + 1}: Invalid specification limits: spec_min ({min_vals.loc[idx]}) "
                            f">= spec_max ({max_vals.loc[idx]}) for parameter '{standard_df.loc[idx, 'parameter_name']}'."
                        ),
                        severity="error",
                        issue_type=ValidationIssueType.INVALID_SPECIFICATION.value,
                    )
                )

    # Check for spec_max consistency within the same parameter
    if "parameter_name" in standard_df.columns and "spec_max" in standard_df.columns:
        for param, group in standard_df.groupby("parameter_name"):
            unique_specs = group["spec_max"].dropna().unique()
            if len(unique_specs) > 1:
                warnings.append(
                    f"Parameter '{param}' has multiple distinct spec_max values across batch: {list(unique_specs)}"
                )

    # Summary
    errors = [iss for iss in issues if iss.severity == "error"]
    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        row_count=row_count,
        column_count=len(columns_found),
        columns_found=columns_found,
        missing_columns=[],
        error_count=len(errors),
        warning_count=len(warnings),
        issues=issues,
        warnings=warnings,
    )


def standardize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize DataFrame column names to canonical names and ensure consistent types.
    """
    col_mapping, _ = resolve_canonical_columns(df)
    std_df = df.rename(columns=col_mapping)

    # Cast numeric columns
    numeric_cols = ["spec_max", "value_0h", "value_24h", "value_96h", "value_168h"]
    for c in numeric_cols:
        if c in std_df.columns:
            std_df[c] = pd.to_numeric(std_df[c], errors="coerce")

    if "spec_min" in std_df.columns:
        std_df["spec_min"] = pd.to_numeric(std_df["spec_min"], errors="coerce")

    # Ensure status column
    if "status" not in std_df.columns:
        std_df["status"] = "PASS"

    return std_df


def compute_parameter_stats(df: pd.DataFrame) -> list[ParameterStats]:
    """Compute comprehensive descriptive statistics per parameter."""
    df_std = standardize_dataframe(df)
    stats_list: list[ParameterStats] = []

    for param, group in df_std.groupby("parameter_name"):
        values = group["value_168h"].dropna()
        if len(values) == 0:
            continue

        mean_val = float(values.mean())
        std_val = float(values.std()) if len(values) > 1 else 0.0

        spec_max = float(group["spec_max"].dropna().iloc[0]) if "spec_max" in group.columns else 0.0
        spec_min = float(group["spec_min"].dropna().iloc[0]) if "spec_min" in group.columns and group["spec_min"].notna().any() else None
        unit = str(group["unit"].dropna().iloc[0]) if "unit" in group.columns else ""

        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = float(q3 - q1)

        stats_list.append(
            ParameterStats(
                parameter=str(param),
                unit=unit,
                spec_min=spec_min,
                abs_max=round(spec_max, 4),
                spec_max=round(spec_max, 4),
                count=int(len(values)),
                mean=round(mean_val, 4),
                std=round(std_val, 4),
                median=round(float(values.median()), 4),
                min=round(float(values.min()), 4),
                max=round(float(values.max()), 4),
                q1=round(q1, 4),
                q3=round(q3, 4),
                iqr=round(iqr, 4),
                cv=round(std_val / mean_val, 4) if mean_val != 0 else None,
            )
        )

    return stats_list


def store_uploaded_file(file_path: Path, file_name: str) -> tuple[str, Path]:
    """
    Standardize and store an uploaded CSV file in backend storage.
    Returns (batch_id, stored_path).
    """
    raw_df = pd.read_csv(file_path)
    std_df = standardize_dataframe(raw_df)

    batch_ids = std_df["batch_id"].dropna().unique()
    if len(batch_ids) == 0:
        batch_id = "BATCH-UPLOADED"
    else:
        batch_id = str(batch_ids[0])

    batch_dir = UPLOAD_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    # Save standardized CSV
    stored_path = batch_dir / file_name
    std_df.to_csv(stored_path, index=False)

    # Save legacy alias CSV (demo_batch_screening.csv) so existing endpoints find it
    legacy_df = std_df.rename(
        columns={
            "component_id": "Component_ID",
            "batch_id": "Batch_ID",
            "parameter_name": "Parameter",
            "unit": "Unit",
            "spec_max": "Abs_Max",
            "value_0h": "Value_0h",
            "value_24h": "Value_24h",
            "value_96h": "Value_96h",
            "value_168h": "Value_168h",
            "status": "Status",
            "ground_truth_label": "True_Label",
        }
    )
    legacy_df.to_csv(batch_dir / "demo_batch_screening.csv", index=False)

    # Save metadata
    param_stats = compute_parameter_stats(std_df)
    meta = {
        "batch_id": batch_id,
        "file_name": file_name,
        "total_components": int(std_df["component_id"].nunique()),
        "total_rows": len(std_df),
        "parameters": sorted(std_df["parameter_name"].unique().tolist()),
        "component_types": sorted(std_df["component_type"].dropna().unique().tolist()) if "component_type" in std_df.columns else [],
        "is_demo": False,
        "parameter_stats": [s.model_dump() for s in param_stats],
    }

    with open(batch_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return batch_id, stored_path


def generate_demo_dataset(
    seed: int = DEFAULT_DEMO_SEED,
    component_count: int = DEFAULT_DEMO_COMPONENTS,
    batch_id: str = "BATCH-DEMO-001",
) -> BatchMetadata:
    """
    Generate synthetic burn-in demo dataset using deterministic seed.
    Saves to data/synthetic/ and backend storage.
    """
    generator = SyntheticDatasetGenerator(
        seed=seed,
        batch_id=batch_id,
        component_count=component_count,
    )

    # Save to data/synthetic/
    saved_paths = generator.save(SYNTHETIC_DATA_DIR)

    # Also save to backend storage
    batch_dir = UPLOAD_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    generator.save(batch_dir)

    # Also update backend/demo/synthetic_data/
    generator.save(DEMO_DATA_DIR)

    df, raw_meta = generator.generate()
    param_stats = compute_parameter_stats(df)

    metadata = BatchMetadata(
        batch_id=batch_id,
        total_components=component_count,
        total_rows=len(df),
        parameters=sorted(df["parameter_name"].unique().tolist()),
        parameter_stats=param_stats,
        is_demo=True,
        file_name="burn_in_demo_screening.csv",
        random_seed=seed,
        component_types=raw_meta.get("component_types", []),
        generated_at=raw_meta.get("generated_at"),
    )

    # Save metadata.json in batch directory
    with open(batch_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2)

    return metadata


def load_demo_data() -> tuple[str, BatchMetadata]:
    """
    Load or generate synthetic demo data.
    """
    batch_id = "BATCH-DEMO-001"
    batch_dir = UPLOAD_DIR / batch_id
    screening_file = batch_dir / "burn_in_demo_screening.csv"
    legacy_file = batch_dir / "demo_batch_screening.csv"

    if not screening_file.exists() and not legacy_file.exists():
        # Generate demo data deterministically
        meta = generate_demo_dataset(seed=DEFAULT_DEMO_SEED, component_count=DEFAULT_DEMO_COMPONENTS, batch_id=batch_id)
        return batch_id, meta

    df = get_batch_data(batch_id)
    param_stats = compute_parameter_stats(df)
    meta = BatchMetadata(
        batch_id=batch_id,
        total_components=int(df["component_id"].nunique()),
        total_rows=len(df),
        parameters=sorted(df["parameter_name"].unique().tolist()),
        parameter_stats=param_stats,
        is_demo=True,
        file_name="burn_in_demo_screening.csv",
        random_seed=DEFAULT_DEMO_SEED,
    )
    return batch_id, meta


def get_batch_data(batch_id: str) -> pd.DataFrame:
    """Load and standardize batch data."""
    batch_dir = UPLOAD_DIR / batch_id
    if not batch_dir.exists():
        # Check synthetic dir
        if batch_id == "BATCH-DEMO-001" and (SYNTHETIC_DATA_DIR / "burn_in_demo_full.csv").exists():
            return standardize_dataframe(pd.read_csv(SYNTHETIC_DATA_DIR / "burn_in_demo_full.csv"))
        raise FileNotFoundError(f"Batch '{batch_id}' not found")

    candidates = [
        batch_dir / "burn_in_demo_full.csv",
        batch_dir / "burn_in_demo_screening.csv",
        batch_dir / "demo_batch_full.csv",
        batch_dir / "demo_batch_screening.csv",
    ]
    for c in candidates:
        if c.exists():
            return standardize_dataframe(pd.read_csv(c))

    csvs = [f for f in batch_dir.glob("*.csv") if "labels" not in f.name]
    if csvs:
        return standardize_dataframe(pd.read_csv(csvs[0]))

    raise FileNotFoundError(f"No data files found for batch '{batch_id}'")


def get_batch_metadata(batch_id: str) -> BatchMetadata:
    """Load or reconstruct batch metadata."""
    batch_dir = UPLOAD_DIR / batch_id
    meta_file = batch_dir / "metadata.json"

    if meta_file.exists():
        with open(meta_file, encoding="utf-8") as f:
            meta_dict = json.load(f)
        return BatchMetadata(**meta_dict)

    df = get_batch_data(batch_id)
    param_stats = compute_parameter_stats(df)
    return BatchMetadata(
        batch_id=batch_id,
        total_components=int(df["component_id"].nunique()),
        total_rows=len(df),
        parameters=sorted(df["parameter_name"].unique().tolist()),
        parameter_stats=param_stats,
    )


def list_batches() -> list[BatchListItem]:
    """List all batches in storage."""
    batches: list[BatchListItem] = []
    if not UPLOAD_DIR.exists():
        return batches

    for bdir in sorted(UPLOAD_DIR.iterdir()):
        if not bdir.is_dir():
            continue
        batch_id = bdir.name
        try:
            meta = get_batch_metadata(batch_id)
            results_dir = RESULTS_DIR / batch_id
            has_anomaly = (results_dir / "anomaly_results.json").exists()
            has_drift = (results_dir / "drift_results.json").exists()

            batches.append(
                BatchListItem(
                    batch_id=batch_id,
                    total_components=meta.total_components,
                    parameters=meta.parameters,
                    is_demo=meta.is_demo,
                    has_anomaly_results=has_anomaly,
                    has_drift_results=has_drift,
                )
            )
        except Exception:
            continue

    return batches


def get_data_summary(batch_id: Optional[str] = None) -> BatchSummaryResponse:
    """
    Get comprehensive screening and statistical summary for a batch.
    If batch_id is None, defaults to latest available batch.
    """
    if batch_id is None:
        batches = list_batches()
        if not batches:
            # Generate demo batch if storage is completely empty
            generate_demo_dataset()
            batch_id = "BATCH-DEMO-001"
        else:
            batch_id = batches[0].batch_id

    df = get_batch_data(batch_id)
    param_stats = compute_parameter_stats(df)

    # Component types
    comp_types = sorted(df["component_type"].dropna().unique().tolist()) if "component_type" in df.columns else []

    # Defect distribution if ground truth available
    defect_dist: Optional[dict[str, int]] = None
    if "defect_type" in df.columns:
        defect_dist = {
            str(k): int(v)
            for k, v in df.groupby("defect_type")["component_id"].nunique().items()
        }

    # Static screening pass/fail counts
    static_fails = 0
    total_comps = int(df["component_id"].nunique())
    if "status" in df.columns:
        failed_comps = df[df["status"] == "FAIL"]["component_id"].nunique()
        static_fails = int(failed_comps)
    else:
        # Evaluate static limit violations
        violators = set()
        for idx, row in df.iterrows():
            v168 = row.get("value_168h")
            s_max = row.get("spec_max")
            s_min = row.get("spec_min")
            if v168 is not None and not pd.isna(v168):
                if s_max is not None and not pd.isna(s_max) and v168 > s_max:
                    violators.add(row["component_id"])
                if s_min is not None and not pd.isna(s_min) and v168 < s_min:
                    violators.add(row["component_id"])
        static_fails = len(violators)

    static_passes = total_comps - static_fails
    pass_rate = round(static_passes / max(total_comps, 1), 4)

    return BatchSummaryResponse(
        batch_id=batch_id,
        total_components=total_comps,
        total_rows=len(df),
        parameters=sorted(df["parameter_name"].unique().tolist()),
        component_types=comp_types,
        parameter_stats=param_stats,
        defect_distribution=defect_dist,
        static_screening_summary={
            "total_screened": total_comps,
            "static_pass_count": static_passes,
            "static_fail_count": static_fails,
            "static_pass_rate": pass_rate,
        },
        is_demo="demo" in batch_id.lower(),
    )


def get_components_list(
    batch_id: Optional[str] = None,
    component_type: Optional[str] = None,
    defect_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> ComponentListResponse:
    """
    Get paginated, filterable component list with parametric measurement summaries.
    """
    if batch_id is None:
        batches = list_batches()
        if not batches:
            generate_demo_dataset()
            batch_id = "BATCH-DEMO-001"
        else:
            batch_id = batches[0].batch_id

    df = get_batch_data(batch_id)

    # Filter dataframe
    if component_type and "component_type" in df.columns:
        df = df[df["component_type"] == component_type]
    if defect_type and "defect_type" in df.columns:
        df = df[df["defect_type"] == defect_type]
    if search:
        search_lower = search.lower()
        df = df[df["component_id"].str.lower().str.contains(search_lower)]

    all_comp_ids = df["component_id"].unique()
    total_components = len(all_comp_ids)

    # Pagination
    total_pages = max(1, math.ceil(total_components / page_size))
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_comp_ids = all_comp_ids[start_idx:end_idx]

    components: list[ComponentSummaryItem] = []
    page_df = df[df["component_id"].isin(page_comp_ids)]

    for comp_id, group in page_df.groupby("component_id"):
        first_row = group.iloc[0]
        params_dict: dict[str, dict[str, Any]] = {}

        for _, row in group.iterrows():
            p_name = str(row["parameter_name"])
            params_dict[p_name] = {
                "unit": row.get("unit", ""),
                "spec_min": row.get("spec_min") if not pd.isna(row.get("spec_min")) else None,
                "spec_max": float(row.get("spec_max", 0.0)),
                "value_0h": float(row.get("value_0h", 0.0)),
                "value_24h": float(row.get("value_24h", 0.0)),
                "value_96h": float(row.get("value_96h", 0.0)),
                "value_168h": float(row.get("value_168h", 0.0)),
                "status": str(row.get("status", "PASS")),
            }

        components.append(
            ComponentSummaryItem(
                component_id=str(comp_id),
                batch_id=batch_id,
                component_type=str(first_row.get("component_type")) if "component_type" in first_row and not pd.isna(first_row.get("component_type")) else None,
                status="FAIL" if any(p.get("status") == "FAIL" for p in params_dict.values()) else "PASS",
                ground_truth_label=str(first_row.get("ground_truth_label")) if "ground_truth_label" in first_row and not pd.isna(first_row.get("ground_truth_label")) else None,
                defect_type=str(first_row.get("defect_type")) if "defect_type" in first_row and not pd.isna(first_row.get("defect_type")) else None,
                parameters=params_dict,
            )
        )

    return ComponentListResponse(
        batch_id=batch_id,
        total_components=total_components,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        components=components,
    )


def get_component_detail(
    component_id: str,
    batch_id: Optional[str] = None,
) -> ComponentDetailResponse:
    """
    Get full parametric time-series profile, physical slopes, and population comparison
    for a specific component.
    """
    if batch_id is None:
        batches = list_batches()
        if not batches:
            generate_demo_dataset()
            batch_id = "BATCH-DEMO-001"
        else:
            batch_id = batches[0].batch_id

    df = get_batch_data(batch_id)
    comp_df = df[df["component_id"] == component_id]

    if comp_df.empty:
        raise FileNotFoundError(f"Component '{component_id}' not found in batch '{batch_id}'")

    first_row = comp_df.iloc[0]
    param_details: list[ComponentParameterDetail] = []

    for _, row in comp_df.iterrows():
        p_name = str(row["parameter_name"])
        p_pop = df[df["parameter_name"] == p_name]["value_168h"].dropna()

        batch_mean = float(p_pop.mean()) if len(p_pop) > 0 else 0.0
        batch_std = float(p_pop.std()) if len(p_pop) > 1 else 1e-6
        batch_median = float(p_pop.median()) if len(p_pop) > 0 else 0.0

        v168 = float(row.get("value_168h", 0.0))
        z_score = (v168 - batch_mean) / (batch_std if batch_std != 0 else 1e-6)

        slopes = extract_time_series_features(row)

        param_details.append(
            ComponentParameterDetail(
                parameter_name=p_name,
                unit=str(row.get("unit", "")),
                spec_min=float(row.get("spec_min")) if "spec_min" in row and not pd.isna(row.get("spec_min")) else None,
                spec_max=float(row.get("spec_max", 0.0)),
                value_0h=float(row.get("value_0h", 0.0)),
                value_24h=float(row.get("value_24h", 0.0)),
                value_96h=float(row.get("value_96h", 0.0)),
                value_168h=v168,
                slopes=slopes,
                batch_mean=round(batch_mean, 4),
                batch_median=round(batch_median, 4),
                batch_std=round(batch_std, 4),
                z_score_168h=round(z_score, 4),
                status=str(row.get("status", "PASS")),
            )
        )

    overall_status = "FAIL" if any(p.status == "FAIL" for p in param_details) else "PASS"

    return ComponentDetailResponse(
        component_id=component_id,
        batch_id=batch_id,
        component_type=str(first_row.get("component_type")) if "component_type" in first_row and not pd.isna(first_row.get("component_type")) else None,
        status=overall_status,
        ground_truth_label=str(first_row.get("ground_truth_label")) if "ground_truth_label" in first_row and not pd.isna(first_row.get("ground_truth_label")) else None,
        defect_type=str(first_row.get("defect_type")) if "defect_type" in first_row and not pd.isna(first_row.get("defect_type")) else None,
        parameters=param_details,
    )
