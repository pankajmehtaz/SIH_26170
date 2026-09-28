"""
FastAPI application entry point.

AI-Driven Anomaly Detection in Component Burn-In & Screening
-------------------------------------------------------------
Engineering Prototype — Decision-support tool for QA/Reliability Engineers.
NOT an official ISRO system.

Run with:
    cd backend && uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from routers import data, analysis, reports

app = FastAPI(
    title="Burn-In Screening Anomaly Detection API",
    description=(
        "AI-driven anomaly detection and parametric drift prediction for "
        "high-reliability electronic component burn-in screening. "
        "PROTOTYPE — Not an official ISRO system."
    ),
    version="0.2.0",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(data.router)
app.include_router(analysis.router)
app.include_router(reports.router)


@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint supporting both root /health and /api/health."""
    return {
        "status": "healthy",
        "service": "burn-in-screening-api",
        "version": "0.2.0",
        "stage": "Data Foundation & Project Architecture",
    }
