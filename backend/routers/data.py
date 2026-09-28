"""
Data Router: CSV upload, screening validation, synthetic benchmark generation,
batch summaries, and component-level queries.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body

from models.schemas import (
    ValidationResult,
    BatchMetadata,
    BatchListItem,
    BatchSummaryResponse,
    ComponentListResponse,
    ComponentDetailResponse,
    GenerateDemoRequest,
)
from services.data_service import (
    validate_csv,
    store_uploaded_file,
    load_demo_data,
    generate_demo_dataset,
    get_batch_data,
    get_batch_metadata,
    list_batches,
    compute_parameter_stats,
    get_data_summary,
    get_components_list,
    get_component_detail,
)

router = APIRouter(prefix="/api/data", tags=["Data Foundation"])


@router.post("/upload", response_model=BatchMetadata)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file for screening analysis.
    Performs comprehensive schema, duplicate, type, checkpoint, unit,
    and specification validations. Does NOT silently discard bad rows.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only CSV files (.csv) are accepted for screening upload.",
        )

    # Save to temp file for validation
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Validate CSV with full diagnostic checks
        validation = validate_csv(tmp_path)
        if not validation.is_valid:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "CSV validation failed. Please correct the listed errors before proceeding.",
                    "error_count": validation.error_count,
                    "warning_count": validation.warning_count,
                    "issues": [issue.model_dump() for issue in validation.issues],
                    "warnings": validation.warnings,
                },
            )

        # Store validated file and persist metadata
        batch_id, stored_path = store_uploaded_file(tmp_path, file.filename)
        metadata = get_batch_metadata(batch_id)
        metadata.file_name = file.filename
        return metadata

    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/validate", response_model=ValidationResult)
async def validate_upload(file: UploadFile = File(...)):
    """
    Validate a CSV file without storing it.
    Returns detailed diagnostics including missing columns, duplicate components,
    unit inconsistencies, and non-numeric checkpoint values.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        return validate_csv(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/generate-demo", response_model=BatchMetadata)
async def generate_demo(request: Optional[GenerateDemoRequest] = None):
    """
    Generate a realistic synthetic burn-in dataset using a deterministic seed.
    Deliberately creates healthy trajectories, population outliers, early/late/accelerating
    drift, and static limit violations.
    """
    req = request or GenerateDemoRequest()
    metadata = generate_demo_dataset(
        seed=req.seed,
        component_count=req.component_count,
        batch_id=req.batch_id,
    )
    return metadata


@router.post("/demo", response_model=BatchMetadata)
async def load_demo():
    """Load or generate the default pre-configured synthetic demo dataset."""
    try:
        _, meta = load_demo_data()
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demo data: {str(e)}")


@router.get("/summary", response_model=BatchSummaryResponse)
async def get_summary(batch_id: Optional[str] = Query(None, description="Batch identifier")):
    """
    Get screening and distribution summary for an uploaded or demo batch.
    Includes parameter statistics, component types, and static screening yield.
    """
    try:
        return get_data_summary(batch_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/components", response_model=ComponentListResponse)
async def list_components(
    batch_id: Optional[str] = Query(None, description="Batch ID"),
    component_type: Optional[str] = Query(None, description="Filter by component type"),
    defect_type: Optional[str] = Query(None, description="Filter by defect type (demo data)"),
    search: Optional[str] = Query(None, description="Search by component ID prefix or substring"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
):
    """
    Get paginated, filterable component list with measurement values across all parameters.
    """
    try:
        return get_components_list(
            batch_id=batch_id,
            component_type=component_type,
            defect_type=defect_type,
            search=search,
            page=page,
            page_size=page_size,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/components/{component_id}", response_model=ComponentDetailResponse)
async def get_component(
    component_id: str,
    batch_id: Optional[str] = Query(None, description="Batch ID (defaults to active batch)"),
):
    """
    Get full component profile including all parametric time-series checkpoints (0h, 24h, 96h, 168h),
    physical drift rates (slopes), and comparison against the batch population distribution.
    """
    try:
        return get_component_detail(component_id=component_id, batch_id=batch_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/batches", response_model=list[BatchListItem])
async def get_batches():
    """List all available batches in backend storage."""
    return list_batches()


@router.get("/batch/{batch_id}", response_model=BatchMetadata)
async def get_batch(batch_id: str):
    """Get metadata and parameter statistics for a specific batch."""
    try:
        return get_batch_metadata(batch_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found")


@router.get("/batch/{batch_id}/data")
async def get_batch_raw_data(batch_id: str):
    """Get raw tabular data for a batch."""
    try:
        df = get_batch_data(batch_id)
        return {
            "batch_id": batch_id,
            "columns": list(df.columns),
            "data": df.to_dict(orient="records"),
            "row_count": len(df),
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found")
