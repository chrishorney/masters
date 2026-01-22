"""Admin endpoints for background jobs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Tournament
from app.services.background_jobs import BackgroundJobService

router = APIRouter()

# Global job service instance (in production, use proper job queue like Celery)
_job_services: dict[int, BackgroundJobService] = {}


@router.post("/jobs/start")
async def start_background_job(
    tournament_id: int = Query(..., description="Tournament ID"),
    interval_seconds: int = Query(60, description="Update interval in seconds"),
    db: Session = Depends(get_db)
):
    """Start background job for automatic score updates."""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Check if job already running
    if tournament_id in _job_services:
        return {
            "message": "Background job already running",
            "tournament_id": tournament_id,
            "status": "running"
        }
    
    # Create and start job service
    job_service = BackgroundJobService(db)
    await job_service.start(tournament_id, interval_seconds)
    _job_services[tournament_id] = job_service
    
    return {
        "message": "Background job started",
        "tournament_id": tournament_id,
        "interval_seconds": interval_seconds,
        "status": "started"
    }


@router.post("/jobs/stop")
async def stop_background_job(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """Stop background job."""
    if tournament_id not in _job_services:
        raise HTTPException(status_code=404, detail="Background job not found")
    
    job_service = _job_services[tournament_id]
    await job_service.stop()
    del _job_services[tournament_id]
    
    return {
        "message": "Background job stopped",
        "tournament_id": tournament_id,
        "status": "stopped"
    }


@router.get("/jobs/status")
async def get_job_status(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """Get background job status."""
    is_running = tournament_id in _job_services
    
    return {
        "tournament_id": tournament_id,
        "running": is_running,
        "status": "running" if is_running else "stopped"
    }


@router.post("/jobs/run-once")
async def run_job_once(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """Run sync and calculation once (manual trigger)."""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    job_service = BackgroundJobService(db)
    results = await job_service.run_once(tournament_id)
    
    return {
        "message": "Job executed successfully",
        "tournament_id": tournament_id,
        "results": results
    }
