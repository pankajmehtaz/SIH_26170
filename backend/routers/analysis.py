"""
Analysis router: anomaly detection and drift prediction endpoints.
Stub — will be implemented in Stage 2 and Stage 3.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("/anomaly/{batch_id}")
async def run_anomaly_detection(batch_id: str):
    """Run Module A — Dynamic Outlier Detection. [Stage 2]"""
    raise HTTPException(status_code=501, detail="Anomaly detection not yet implemented (Stage 2)")


@router.post("/drift/{batch_id}")
async def run_drift_prediction(batch_id: str):
    """Run Module B — Drift Prediction. [Stage 3]"""
    raise HTTPException(status_code=501, detail="Drift prediction not yet implemented (Stage 3)")


@router.get("/results/{batch_id}")
async def get_results(batch_id: str):
    """Get combined analysis results. [Stage 4]"""
    raise HTTPException(status_code=501, detail="Combined results not yet implemented (Stage 4)")


@router.get("/component/{batch_id}/{component_id}")
async def get_component_profile(batch_id: str, component_id: str):
    """Get full component profile. [Stage 4]"""
    raise HTTPException(status_code=501, detail="Component profiles not yet implemented (Stage 4)")


@router.get("/metrics/{batch_id}")
async def get_metrics(batch_id: str):
    """Get model evaluation metrics. [Stage 5]"""
    raise HTTPException(status_code=501, detail="Metrics not yet implemented (Stage 5)")
