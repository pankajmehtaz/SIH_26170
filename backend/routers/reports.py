"""
Reports router: QA report generation and export.
Stub — will be implemented in Stage 5.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/{batch_id}")
async def get_report(batch_id: str):
    """Generate and return QA screening report. [Stage 5]"""
    raise HTTPException(status_code=501, detail="Report generation not yet implemented (Stage 5)")
